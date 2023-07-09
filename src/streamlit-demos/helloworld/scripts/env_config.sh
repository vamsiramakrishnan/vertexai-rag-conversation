. ./env_settings.sh

# login and set default project
gcloud config set project $PROJECT_ID
gcloud auth login
gcloud auth application-default login
gcloud auth application-default set-quota-project $PROJECT_ID