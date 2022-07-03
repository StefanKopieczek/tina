import base64
from urllib import request, parse
from .secrets import get_sender_number, get_recipients, get_twilio_creds

TWILIO_SMS_URL = "https://api.twilio.com/2010-04-01/Accounts/{}/Messages.json"


def notify(message: str) -> None:
    for recipient in get_recipients():
        send_sms(recipient, message)


def send_sms(destination: str, body: str) -> None:
    to_number = destination
    from_number = get_sender_number()
    body = body
    sid, token = get_twilio_creds()

    if not sid:
        return "Unable to access Twilio Account SID."
    elif not token:
        return "Unable to access Twilio Auth Token."
    elif not to_number:
        return "The function needs a 'To' number in the format +12023351493"
    elif not from_number:
        return "The function needs a 'From' number in the format +19732644156"
    elif not body:
        return "The function needs a 'Body' message to send."

    # insert Twilio Account SID into the REST API URL
    populated_url = TWILIO_SMS_URL.format(sid)
    post_params = {"To": to_number, "From": from_number, "Body": body}

    # encode the parameters for Python's urllib
    data = parse.urlencode(post_params).encode()
    req = request.Request(populated_url)

    # add authentication header to request based on Account SID + Auth Token
    authentication = "{}:{}".format(sid, token)
    base64string = base64.b64encode(authentication.encode("utf-8"))
    req.add_header("Authorization", "Basic %s" % base64string.decode("ascii"))

    try:
        # perform HTTP POST request
        with request.urlopen(req, data) as f:
            print("Twilio returned {}".format(str(f.read().decode("utf-8"))))
    except Exception as e:
        # something went wrong!
        return e

    return "SMS sent successfully!"
