#!/bin/bash

# Function to prettify JSON using Python
prettify_json() {
    python -c "import json, sys; print(json.dumps(json.load(sys.stdin), indent=4))"
}

# Function to display a progress bar
progress_bar() {
    local width=50
    local percentage=$1
    local completed=$(( percentage * width / 100 ))
    local remaining=$(( width - completed ))
    printf "\r[%-${completed}s%${remaining}s] %d%%" "$bar_fill" "$bar_empty" "$percentage"
}

# Function to display current question and progress
display_question() {
    local question_number=$1
    local total_questions=$2
    local question=$3
    printf "Question %d/%d: %s\n" "$question_number" "$total_questions" "$question"
}

# Default values
url="http://localhost:8000/routeragent"
input_file="questions.txt"
timestamp=$(date +"%d%m%y_%H%M")
output_folder="output_$timestamp"
concurrency=1

# Parse command-line arguments
while [[ $# -gt 0 ]]; do
    key="$1"
    case $key in
        --input-file)
        input_file="$2"
        shift
        shift
        ;;
        --url)
        url="$2"
        shift
        shift
        ;;
        --output-folder)
        output_folder="$2"
        shift
        shift
        ;;
        --concurrency)
        concurrency="$2"
        shift
        shift
        ;;
        *)
        echo "Unknown option: $1"
        exit 1
        ;;
    esac
done

# Check if input file is provided
if [[ ! -f $input_file ]]; then
    echo "Input file not found: $input_file"
    exit 1
fi

# Create output folder with timestamp if it doesn't exist
mkdir -p "$output_folder"

# Count the number of lines in the input file
total_lines=$(wc -l < "$input_file")

# Initialize variables for progress bar
current_line=0
bar_fill=""
bar_empty=$(printf "%0.s " $(seq 1 50))

# Function to append data to JSON file with header
append_to_json() {
    local file=$1
    local data=$2

    # Check if file exists
    if [[ ! -f $file ]]; then
        echo -e "[$data]" > "$file"
    else
        # Remove the trailing ']' from the file
        sed -i '$ d' "$file"
        # Append the new data
        echo -e ",\n$data\n]" >> "$file"
    fi
}

# Read questions from input file and send requests concurrently
while IFS= read -r question || [[ -n "$question" ]]; do
    # Increment the line counter
    ((current_line++))

    # Display current question and progress bar
    display_question "$current_line" "$total_lines" "$question"
    progress=$(( current_line * 100 / total_lines ))
    progress_bar "$progress"

    # Make the curl request in the background and measure the response time
    (
        # Measure start time
        start_time=$(date +%s%N)

        # Make the curl request
        response=$(curl -s -X POST \
            -H "Content-Type: application/json" \
            -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
            -d '{
                "llmRouterRequest": "'"$question"'",
                "requestMetadata": {
                    "metadataField1": "value1",
                    "metadataField2": "value2"
                },
                "developerOptions": {
                    "option1": "value1",
                    "option2": "value2"
                }
            }' \
            "$url")

        # Measure end time
        end_time=$(date +%s%N)

        # Calculate response time in milliseconds
        response_time=$(( (end_time - start_time) / 1000000 ))

        # Prettify the response body
        pretty_response=$(echo "$response" | prettify_json)

        # Prepare the response data as a JSON object
        response_data=$(echo "$response" | jq -c --arg q "$question" --arg rt "$response_time" '. | .question = $q | .responseTime = $rt')

        # Parse the response and append to the corresponding JSON file
        response_type=$(echo "$response" | jq -r '.responseType')
        case $response_type in
            "smallTalk")
                output_file="$output_folder/smallTalkResponse.json"
                original_user_query=$(echo "$response" | jq -r '.originalUserQuery')
                answer=$(echo "$response" | jq -r '.smallTalkResponse.answer')
                response_data=$(echo "$response_data" | jq --arg auq "$original_user_query" --arg a "$answer" '. | .originalUserQuery = $auq | .answer = $a')
                ;;
            "staticKnowledgebaseQnA")
                output_file="$output_folder/staticKnowledgebaseQnAResponse.json"
                original_user_query=$(echo "$response" | jq -r '.originalUserQuery')
                topic=$(echo "$response" | jq -r '.staticKnowledgebaseQnAResponse.topic')
                sub_topic=$(echo "$response" | jq -r '.staticKnowledgebaseQnAResponse.subTopic')
                answer=$(echo "$response" | jq -r '.staticKnowledgebaseQnAResponse.answer')
                response_data=$(echo "$response_data" | jq --arg auq "$original_user_query" --arg t "$topic" --arg st "$sub_topic" --arg a "$answer" '. | .originalUserQuery = $auq | .topic = $t | .subTopic = $st | .answer = $a')
                ;;
            "dynamicAPIFlow")
                output_file="$output_folder/dynamicAPIFlowResponse.json"
                original_user_query=$(echo "$response" | jq -r '.originalUserQuery')
                flow_type=$(echo "$response" | jq -r '.dynamicAPIFlowResponse.flowType')
                sub_flow_type=$(echo "$response" | jq -r '.dynamicAPIFlowResponse.subFlowType')
                response_data=$(echo "$response_data" | jq --arg auq "$original_user_query" --arg ft "$flow_type" --arg sft "$sub_flow_type" '. | .originalUserQuery = $auq | .flowType = $ft | .subFlowType = $sft')
                ;;
            "fallbackIntent")
                output_file="$output_folder/fallbackIntentResponse.json"
                original_user_query=$(echo "$response" | jq -r '.originalUserQuery')
                response_data=$(echo "$response_data" | jq --arg auq "$original_user_query" '. | .originalUserQuery = $auq')
                ;;
            *)
                echo "Unknown response type: $response_type"
                ;;
        esac

        # Append the response data to the JSON file
        append_to_json "$output_file" "$response_data"
    ) &

    # Limit the concurrency by waiting for background processes
    if (( current_line % concurrency == 0 )); then
        wait
    fi
done < "$input_file"

# Wait for any remaining background processes
wait

# Print a new line to clear the progress bar
echo

echo "Processing complete. Results saved in $output_folder."
