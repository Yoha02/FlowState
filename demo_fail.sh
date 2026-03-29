#!/bin/bash
# Demo: This command will fail because Kubernetes Engine API is not enabled
echo "Deploying FlowState to GKE cluster..."
echo ""
gcloud container clusters list --project=multimodal-491620 2>&1
echo ""
echo "ERROR: Deployment failed. Need to fix this..."
