#!/bin/bash

# Function to prettify JSON using Python
prettify_json() {
    python -c "import json, sys; print(json.dumps(json.load(sys.stdin), indent=4))"
}

# Function to parse and display response based on response type
parse_response() {
    #local response=$1
    response=$1
    local response_type=$(echo "$response" | jq -r '.responseType')

    case $response_type in
        "smallTalk")
            answer=$(echo "$response" | jq -r '.smallTalkResponse.answer')
            echo "Answer: $answer"
            ;;
        "staticKnowledgebaseQnA")
            answer=$(echo "$response" | jq -r '.staticKnowledgebaseQnAResponse.answer')
            echo "Answer: $answer"
            ;;
        "dynamicAPIFlow")
            flow_type=$(echo "$response" | jq -r '.dynamicAPIFlowResponse.flowType')
            echo "Flow Type: $flow_type"
            ;;
        "fallbackIntent")
            response_data=$(echo "$response" | jq '.fallbackIntentResponse.fallBackResponse')
            echo "Response Data: $response_data"
            ;;
        *)
            echo "Unknown response type: $response_type"
            ;;
    esac
}

# Default values to initialize
url="http://localhost:8000/routeragent"

while getopts u: flag
do
    case "${flag}" in
        u) url=${OPTARG};;
    esac
done

echo "Connecting to URL - " $url

while true; do
    read -p "Enter your question: " question

    # Make the curl request and measure the response time
    response=$(curl -s -X POST \
        -H "Content-Type: application/json" \
        -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
        -d '{
            "llmRouterRequest": "'"$question"'",
            "requestMetadata": {
                "clientInfo": "kata.ai",
                "sessionInfo": "123456",
                "userInfo":"0192787785"
            },
            "developerOptions": {
                "option1": "value1",
                "option2": "value2"
            }
        }' \
        "$url")

    # Prettify the response body
    pretty_response=$(echo "$response" | prettify_json)

    # Display the parsed response
    parse_response "$response"

    echo
done


