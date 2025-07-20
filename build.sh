#!/bin/bash

# Install the package in development mode
echo "Installing Richtato package..."
pip install .

# Run the demo setup script
echo "Setting up demo data..."
./create_or_reset_demo.sh

echo "Build completed successfully!"
