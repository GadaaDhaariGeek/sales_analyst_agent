"""
LangGraph agent workflow for Sales Analyst.
Defines the graph structure, nodes, edges, and tool implementations.
"""

import sqlite3
import pandas as pd
from pathlib import Path
from typing import Any, Dict, List
from datetime import datetime

from langchain_openai import ChatOpenAI
from langchain_core.messages import BaseMessage, HumanMessage, AIMessage, ToolMessage
from langchain_core.tools import BaseTool
from langchain.tools import tool
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import ToolNode
from langgraph.types import StreamWriter
from sqlalchemy import create_engine, inspect, text

from src.prompts import (
    SYSTEM_PROMPT,
    TOOL_DESCRIPTIONS,
)
from src.logger import setup_logging, log_graph_execution, log_tool_call


# Initialize logger
logger = setup_logging("SalesAnalystAgent")


# ============================================================================
# TOOL IMPLEMENTATIONS
# ============================================================================

class SalesDataAgent:
    """Core sales data agent with tool implementations"""
    
    def __init__(self, db_path: str, tables_folder: str):
        """Initialize the agent with database connection"""
        self.db_path = db_path
        self.tables_folder = Path(tables_folder)
        self.engine = None
        self.connection = None
        
        logger.info("Initializing SalesDataAgent")
        self._setup_database()
        self._initialize_tools()
    
    def _setup_database(self):
        """Setup SQLite database with CSV data"""
        logger.info("Setting up database...")
        
        try:
            # Load CSV files
            conn = sqlite3.connect(self.db_path)
            
            csv_files = {
                'cities': 'cities.csv',
                'countries': 'countries.csv',
                'customers': 'customers.csv',
                'employees': 'employees.csv',
                'products': 'products.csv',
                'sales': 'sales.csv'
            }
            
            for table_name, csv_file in csv_files.items():
                file_path = self.tables_folder / csv_file
                if file_path.exists():
                    df = pd.read_csv(file_path)
                    df.to_sql(table_name, conn, if_exists='replace', index=False)
                    logger.info(f"Loaded table '{table_name}': {len(df)} rows")
                else:
                    logger.warning(f"CSV file not found: {csv_file}")
            
            conn.close()
            
            # Create SQLAlchemy engine
            self.engine = create_engine(f"sqlite:///{self.db_path}")
            logger.info("Database setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up database: {str(e)}", exc_info=True)
            raise
    
    def _initialize_tools(self):
        """Initialize tool definitions"""
        logger.debug("Initializing tools")
        self.tools = [
            self.query_sales_database,
            self.generate_visualization,
            self.analyze_metrics
        ]
    
    @tool
    def query_sales_database(self, query: str, query_type: str = "general") -> str:
        """Query the sales database using natural language."""
        log_tool_call(logger, "query_sales_database", {"query": query, "query_type": query_type})
        
        try:
            # For demonstration, execute a sample query
            # In production, you'd use NLtoSQL engine
            with self.engine.connect() as conn:
                # Example: Get sales summary
                result = conn.execute(text("""
                    SELECT 
                        COUNT(*) as total_sales,
                        SUM(amount) as total_revenue,
                        AVG(amount) as avg_sale,
                        MAX(amount) as max_sale
                    FROM sales
                """))
                
                row = result.fetchone()
                response = f"""
                Sales Summary:
                - Total Sales: {row[0]}
                - Total Revenue: ${row[1]:,.2f}
                - Average Sale: ${row[2]:,.2f}
                - Maximum Sale: ${row[3]:,.2f}
                """
                
                logger.info(f"Database query executed: {query_type}")
                return response
        
        except Exception as e:
            logger.error(f"Error querying database: {str(e)}", exc_info=True)
            return f"Error querying database: {str(e)}"
    
    @tool
    def generate_visualization(
        self,
        title: str,
        chart_type: str,
        data_description: str,
        x_axis: str = "",
        y_axis: str = ""
    ) -> str:
        """Generate a visualization."""
        log_tool_call(logger, "generate_visualization", {
            "title": title,
            "chart_type": chart_type,
            "data_description": data_description
        })
        
        try:
            valid_types = ["bar", "line", "pie", "scatter", "histogram", "box"]
            if chart_type not in valid_types:
                logger.warning(f"Invalid chart type: {chart_type}")
                chart_type = "bar"
            
            response = f"""
            Visualization Generated:
            - Title: {title}
            - Type: {chart_type.upper()}
            - Description: {data_description}
            - X-Axis: {x_axis or "Not specified"}
            - Y-Axis: {y_axis or "Not specified"}
            
            [Chart would be displayed in UI]
            """
            
            logger.info(f"Visualization created: {chart_type}")
            return response
        
        except Exception as e:
            logger.error(f"Error generating visualization: {str(e)}")
            return f"Error generating visualization: {str(e)}"
    
    @tool
    def analyze_metrics(
        self,
        metric_type: str,
        description: str,
        time_period: str = "current"
    ) -> str:
        """Analyze business metrics."""
        log_tool_call(logger, "analyze_metrics", {
            "metric_type": metric_type,
            "description": description,
            "time_period": time_period
        })
        
        try:
            response = f"""
            Metrics Analysis:
            - Metric Type: {metric_type}
            - Analysis: {description}
            - Time Period: {time_period}
            
            [Detailed analysis would be provided based on actual data]
            """
            
            logger.info(f"Metrics analysis completed: {metric_type}")
            return response
        
        except Exception as e:
            logger.error(f"Error analyzing metrics: {str(e)}")
            return f"Error analyzing metrics: {str(e)}"


