#!/bin/bash

# Configuration
NOTEBOOK_ID="1GYJgsSc7zWN-wEUUC7_aANUH807rLmgp"
NEW_NAME="PeteOllama_Direct_GPU_v2.ipynb"
SOURCE_FILE="colab_notebooks/PeteOllama_Direct_GPU.ipynb"

# Check if gcloud is installed
if ! command -v gcloud &> /dev/null; then
    echo "❌ gcloud CLI not found. Installing..."
    # Install Google Cloud SDK
    curl https://sdk.cloud.google.com | bash
    exec -l $SHELL
    gcloud init
fi

# Ensure we're authenticated
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" &> /dev/null; then
    echo "🔑 Please authenticate with Google Cloud..."
    gcloud auth login
fi

# Enable Drive API if not already enabled
gcloud services enable drive.googleapis.com

# Create a copy with new version name
cp "$SOURCE_FILE" "$NEW_NAME"

# Upload to Google Drive
echo "📤 Uploading to Google Drive..."
gcloud alpha drive files upload "$NEW_NAME" \
    --drive-id "$NOTEBOOK_ID" \
    --name "$NEW_NAME" \
    --mime-type "application/x-ipynb+json"

echo "✅ Notebook pushed to Colab!"
echo "🔗 Access at: https://colab.research.google.com/drive/$NOTEBOOK_ID"