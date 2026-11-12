import os

# Local development only
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

from google_auth_oauthlib.flow import Flow
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
import webbrowser

SCOPES = [
    "https://www.googleapis.com/auth/gmail.send"
]

REDIRECT_URI = "http://localhost:8080/"

flow = Flow.from_client_secrets_file(
    "oauth_client.json",
    scopes=SCOPES
)

flow.redirect_uri = REDIRECT_URI

authorization_url, state = flow.authorization_url(
    access_type="offline",
    prompt="consent",
    include_granted_scopes="true"
)

class OAuthHandler(BaseHTTPRequestHandler):

    def do_GET(self):
        try:
            callback_url = REDIRECT_URI.rstrip("/") + self.path

            query = parse_qs(urlparse(self.path).query)

            if "error" in query:
                raise Exception(query["error"][0])

            flow.fetch_token(
                authorization_response=callback_url
            )

            credentials = flow.credentials

            if not credentials.refresh_token:
                raise Exception(
                    "No refresh token received. Try granting consent again."
                )

            print("\nSUCCESS! Gmail refresh token generated.")
            print("\nGMAIL_REFRESH_TOKEN:")
            print(credentials.refresh_token)

            message = b"Google authorization successful. "
            message += b"You can close this browser window."

            self.send_response(200)
            self.send_header("Content-Type", "text/plain")
            self.end_headers()
            self.wfile.write(message)

        except Exception as error:
            print("\nOAuth ERROR:", str(error))

            self.send_response(400)
            self.end_headers()
            self.wfile.write(b"OAuth failed. Check your VS Code terminal.")

    def log_message(self, *args):
        pass


print("\nOpening Google authorization...")
print("\nIf the browser does not open, visit:")
print(authorization_url)

server = HTTPServer(("localhost", 8080), OAuthHandler)

webbrowser.open(authorization_url)

print("\nWaiting for Google authorization...")
server.handle_request()
server.server_close()