# ============================================================================
# GRAPH NODE DEFINITIONS
# ============================================================================

def create_agent_graph(agent: SalesDataAgent, model: ChatOpenAI):
    """
    Create and compile the agent graph.
    
    Args:
        agent: SalesDataAgent instance
        model: ChatOpenAI model instance
    
    Returns:
        Compiled graph ready for execution
    """
    
    logger.info("Creating agent graph")
    
    # Bind tools to model
    tools_list = agent.tools
    model_with_tools = model.bind_tools(tools_list)
    
    # Define state as a dictionary
    from typing import TypedDict, Annotated
    import operator
    
    class MessagesState(TypedDict):
        """State for the graph"""
        messages: Annotated[List[BaseMessage], operator.add]
    
    # Node 1: Agent reasoning and tool selection
    def agent_node(state: MessagesState, writer: StreamWriter):
        """Agent node - calls LLM to decide next action"""
        logger.info("Executing agent node")
        
        messages = state["messages"]
        
        # Add system prompt
        messages_with_system = [
            HumanMessage(content=SYSTEM_PROMPT)
        ] + messages
        
        # Call LLM
        response = model_with_tools.invoke(messages_with_system)
        
        logger.debug(f"Agent response type: {type(response).__name__}")
        logger.debug(f"Response has tool calls: {hasattr(response, 'tool_calls')}")
        
        # Stream the response
        writer(f"Agent: {response.content}\n")
        
        return {"messages": [response]}
    
    # Node 2: Tool execution
    def tool_node(state: MessagesState, writer: StreamWriter):
        """Execute tools and return results"""
        logger.info("Executing tool node")
        
        tool_node = ToolNode(tools_list)
        result = tool_node.invoke(state)
        
        # Log and stream tool results
        if result.get("messages"):
            for msg in result["messages"]:
                if isinstance(msg, ToolMessage):
                    logger.info(f"Tool result: {msg.tool_name}")
                    writer(f"Tool {msg.tool_name}: {msg.content}\n")
        
        return result
    
    # Edge function: Should we continue or end?
    def should_continue(state: MessagesState) -> str:
        """Determine if we should continue with tools or end"""
        messages = state["messages"]
        last_message = messages[-1]
        
        # If LLM wants to use tools, go to tool execution
        if hasattr(last_message, "tool_calls") and last_message.tool_calls:
            logger.info("Agent selected tools, routing to tool_node")
            return "tools"
        else:
            logger.info("Agent finished, routing to END")
            return "end"
    
    # Build the graph
    graph_builder = StateGraph(MessagesState)
    
    # Add nodes
    graph_builder.add_node("agent", agent_node)
    graph_builder.add_node("tools", tool_node)
    
    # Add edges
    graph_builder.add_edge(START, "agent")
    graph_builder.add_conditional_edges(
        "agent",
        should_continue,
        {
            "tools": "tools",
            "end": END,
        },
    )
    graph_builder.add_edge("tools", "agent")
    
    # Compile the graph
    graph = graph_builder.compile()
    
    logger.info("Agent graph created and compiled successfully")
    
    return graph


# ============================================================================
# INITIALIZATION HELPER
# ============================================================================

def initialize_agent(
    db_path: str = "sales_data.db",
    tables_folder: str = "./data",
    model_name: str = "gpt-4o-mini",
    temperature: float = 0.0
):
    """
    Initialize the complete agent with database and model.
    
    Args:
        db_path: Path to SQLite database
        tables_folder: Path to CSV files
        model_name: OpenAI model name
        temperature: Model temperature
    
    Returns:
        Compiled graph ready for execution
    """
    
    logger.info("Starting agent initialization")
    
    # Initialize agent
    agent = SalesDataAgent(db_path, tables_folder)
    
    # Initialize LLM
    logger.info(f"Initializing LLM: {model_name}")
    llm = ChatOpenAI(model=model_name, temperature=temperature)
    
    # Create and compile graph
    graph = create_agent_graph(agent, llm)
    
    logger.info("Agent fully initialized and ready")
    
    return graph, agent, llm