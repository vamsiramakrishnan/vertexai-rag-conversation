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

    # Make the curl request in the background and measure the response time
    # Measure start time
    start_time=$(date +%s%N)    

    echo "\nSession ID $timestamp"__"$current_q" "|" "Question :::" $question
    start_time=$(date +%s%N)    
    echo `date` "Connecting to URL " $url "\n"
    
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

    echo "Response Time - " $response_time
    echo $response | \
        python -c 'import json,sys; \
                   from parse_router_response import fn_print_router_response; \
                   obj=json.load(sys.stdin, strict=False);\
                   print(obj);\
                   print(f"\nRESPONSE ::: {fn_print_router_response(obj)}");'   

    parse_response=`echo $response | \
                    python -c 'import json,sys; \
                            from parse_router_response import fn_get_router_response; \
                            obj=json.load(sys.stdin, strict=False);\
                            print(obj);\
                            print(f"\nRESPONSE ::: {fn_get_router_response(obj)}");'`
    
    query_response=`echo $parse_response | awk -F"RESPONSE ::: " '/RESPONSE ::: /{print $2}'`

    user_1=$user_2
    user_2=$user_3
    user_3=$question
    bot_1=$bot_2
    bot_2=$bot_3
    bot_3=$query_response    

    echo

done