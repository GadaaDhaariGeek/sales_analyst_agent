from src.prompts import FINANCIAL_ANALYST_AGENT_PROMPT
from typing import TypedDict, List, Union
from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_openai import ChatOpenAI
import sqlite3
import os
from dotenv import load_dotenv
load_dotenv()
from langchain_core.tools import tool
from langgraph.graph import StateGraph, END

from langchain.prompts import ChatPromptTemplate



class AgentSchema(TypedDict):
    messages: List[Union[HumanMessage, AIMessage]]




# @tool
# def sql_generator_and_executor_tool():
#     """" Function to generate and execute SQL queries based on user input."""
#     pass

@tool
def sql_executor(query: str) -> dict:
    """Function to execute the given SQL query and return the results in json format."""
    conn = sqlite3.connect(os.environ["DB_NAME"])
    conn.row_factory = sqlite3.Row  # To access columns by name
    cursor = conn.cursor()
    try:
        cursor.execute(str)
        rows = cursor.fetchall()
        results = [dict(row) for row in rows]
        return {"results": results}
    except sqlite3.Error as e:
        return {"error": str(e)}
    

def data_analyzer():
    pass

def data_visualizer():
    pass

def financial_analyst_agent(state: AgentSchema, user_query: str) -> AgentSchema:
    # system_prompt = SystemMessage(FINANCIAL_ANALYST_AGENT_PROMPT.format(user_query=user_query))
    template = ChatPromptTemplate.from_template(
        FINANCIAL_ANALYST_AGENT_PROMPT,
        template_format="jinja2"
    )
    
    # print(system_prompt)
    llm = ChatOpenAI(model=os.environ["LLM_MODEL"], temperature=0)

    user_query = input("What do you want to ask? ")
    print(f"User Query: {user_query}")
    system_prompt = template.format_messages(user_query=user_query)
    print(len(system_prompt))
    # print(f"\n\nSystem Prompt: \n{system_prompt}")
    while user_query != "exit" or "bye":
        user_message = HumanMessage(content=user_query)
        print(f"\n\nUser message: \n{user_message}")

        print(type(system_prompt), type(state["messages"]), type(user_message))

        all_messages = system_prompt + list(state["messages"]) + [user_message]
        # print(f"\n\nAll messages: \n{all_messages}")

        response = llm.invoke(all_messages)
        # print(f"\n\nResponse: \n {response}")
        # print(response)
        print(response.content)
        
        state = {"messages": list(state["messages"]) + [user_message, response]}
        user_query = input()
        # print(state)
        # break


def should_continue(state: AgentSchema) -> bool:
    last_message = state["messages"][-1]
    print(f"\n\nLast message: \n{last_message}")
    return hasattr(last_message, "tool_calls") and len(last_message.tool_calls) > 0


def build_the_graph():
    graph = StateGraph(AgentSchema)
    graph.add_node("financial_analyst_agent", financial_analyst_agent)
    graph.set_entry_point("financial_analyst_agent")
    graph.add_conditional_edges(
        source = "financial_analyst_agent", 
        path = should_continue, 
        path_map = {
            True: "financial_analyst_agent",
            False: END
        }
    )

    return graph

    


