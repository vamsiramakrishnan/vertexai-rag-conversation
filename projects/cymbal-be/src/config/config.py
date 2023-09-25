import configparser
import google.auth


class AppConfigKeyNotFoundError(Exception):
    """Exception raised when a key is not found in the application configuration."""
    pass

class AppConfig:
    """Class to handle application configuration."""
    def __init__(self, filename):
        """Initialize AppConfig with a configuration file."""
        self._config = configparser.ConfigParser()
        self._config.read(filename)
        self._load_config()

    def _get_config_value(self, section, key):
        """Get a configuration value from a given section and key."""
        if self._config.has_option(section, key):
            return self._config.get(section, key)
        raise AppConfigKeyNotFoundError(f"{key} not found in {section}")

    def _load_config(self):
        """Load configuration values from the configuration file."""
        self.project_id = google.auth.default()[1]
        self.region = self._get_config_value("AppConfig", "REGION")
        self.bucket_prefix = self._get_config_value("AppConfig", "BUCKET_PREFIX")
        self.deployment_env = self._get_config_value("AppConfig", "DEPLOYMENT_ENV")
        self.index_en = self._get_config_value("AppConfig", "INDEX_EN")
        self.index_id = self._get_config_value("AppConfig", "INDEX_ID")
        self.feature_kdb_id = self._get_config_value("AppConfig", "FEATURE_KDB_ID")
        self.feature_chat_bison = self._get_config_value("AppConfig", "FEATURE_CHAT_BISON")
        self.feature_llmlang_detect = self._get_config_value("AppConfig", "FEATURE_LLMLANG_DETECT")
        self.feature_llmlang_translate = self._get_config_value("AppConfig", "FEATURE_LLMLANG_TRANSLATE")
        self.feature_reframe_query = self._get_config_value("AppConfig", "FEATURE_REFRAME_QUERY")
        self.feature_reformat_answer = self._get_config_value("AppConfig", "FEATURE_REFORMAT_ANSWER")
        self.config_msg_history = self._get_config_value("AppConfig", "CONFIG_MSG_HISTORY")

    def get_config_as_string(self):
        """Return the configuration values as a string."""
        return f"""
            PROJECT_ID - {self.project_id}
            REGION - {self.region}
            BUCKET_PREFIX - {self.bucket_prefix}
            DEPLOYMENT_ENV - {self.deployment_env}
            INDEX_EN - {self.index_en}
            INDEX_ID - {self.index_id}
            FEATURE_KDB_ID - {self.feature_kdb_id}
            FEATURE_CHAT_BISON - {self.feature_chat_bison}
            FEATURE_LLMLANG_DETECT = {self.feature_llmlang_detect}
            FEATURE_LLMLANG_TRANSLATE = {self.feature_llmlang_translate}
            FEATURE_REFRAME_QUERY = {self.feature_reframe_query}
            FEATURE_REFORMAT_ANSWER = {self.feature_reformat_answer}
            CONFIG_MSG_HISTORY = {self.config_msg_history}            
            """        

class AppConfigContext:
    """Class to handle the context of the application configuration."""
    def __init__(self, appconfig: AppConfig):
        """Initialize AppConfigContext with an AppConfig instance."""
        self.appconfig = appconfig

def initialize_appconfig(
    configfile="./config/config.ini"
    #configfile="/home/user/repos/genai-e2e-demos/dev/GenAI-E2E-Demos/projects/cymbal-be/src/config/config.ini"
):
    """Initialize the application configuration context."""
    return AppConfigContext(AppConfig(configfile))

appconfigcontext = initialize_appconfig()
config_context = appconfigcontext.appconfig
