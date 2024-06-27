from requests_oauth2client import OAuth2Client, OAuth2ClientCredentialsAuth
import os


oauth2client = OAuth2Client(
    token_endpoint="https://r-hi2.cigna.com/mga/sps/oauth/oauth20/token",
    authorization_endpoint="https://r-hi2.cigna.com/mga/sps/oauth/oauth20/authorize",
    redirect_uri="https://dheeraj-insurancechat.streamlit.app/",
    userinfo_endpoint="https://fhir.cigna.com/PatientAccess/v1-devportal/$userinfo",
    client_id="658bc97e-bb97-41b6-8556-589d10cd7114",
    client_secret="af4989b9-6f74-4f3a-a940-1ac22c35b2c4",
)

print(oauth2client)
"""auth = OAuth2ClientCredentialsAuth(
    oauth2client, scope="openid fhirUser patient/*.read"
)

print(auth.token)"""

az_request = oauth2client.authorization_request(scope="openid fhirUser patient/*.read")
print(az_request)
import webbrowser

webbrowser.open(az_request.uri)