#!/bin/bash
set -e
# Install Python dependencies
pip install -r requirements.txt
# Run the build command
npm run build