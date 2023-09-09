import configparser
import google.auth


class AppConfigKeyNotFoundError(Exception):
    pass

class AppConfig:
    def __init__(self, filename):
        self._config = configparser.ConfigParser()
        self._config.read(filename)
        self._load_config()

    def _get_config_value(self, section, key):
        if self._config.has_option(section, key):
            return self._config.get(section, key)
        raise AppConfigKeyNotFoundError(f"{key} not found in {section}")

    def _load_config(self):
        self.PROJECT_ID = google.auth.default()[1]
        self.REGION = self._get_config_value("AppConfig", "REGION")
        self.BUCKET_PREFIX = self._get_config_value("AppConfig", "BUCKET_PREFIX")
        self.DEPLOYMENT_ENV = self._get_config_value("AppConfig", "DEPLOYMENT_ENV")
        self.INDEX_EN = self._get_config_value("AppConfig", "INDEX_EN")
        self.INDEX_ID = self._get_config_value("AppConfig", "INDEX_ID")
        self.FEATURE_KDB_ID = self._get_config_value("AppConfig", "FEATURE_KDB_ID")
        self.FEATURE_CHAT_BISON = self._get_config_value("AppConfig", "FEATURE_CHAT_BISON")
        self.FEATURE_LLMLANG_DETECT = self._get_config_value("AppConfig", "FEATURE_LLMLANG_DETECT")
        self.FEATURE_LLMLANG_TRANSLATE = self._get_config_value("AppConfig", "FEATURE_LLMLANG_TRANSLATE")
        self.FEATURE_REFRAME_QUERY = self._get_config_value("AppConfig", "FEATURE_REFRAME_QUERY")
        self.FEATURE_REFORMAT_ANSWER = self._get_config_value("AppConfig", "FEATURE_REFORMAT_ANSWER")
        self.CONFIG_MSG_HISTORY = self._get_config_value("AppConfig", "CONFIG_MSG_HISTORY")

    def getConfigAsString(self):
        return f"""
            PROJECT_ID - {self.PROJECT_ID}
            REGION - {self.REGION}
            BUCKET_PREFIX - {self.BUCKET_PREFIX}
            DEPLOYMENT_ENV - {self.DEPLOYMENT_ENV}
            INDEX_EN - {self.INDEX_EN}
            INDEX_ID - {self.INDEX_ID}
            FEATURE_KDB_ID - {self.FEATURE_KDB_ID}
            FEATURE_CHAT_BISON - {self.FEATURE_CHAT_BISON}
            FEATURE_LLMLANG_DETECT = {self.FEATURE_LLMLANG_DETECT}
            FEATURE_LLMLANG_TRANSLATE = {self.FEATURE_LLMLANG_TRANSLATE}
            FEATURE_REFRAME_QUERY = {self.FEATURE_REFRAME_QUERY}
            FEATURE_REFORMAT_ANSWER = {self.FEATURE_REFORMAT_ANSWER}
            CONFIG_MSG_HISTORY = {self.CONFIG_MSG_HISTORY}            
            """        

class AppConfigContext:
    def __init__(self, appconfig: AppConfig):
        self.appconfig = appconfig

def initialize_appconfig(
    configfile="./config/config.ini"
    # configfile="/home/user/repos/genai-e2e-demos/dev/GenAI-E2E-Demos/projects/cymbal-be/src/config/config.ini"
):
    return AppConfigContext(AppConfig(configfile))

appconfigcontext = initialize_appconfig()
configcontex = appconfigcontext.appconfig