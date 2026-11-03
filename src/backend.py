import os 
import certifi
from dotenv import load_dotenv

load_dotenv()

os.environ["SSL_CERT_FILE"] = certifi.where()
os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()

from typing import TypedDict, Annotated
import operator
import uuid

import psycopg
from psycopg.rows import dict_row

from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.postgres import PostgresSaver
from langchain_core.messages import (
    AnyMessage,
    HumanMessage,
    AIMessage,
    SystemMessage,
)
from langchain_groq import ChatGroq
from tools.tavily_tool import tavily_search
from tools.flight_tool import search_flights

from pydantic import BaseModel, SecretStr
# from src.keys import SecretKeys

def get_database_url():
    db_url = os.getenv("EXTERNAL_DB_URL",None)
    assert db_url is not None,"no db url is found. pls specify db_url"
    separator="&" if "?" in db_url else "?"
    db_url+=f"{separator}sslmode=require"
    return db_url


#=============
# LLM
#=============

GROQ_API_KEY = os.getenv("GROQ_API_KEY",None) # TODO do a load env module separately and check if all needed APIs are avaiable. Also include what to do if not avaiabale and fallbacks.# TODO make them into secrets

assert GROQ_API_KEY is not None,"missing GROQ_API_KEY, get new one from groqconsole and add to .env"

llm = ChatGroq(
    model="llama-3.3-70b-versatile",
    api_key=SecretStr(GROQ_API_KEY)# TODO check if this is correct
    )


# =============
# STATE
# =============

class TravelState(TypedDict):
    messages:Annotated[list[AnyMessage],operator.add]
    user_query:str
    flight_results:str
    hotel_results:str
    itinerary:str
    llm_calls:int


# =============
# FLIGHT AGENT
# =============


def flight_agent(state:TravelState) -> dict:
    query=state.get("user_query",None)

    assert query is not None,"No query raised."

    return {
        "flight_results" : search_flights(query,20),
        "messages" : [
            AIMessage(content="Flight results fetched"),
        ],
        "llm_calls":state.get("llm_calls",0)+1
    }


# =============
# HOTEL AGENT
# =============

def hotel_agent(state:TravelState) ->dict:

    # TODO - look for mentions or semantic equivalence for hotels. if not found, add specifically.

    query = state.get("user_query",None)
    query += "Look for hotels as well."

    assert query is not None,"No query raised."

    return {
        "hotel_results" : tavily_search(query),
        "messages" : [
            AIMessage(content="hotel results fetched"),
        ],
        "llm_calls":state.get("llm_calls",0)+1
    }





