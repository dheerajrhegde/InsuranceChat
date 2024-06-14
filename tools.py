import requests, json
from langchain.pydantic_v1 import BaseModel, Field
from langchain.agents import tool
from langgraph.graph import StateGraph, END
from typing import TypedDict, Annotated
from langchain_core.messages import AnyMessage, SystemMessage, HumanMessage, ToolMessage
import operator


class SubscriberOrBeneficiarySearch(BaseModel):
    token: str = Field(..., description="Bearer token to use for invoking CIGNA APIs")
    identifier: str = Field(..., description="Identifier of the subscriber or beneficiary. Example is ifp-8972693f-069b-4714-82f9-f805ebf7800f")

@tool(args_schema=SubscriberOrBeneficiarySearch)
def get_person_details(token, identifier):
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
    headers = {"Authorization":
                   f"Bearer {token}"
               }
    url = f"https://fhir.cigna.com/PatientAccess/v1-devportal/Coverage?patient={identifier}"
    jsonString = requests.get(url, headers=headers)
    data = json.loads(jsonString.content)
    return data

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



