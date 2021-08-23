import boto3
import json
import os

def header_to_dict(header: str) -> dict:
    output = {}
    kv_pairs = header.split("&")
    for pair in kv_pairs:
        pair_array = pair.split("=")
        output[pair_array[0]] = pair_array[1]

    return output


def is_oddone(username: str) -> bool:
    return True


def get_access_token() -> str:
    lambda_client = boto3.client("lambda")
    env = os.environ.get("ENV")
    response = lambda_client.invoke(
        FunctionName=f"{env}-twitch-oauth",
        InvocationType="RequestResponse",
        LogType="None",
    )

    token = response["Payload"].read().decode("utf-8")
    if token == " ":
        raise RuntimeError("Could not retrieve access token")

    return token
