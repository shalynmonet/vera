"""
Create the 6 EventBridge Scheduler schedules (3 residents x 2 call types),
all in a DISABLED state. Uses boto3 directly to avoid shell JSON-quoting
issues with the AWS CLI.
"""

import json

import boto3

LAMBDA_ARN = "arn:aws:lambda:us-east-1:381183037235:function:vera-call-orchestrator"
SCHEDULER_ROLE_ARN = "arn:aws:iam::381183037235:role/vera-scheduler-execution-role"
TIMEZONE = "America/Chicago"

RESIDENTS = ["resident_1", "resident_2", "resident_3"]
CALL_TYPES = [
    {"action": "social_checkin", "name_suffix": "social-checkin", "cron": "cron(0 12 * * ? *)"},
    {"action": "activity", "name_suffix": "activity", "cron": "cron(0 16 * * ? *)"},
]


def main() -> None:
    client = boto3.client("scheduler", region_name="us-east-1")

    for resident_id in RESIDENTS:
        for call_type in CALL_TYPES:
            name = f"vera-{resident_id}-{call_type['name_suffix']}"
            payload = json.dumps({"action": call_type["action"], "resident_id": resident_id})
            print(f"Creating {name} -> {call_type['cron']} ({TIMEZONE}), input={payload}")
            client.create_schedule(
                Name=name,
                ScheduleExpression=call_type["cron"],
                ScheduleExpressionTimezone=TIMEZONE,
                FlexibleTimeWindow={"Mode": "OFF"},
                State="DISABLED",
                Target={
                    "Arn": LAMBDA_ARN,
                    "RoleArn": SCHEDULER_ROLE_ARN,
                    "Input": payload,
                },
            )
    print("Done.")


if __name__ == "__main__":
    main()
