from typing import List, Tuple
from ..secrets import get_secret


def get_twilio_creds() -> Tuple[str, str]:
    secret_name = "arn:aws:secretsmanager:eu-west-1:833033589552:secret:twilio-NNMyv4"
    secret = get_secret(secret_name)
    return secret["sid"], secret["api_key"]


def get_sender_number() -> str:
    secret_name = "arn:aws:secretsmanager:eu-west-1:833033589552:secret:twilio_phone_numbers-YRSMgN"
    return get_secret(secret_name)["sender_number"]


def get_recipients() -> List[str]:
    secret_name = "arn:aws:secretsmanager:eu-west-1:833033589552:secret:twilio_phone_numbers-YRSMgN"
    return get_secret(secret_name)["recipients"].split(",")
