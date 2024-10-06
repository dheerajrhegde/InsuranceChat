import tools, datetime, os, requests, json, base64
from io import StringIO
from langchain_core.messages import HumanMessage
import streamlit as st
from streamlit_oauth import OAuth2Component
from langchain_openai import ChatOpenAI
import tools, uuid
from langgraph.checkpoint.sqlite import SqliteSaver
from requests_oauth2client import OAuth2Client

memory = SqliteSaver.from_conn_string(":memory:")

# Set up the page configuration
st.set_page_config(
    page_title="Chat App",
    page_icon="💬",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def add_message(user, text):
    """
    Adds a new message to the session state.

    Args:
        user (str): The user who sent the message.
        text (str): The text message sent by the user.
    """
    st.session_state["user_queries"].append({
        "user": user,
        "text": text,
        "time": datetime.datetime.now().strftime("%H:%M:%S")
    })


# Function to display chat messages
def display_messages():
    """
    Displays chat messages stored in session state.

    Messages are displayed in reverse order (most recent first).
    """
    for message in st.session_state["user_queries"][::-1]:
        st.write(f"[{message['time']}] {message['user']}: {message['text']}")

markdown = """
### Overview


### Cigna API Integration


### Tech Stack

"""

CLIENT_ID = os.environ.get("CIGNA_CLIENT_ID")
CLIENT_SECRET = os.environ.get("CIGNA_CLIENT_SECRET")
AUTHORIZE_ENDPOINT = "https://r-hi2.cigna.com/mga/sps/oauth/oauth20/authorize"
TOKEN_ENDPOINT = "https://r-hi2.cigna.com/mga/sps/oauth/oauth20/token"
REVOKE_ENDPOINT = "https://r-hi2.cigna.com/mga/sps/oauth/oauth20/revoke"
oauth2 = OAuth2Component(CLIENT_ID, CLIENT_SECRET, AUTHORIZE_ENDPOINT, TOKEN_ENDPOINT, REVOKE_ENDPOINT)
REDIRECT_URI = "https://dheeraj-insurancechat.streamlit.app/"
SCOPE = "openid fhirUser patient/*.read"

if 'token' not in st.session_state:
    # Authenticate using Cigna authorization API
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
        # Rerun the app to get the token and display the UI components
        # Done only whenn token is retrived
        st.session_state.token = result.get('token')
        st.rerun()
else:
    token = st.session_state.token["access_token"]
    headers = {"Authorization":
                   f"Bearer {token}"
               }

    # Get user identifier
    url = "https://fhir.cigna.com/PatientAccess/v1-devportal/$userinfo"
    jsonString = requests.get(url, headers=headers)
    data = json.loads(jsonString.content)
    #st.write(token)
    #st.write(data)
    user_id = data["parameter"][0]["valueString"]

    # Get user details
    headers = {"Authorization":
                   f"Bearer {token}"
               }
    url = f"https://fhir.cigna.com/PatientAccess/v1-devportal/Patient?_id={user_id}"
    #st.write(url)
    jsonString = requests.get(url, headers=headers)
    #st.write(jsonString)
    data = json.loads(jsonString.content)
    #st.write(data)
    customer_name = data["entry"][0]["resource"]["name"][0]["given"][0]
    identifier = data["entry"][0]["resource"]["id"]

    prompt = f"""
    You are a very polite customer care agent.You have access to certain tools that help you get information about 
    - Subscriber or Beneficiary
    - Coverage Details
    - Explanation of Benefits
    - Past Visits
    
    Steps to follow:
    Step 1: Check if the question is related to Cigna insurnance products ad the plan that the customer has. 
    Step 2: Identify the questions that are not related to Cigna insurance products and provide the customer with the right contact information. And respectfully declline to answer them
    Step 3: Take the questions related to Cigna insurance products and use the tools provided to answer the customer queries
        - You use these provided tools to answer customer queries 
        - You are allowed to make multiple calls (either together or in sequence). \
        - Only look up information when you are sure of what you want. \
    Step 4: If you need to look up some information before asking a follow up question, you are allowed to do that!
    Step 5: If you are not able to answer, you can tell the user that a agent will back at the customer's phone number.
        - Give the phone number of the customer and ask if that is the number he/she should be called at?

    Only when the conversation has fully ended, you can thank the user for the opportunity to server and end the chat.
    
    Calling customer's name is {customer_name}
    Calling customer's identifier is {identifier}
    Additional customer information available in {data}
    Token for the API is {token}
    """

    tool = [tools.get_person_details, tools.get_coverage_details, tools.get_plan_information,
            tools.get_explanation_of_benefit, tools.get_encounters, tools.get_doctors]

    model = ChatOpenAI(model="gpt-4o")
    if "abot" not in st.session_state:
        st.session_state.abot = tools.Agent(model, tool, system=prompt, checkpointer=memory)
        st.session_state.thread = {"configurable": {"thread_id": uuid.uuid4() }}

    if "user_queries" not in st.session_state:
        st.session_state["user_queries"] = []

    # Title of the app
    st.title("Customer InsurAssist")

    # create 3 columns to organize the UI
    # col1: markdown content describing the app
    # col2: input form for sending a new message
    # col3: chat messages from user and the model
    st.session_state.col1, st.session_state.col2, st.session_state.col3 = st.columns([0.3, 0.2, 0.5])
    with st.session_state.col1:
        st.markdown(markdown)

    # Input form for sending a new message
    with st.session_state.col2:
        with st.form("message_form", clear_on_submit=True):
            user = st.text_input("Your name", key="name", max_chars=50,
                                 value=data["entry"][0]["resource"]["name"][0]["given"][0])
            user_query = st.text_area("Message", key="user_query", max_chars=500)
            send_button = st.form_submit_button("Send")

            add_message(customer_name, user_query)

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
