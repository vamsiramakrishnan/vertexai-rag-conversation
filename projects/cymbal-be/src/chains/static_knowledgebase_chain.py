from typing import Optional
import logging

from helpers.vertexai import LoggingVertexAI, LoggingVertexAIChat
from helpers.vertexai import LoggingVertexAIEmbeddings
from helpers.kdb_processor import KDBProcessor
from langchain.vectorstores.base import VectorStoreRetriever
from langchain.chains import RetrievalQA
from langchain.retrievers import ContextualCompressionRetriever
from langchain.retrievers.document_compressors import DocumentCompressorPipeline
from langchain.retrievers.document_compressors import EmbeddingsFilter
from prompts.retrieval_prompt import RETRIEVAL_PROMPT
from helpers.logging_configurator import logger, request_origin
from langchain.text_splitter import CharacterTextSplitter
from config.config import configcontex
from langchain.llms.vertexai import _VertexAICommon


class StaticKnowledgebaseChain:
    """Creates a chain for question-answering tasks based on VertexAI, with logging."""

    def __init__(
        self,
        bucket_name: str = "gs://cymbal-kb-bucket",
        index_name: str = "cymbal_kb_index_EN",
        llm: Optional[_VertexAICommon] = None,
        search_type: str = "similarity",
        k: int = 3,
        retriever: Optional[VectorStoreRetriever] = None,
        retrieval_prompt: Optional[str] = RETRIEVAL_PROMPT,
        qa_chain: Optional[RetrievalQA] = None,
        chain_type: Optional[str] = "stuff",
        contextual_compression_enabled: Optional[bool] = True,
        vertexai_params: Optional[dict] = {
            "temperature": 0.1,
            "max_output_tokens": 400,
            "top_p": 0.5,
            "top_k": 20,
        },
        similarity_threshold: Optional[float] = 0.7,
        embeddings_non_english: Optional[bool] = false
    ):
        self.logger = self._setup_logger()
        self.bucket_name = bucket_name
        self.index_name = index_name
        if(configcontex.FEATURE_CHAT_BISON == "True"):
            self.llm = llm if llm else LoggingVertexAIChat(**vertexai_params)
        else:
            self.llm = llm if llm else LoggingVertexAI(**vertexai_params)
        self.search_type = search_type
        self.k = k
        self.retriever = retriever
        self.retrieval_prompt = retrieval_prompt
        self.chain_type = chain_type
        self.compression_retriever = None
        self.similarity_threshold = similarity_threshold
        self.contextual_compression_enabled = contextual_compression_enabled
        self.qa_chain = (
            qa_chain
            if qa_chain
            else self.create_qa_chain(
                contextual_compression_enabled=contextual_compression_enabled
            )
        )
        self.embeddings_non_english = embeddings_non_english
        self.embeddings = None
        if(embeddings_non_english):
            self.embeddings = VertexAIEmbeddings(model_name='textembedding-gecko-multilingual@latest', task_type='RETRIEVAL_QUERY')
        else:
            self.embeddings = VertexAIEmbeddings(model_name='textembedding-gecko@latest', task_type='RETRIEVAL_QUERY')

    def _setup_logger(self):
        logger = logging.getLogger(__name__)
        return logger

    def log(self, level, message):
        self.logger.log(
            level, f"StaticKnowledgebaseChain - Origin: {request_origin.get()} | {message}"
        )

    def create_retriever(self):
        kdb_processor = KDBProcessor(
            bucket_name=self.bucket_name, index_name=self.index_name, embeddings_non_english=self.embeddings_non_english
        )
        vector_db = kdb_processor.load_embeddings()
        return vector_db.as_retriever(search_type=self.search_type, k=self.k)

    def create_compressor_retriever(self):        
        embeddings_filter = EmbeddingsFilter(
            embeddings=self.embeddings, similarity_threshold=self.similarity_threshold
        )
        text_splitter = CharacterTextSplitter(
            separator="\n\n", chunk_size=256, chunk_overlap=0, length_function=len
        )
        pipeline_compressor = DocumentCompressorPipeline(
            transformers=[text_splitter, embeddings_filter]
        )
        return ContextualCompressionRetriever(
            base_compressor=pipeline_compressor, base_retriever=self.retriever
        )

    def create_qa_chain(self, contextual_compression_enabled: bool = False):
        """Create a QA chain, potentially initializing the retriever."""
        try:
            if self.retriever is None:
                self.retriever = self.create_retriever()
                self.compression_retriever = self.create_compressor_retriever()
            else:
                self.compression_retriever = self.retriever

            retriever_to_use = (
                self.compression_retriever
                if contextual_compression_enabled
                else self.retriever
            )
            return RetrievalQA.from_chain_type(
                llm=self.llm,
                retriever=retriever_to_use,
                chain_type=self.chain_type,
                chain_type_kwargs={"prompt": self.retrieval_prompt},
            )
        except Exception as e:
            self.log(
                logging.ERROR,
                f"An error occurred while creating the QA chain: {str(e)}",
            )
            return None

    def process_query(self, input_query: str, return_only_outputs: bool = False):
        """Process a query using the QA chain and log the process."""
        if not self.qa_chain:
            self.log(
                logging.ERROR,
                "No QA Chain available. Ensure it is created successfully before processing queries.",
            )
            #return None
            self.qa_chain = self.create_qa_chain(contextual_compression_enabled=self.contextual_compression_enabled)
            self.log(
                logging.WARNING,
                "No QA Chain available. Recreating before processing queries.",
            )            

        try:
            compressed_docs = self.compression_retriever.get_relevant_documents(
                input_query
            )
            compressed_docs_metadata = [
                compressed_doc.metadata["source"] for compressed_doc in compressed_docs
            ]
            self.log(logging.DEBUG, f"Metadata: {compressed_docs_metadata}")
            response = self.qa_chain(
                {"query": input_query}, return_only_outputs=return_only_outputs
            )
            return response["result"]
        except Exception as e:
            self.log(
                logging.ERROR, f"An error occurred while processing the query: {str(e)}"
            )
            return None
