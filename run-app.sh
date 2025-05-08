#!/bin/bash

echo "Starting Live Language Translator..."

# Check if npm is installed
if ! command -v npm &> /dev/null; then
    echo "Error: npm is not installed. Please install Node.js and npm."
    exit 1
fi

# Change to the script's directory
cd "$(dirname "$0")"

# Run the setup script if first time or if requested
if [ "$1" = "--setup" ]; then
    echo "Running setup..."
    npm run setup
else
    # Check if node_modules exists, if not, run setup
    if [ ! -d "node_modules" ]; then
        echo "First-time setup detected, installing dependencies..."
        npm run setup
    fi
fi

# Run the application
echo "Starting the application..."
npm start 