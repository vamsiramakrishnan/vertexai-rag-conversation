#!/bin/bash

while true; do
    echo "Enter your customer question (or 'exit' to quit):"
    read -r question

    if [[ "$question" == "exit" ]]; then
        echo "Exiting..."
        break
    fi

    # Replace the <API_ENDPOINT> with the actual endpoint URL
    response=$(curl --location --request POST 'http://localhost:8000/chatagent' \
        --header 'Accept: application/json' \
        --header 'Content-Type: application/json' \
        --header 'x-api-key: YOUR_API_KEY' \
        --data-raw '{
            "llmChatRequest": {
                "context": "You are a customer care bot who will respond to customer query in CUSTOMER_QUESTION: using information in CUSTOMER_INFORMATION: in language XXXLANGUAGEXXX \n Follow the GENERAL_RULES and RESPONSE_RULES listed below. \nGENERAL_RULES - Use the following rules while framing your general response 1. Always answer in the language of the customer. 2. Always be polite. 3. If you cannot find the information below, say please ask user to check via MyIM3 portal. 4. Always provide main balance information in IDR. \n RESPONSE_RULES - Rules for answering query 1. For any general enquiry on balance or quota include the main balance, and all remaining quota buckets with expiry dates 2. For any enquiry specific to a particular type of balance or quota, respond with all the specific quota balances that match the type of balance in request. \n CUSTOMER_INFORMATION - {\"result\":1,\"arResult\":{\"ServiceClass\":\"696\",\"Msisdn\":\"6285703460765\",\"Services\":{\"Service\":[{\"ServiceName\":\"SPIM33GBJabar&Jateng(kecualiBotabek&Sukabumi)\",\"ServiceType\":\"MainPackage\",\"ServiceDescription\":\"SPIM33GBJabar&Jateng(kecualiBotabek&Sukabumi)\",\"StartDate\":\"20230224\",\"EndDate\":\"20230528\",\"Sms\":[{\"Name\":\"FlagCounterBonusSPData\",\"Description\":\"FlagCounterBonusSPData\",\"ExpiryDate\":\"20240219\",\"InitialQuota\":\"0SMS\",\"RemainingQuota\":\"5 SMS\",\"BenefitType\":\"SMS\"},{\"Name\":\"FlagCounterBonusSPData\",\"Description\":\"FlagCounterBonusSPData\",\"ExpiryDate\":\"20240219\",\"InitialQuota\":\"0 SMS\",\"RemainingQuota\":\"0 SMS\",\"BenefitType\":\"SMS\"}]}]},\"SubsType\":\"PREPAID\",\"CustBalanceInfo\":\"30000\",\"SimType\":\"USIM\",\"ExpiredDate\":\"20230528\",\"TerminateDate\":\"20230627\"},\"desc\":\"success\"} \n CUSTOMER_QUESTION: '"$question"'",
                "examples": [
                    {
                        "input": {
                            "content": "Check account OR check balance"
                        },
                        "output": {
                            "content": "Your main balance is IDR 70721. You have 51200 MB of data, 4991.00009982 MNT of voice calls to IM3 Ooredoo & Tri, 47.00000094 MNT of voice calls to other operators, and 44 SMS."
                        }
                    },
                    {
                        "input": {
                            "content": "saldo saya"
                        },
                        "output": {
                            "content": "Saldo utama Anda adalah Rp 70721. Anda memiliki 51200 MB data, 4991.00009982 MNT panggilan suara ke IM3 Ooredoo & Tri, 47.00000094 MNT panggilan suara ke operator lain, dan 44 SMS."
                        }
                    }
                ],
                "messages": [],
                "parameters": {
                    "temperature": 0.2,
                    "maxOutputTokens": 1024,
                    "topP": 0.8,
                    "topK": 40
                }
            },
            "requestMetadata": {
                "clientInfo": "Kata.ai",
                "sessionInfo": "6285795033685",
                "userInfo": "6285795033685"
            },
            "developerOptions": {
                "enableBasicLogging": false
            }
        }' 2>/dev/null >/dev/null)  # Redirect both stdout and stderr to /dev/null

    answer=$(echo "$response" | jq -r '.llmChatResponse.answer')

    echo "Answer:"
    echo "$answer"
    echo
done
