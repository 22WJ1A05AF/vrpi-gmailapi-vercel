"""Run locally once to authorize the old Gmail account and print a refresh token."""
from google_auth_oauthlib.flow import InstalledAppFlow

SCOPES = ["https://www.googleapis.com/auth/gmail.send"]
flow = InstalledAppFlow.from_client_secrets_file("oauth_client.json", SCOPES)
creds = flow.run_local_server(port=0, access_type="offline", prompt="consent")
print("\nGMAIL_CLIENT_ID=" + creds.client_id)
print("GMAIL_CLIENT_SECRET=" + creds.client_secret)
print("GMAIL_REFRESH_TOKEN=" + creds.refresh_token)
print("\nCopy these values to Vercel Environment Variables. Do not share them.")
