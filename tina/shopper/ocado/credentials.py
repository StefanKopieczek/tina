from typing import Tuple
from ...secrets import get_secret


SECRET_ARN = (
    "arn:aws:secretsmanager:eu-west-1:833033589552:secret:website_logins-2HbFM3"
)


def get_test_login() -> Tuple[str, str]:
    logins = get_secret(SECRET_ARN)
    return logins["ocado_test_username"], logins["ocado_test_password"]


def get_prod_login() -> Tuple[str, str]:
    logins = get_secret(SECRET_ARN)
    return logins["ocado_username"], logins["ocado_password"]
