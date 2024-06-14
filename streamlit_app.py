import tools, datetime, os, requests, json, base64
from io import StringIO
from langchain_core.messages import HumanMessage
import streamlit as st
from streamlit_oauth import OAuth2Component

# Set up the page configuration
st.set_page_config(
    page_title="Chat App",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

markdown="""
### Overview
This application is designed to provide automated support to insurance customers.
Can answer questions related to
- Plan that the user has subscribed to (Cigna CarePLan API)
- Basic plan information found on insurance cards (Cigna Coverage API)
- Explanation of Benefit (Cigna ExplanationOfBenefit API)
- Past Visits

Future Scope:
- Raise Claim

### Cigna API Integration
- Use CIgna Authorization API endpoint to authenticate user
- Use Cigna Patient Access API to get user information

### Tech Stack
- **Streamlit**: For building the interactive web application.
- **Langchain**: To extend the capabilities of the LLM with tools.
- **LangGraph**: For managing workflows and integrations.
- **OpenAI**: For natural language processing and responses.
- **ServiceNow Cloud APIs**: For ticketing and knowledge management.
- **Tavily**: For real-time web search and information retrieval.
"""

CLIENT_ID = os.environ.get("CIGNA_CLIENT_ID")
CLIENT_SECRET = os.environ.get("CIGNA_CLIENT_SECRET")
AUTHORIZE_ENDPOINT = "https://r-hi2.cigna.com/mga/sps/oauth/oauth20/authorize"
TOKEN_ENDPOINT = "https://r-hi2.cigna.com/mga/sps/oauth/oauth20/token"
REVOKE_ENDPOINT = "https://oauth2.googleapis.com/revoke"
oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_ENDPOINT, TOKEN_ENDPOINT, TOKEN_ENDPOINT)
REDIRECT_URI = "https://dheeraj-insurancechat.streamlit.app/"
SCOPE = "openid fhirUser patient/*.read"

if 'token' not in st.session_state:
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
  if result:
    st.session_state.token = result.get('token')
    st.rerun()
else:
    token = st.session_state.token["access_token"]
    headers = {"Authorization":
                   f"Bearer {token}"
               }
    st.write(token)
    # url = "https://fhir.cigna.com/PatientAccess/v1/$userinfo"
    url = "https://fhir.cigna.com/PatientAccess/v1-devportal/$userinfo"
    jsonString = requests.get(url, headers=headers)
    data = json.loads(jsonString.content)
    user_id = data["parameter"][0]["valueString"]

    headers = {"Authorization":
                   f"Bearer {token}"
               }
    url = f"https://fhir.cigna.com/PatientAccess/v1-devportal/Patient?_id={user_id}"
    print(url)
    jsonString = requests.get(url, headers=headers)
    data = json.loads(jsonString.content)
    #st.write(data)
    customer_name = data["entry"][0]["resource"]["name"][0]["given"][0]
    identifier = data["entry"][0]["resource"]["id"]


    # customer_name has the name of the logged in user
    # token has the bearer token to use with APIs
    url = f"https://fhir.cigna.com/PatientAccess/v1-devportal/CarePlan?patient={identifier}"
    st.write(url)
    jsonString = requests.get(url, headers=headers)
    data = json.loads(jsonString.content)
    st.write(data)

