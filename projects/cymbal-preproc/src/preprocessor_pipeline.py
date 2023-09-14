from preprocessors.kdb_preprocessor import KDBPreProcessor
from preprocessors.config_preprocessor import ConfigPreProcessor
from preprocessors.routing_example_preprocessor import SemanticSimilarityExamplePreprocessor
from langchain.vectorstores import FAISS
from helpers.vertexai import VertexAIEmbeddings
import google.auth
import vertexai
import configparser

class Config:
    def __init__(self, filename):
        config = configparser.ConfigParser()
        config.read(filename)
        self.PROJECT_ID = google.auth.default()[1]
        self.REGION = config.get('AppConfig', 'REGION')
        self.BUCKET_PREFIX = config.get('AppConfig', 'BUCKET_PREFIX')
        self.DEPLOYMENT_ENV = config.get('AppConfig', 'DEPLOYMENT_ENV')        
        self.BUCKET_NAME = "gs://" + self.PROJECT_ID + "-" + self.BUCKET_PREFIX + "-" + self.DEPLOYMENT_ENV

#config = Config('/home/user/repos/genai-e2e-demos/dev/GenAI-E2E-Demos/projects/cymbal-preproc/src/config.ini')
config = Config('config.ini')
vertexai.init(project=config.PROJECT_ID, location=config.REGION)

# Load Preprocessor Configuration
config_preprocessor = ConfigPreProcessor(bucket_name = config.BUCKET_NAME, project_id = config.PROJECT_ID)
config_preprocessor.load_preproc_config_parameters()

## KDB enhancement and embeddings generation settings
kdb_reprocessing = config_preprocessor.loadconfig_reprocess_kdb()
routing_reprocessing = config_preprocessor.loadconfig_reprocess_routing()
# Enhance KDB with summary and questions that can be answered. EXPERIMENTAL
force_enhance_kdb = config_preprocessor.loadconfig_enhance_kdb()
# Default to True to ensure embeddings are regenerated. False only during CODE TESTING
force_regenerate_embeddings = config_preprocessor.loadconfig_regen_kdb_embeddings()

print(f"Configuration Settings reprocess_kdb - {kdb_reprocessing}, reprocess_routing - {routing_reprocessing}, enhance_kdb - {force_enhance_kdb}, regen_kdb_embeddings - {force_regenerate_embeddings}")

# KDB embeddings generation flow
if kdb_reprocessing:
    KDBPreProcessor(embeddings = VertexAIEmbeddings(requests_per_minute=600, model_name='textembedding-gecko@latest', task_type='RETRIEVAL_DOCUMENT'), bucket_name = config.BUCKET_NAME, project_id = config.PROJECT_ID).create_embeddings(force_enhance=force_enhance_kdb, force_regenerate = force_regenerate_embeddings, glob_expr = "**/*_EN.txt")
    KDBPreProcessor(embeddings = VertexAIEmbeddings(requests_per_minute=600, model_name='textembedding-gecko-multilingual@latest', task_type='RETRIEVAL_DOCUMENT'), bucket_name = config.BUCKET_NAME, project_id = config.PROJECT_ID).create_embeddings(force_enhance=force_enhance_kdb, force_regenerate = force_regenerate_embeddings, glob_expr = "**/*_ID.txt")
    KDBPreProcessor(embeddings = VertexAIEmbeddings(requests_per_minute=600, model_name='textembedding-gecko-multilingual@latest', task_type='RETRIEVAL_DOCUMENT'), bucket_name = config.BUCKET_NAME, project_id = config.PROJECT_ID).create_embeddings(force_enhance=force_enhance_kdb, force_regenerate = force_regenerate_embeddings, glob_expr = "**/*_TH.txt")    

# Routing examples embeddings generation flow
if routing_reprocessing:
    ss_preprocessor = SemanticSimilarityExamplePreprocessor.load_and_process_data(bucket_name = config.BUCKET_NAME, embeddings = VertexAIEmbeddings(requests_per_minute=600, model_name='textembedding-gecko@latest', task_type='SEMANTIC_SIMILARITY'), vectorstore_cls = FAISS, routing_example_filename = "nlu-router-examples.xlsx", routing_example_fileheader = ["Query", "Intent"], index_name = "nlp_router_examples")
    ss_preprocessor_dynamic = SemanticSimilarityExamplePreprocessor.load_and_process_data(bucket_name = config.BUCKET_NAME, embeddings = VertexAIEmbeddings(requests_per_minute=600, model_name='textembedding-gecko@latest', task_type='SEMANTIC_SIMILARITY'), vectorstore_cls = FAISS, routing_example_filename = "nlu-router-examples-dynamic.xlsx", routing_example_fileheader = ["Query", "Response"], index_name = "nlp_router_examples_dynamic")
