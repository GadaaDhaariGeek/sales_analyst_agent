from langgraph.graph import StateGraph, START, END
from langchain_core.messages import BaseMessage, SystemMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from typing import TypedDict
import json
from dotenv import load_dotenv

import os
load_dotenv()

from src.analysis_agent_spec import build_the_graph, financial_analyst_agent

    
from src.utils import load_csv_files_into_sqlitedb, get_table_schema_and_sample_rows
# class AgentSchema(TypedDict):


def print_messages(messages):
    """Function I made to print the messages in a more readable format"""
    if not messages:
        return

    for message in messages[-3:]:
        if isinstance(message, ToolMessage):
            print(f"\n🛠️ TOOL RESULT: {message.content}")

# def run_document_agent():
#     print("\n ===== DRAFTER =====")

#     state = {"messages": []}

#     for step in app.stream(state, stream_mode="values"):
#         if "messages" in step:
#             print_messages(step["messages"])

#     print("\n ===== DRAFTER FINISHED =====")





if __name__ == "__main__":
    print("Hello: ")
    if not os.path.exists(os.environ["DB_NAME"]):
        # print("Hi")
        load_csv_files_into_sqlitedb()
    else:
        # print("hi2")
        print(f"Database {os.environ['DB_NAME']} already exists. Skipping CSV load.")

    graph = build_the_graph()
    app = graph.compile()

    financial_analyst_agent(
        state = {"messages": []},
        user_query = "Show me the top 5 customers by sales amount."
    )





    

    # schemas, samples = get_table_schema_and_sample_rows(os.environ["DB_NAME"])
    # schemas_and_samples = get_table_schema_and_sample_rows(os.environ["DB_NAME"])
    # print(json.dumps(schemas_and_samples, indent=4))



    
    

    