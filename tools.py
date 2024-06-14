import requests, json, os
from langchain.pydantic_v1 import BaseModel, Field
from langchain.agents import tool
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
import operator
from tavily import TavilyClient
from langchain.adapters.openai import convert_openai_messages
from langchain_openai import ChatOpenAI
from langchain_community.tools.tavily_search import TavilySearchResults

tavily_tool = TavilySearchResults(max_results=4) #increased number of results

class SubscriberOrBeneficiarySearch(BaseModel):
    token: str = Field(..., description="Bearer token to use for invoking CIGNA APIs")
    identifier: str = Field(..., description="Identifier of the subscriber or beneficiary. Example is ifp-8972693f-069b-4714-82f9-f805ebf7800f")

@tool(args_schema=SubscriberOrBeneficiarySearch)
def get_person_details(token, identifier):
    """Get subscriber or beneficiary details based on the identifier provided"""
    headers = {"Authorization":
                   f"Bearer {token}"
               }
    url = f"https://fhir.cigna.com/PatientAccess/v1-devportal/Patient/{identifier}"
    jsonString = requests.get(url, headers=headers)
    data = json.loads(jsonString.content)
    return data

class CoverageDetails(BaseModel):
    token: str = Field(..., description="Bearer token to use for invoking CIGNA APIs")
    identifier: str = Field(..., description="Identifier of the subscriber. Example is ifp-8972693f-069b-4714-82f9-f805ebf7800f")

@tool(args_schema=CoverageDetails)
def get_coverage_details(token, identifier):
    """Get coverage / benefits details based on the identifier provided."""
    headers = {"Authorization":
                   f"Bearer {token}"
               }
    url = f"https://fhir.cigna.com/PatientAccess/v1-devportal/Coverage?patient={identifier}"
    jsonString = requests.get(url, headers=headers)
    data = json.loads(jsonString.content)
    return data


class SearchInput(BaseModel):
    query: str = Field(description="should be a search query")

client = TavilyClient(os.getenv("TAVILY_API_KEY"))

@tool(args_schema=SearchInput)
def get_help(query):
    """Does a search to get detailed instructions/help based on user query"""
    content = client.search(query, search_depth="advanced")["results"]

    # setup prompt
    prompt = [{
        "role": "system",
        "content": f'You are an AI research assistant. ' \
                   f'Your sole purpose is to provide a steps to setup instructions for user query'
    }, {
        "role": "user",
        "content": f'Information: """{content}"""\n\n' \
                   f'Using the above information, answer the following' \
                   f'query: "{query}" as a series if setps to take --' \
        }]

    # run gpt-4
    lc_messages = convert_openai_messages(prompt)
    report = ChatOpenAI(model='gpt-4o', openai_api_key=os.getenv("OPENAI_API_KEY")).invoke(lc_messages).content

    # print report
    return report


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], operator.add]


class Agent:
    def __init__(self, model, tools, checkpointer, system=""):
        self.system = system
        graph = StateGraph(AgentState)
        graph.add_node("llm", self.call_openai)
        graph.add_node("action", self.take_action)
        graph.add_conditional_edges("llm", self.exists_action, {True: "action", False: END})
        graph.add_edge("action", "llm")
        graph.set_entry_point("llm")
        self.graph = graph.compile(checkpointer=checkpointer)
        self.tools = {t.name: t for t in tools}
        self.model = model.bind_tools(tools)

    def call_openai(self, state: AgentState):
        # print("Calling open AI")
        messages = state['messages']
        if self.system:
            messages = [SystemMessage(content=self.system)] + messages
        message = self.model.invoke(messages)
        return {'messages': [message]}

    def exists_action(self, state: AgentState):
        # print("in exists action")
        result = state['messages'][-1]
        return len(result.tool_calls) > 0

    def take_action(self, state: AgentState):
        tool_calls = state['messages'][-1].tool_calls
        results = []
        for t in tool_calls:
            # print(f"Calling: {t}")
            result = self.tools[t['name']].invoke(t['args'])
            results.append(ToolMessage(tool_call_id=t['id'], name=t['name'], content=str(result)))

        # print("Back to the model!")
        return {'messages': results}



