#!/bin/bash

set -e  # Exit immediately if a command exits with a non-zero status

# Get the directory of the script
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Change to the script's directory
cd "$SCRIPT_DIR"

ENVIRONMENT=$1
IMAGE_NAME=$2
NAMESPACE=$3
MANIFESTS_DIRECTORY="./k8s_deploy/overlays/$ENVIRONMENT"

# Check current Kubernetes context
kubectl config current-context || { echo "Failed to get current Kubernetes context"; exit 1; }

# Deploy using Kustomize
cd $MANIFESTS_DIRECTORY || { echo "Failed to change directory to $MANIFESTS_DIRECTORY"; exit 1; }

# which utility tool
which kubectl
which kustomize

kustomize edit set image nylabankservice=$IMAGE_NAME || { echo "Failed to edit image with kustomize"; exit 1; }
kustomize build . | kubectl apply -f - || { echo "Failed to build and apply kustomize"; exit 1; }

# Wait for deployment rollout to complete
kubectl rollout status deployment/nylabankservice -n $NAMESPACE || { echo "Failed to get rollout status for nylabankservice"; exit 1; }

# Print services and ingress details
kubectl get services -o wide -n $NAMESPACE || { echo "Failed to get services"; exit 1; }
kubectl get ingress -n $NAMESPACE || { echo "Failed to get ingress"; exit 1; }


echo "Deployment to $ENVIRONMENT environment completed."
