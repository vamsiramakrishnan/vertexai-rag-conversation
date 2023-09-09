import os
import re
import time
from pathlib import Path
from tqdm import tqdm
from typing import List
from google.cloud import storage, logging as cloud_logging
from langchain import PromptTemplate
from langchain.chains import AnalyzeDocumentChain
from langchain.chains.summarize import load_summarize_chain
from langchain.document_loaders import DirectoryLoader, UnstructuredFileLoader
from langchain.vectorstores import FAISS
from langchain.llms import VertexAI
from helpers.vertexai import VertexAIEmbeddings
from langchain.embeddings.base import Embeddings

class KDBPreProcessor:
    def __init__(self, embeddings: Embeddings, bucket_name: str = 'your_bucket', project_id='your_project_id', local_path = "./"):
        self.storage_client = storage.Client()
        self.embeddings = embeddings
        self.llm = VertexAI(temperature=0, max_output_tokens=1024)
        self.bucket_name = bucket_name[5:] if "gs://" in bucket_name else bucket_name
        self.bucket = self.storage_client.get_bucket(self.bucket_name)
        self.logging_client = cloud_logging.Client()
        self.logger = self.logging_client.logger("kdb_preprocessor_log")
        self.local_path = Path(local_path)

    def get_gcs_blob(self, gcs_path: str):
        return self.bucket.blob(gcs_path)

    def sync_from_gcs_to_local(self, gcs_path: str, file_filter: str = None):
        blobs = None
        try:
            listedblobs = self.bucket.list_blobs(prefix=gcs_path)

            if file_filter:
                blobs = [blob for blob in listedblobs if file_filter in blob.name]
                print(f"No. of files matching filter {file_filter} found - {len(blobs)}")
            else:
                blobs = listedblobs
                print(f"No. of files found, no filter applied - {len(blobs)}")
                
        except Exception as e:
            self.logger.log_struct(
                info={
                'message': f"Failed to list blobs in {gcs_path}",
                'gcs_path': gcs_path,
                'error': str(e)
                },
                severity="ERROR")
            return None

        for blob in tqdm(blobs, desc='Downloading blobs', unit='blob'):
            local_file_path = self.local_path / blob.name
            local_file_path.parent.mkdir(parents=True, exist_ok=True)
            try: 
                blob.download_to_filename(local_file_path.as_posix())
                self.logger.log_struct(
                    info = {'message': f"Downloaded {blob.name} to { local_file_path.as_posix()}", 
                    'local_file':  local_file_path.as_posix(), 
                    'gcs_file': blob.name}, 
                    severity="INFO")
            except Exception as e:
                self.logger.log_struct(
                    info={'message': f"Failed to download {blob.name}",
                      'local_file': local_file_path.as_posix(),
                      'gcs_file': blob.name,
                      'error': str(e)},
                severity="ERROR"
            )
            
    def sync_from_local_to_gcs(self, local_path: Path, gcs_path: str):
        print(f"Copying files in location {local_path} to {gcs_path}")
        for file in tqdm(local_path.rglob('*'), desc='Uploading files', unit='file'):
            if file.is_file():
                try:
                    relative_path = file.relative_to(local_path)
                    relative_path_posix = relative_path.as_posix()
                    gcs_file_name = f"{gcs_path}/{relative_path_posix}"
                    blob = self.bucket.blob(gcs_file_name)
                    blob.upload_from_filename(file.as_posix())
                    self.logger.log_struct(
                        info={
                            'message': f"Uploaded {file.as_posix()} to {gcs_file_name}",
                            'local_file': file.as_posix(),
                            'gcs_file': gcs_file_name
                        },
                        severity="INFO"
                    )
                except Exception as e:
                    self.logger.log_struct(
                        info={
                            'message': f"Failed to upload {file.as_posix()} to {gcs_file_name}",
                            'local_file': file.as_posix(),
                            'gcs_file': gcs_file_name,
                            'error': str(e)
                        },
                        severity="ERROR"
                    )

    def generate_and_persist_embeddings(self, docs: List[str], vector_db_gcs_path: Path, glob_expr: str):
        extracted_language = self._extract_language(glob_expr)
        index_name = "cymbal_kb_index_" + extracted_language
        
        # Create a new directory for these embeddings
        local_index_dir = self.local_path / vector_db_gcs_path
        local_index_dir.mkdir(parents=True, exist_ok=True)
        
        local_index_path = local_index_dir / index_name
        remote_index_path = vector_db_gcs_path / index_name
        db = FAISS.from_documents(documents=docs, embedding=self.embeddings)
        db.save_local(local_index_path.as_posix())
        
        # Sync the index directory to GCS
        self.sync_from_local_to_gcs(local_index_path, remote_index_path.as_posix())
        self.logger.log_struct(info = {'message': 'Embeddings generation completed successfully.', 'index_name': index_name, 'bucket_name': self.bucket_name}, severity="INFO")
        return db


    def _extract_language(self, glob_expr: str):
        match = re.search(r"_([A-Z]{2})\.txt$", glob_expr)
        language = match.group(1) if match else None
        if not language:
            raise ValueError("Language extracted from Knowledgebase Cannot be Empty")
        return language

    def enhance_doc(self, doc, analyze_document_chain, enhanced_dir: Path) -> None:
        source_path = Path(doc.metadata["source"])
        # Build enhanced path to mimic the subdirectory structure of the source.
        enhanced_path = enhanced_dir.joinpath(*source_path.parts[1:])
        enhanced_path.parent.mkdir(parents=True, exist_ok=True)  # Ensure subdirectories exist.

        language_detected = "Indonesian" if "_ID" in source_path.name else "English"
        
        with source_path.open('r') as f_orig, enhanced_path.open('w') as f_enhanced:
            faq_doc = f_orig.read()
            enhanced_doc = analyze_document_chain.run({"input_document": faq_doc, "language_detected": language_detected})
            f_enhanced.write(f"{enhanced_doc}\n\nORIGINAL DOC: \n{faq_doc}")
            
        self.logger.log_struct(info={
            'message': f'Enhanced document: {source_path.as_posix()} and wrote to {enhanced_path.as_posix()}',
            'source': source_path.as_posix(),
            'enhanced': enhanced_path.as_posix(),
            'language': language_detected
        }, severity = "INFO")


    def enhance_docs(self, docs: List[str], analyze_document_chain, enhanced_dir: Path):
        for doc in tqdm(docs, desc="Enhancing FAQs", unit="doc"):
            self.enhance_doc(doc, analyze_document_chain, enhanced_dir)
            time.sleep(0.1)

    def process_kdb(self, input_kdb_gcs_path: str, force_enhance: bool, enhanced_kdb_gcs_path: Path, glob_expr: str):

        local_dir = self.local_path / input_kdb_gcs_path
        enhanced_dir = self.local_path / enhanced_kdb_gcs_path
        enhanced_dir.mkdir(parents=True, exist_ok=True)

        if force_enhance:
            self.sync_from_gcs_to_local(input_kdb_gcs_path, file_filter=glob_expr.split('_', 1)[1])
            loader = DirectoryLoader(local_dir.as_posix(), glob=glob_expr, loader_cls=UnstructuredFileLoader, show_progress=True)
            docs = loader.load()
            enhancement_template = """
            You are an text analysis, summarization and question generation expert.
            1. Write a Factual Document Summary in {language_detected} in section Summary: 
            2. Generate Questions in {language_detected} that Document can factually answer in section Questions: 
            Document:
            {text}
            
            Summary:
            Questions: 

            """
            faq_enhancement_prompt = PromptTemplate(template=enhancement_template, input_variables=["text", "language_detected"])
            summary_chain = load_summarize_chain(self.llm, chain_type="stuff", prompt=faq_enhancement_prompt)
            analyze_document_chain = AnalyzeDocumentChain(combine_docs_chain=summary_chain)
            self.enhance_docs(docs, analyze_document_chain, enhanced_dir)
            self.sync_from_local_to_gcs(enhanced_dir, enhanced_kdb_gcs_path.as_posix())
            loader = DirectoryLoader(enhanced_dir.as_posix(), glob=glob_expr, loader_cls=UnstructuredFileLoader, show_progress=True)
            docs = loader.load()
        else:
            self.sync_from_gcs_to_local(input_kdb_gcs_path, file_filter=glob_expr.split('_', 1)[1])
            loader = DirectoryLoader(local_dir.as_posix(), glob=glob_expr, loader_cls=UnstructuredFileLoader, show_progress=True)
            docs = loader.load()

        return docs


    def create_embeddings(self, input_kdb_gcs_path="raw_input", enhanced_kdb_gcs_path="enhanced_input", vector_db_gcs_path="preprocessed_output", force_enhance=True, force_regenerate=True, glob_expr="*"):
        docs = self.process_kdb(input_kdb_gcs_path, force_enhance, Path(enhanced_kdb_gcs_path),  glob_expr)
        if force_regenerate:
            return self.generate_and_persist_embeddings(docs, Path(vector_db_gcs_path), glob_expr)
        else:
            return True
