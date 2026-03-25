#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID="${ACCOUNT_ID:?Set ACCOUNT_ID to your AWS account id}"
BEDROCK_MODEL_ID="${BEDROCK_MODEL_ID:-qwen.qwen3-coder-next}"
REPO_NAME="${REPO_NAME:-autonomous-commander}"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is not installed or not on PATH."
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon is not running. Start Docker Desktop and retry."
  exit 1
fi

echo "Logging in to ECR..."
aws ecr get-login-password --region "${AWS_REGION}" | \
  docker login --username AWS --password-stdin "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com"

echo "Ensuring ECR repository exists..."
aws ecr describe-repositories --repository-names "${REPO_NAME}" --region "${AWS_REGION}" >/dev/null 2>&1 || \
  aws ecr create-repository --repository-name "${REPO_NAME}" --region "${AWS_REGION}" >/dev/null

echo "Building image..."
docker build -f deployment/Dockerfile -t "${REPO_NAME}:latest" .

echo "Tagging image..."
docker tag "${REPO_NAME}:latest" "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}:cli"
docker tag "${REPO_NAME}:latest" "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}:streamlit"

echo "Pushing image tags..."
docker push "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}:cli"
docker push "${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}:streamlit"

echo "Storing BEDROCK_MODEL_ID in SSM..."
aws ssm put-parameter \
  --name /autonomous-commander/bedrock-model-id \
  --type String \
  --value "${BEDROCK_MODEL_ID}" \
  --overwrite \
  --region "${AWS_REGION}" >/dev/null

echo "Done."
echo "ECR: ${ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${REPO_NAME}"
echo "BEDROCK_MODEL_ID: ${BEDROCK_MODEL_ID}"
