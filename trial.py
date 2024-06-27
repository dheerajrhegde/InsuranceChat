from requests_oauth2client import OAuth2Client, OAuth2ClientCredentialsAuth
import os, requests
import streamlit as st

CLIENT_ID = os.environ.get("CIGNA_CLIENT_ID")
CLIENT_SECRET = os.environ.get("CIGNA_CLIENT_SECRET")

oauth2client = OAuth2Client(
    token_endpoint="https://r-hi2.cigna.com/mga/sps/oauth/oauth20/token",
    authorization_endpoint="https://r-hi2.cigna.com/mga/sps/oauth/oauth20/authorize",
    redirect_uri="https://dheeraj-insurancechat.streamlit.app/",
    userinfo_endpoint="https://fhir.cigna.com/PatientAccess/v1-devportal/$userinfo",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
)

st.write(oauth2client)
az_request = oauth2client.authorization_request(scope="openid fhirUser patient/*.read")
st.write(az_request.uri)

import webbrowser
response = webbrowser.open(az_request.uri)
print(response)