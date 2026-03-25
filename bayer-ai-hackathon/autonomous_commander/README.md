# Autonomous Commander — Multi-Agent Incident Investigation System

An autonomous AI system built on **LangGraph** + **AWS Bedrock (Claude)** that investigates production incidents end-to-end without human intervention.

---

## Architecture

```
┌──────────────────────────────────────────────────────────────────────┐
│                     AWS PRODUCTION ENVIRONMENT                       │
│                                                                      │
│  CloudWatch Alarm ──► SNS Topic ──► Lambda Trigger                  │
│                                          │                           │
│                                          ▼                           │
│                              ┌─────────────────────┐                │
│                              │   COMMANDER AGENT   │                │
│                              │   (Orchestrator)    │                │
│                              │                     │                │
│                              │  • Evaluate alert   │                │
│                              │  • Classify P1/P2/P3│                │
│                              │  • Build inv. plan  │                │
│                              │  • Coordinate agents│                │
│                              └──────────┬──────────┘                │
│                                         │                            │
│                    ┌────────────────────┼────────────────────┐      │
│                    │                    │                    │      │
│                    ▼                    ▼                    ▼      │
│         ┌──────────────┐    ┌──────────────────┐  ┌──────────────┐ │
│         │  LOGS AGENT  │    │  METRICS AGENT   │  │ DEPLOY AGENT │ │
│         │  Forensic    │    │  Telemetry       │  │  Historian   │ │
│         │  Expert      │    │  Analyst         │  │              │ │
│         │              │    │                  │  │              │ │
│         │ CloudWatch   │    │ CloudWatch       │  │ CodeDeploy   │ │
│         │ Logs Insights│    │ Metrics + X-Ray  │  │ ECS + SSM    │ │
│         │              │    │                  │  │              │ │
│         │• Stack traces│    │• CPU spikes      │  │• CI/CD diff  │ │
│         │• Error corr. │    │• Latency p99     │  │• Config chg  │ │
│         │• Trace IDs   │    │• Memory leaks    │  │• Rollback?   │ │
│         └──────┬───────┘    └──────┬───────────┘  └──────┬───────┘ │
│                │                   │                      │         │
│                └───────────────────┼──────────────────────┘         │
│                                    │                                 │
│                                    ▼                                 │
│                         ┌─────────────────────┐                     │
│                         │   SYNTHESIS NODE    │                     │
│                         │  (Commander RCA)    │                     │
│                         │                     │                     │
│                         │ • Root Cause        │                     │
│                         │ • Contributing Fctrs│                     │
│                         │ • Timeline          │                     │
│                         │ • Remediation Steps │                     │
│                         └──────────┬──────────┘                     │
│                                    │                                 │
│                                    ▼                                 │
│                         ┌─────────────────────┐                     │
│                         │  RCA REPORT         │                     │
│                         │  → S3 / SNS / Slack │                     │
│                         └─────────────────────┘                     │
└──────────────────────────────────────────────────────────────────────┘
```

---

## Agent Roles

| Agent | Role | Data Sources |
|---|---|---|
| Commander | Orchestrator — evaluates alerts, plans investigation, synthesizes RCA | Alert payload |
| Logs Agent | Forensic Expert — stack traces, error correlations, log anomalies | CloudWatch Logs Insights |
| Metrics Agent | Telemetry Analyst — CPU, latency p99, memory leaks, error rates | CloudWatch Metrics, X-Ray |
| Deploy Agent | Historian — CI/CD timeline, config changes, rollback decisions | CodeDeploy, ECS, SSM |

---

## Project Structure

```
autonomous_commander/
├── agents/
│   ├── commander_agent.py      # Orchestrator + synthesis
│   ├── logs_agent.py           # Forensic log analysis
│   ├── metrics_agent.py        # Telemetry analysis
│   └── deploy_agent.py         # Deployment correlation
├── graph/
│   ├── workflow.py             # LangGraph graph definition
│   └── visualize.py            # ASCII + PNG diagram renderer
├── deployment/
│   ├── Dockerfile
│   └── aws/
│       ├── ecs_task_definition.json
│       └── lambda_trigger.py   # CloudWatch Alarm → Lambda → ECS
├── autonomous_commander.ipynb  # Interactive notebook walkthrough
├── main.py                     # CLI entry point
├── requirements.txt
└── README.md
```

---

## Local Setup

```bash
cd autonomous_commander

# Create virtual environment
python -m venv venv
# Windows (CMD):
venv\Scripts\activate
# Windows (PowerShell):
.\venv\Scripts\Activate.ps1
# macOS/Linux:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Configure AWS credentials (needs Bedrock access)
aws configure

# Run the investigation
python main.py
```

---

## AWS Deployment

