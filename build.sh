#!/bin/bash
set -e
# Debug: Print Python version
python --version
# Install Python dependencies
pip install -r requirements.txt
# Run the build command
npm run build