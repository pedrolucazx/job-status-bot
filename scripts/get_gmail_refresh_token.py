import os
import secrets
from http.server import BaseHTTPRequestHandler, HTTPServer
from urllib.parse import parse_qs, urlencode, urlparse

import requests
from dotenv import load_dotenv

load_dotenv()

SCOPES = ["https://www.googleapis.com/auth/gmail.modify"]


class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True


def make_server(handler, preferred_port):
    for port in range(preferred_port, preferred_port + 20):
        try:
            return ReusableHTTPServer(("localhost", port), handler), port
        except OSError:
            continue
    raise OSError(f"No free localhost port from {preferred_port} to {preferred_port + 19}")


def main():
    client_id = os.environ["GMAIL_CLIENT_ID"]
    client_secret = os.environ["GMAIL_CLIENT_SECRET"]
    state = secrets.token_urlsafe(24)
    preferred_port = int(os.getenv("OAUTH_LOCAL_PORT", "8080"))

    class Handler(BaseHTTPRequestHandler):
        code = None
        error = None

        def log_message(self, *_args):
            pass

        def do_GET(self):
            params = parse_qs(urlparse(self.path).query)
            if params.get("state", [""])[0] != state:
                self.send_response(400)
                self.end_headers()
                self.wfile.write(b"Wrong OAuth tab. Close this and open the latest URL.")
                print("Ignored stale OAuth callback.")
                return

            Handler.error = params.get("error", [None])[0]
            Handler.code = params.get("code", [None])[0]

            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"The authentication flow has completed. You may close this window.")

    server, port = make_server(Handler, preferred_port)
    redirect_uri = f"http://localhost:{port}/"
    auth_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(
        {
            "response_type": "code",
            "client_id": client_id,
            "redirect_uri": redirect_uri,
            "scope": " ".join(SCOPES),
            "state": state,
            "prompt": "consent",
            "access_type": "offline",
        }
    )

    print(f"Please visit this URL to authorize this application: {auth_url}", flush=True)

    while Handler.code is None and Handler.error is None:
        server.handle_request()

    if Handler.error:
        raise SystemExit(f"OAuth error: {Handler.error}")

    response = requests.post(
        "https://oauth2.googleapis.com/token",
        data={
            "code": Handler.code,
            "client_id": client_id,
            "client_secret": client_secret,
            "redirect_uri": redirect_uri,
            "grant_type": "authorization_code",
        },
        timeout=30,
    )
    response.raise_for_status()

    refresh_token = response.json().get("refresh_token")
    if not refresh_token:
        raise SystemExit("Google did not return a refresh token. Revoke the app grant and retry.")

    print(f"REFRESH_TOKEN={refresh_token}")


if __name__ == "__main__":
    main()
