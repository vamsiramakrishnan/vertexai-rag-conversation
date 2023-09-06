import os
import re
import time
from pathlib import Path
from tqdm import tqdm
from typing import List
from google.cloud import storage, logging as cloud_logging
import configparser

class ConfigPreProcessor:
    def __init__(self, bucket_name: str = 'your_bucket', project_id='your_project_id', local_path = "./", reprocess_kdb: bool = True, reprocess_routing: bool = True, enhance_kdb: bool = False, regen_kdb_embeddings: bool = True):
        self.storage_client = storage.Client()
        self.bucket_name = bucket_name[5:] if "gs://" in bucket_name else bucket_name
        self.bucket = self.storage_client.get_bucket(self.bucket_name)
        self.logging_client = cloud_logging.Client()
        self.logger = self.logging_client.logger("config_preprocessor_log")
        self.local_path = Path(local_path)
        self.reprocess_kdb = reprocess_kdb
        self.reprocess_routing = reprocess_routing
        self.enhance_kdb = enhance_kdb
        self.regen_kdb_embeddings = regen_kdb_embeddings

    def loadconfig_reprocess_kdb(self):
        return self.reprocess_kdb

    def loadconfig_reprocess_routing(self):
        return self.reprocess_routing

    def loadconfig_enhance_kdb(self):
        return self.enhance_kdb

    def loadconfig_regen_kdb_embeddings(self):
        return self.regen_kdb_embeddings        

    def load_preproc_config_parameters(self, config_file_folder: str = "raw_input", config_file_name: str = "preprocessor.conf"):
        try:
            gcs_config_path = Path(config_file_folder) / Path(config_file_name)
            gcs_config_bucket = self.storage_client.bucket(self.bucket_name)
            
            # Check if there is a config file in the first place in GCS bucket  
            print(f"Checking for preprocessor configuration file in bucket {self.bucket_name} in location {gcs_config_path.as_posix()}")
            if(gcs_config_bucket.blob(gcs_config_path.as_posix()).exists(self.storage_client)):
                local_file_path = self.local_path / config_file_folder
                local_file_name = self.local_path / config_file_folder / config_file_name
                local_file_path.mkdir(parents=True, exist_ok=True)
                
                print(f"Downloading preprocessor configuration file to {local_file_name.as_posix()}")
                gcs_config_bucket.blob(gcs_config_path.as_posix()).download_to_filename(local_file_name.as_posix())
                
                # Parse local copy of configuration files
                preprocessor_conf = configparser.ConfigParser()
                preprocessor_conf.read(local_file_name.as_posix())

                # Set configuration
                print(f"Preprocessor configuration is {list(preprocessor_conf.items('DEFAULT'))}")
                self.reprocess_kdb = preprocessor_conf['DEFAULT'].getboolean('reprocess_kdb', fallback=False)
                self.reprocess_routing = preprocessor_conf['DEFAULT'].getboolean('reprocess_routing', fallback=False)
                self.enhance_kdb = preprocessor_conf['DEFAULT'].getboolean('enhance_kdb', fallback=False)
                self.regen_kdb_embeddings = preprocessor_conf['DEFAULT'].getboolean('regen_kdb_embeddings', fallback=True)
            else:
                return None
        except Exception as e:
            print(f"error: {str(e)}")
            self.logger.log_struct(
                info={
                    'message': f"Failed to retrieve preprocessor configuration in bucket {gcs_config_bucket}, path {gcs_config_path}",
                    'error': str(e)
                },
                severity="ERROR")
            return None