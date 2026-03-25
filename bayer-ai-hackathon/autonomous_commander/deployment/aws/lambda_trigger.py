"""
AWS Lambda — CloudWatch Alarm Trigger
Receives SNS/CloudWatch alarm events and kicks off the Commander investigation.
Deploy this as a Lambda function subscribed to your CloudWatch Alarm SNS topic.
"""

import json
import boto3
import os


def handler(event, context):
    """
    Lambda handler triggered by CloudWatch Alarm via SNS.
    Parses the alarm, builds an alert dict, and invokes the Commander ECS task.
    """
    print(f"Received event: {json.dumps(event)}")

    # Parse SNS message from CloudWatch Alarm
    for record in event.get("Records", []):
        sns_message = json.loads(record["Sns"]["Message"])

        alert = {
            "alert_id": sns_message.get("AlarmName", "unknown"),
            "service": extract_service_name(sns_message),
            "environment": os.environ.get("ENVIRONMENT", "production"),
            "error_type": sns_message.get("AlarmName", "UnknownAlarm"),
            "error_message": sns_message.get("AlarmDescription", ""),
            "severity_hint": map_severity(sns_message.get("NewStateValue", "ALARM")),
            "timestamp": sns_message.get("StateChangeTime", ""),
            "time_range": "last 30 minutes",
            "source": "CloudWatch Alarm",
        }

        # Invoke Commander via ECS RunTask or Step Functions
        trigger_commander(alert)

    return {"statusCode": 200, "body": "Investigation triggered"}


def extract_service_name(alarm_message: dict) -> str:
    """Extract service name from alarm dimensions."""
    dimensions = alarm_message.get("Trigger", {}).get("Dimensions", [])
    for dim in dimensions:
        if dim.get("name") in ("ServiceName", "service", "FunctionName"):
            return dim.get("value", "unknown")
    return "unknown"


def map_severity(alarm_state: str) -> str:
    return {"ALARM": "P1", "INSUFFICIENT_DATA": "P2", "OK": "P3"}.get(alarm_state, "P2")


def trigger_commander(alert: dict):
    """
    Trigger the Commander agent.
    Option A: ECS RunTask (for long-running investigations)
    Option B: Step Functions StartExecution
    """
    ecs = boto3.client("ecs", region_name=os.environ.get("AWS_DEFAULT_REGION", "us-east-1"))

    response = ecs.run_task(
        cluster=os.environ["ECS_CLUSTER_NAME"],
        taskDefinition=os.environ["ECS_TASK_DEFINITION"],
        launchType="FARGATE",
        networkConfiguration={
            "awsvpcConfiguration": {
                "subnets": os.environ["SUBNET_IDS"].split(","),
                "securityGroups": os.environ["SECURITY_GROUP_IDS"].split(","),
                "assignPublicIp": "DISABLED",
            }
        },
        overrides={
            "containerOverrides": [
                {
                    "name": "autonomous-commander",
                    "environment": [
                        {"name": "ALERT_PAYLOAD", "value": json.dumps(alert)}
                    ],
                }
            ]
        },
    )

    print(f"ECS task started: {response['tasks'][0]['taskArn']}")
