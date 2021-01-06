#!/bin/bash

# Read input arguments
YAML_PATH=$1
OUTPUT_DB_FILE=$2
OUTPUT_XTCE_FILE=$3

# Get directory of this script no matter where it is being called from.
AUTO_YAMCS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"

# Delete any existing files, if there are any.
if test -f "${OUTPUT_DB_FILE}"; then
    echo "Cleaning database."; \
    rm "${OUTPUT_DB_FILE}"
fi
if test -f "${OUTPUT_XTCE_FILE}"; then
    echo "Cleaning XTCE."; \
    rm "${OUTPUT_XTCE_FILE}"
fi

# Set working directory to the auto_yamcs directory.
cd ${AUTO_YAMCS_DIR}

python3 squeezer.py singleton --singleton_yaml_path "${YAML_PATH}"  --output_file "${OUTPUT_DB_FILE}" --verbosity 3 --xtce_output_path "${OUTPUT_XTCE_FILE}"
