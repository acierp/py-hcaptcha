from http.client import HTTPSConnection
from base64 import b64encode, b64decode
import json
import random
import string

def is_main_process():
    return __import__("multiprocessing").current_process().name == "MainProcess"

def latest_version_id():
    conn = HTTPSConnection("hcaptcha.com", 443)
    conn.request("GET", "/1/api.js")
    resp = conn.getresponse()
    return resp.headers["location"]\
        .split("v1/", 1)[1].split("/", 1)[0]

def random_widget_id():
    widget_id = "".join(random.choices(
        string.ascii_lowercase + string.digits,
        k=random.randint(10, 12)
    ))
    return widget_id

def parse_jsw(req):
    fields = req.split(".")
    return {
        "header": json.loads(b64decode(fields[0])),
        "payload": json.loads(b64decode(fields[1] + ("=" * ((4 - len(fields[1]) % 4) % 4)))),
        "signature": b64decode(fields[2].replace("_", "/").replace("-", "+")  + ("=" * ((4 - len(fields[1]) % 4) % 4))),
        "raw": {
            "header": fields[0],
            "payload": fields[1],
            "signature": fields[2]
        }
    }

def parse_proxy_string(proxy_str):
    if not proxy_str:
        return

    proxy_str = proxy_str.rpartition("://")[2]
    auth, _, fields = proxy_str.rpartition("@")
    fields = fields.split(":", 2)

    if len(fields) == 2:
        hostname, port = fields
        if auth:
            auth = "Basic " + b64encode(auth.encode()).decode()
        addr = (hostname.lower(), int(port))
        return auth, addr

    elif len(fields) == 3:
        hostname, port, auth = fields
        auth = "Basic " + b64encode(auth.encode()).decode()
        addr = (hostname.lower(), int(port))
        return auth, addr
    
    raise Exception(f"Unrecognized proxy format: {proxy_str}")