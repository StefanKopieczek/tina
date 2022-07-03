import boto3
import json
from botocore.exceptions import ClientError


def get_twilio_creds() -> tuple[str, str]:
    secret_name = "arn:aws:secretsmanager:eu-west-1:833033589552:secret:twilio-NNMyv4"
    region_name = "eu-west-1"
    secret = get_secret(secret_name, region_name)
    return secret["sid"], secret["api_key"]


def get_sender_number() -> str:
    secret_name = "arn:aws:secretsmanager:eu-west-1:833033589552:secret:twilio_phone_numbers-YRSMgN"
    region_name = "eu-west-1"
    return get_secret(secret_name, region_name)["sender_number"]


def get_recipients() -> list[str]:
    secret_name = "arn:aws:secretsmanager:eu-west-1:833033589552:secret:twilio_phone_numbers-YRSMgN"
    region_name = "eu-west-1"
    return get_secret(secret_name, region_name)["recipients"].split(",")


def get_secret(secret_name, region_name):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(service_name="secretsmanager", region_name=region_name)

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(SecretId=secret_name)
        assert "SecretString" in get_secret_value_response
        secret = json.loads(get_secret_value_response["SecretString"])
        return secret
    except ClientError as e:
        if e.response["Error"]["Code"] == "DecryptionFailureException":
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response["Error"]["Code"] == "InternalServiceErrorException":
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response["Error"]["Code"] == "InvalidParameterException":
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response["Error"]["Code"] == "InvalidRequestException":
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response["Error"]["Code"] == "ResourceNotFoundException":
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        else:
            raise e
