import warnings 
warnings.filterwarnings('ignore')
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage,SystemMessage
import google.generativeai as genai
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.tools import tool
import requests
from langgraph.graph import StateGraph, END
from langchain_tavily import TavilySearch
from typing import (Annotated,Sequence,TypedDict)
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages
from langchain_community.tools.tavily_search import TavilySearchResults
from langchain.tools import tool
import os
import json
from dotenv import load_dotenv

load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY)

model = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")
search = TavilySearchResults()

@tool
def search_tool(query: str):
    """
    Search the web for information using Tavily API.

    :param query: The search query string
    :return: Search results related to the query
    """
    return search.invoke(query)

@tool
def recommend_clothing(weather: str) -> str:
    """
    Returns a clothing recommendation based on the provided weather description.

    This function examines the input string for specific keywords or temperature indicators 
    (e.g., "snow", "freezing", "rain", "85°F") to suggest appropriate attire. It handles 
    common weather conditions like snow, rain, heat, and cold by providing simple and practical 
    clothing advice.

    :param weather: A brief description of the weather (e.g., "Overcast, 64.9°F")
    :return: A string with clothing recommendations suitable for the weather
    """
    weather = weather.lower()
    if "snow" in weather or "freezing" in weather:
        return "Wear a heavy coat, gloves, and boots."
    elif "rain" in weather or "wet" in weather:
        return "Bring a raincoat and waterproof shoes."
    elif "hot" in weather or "85" in weather:
        return "T-shirt, shorts, and sunscreen recommended."
    elif "cold" in weather or "50" in weather:
        return "Wear a warm jacket or sweater."
    else:
        return "A light jacket should be fine."



chat_prompt = ChatPromptTemplate.from_messages([
    ("system", """
You are a helpful AI assistant that thinks step-by-step and uses tools when needed.

When responding to queries:
1. First, think about what information you need
2. Use available tools if you need current data or specific capabilities  
3. Provide clear, helpful responses based on your reasoning and any tool results

Always explain your thinking process to help users understand your approach.
"""),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="scratch_pad")
])



@tool
def get_current_weather(location: str) -> dict:
    """Returns the current weather for a given location using Open-Meteo API."""
    # Geocoding to get latitude and longitude
    geo_url = f"https://geocoding-api.open-meteo.com/v1/search?name={location}&count=1"
    geo_resp = requests.get(geo_url)
    geo_data = geo_resp.json()
    if not geo_data.get("results"):
        return {"error": "Location not found"}
    lat = geo_data["results"][0]["latitude"]
    lon = geo_data["results"][0]["longitude"]

    # Get current weather
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}"
        "&current_weather=true"
    )
    weather_resp = requests.get(weather_url)
    weather_data = weather_resp.json()
    if "current_weather" not in weather_data:
        return {"error": "Weather data not available"}
    current = weather_data["current_weather"]
    return {
        "temperature": f"{current['temperature']}°C",
        "windspeed": f"{current['windspeed']} km/h",
        "weathercode": current["weathercode"]
    }

# Unify all tools into a single list and bind once
tools = [search_tool, recommend_clothing, get_current_weather]
tools_by_name = {tool.name: tool for tool in tools}
model_react = model.bind_tools(tools)


class AgentState(TypedDict):
    """The state of the agent."""

    # add_messages is a reducer
    # See https://langchain-ai.github.io/langgraph/concepts/low_level/#reducers
    messages: Annotated[Sequence[BaseMessage], add_messages]
    
# Example conversation flow:
state: AgentState = {"messages": []}

# append a message using the reducer properly
state["messages"] = add_messages(state["messages"], [HumanMessage(content="Hi")])
print("After greeting:", state["messages"])

# add another message (e.g. a question)
state["messages"] = add_messages(state["messages"], [HumanMessage(content="Weather in NYC?")])
print("After question:", state)    


dummy_state: AgentState = {
    "messages": [HumanMessage("What's the weather like in Zurich, and what should I wear based on the temperature?")]
}




# Use the chain with the prompt template
chain = chat_prompt | model_react
response = chain.invoke({
    "input": "What's the weather like in Zurich, and what should I wear based on the temperature?",
    "scratch_pad": []
})

# The rest of your code to process the response
# Note: I am assuming `add_messages` is a function from your langgraph setup.
dummy_state["messages"] = add_messages(dummy_state["messages"], [response])
print(dummy_state)




response = chain.invoke({
    "input": "What's the weather like in Zurich, and what should I wear based on the temperature?",
    "scratch_pad": []
})

dummy_state['messages'] = add_messages(dummy_state['messages'], [response])

# check if the model wants to use another tool
if response.tool_calls:
    tool_call = response.tool_calls[0]
    tool_result = tools_by_name[tool_call["name"]].invoke(tool_call["args"])
    tool_message = ToolMessage(
        content=json.dumps(tool_result),
        name=tool_call["name"],
        tool_call_id=tool_call["id"]
    )
    dummy_state['messages'] = add_messages(dummy_state['messages'], [tool_message])
    
    
def call_model(state: AgentState):
    print("\n[DEBUG] call_model - messages:", state["messages"])
    print("[DEBUG] call_model - types:", [type(m) for m in state["messages"]])
    for i, m in enumerate(state["messages"]):
        print(f"[DEBUG] call_model - message {i} content:", getattr(m, 'content', m))
    response = model_react.invoke(state["messages"])
    # Return the full message history, appending the new response
    return {"messages": state["messages"] + [response]}

def tool_node(state: AgentState):
    print("\n[DEBUG] tool_node - messages:", state["messages"])
    print("[DEBUG] tool_node - types:", [type(m) for m in state["messages"]])
    for i, m in enumerate(state["messages"]):
        print(f"[DEBUG] tool_node - message {i} content:", getattr(m, 'content', m))
    outputs = []
    for tool_call in state["messages"][-1].tool_calls:
        tool_result = tools_by_name[tool_call["name"]].invoke(tool_call["args"])
        outputs.append(
            ToolMessage(
                content=json.dumps(tool_result),
                name=tool_call["name"],
                tool_call_id=tool_call["id"]
            )
        )
    # Return the full message history, appending all tool outputs
    return {"messages": state["messages"] + outputs}

def should_continue(state: AgentState):
    """Determine whether to continue with tool use or end the conversation."""
    messages = state["messages"]
    last_message = messages[-1]
    # If there is no function call, then we finish
    if not last_message.tool_calls:
        return "end"
    # Otherwise if there is, we continue
    else:
        return "continue"


# Define a new graph
workflow = StateGraph(AgentState)

# Define the two nodes we will cycle between
workflow.add_node("agent", call_model)
workflow.add_node("tools", tool_node)

# Add edges between nodes
workflow.add_edge("tools", "agent")  # After tools, always go back to agent

# Add conditional logic
workflow.add_conditional_edges(
    "agent",
    should_continue,
    {
        "continue": "tools",  # If tools needed, go to tools node
        "end": END,           # If done, end the conversation
    },
)

# Set entry point
workflow.set_entry_point("agent")

# Compile the graph
graph = workflow.compile()


def print_stream(stream):
    """Helper function for formatting the stream nicely."""
    for s in stream:
        message = s["messages"][-1]
        if isinstance(message, tuple):
            print(message)
        else:
            message.pretty_print()

inputs = {"messages": [HumanMessage(content="What's the weather like in Addis Ababa , and what should I wear based on the temperature?")]}

print_stream(graph.stream(inputs, stream_mode="values"))