#!/bin/bash

echo "Usage: sh test.sh -e <default local, other options ["uat"]>"

env="local"
while getopts e: flag
do
    case "${flag}" in
        e) env=${OPTARG};;     
    esac
done

# Function to display a progress bar
progress_bar() {
    width=50
    current_q=$1
    total_q=$2
    
    percentage_float=$(( current_q * 100 / total_q ))
    completed_float=$(( percentage_float * width / 100 ))
    remaining_float=$(( width - completed_float ))

    completed=$( printf "%.0f" $completed_float )
    remaining=$( printf "%.0f" $remaining_float )

    done_sub_bar=$(printf "%0.s*" $(seq 0 $completed))
    todo_sub_bar=$(printf "%0.s " $(seq 0 $remaining))
    echo "Progress : [${done_sub_bar}${todo_sub_bar}] ${percentage_float}%"
}

# Initialize variables for progress bar
current_line=0
bar_fill=""
bar_empty=$(printf "%0.s " $(seq 1 50))

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

# Default values
input_file="questions.txt"
timestamp=$(date +"%d%m%y%H%M")
concurrency=1
output_file="responses_$timestamp.txt"
input_file_tmp=$input_file"_"$timestamp.tmp
tpm=60

grep -v -e '^[[:blank:]]*$' questions.txt > $input_file_tmp

# Check if the file exists
if [ -f "$input_file_tmp" ]; then
    # Count the number of lines in the input file
    total_q=$(wc -l < "$input_file_tmp")
    echo "$total_q Queries to be processed.\n"
else
    echo "File not found: $input_file_tmp"
    exit 1
fi

current_q=0

echo "Connecting to URL " $url
echo "Connecting to URL " $url "\n" >> $output_file

echo "Processing start time $timestamp"

while IFS= read -r question || [ -n "$question" ]; do 
        
    current_q=$((current_q + 1))

    # Display current question and progress bar
    progress_bar $current_q $total_q

    # Make the curl request in the background and measure the response time
    # Measure start time
    start_time=$(date +%s%N)

    echo "Processing start time $timestamp" >> $output_file   
    
    echo "Session ID $timestamp"__"$current_q"
    echo "Session ID $timestamp"__"$current_q" >> $output_file

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

    echo "Question $current_q / $total_q - $question \nResponse - $response \nResponse Time - $response_time ms\n\n" >> $output_file 

done < "$input_file_tmp"

rm $input_file_tmp

echo "Processing end time $(date +"%d%m%y%H%M")"
echo "Processing end time $(date +"%d%m%y%H%M")"  >> $output_file