#!/bin/bash

# Build React frontend
echo "Building React frontend..."
cd frontend
yarn build

# Copy build files to Django static directory
echo "Copying build files to Django static directory..."
cp -r dist/* ../richtato/static/

# Copy index.html to pages directory
echo "Copying index.html to pages directory..."
cp dist/index.html ../richtato/pages/

echo "Frontend build complete!"
