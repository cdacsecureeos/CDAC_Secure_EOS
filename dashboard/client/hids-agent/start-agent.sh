#!/bin/bash
# start-agent.sh (FINAL, ROBUST VERSION 2)
# This script is designed to be run from the PROJECT ROOT directory.

set -e

SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
CLIENT_CODE_DIR="${SCRIPT_DIR}/client"
CLIENT_MAIN_PY="${CLIENT_CODE_DIR}/main.py"
CONFIG_FILE="${SCRIPT_DIR}/.env"

echo "--- HIDS Agent Launcher ---"

if [ ! -f "$CLIENT_MAIN_PY" ]; then
    echo "[FATAL ERROR] Cannot find the agent script at: $CLIENT_MAIN_PY"
    exit 1
fi

if [ ! -f "$CONFIG_FILE" ]; then
    echo "[!] Configuration file ($CONFIG_FILE) not found."
    echo "[+] Starting first-time setup for API Key."
    
    while true; do
        read -s -p "Please enter your secret API Key: " agent_api_key
        echo ""
        read -s -p "Please confirm your API Key: " agent_api_key_confirm
        echo ""

        if [ "$agent_api_key" == "$agent_api_key_confirm" ]; then
            # --- CHANGE 1: How the key is SAVED ---
            # We now include the 'export' keyword directly in the file.
            # This makes the .env file a valid script that can be "sourced".
            echo "export VALID_API_KEY=\"$agent_api_key\"" > "$CONFIG_FILE"
            
            echo "[SUCCESS] API Key saved to the '$CONFIG_FILE' file."
            break
        else
            echo "[ERROR] The keys did not match. Please try again."
        fi
    done
fi

echo "[+] Loading API Key from '$CONFIG_FILE'..."

# --- CHANGE 2: How the key is LOADED ---
# The `source` command is the correct and robust way to load shell variables
# from a file. It correctly ignores comments and blank lines.
source "$CONFIG_FILE"

echo "[+] Starting the Python agent..."
echo "    (Press Ctrl+C to stop the agent)"
echo "-----------------------------------------"

cd "$CLIENT_CODE_DIR"
python3 ./main.py
