#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-us-east-1}"
VPC_CIDR="${VPC_CIDR:-10.0.0.0/16}"
PUBLIC_SUBNET_CIDR_A="${PUBLIC_SUBNET_CIDR_A:-10.0.1.0/24}"
PUBLIC_SUBNET_CIDR_B="${PUBLIC_SUBNET_CIDR_B:-10.0.2.0/24}"

echo "Creating VPC in ${AWS_REGION}..."
VPC_ID="$(aws ec2 create-vpc --region "${AWS_REGION}" --cidr-block "${VPC_CIDR}" --query 'Vpc.VpcId' --output text)"
aws ec2 modify-vpc-attribute --region "${AWS_REGION}" --vpc-id "${VPC_ID}" --enable-dns-support "{\"Value\":true}"
aws ec2 modify-vpc-attribute --region "${AWS_REGION}" --vpc-id "${VPC_ID}" --enable-dns-hostnames "{\"Value\":true}"

IGW_ID="$(aws ec2 create-internet-gateway --region "${AWS_REGION}" --query 'InternetGateway.InternetGatewayId' --output text)"
aws ec2 attach-internet-gateway --region "${AWS_REGION}" --internet-gateway-id "${IGW_ID}" --vpc-id "${VPC_ID}"

AZ_A="$(aws ec2 describe-availability-zones --region "${AWS_REGION}" --query 'AvailabilityZones[0].ZoneName' --output text)"
AZ_B="$(aws ec2 describe-availability-zones --region "${AWS_REGION}" --query 'AvailabilityZones[1].ZoneName' --output text)"

SUBNET_A="$(aws ec2 create-subnet --region "${AWS_REGION}" --vpc-id "${VPC_ID}" --cidr-block "${PUBLIC_SUBNET_CIDR_A}" --availability-zone "${AZ_A}" --query 'Subnet.SubnetId' --output text)"
SUBNET_B="$(aws ec2 create-subnet --region "${AWS_REGION}" --vpc-id "${VPC_ID}" --cidr-block "${PUBLIC_SUBNET_CIDR_B}" --availability-zone "${AZ_B}" --query 'Subnet.SubnetId' --output text)"

aws ec2 modify-subnet-attribute --region "${AWS_REGION}" --subnet-id "${SUBNET_A}" --map-public-ip-on-launch
aws ec2 modify-subnet-attribute --region "${AWS_REGION}" --subnet-id "${SUBNET_B}" --map-public-ip-on-launch

ROUTE_TABLE_ID="$(aws ec2 create-route-table --region "${AWS_REGION}" --vpc-id "${VPC_ID}" --query 'RouteTable.RouteTableId' --output text)"
aws ec2 create-route --region "${AWS_REGION}" --route-table-id "${ROUTE_TABLE_ID}" --destination-cidr-block 0.0.0.0/0 --gateway-id "${IGW_ID}"
aws ec2 associate-route-table --region "${AWS_REGION}" --subnet-id "${SUBNET_A}" --route-table-id "${ROUTE_TABLE_ID}"
aws ec2 associate-route-table --region "${AWS_REGION}" --subnet-id "${SUBNET_B}" --route-table-id "${ROUTE_TABLE_ID}"

SG_STREAMLIT="$(aws ec2 create-security-group --region "${AWS_REGION}" --group-name autonomous-commander-streamlit-sg --description 'Streamlit public access' --vpc-id "${VPC_ID}" --query 'GroupId' --output text)"
aws ec2 authorize-security-group-ingress --region "${AWS_REGION}" --group-id "${SG_STREAMLIT}" --protocol tcp --port 8501 --cidr 0.0.0.0/0

SG_TASK="$(aws ec2 create-security-group --region "${AWS_REGION}" --group-name autonomous-commander-task-sg --description 'Commander tasks' --vpc-id "${VPC_ID}" --query 'GroupId' --output text)"

echo ""
echo "Network created."
echo "VPC_ID=${VPC_ID}"
echo "SUBNET_IDS=${SUBNET_A},${SUBNET_B}"
echo "SECURITY_GROUP_STREAMLIT=${SG_STREAMLIT}"
echo "SECURITY_GROUP_TASKS=${SG_TASK}"
