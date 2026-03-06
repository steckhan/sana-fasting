#!/usr/bin/env python3
"""
Withings OAuth2 setup — run once to authenticate.
Stores credentials to tools/.withings-credentials.json
"""

import json
import sys
import time
import requests
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path
from urllib.parse import urlparse, parse_qs, urlencode

CREDENTIALS_FILE = Path(__file__).parent / ".withings-credentials.json"

AUTH_CODE = None
AUTH_STATE = None


class CallbackHandler(BaseHTTPRequestHandler):
    def do_GET(self):
        global AUTH_CODE
        parsed = urlparse(self.path)
        params = parse_qs(parsed.query)
        if "code" in params:
            AUTH_CODE = params["code"][0]
            self.send_response(200)
            self.send_header("Content-type", "text/html")
            self.end_headers()
            self.wfile.write(b"<h2>Auth complete! You can close this tab.</h2>")
        else:
            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"<h2>Error: no code in callback</h2>")

    def log_message(self, format, *args):
        pass


def main():
    if len(sys.argv) < 3:
        print("Usage: python3 withings-auth.py <client_id> <client_secret> [redirect_uri]")
        sys.exit(1)

    client_id = sys.argv[1]
    client_secret = sys.argv[2]
    redirect_uri = sys.argv[3] if len(sys.argv) > 3 else "http://localhost:8765/callback"

    parsed = urlparse(redirect_uri)
    port = parsed.port or 8765

    # Build authorization URL manually
    params = {
        "response_type": "code",
        "client_id": client_id,
        "redirect_uri": redirect_uri,
        "scope": "user.metrics,user.activity",
        "state": "healthcoach",
    }
    auth_url = "https://account.withings.com/oauth2_user/authorize2?" + urlencode(params)

    print(f"\n📋 Open this URL in your browser:\n\n  {auth_url}\n")
    print(f"⏳ Waiting for OAuth callback on port {port}...\n")
    sys.stdout.flush()

    # Start local callback server
    server = HTTPServer(("", port), CallbackHandler)
    server.timeout = 180
    server.handle_request()

    if not AUTH_CODE:
        print("❌ No auth code received.")
        sys.exit(1)

    print(f"✅ Got auth code. Exchanging for tokens...")
    sys.stdout.flush()

    # Exchange code for tokens
    resp = requests.post(
        "https://wbsapi.withings.net/v2/oauth2",
        data={
            "action": "requesttoken",
            "grant_type": "authorization_code",
            "client_id": client_id,
            "client_secret": client_secret,
            "code": AUTH_CODE,
            "redirect_uri": redirect_uri,
        },
    )
    resp.raise_for_status()
    body = resp.json()

    if body.get("status") != 0:
        print(f"❌ Withings error: {body}")
        sys.exit(1)

    token = body["body"]
    creds = {
        "client_id": client_id,
        "client_secret": client_secret,
        "access_token": token["access_token"],
        "refresh_token": token["refresh_token"],
        "expires_in": token["expires_in"],
        "userid": token["userid"],
        "fetched_at": int(time.time()),
    }

    CREDENTIALS_FILE.write_text(json.dumps(creds, indent=2))
    CREDENTIALS_FILE.chmod(0o600)
    print(f"✅ Credentials saved to {CREDENTIALS_FILE}")
    print("✅ Run withings-sync.py to fetch measurements.")


if __name__ == "__main__":
    main()
