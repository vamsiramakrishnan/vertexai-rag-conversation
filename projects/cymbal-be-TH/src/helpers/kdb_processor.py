from typing import Dict, Union, Optional
import logging
import pathlib
from google.cloud import storage
from langchain.document_loaders import DirectoryLoader, UnstructuredFileLoader
from langchain.vectorstores import FAISS
from helpers.vertexai import LoggingVertexAIEmbeddings
from helpers.logging_configurator import logger, request_origin


class KDBProcessor:
    def __init__(
        self,
        index_name: str = "cymbal_kb_index_EN",
        bucket_name: str = "gs://cymbal-kb-bucket",
        folder_name: str = "preprocessed_output",
        embeddings_non_english: Optional[bool] = False
    ):
        self.storage_client = storage.Client()
        self.bucket_name = bucket_name.replace("gs://", "").split("/")[0]
        self.index_name = index_name
        self.bucket = self.storage_client.get_bucket(self.bucket_name)
        self.folder_name = pathlib.Path(folder_name)
        self.local_path = self.folder_name
        self.local_index_file = self.local_path / self.index_name
        self.gcs_index_file = self.folder_name / self.index_name
        self.embedding_model = None
        if(embeddings_non_english):
            self.embedding_model = LoggingVertexAIEmbeddings(model_name='textembedding-gecko-multilingual@latest', task_type='RETRIEVAL_DOCUMENT')
        else:
            self.embedding_model = LoggingVertexAIEmbeddings(model_name='textembedding-gecko@latest', task_type='RETRIEVAL_DOCUMENT')        
        self.logger = self._setup_logger()
        self.copy_from_gcs()

    def _setup_logger(self):
        logger = logging.getLogger(__name__)
        return logger

    def log(self, level, message):
        self.logger.log(
            level, f"KDBProcessor - Origin: {request_origin.get()} | {message}"
        )

    def copy_from_gcs(self):
        blobs = self.bucket.list_blobs(prefix=str(self.gcs_index_file))

        if not self.local_index_file.exists():
            self.local_index_file.mkdir(parents=True, exist_ok=True)

        for blob in blobs:
            file_name = blob.name.split("/")[-1]
            destination_file_name = self.local_index_file / file_name
            blob.download_to_filename(str(destination_file_name))
            self.log(
                logging.INFO,
                f"Blob {blob.name} downloaded to {destination_file_name}.",
            )

    def load_embeddings(self):
        try:
            faiss = FAISS.load_local(str(self.local_index_file), self.embedding_model)
            self.log(
                logging.INFO, "Embeddings loading generated completed successfully."
            )
            return faiss
        except FileNotFoundError:
            self.log(
                logging.ERROR,
                "Could not find local embeddings, trying to create from raw text.",
            )
            return None
