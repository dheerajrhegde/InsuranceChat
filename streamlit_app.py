import tools, datetime, os, requests, json, base64
from io import StringIO
from langchain_core.messages import HumanMessage
import streamlit as st
from streamlit_oauth import OAuth2Component
from langchain_openai import ChatOpenAI
import tools
from langgraph.checkpoint.sqlite import SqliteSaver

memory = SqliteSaver.from_conn_string(":memory:")

# Set up the page configuration
st.set_page_config(
    page_title="Chat App",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)


def add_message(user, text):
    st.session_state["user_queries"].append({
        "user": user,
        "text": text,
        "time": datetime.datetime.now().strftime("%H:%M:%S")
    })


# Function to display chat messages
def display_messages():
    for message in st.session_state["user_queries"][::-1]:
        st.write(f"[{message['time']}] {message['user']}: {message['text']}")

markdown="""
### Overview


### Cigna API Integration


### Tech Stack

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
    #st.write(data)
    user_id = data["parameter"][0]["valueString"]

    headers = {"Authorization":
                   f"Bearer {token}"
               }
    url = f"https://fhir.cigna.com/PatientAccess/v1-devportal/Patient?_id={user_id}"
    #st.write(url)
    jsonString = requests.get(url, headers=headers)
    data = json.loads(jsonString.content)
    #st.write(data)
    customer_name = data["entry"][0]["resource"]["name"][0]["given"][0]
    identifier = data["entry"][0]["resource"]["id"]

    prompt = """
    You are a very polite customer care agent. You have acccess to certain
    tools that help you get information about 
    - Subscriber or Beneficiary
    - Coverage Details
    - Explanation of Benefits
    - Past Visits

    You use these provided tools to answer customer queries 
    You are allowed to make multiple calls (either together or in sequence). \
    Only look up information when you are sure of what you want. \
    If you need to look up some information before asking a follow up question, you are allowed to do that!

    If you are not able to answer, you can tell the user that a agent will back at the customer's phone number

    Thank the user for the opportunity to server and end the call.
    
    Calling customer's name is {customer_name}
    Calling customer's identifier is {identifier}
    """

    tool = [tools.get_person_details]
    model = ChatOpenAI(model="gpt-4o")
    if "abot" not in st.session_state:
        st.session_state.abot = tools.Agent(model, tool, system=prompt, checkpointer=memory)
        st.session_state.thread = {"configurable": {"thread_id": "1"}}

    if "user_queries" not in st.session_state:
        st.session_state["user_queries"] = []


    def add_message(user, text):
        st.session_state["user_queries"].append({
            "user": user,
            "text": text,
            "time": datetime.datetime.now().strftime("%H:%M:%S")
        })

    # Function to display chat messages
    def display_messages():
        for message in st.session_state["user_queries"][::-1]:
            st.write(f"[{message['time']}] {message['user']}: {message['text']}")

    # Title of the app
    st.title("Customer InsurAssist")

    st.session_state.col1, st.session_state.col2, st.session_state.col3 = st.columns([0.3, 0.2, 0.5])
    with st.session_state.col1:
        st.markdown(markdown)
    # Input form for sending a new message
    with st.session_state.col2:
        with st.form("message_form", clear_on_submit=True):
            user = st.text_input("Your name", key="name", max_chars=50,
                                 value=data["entry"][0]["resource"]["name"][0]["given"][0])
            user_query = st.text_input("Message", key="user_query", max_chars=500)
            send_image = st.file_uploader("Choose a file")
            send_button = st.form_submit_button("Send")

            if send_button and user_query:
                messages = [HumanMessage(content=user_query)]
                result = st.session_state.abot.graph.invoke({"messages": messages}, st.session_state.thread)
                add_message("agent", result['messages'][-1].content)

    with st.session_state.col3:
        # Display the chat messages
        st.subheader("Chat History")
        display_messages()

    # Streamlit application
    st.write("---")
    st.write("Simple chat application using Streamlit.")