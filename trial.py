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


AUTHORIZE_ENDPOINT = "https://r-hi2.cigna.com/mga/sps/oauth/oauth20/authorize"
TOKEN_ENDPOINT = "https://r-hi2.cigna.com/mga/sps/oauth/oauth20/token"
REVOKE_ENDPOINT = "https://r-hi2.cigna.com/mga/sps/oauth/oauth20/revoke"
oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_ENDPOINT, TOKEN_ENDPOINT, REVOKE_ENDPOINT)
REDIRECT_URI = "https://trialpy.streamlit.app/"
SCOPE = "openid fhirUser patient/*.read"

result = oauth2.authorize_button(
        name="Continue with Cigna",
        icon="https://www.google.com.tw/favicon.ico",
        redirect_uri=REDIRECT_URI,
        scope=SCOPE,
        key="cigna",
        extras_params={"prompt": "consent", "access_type": "offline"},
        use_container_width=True,
        pkce='S256',
    )

st.write(result.get('token'))

token = result.get("token")["access_token"]
headers = {"Authorization":
               f"Bearer {token}"
           }

# Get user identifier
url = "https://fhir.cigna.com/PatientAccess/v1-devportal/$userinfo"
jsonString = requests.get(url, headers=headers)
data = json.loads(jsonString.content)
st.write(token)
st.write(data)
user_id = data["parameter"][0]["valueString"]


url = f"https://fhir.cigna.com/PatientAccess/v1-devportal/Patient?_id={user_id}"
#st.write(url)
jsonString = requests.get(url, headers=headers)
st.write(jsonString.headers)
data = json.loads(jsonString.content)
st.write(data)