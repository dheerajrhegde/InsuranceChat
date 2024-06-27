from requests_oauth2client import OAuth2Client, OAuth2ClientCredentialsAuth
import os, requests, json
import streamlit as st
from streamlit_oauth import OAuth2Component

CLIENT_ID = os.environ.get("CIGNA_CLIENT_ID")
CLIENT_SECRET = os.environ.get("CIGNA_CLIENT_SECRET")

oauth2client = OAuth2Client(
    token_endpoint="https://r-hi2.cigna.com/mga/sps/oauth/oauth20/token",
    authorization_endpoint="https://r-hi2.cigna.com/mga/sps/oauth/oauth20/authorize",
    redirect_uri="https://trialpy.streamlit.app/",
    userinfo_endpoint="https://fhir.cigna.com/PatientAccess/v1-devportal/$userinfo",
    client_id=CLIENT_ID,
    client_secret=CLIENT_SECRET,
)

st.write(oauth2client)
az_request = oauth2client.authorization_request(scope="openid fhirUser patient/*.read")
st.write(az_request.uri)

st.write(st.session_state)
st.write(st.query_params)

token_url = "https://hi2.cigna.com/mga/sps/oauth/oauth20/token"
body = {
    "grant_type": "authorization_code",
    "code": st.query_params["code"],
    "redirect_uri": "https://trialpy.streamlit.app/",
    "client_id":CLIENT_ID,
    "client_secret":CLIENT_SECRET
}
st.write("body to post is ...",body)
response = requests.post(token_url, body=body)
st.write(response.json())


