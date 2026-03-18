"""Acquire token via device code flow. Writes code message and token to files."""
import sys
sys.path.insert(0, "src")

import msal

CLIENT_ID = "c44051af-0358-4845-aac1-0d83741dca16"
TENANT_ID = "consumers"
SCOPES    = ["https://graph.microsoft.com/Mail.ReadWrite"]

app = msal.PublicClientApplication(
    client_id=CLIENT_ID,
    authority=f"https://login.microsoftonline.com/{TENANT_ID}",
)

flow = app.initiate_device_flow(scopes=SCOPES)
if "user_code" not in flow:
    raise RuntimeError(flow.get("error_description"))

# Write the message immediately so it can be read before sign-in completes
with open("/tmp/corpus_device_msg.txt", "w") as f:
    f.write(flow["message"])

print(flow["message"], flush=True)

result = app.acquire_token_by_device_flow(flow)

if "access_token" not in result:
    raise RuntimeError(result.get("error_description"))

with open("/tmp/corpus_token.txt", "w") as f:
    f.write(result["access_token"])

print("Token saved to /tmp/corpus_token.txt")
