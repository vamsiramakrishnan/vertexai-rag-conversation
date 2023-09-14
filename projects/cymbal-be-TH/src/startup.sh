#!/bin/bash

rm application.log
rm -rf preprocessed_output

hypercorn llm_cr_be_main:app --workers 2  --bind 0.0.0.0:8080
