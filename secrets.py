"""
Small AWS Secrets Manager helper, used identically from local dev (via your
`aws configure` credentials) and from Lambda (via its execution role) - the
same secret names, the same read path, everywhere.
"""

from functools import lru_cache

import boto3


@lru_cache(maxsize=None)
def get_secret_string(secret_name: str, region_name: str = "us-east-1") -> str:
    client = boto3.client("secretsmanager", region_name=region_name)
    response = client.get_secret_value(SecretId=secret_name)
    return response["SecretString"]
