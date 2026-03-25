#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-us-east-1}"
ACCOUNT_ID="${ACCOUNT_ID:?Set ACCOUNT_ID to your AWS account id}"

TASK_ROLE_NAME="autonomousCommanderTaskRole"
EXEC_ROLE_NAME="ecsTaskExecutionRole"
LAMBDA_ROLE_NAME="autonomous-commander-lambda-role"

TASK_TRUST='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"ecs-tasks.amazonaws.com"},"Action":"sts:AssumeRole"}]}'
LAMBDA_TRUST='{"Version":"2012-10-17","Statement":[{"Effect":"Allow","Principal":{"Service":"lambda.amazonaws.com"},"Action":"sts:AssumeRole"}]}'

if ! aws iam get-role --role-name "${EXEC_ROLE_NAME}" >/dev/null 2>&1; then
  aws iam create-role --role-name "${EXEC_ROLE_NAME}" --assume-role-policy-document "${TASK_TRUST}"
  aws iam attach-role-policy --role-name "${EXEC_ROLE_NAME}" --policy-arn arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
fi

if ! aws iam get-role --role-name "${TASK_ROLE_NAME}" >/dev/null 2>&1; then
  aws iam create-role --role-name "${TASK_ROLE_NAME}" --assume-role-policy-document "${TASK_TRUST}"
fi

aws iam put-role-policy \
  --role-name "${TASK_ROLE_NAME}" \
  --policy-name AutonomousCommanderTaskPolicy \
  --policy-document file://deployment/aws/policies/autonomous_commander_task_policy.json

if ! aws iam get-role --role-name "${LAMBDA_ROLE_NAME}" >/dev/null 2>&1; then
  aws iam create-role --role-name "${LAMBDA_ROLE_NAME}" --assume-role-policy-document "${LAMBDA_TRUST}"
  aws iam attach-role-policy --role-name "${LAMBDA_ROLE_NAME}" --policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole
fi

aws iam put-role-policy \
  --role-name "${LAMBDA_ROLE_NAME}" \
  --policy-name AutonomousCommanderLambdaPolicy \
  --policy-document file://deployment/aws/policies/lambda_trigger_policy.json

echo "Roles ready:"
echo " - ${EXEC_ROLE_NAME}"
echo " - ${TASK_ROLE_NAME}"
echo " - ${LAMBDA_ROLE_NAME}"