### Prerequisites
- AWS account with Bedrock enabled in `us-east-1`
- IAM role with permissions: `bedrock:InvokeModel`, `logs:*`, `cloudwatch:GetMetricData`, `codedeploy:List*`, `ecs:RunTask`, `ssm:GetParameter`

### Step 1 — Build & Push Docker Image

```bash
# Authenticate to ECR
aws ecr get-login-password --region us-east-1 | \
  docker login --username AWS --password-stdin ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com

# Create ECR repo
aws ecr create-repository --repository-name autonomous-commander --region us-east-1

# Build and push
docker build -f deployment/Dockerfile -t autonomous-commander .
docker tag autonomous-commander:latest ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/autonomous-commander:latest
docker push ACCOUNT_ID.dkr.ecr.us-east-1.amazonaws.com/autonomous-commander:latest
```

### Step 2 — Register ECS Task Definition

```bash
# Update ACCOUNT_ID in the file first
aws ecs register-task-definition \
  --cli-input-json file://deployment/aws/ecs_task_definition.json \
  --region us-east-1
```

### Step 3 — Create ECS Cluster & Service

```bash
# Create cluster
aws ecs create-cluster --cluster-name autonomous-commander --region us-east-1

# Create CloudWatch log group
aws logs create-log-group --log-group-name /ecs/autonomous-commander --region us-east-1
```

### Step 4 — Deploy Lambda Trigger

```bash
# Zip and deploy the Lambda trigger
zip lambda_trigger.zip deployment/aws/lambda_trigger.py

aws lambda create-function \
  --function-name autonomous-commander-trigger \
  --runtime python3.11 \
  --role arn:aws:iam::ACCOUNT_ID:role/lambdaExecutionRole \
  --handler lambda_trigger.handler \
  --zip-file fileb://lambda_trigger.zip \
  --environment Variables="{
    ECS_CLUSTER_NAME=autonomous-commander,
    ECS_TASK_DEFINITION=autonomous-commander,
    SUBNET_IDS=subnet-xxx,
    SECURITY_GROUP_IDS=sg-xxx,
    ENVIRONMENT=production
  }" \
  --region us-east-1
```

### Step 5 — Wire CloudWatch Alarm → SNS → Lambda

```bash
# Create SNS topic
aws sns create-topic --name autonomous-commander-alerts --region us-east-1

# Subscribe Lambda to SNS
aws sns subscribe \
  --topic-arn arn:aws:sns:us-east-1:ACCOUNT_ID:autonomous-commander-alerts \
  --protocol lambda \
  --notification-endpoint arn:aws:lambda:us-east-1:ACCOUNT_ID:function:autonomous-commander-trigger

# Add SNS trigger permission to Lambda
aws lambda add-permission \
  --function-name autonomous-commander-trigger \
  --statement-id sns-invoke \
  --action lambda:InvokeFunction \
  --principal sns.amazonaws.com \
  --source-arn arn:aws:sns:us-east-1:ACCOUNT_ID:autonomous-commander-alerts
```

### Step 6 — Point CloudWatch Alarms at SNS Topic

In the AWS Console or via CLI, set your existing CloudWatch Alarms to send notifications to:
`arn:aws:sns:us-east-1:ACCOUNT_ID:autonomous-commander-alerts`

---

## IAM Policy (Minimum Required)

```json
{
  "Version": "2012-10-17",
  "Statement": [
    { "Effect": "Allow", "Action": ["bedrock:InvokeModel"], "Resource": "*" },
    { "Effect": "Allow", "Action": ["logs:StartQuery", "logs:GetQueryResults", "logs:DescribeLogGroups"], "Resource": "*" },
    { "Effect": "Allow", "Action": ["cloudwatch:GetMetricData", "cloudwatch:DescribeAlarms"], "Resource": "*" },
    { "Effect": "Allow", "Action": ["codedeploy:ListDeployments", "codedeploy:GetDeployment"], "Resource": "*" },
    { "Effect": "Allow", "Action": ["ecs:DescribeTaskDefinition", "ecs:ListTaskDefinitions"], "Resource": "*" },
    { "Effect": "Allow", "Action": ["ssm:GetParameter", "ssm:GetParameterHistory"], "Resource": "*" },
    { "Effect": "Allow", "Action": ["xray:GetTraceSummaries", "xray:BatchGetTraces"], "Resource": "*" }
  ]
}
```

---

## Notebook

Open `autonomous_commander.ipynb` for an interactive walkthrough with inline visualizations of the telemetry data and the full investigation flow.

---

## Tech Stack

- LangGraph — multi-agent graph orchestration
- AWS Bedrock (Claude 3.5 Sonnet) — LLM backbone
- AWS CloudWatch Logs Insights — log forensics
- AWS CloudWatch Metrics + X-Ray — telemetry
- AWS CodeDeploy + ECS + SSM — deployment history
- AWS Lambda — alarm trigger
- AWS ECS Fargate — container runtime
