#!/bin/bash

resume_file=$1  # No spaces around the '=' sign

# Add the src directory to PYTHONPATH
export PYTHONPATH=$PYTHONPATH:$(pwd)/src

# Run the Python script with the specified resume file
if [ -z "$resume_file" ]; then  # Check if resume_file is empty
    python main.py
else
    python main.py --resume "$resume_file"
fi
