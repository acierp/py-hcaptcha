from .utils import is_main_process, parse_jsw
from http.client import HTTPSConnection
import os
import json

def download_files():
    conn = HTTPSConnection("hcaptcha.com", 443)
    conn.request("GET", "/checksiteconfig?host=dashboard.hcaptcha.com"
                        "&sitekey=13257c82-e129-4f09-a733-2a7cb3102832"
                        "&sc=0&swa=0", headers={"User-Agent": "a"})
    resp = conn.getresponse()
    data = resp.read()
    base_path = parse_jsw(
        json.loads(data)["c"]["req"]
        )["payload"]["l"].split("hcaptcha.com", 1)[1]
    if not os.path.isdir("hcaptcha-js"):
        os.mkdir("hcaptcha-js")

    conn = HTTPSConnection("newassets.hcaptcha.com", 443)
    for filename in ("hsw.js",):
        conn.request("GET", f"{base_path}/{filename}")
        resp = conn.getresponse()
        with open(f"hcaptcha-js/{filename}", "wb") as fp:
            fp.write(resp.read())

if is_main_process():
    download_files()