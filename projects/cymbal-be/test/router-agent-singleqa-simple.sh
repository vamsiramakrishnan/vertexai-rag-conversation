#!/bin/bash

echo "Usage: sh test.sh -e <default local, other options ["dev","uat"]>"

env="local"
while getopts e: flag
do
    case "${flag}" in
        e) env=${OPTARG};;     
    esac
done

# Env settings
if [ $env = "dev" ]; then
    url="https://crbe-llm-dev-v1-gw1-ryazos7xna-et.a.run.app/routeragent"
    auth="x-api-key: AIzaSyDoghdbK7nAN4n8Aj7kk5X8sqpKp3b0yxY"
elif [ $env = "uat" ]; then
    url="https://crbe-llm-v1-gw1-ryazos7xna-et.a.run.app/routeragent"
    auth="x-api-key: AIzaSyDoghdbK7nAN4n8Aj7kk5X8sqpKp3b0yxY"
else
    url="http://localhost:8080/routeragent"
    auth="Authorization: Bearer $(gcloud auth print-identity-token)"
fi
echo "Selected Environment: $env";

current_q=0

timestamp=$(date +"%d%m%y%H%M")

while true; do
    read -p "Enter your question: " question

    current_q=$((current_q + 1))

    echo "Question" $question

    # Make the curl request in the background and measure the response time
    # Measure start time
    start_time=$(date +%s%N)    

    echo "Session ID $timestamp"__"$current_q"
    echo "Connecting to URL " $url
    
    # Make the curl request and measure the response time
    response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -H "$auth" \
        -d '{
            "llmRouterRequest": "'"$question"'",
            "requestMetadata": {
                "clientInfo": "Shanky",
                "sessionInfo": "'$timestamp'__'$current_q'",
                "userInfo": "0192787785"
            }           
        }' \
        "$url")

    # Measure end time
    end_time=$(date +%s%N)

    # Calculate response time in milliseconds
    response_time=$(( (end_time - start_time) / 1000000 ))         

    echo "UNMODIFIED" $response "\n" "Response Time - " $response_time

    echo 

done