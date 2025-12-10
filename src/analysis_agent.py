import sqlite3
import pandas as pd
import json
import logging
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from dataclasses import dataclass

from llama_index.core import SQLDatabase
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core.tools import QueryEngineTool, FunctionTool
from llama_index.llms.openai import OpenAI
from llama_index.core.agent.workflow import ReActAgent, AgentStream
from llama_index.core.workflow import Context
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv
from src.logger import logger
from src.prompts import SYSTEM_PROMPT, TOOL_DESCRIPTIONS

load_dotenv()



# ============================================================================
# CONFIGURATION
# ============================================================================

@dataclass
class AgentConfig:
    """Configuration for the agent"""
    # LLM Settings
    model: str = "gpt-5-nano"
    temperature: float = 0.0
    max_tokens: int = 2048
    top_p: float = 1.0
    
    # Database Settings
    db_path: str = "sales_data.db"
    tables: List[str] = None
    
    # Agent Settings
    verbose: bool = True
    enable_sql_explain: bool = True
    
    # Tool Settings
    use_sql_tool: bool = True
    use_visualization_tool: bool = True
    use_analysis_tool: bool = True
    use_chitchat_tool: bool = True
    
    def __post_init__(self):
        if self.tables is None:
            self.tables = ["cities", "countries", "customers", "employees", "products", "sales"]

# ============================================================================
# ENHANCED SALES DATA ANALYST
# ============================================================================

class EnhancedSalesDataAnalyst:
    """Enhanced Sales Data Analyst with full control over prompts and logging"""
    
    def __init__(
        self,
        tables_folder: str,
        config: Optional[AgentConfig] = None,
        system_prompt: Optional[str] = None
    ):
        self.tables_folder = Path(tables_folder)
        self.config = config or AgentConfig()
        self.system_prompt = SYSTEM_PROMPT
        
        logger.info(f"Initializing Enhanced Sales Data Analyst")
        logger.debug(f"Configuration: {self.config}")
        
        self.engine = None
        self.sql_database = None
        self.agent = None
        self.llm = None
        self.tools = []
        self.conversation_history = []
        
        # Initialize components
        self._setup_database()
        self._create_llm()
        self._create_tools()
        self._create_agent()
        
        logger.info("Agent initialization complete")
    
    def _setup_database(self):
        """Load CSV files into SQLite database"""
        logger.info("Setting up database...")
        
        try:
            conn = sqlite3.connect(self.config.db_path)
            
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
                    logger.info(f"Loaded table '{table_name}': {len(df)} rows, {len(df.columns)} columns")
                    logger.debug(f"Columns in {table_name}: {list(df.columns)}")
                else:
                    logger.warning(f"CSV file not found: {csv_file}")
            
            conn.close()
            
            # Create SQLAlchemy engine
            self.engine = create_engine(f"sqlite:///{self.config.db_path}")
            self.sql_database = SQLDatabase(self.engine)
            
            # Log database schema
            inspector = inspect(self.engine)
            logger.debug(f"Database schema: {inspector.get_table_names()}")
            
            logger.info("Database setup complete")
            
        except Exception as e:
            logger.error(f"Error setting up database: {str(e)}", exc_info=True)
            raise
    
    def _create_llm(self):
        """Create and configure the LLM"""
        logger.info("Creating LLM instance")
        logger.debug(f"LLM Config - Model: {self.config.model}, Temp: {self.config.temperature}, Max Tokens: {self.config.max_tokens}")
        
        self.llm = OpenAI(
            model=self.config.model,
            temperature=self.config.temperature,
            max_tokens=self.config.max_tokens,
            top_p=self.config.top_p,
        )
        
        logger.info(f"LLM created: {self.config.model}")
    
    def _create_sql_query_tool(self) -> Optional[QueryEngineTool]:
        """Create SQL query tool with enhanced logging"""
        if not self.config.use_sql_tool:
            logger.debug("SQL query tool disabled in config")
            return None
        
        logger.info("Creating SQL query tool")
        
        try:
            sql_query_engine = NLSQLTableQueryEngine(
                sql_database=self.sql_database,
                tables=self.config.tables,
                verbose=self.config.verbose,
                synthesize_response=True
            )
            
            tool_desc = TOOL_DESCRIPTIONS["sql_query"]
            sql_tool = QueryEngineTool.from_defaults(
                query_engine=sql_query_engine,
                name=tool_desc["name"],
                description=tool_desc["description"]
            )
            
            logger.debug(f"SQL tool created with {len(self.config.tables)} tables: {self.config.tables}")
            return sql_tool
            
        except Exception as e:
            logger.error(f"Error creating SQL query tool: {str(e)}", exc_info=True)
            return None
    
    def _create_visualization_tool(self) -> Optional[FunctionTool]:
        """Create visualization tool with enhanced logging"""
        if not self.config.use_visualization_tool:
            logger.debug("Visualization tool disabled in config")
            return None
        
        logger.info("Creating visualization tool")
        
        def generate_visualization(
            data_description: str,
            chart_type: str = "bar"
        ) -> str:
            logger.debug(f"Visualization request - Type: {chart_type}, Description: {data_description}")
            
            valid_types = ["bar", "line", "pie", "scatter", "histogram", "box"]
            if chart_type not in valid_types:
                logger.warning(f"Invalid chart type: {chart_type}. Valid types: {valid_types}")
                chart_type = "bar"
            
            result = f"Generated {chart_type.upper()} chart for: {data_description}. Chart would be displayed in the UI."
            logger.info(f"Visualization generated: {chart_type}")
            return result
        
        tool_desc = TOOL_DESCRIPTIONS["visualization"]
        viz_tool = FunctionTool.from_defaults(
            fn=generate_visualization,
            name=tool_desc["name"],
            description=tool_desc["description"]
        )
        
        logger.debug("Visualization tool created")
        return viz_tool
    
    def _create_data_analysis_tool(self) -> Optional[FunctionTool]:
        """Create data analysis tool with enhanced logging"""
        if not self.config.use_analysis_tool:
            logger.debug("Data analysis tool disabled in config")
            return None
        
        logger.info("Creating data analysis tool")
        
        def analyze_data(query: str) -> str:
            logger.debug(f"Analysis request: {query}")
            
            result = f"Analyzing: {query}. The LLM will provide detailed insights based on the data retrieved."
            logger.info(f"Analysis initiated for: {query[:100]}...")
            return result
        
        tool_desc = TOOL_DESCRIPTIONS["analysis"]
        analysis_tool = FunctionTool.from_defaults(
            fn=analyze_data,
            name=tool_desc["name"],
            description=tool_desc["description"]
        )
        
        logger.debug("Data analysis tool created")
        return analysis_tool
    
    def _create_chitchat_tool(self) -> Optional[FunctionTool]:
        """Create chitchat tool with enhanced logging"""
        if not self.config.use_chitchat_tool:
            logger.debug("Chitchat tool disabled in config")
            return None
        
        logger.info("Creating chitchat tool")
        
        def handle_chitchat(message: str) -> str:
            logger.debug(f"Chitchat message: {message}")
            
            greetings = ["hello", "hi", "hey", "greetings", "good morning", "good afternoon"]
            message_lower = message.lower()
            
            if any(greeting in message_lower for greeting in greetings):
                response = "Hello! I'm your AI Sales Data Analyst. I can help you analyze sales data, answer questions about customers, products, employees, and sales trends. What would you like to know?"
            else:
                response = "I'm here to help you analyze sales data. Feel free to ask me questions about sales, customers, products, employees, or any data analysis needs!"
            
            logger.info(f"Chitchat response generated")
            return response
        
        tool_desc = TOOL_DESCRIPTIONS["chitchat"]
        chitchat_tool = FunctionTool.from_defaults(
            fn=handle_chitchat,
            name=tool_desc["name"],
            description=tool_desc["description"]
        )
        
        logger.debug("Chitchat tool created")
        return chitchat_tool
    
    def _create_tools(self):
        """Create all agent tools with enhanced logging"""
        logger.info("Creating all agent tools")
        
        tools_list = [
            self._create_sql_query_tool(),
            self._create_visualization_tool(),
            self._create_data_analysis_tool(),
            self._create_chitchat_tool()
        ]
        
        self.tools = [tool for tool in tools_list if tool is not None]
        logger.info(f"Total tools created: {len(self.tools)}")
        for i, tool in enumerate(self.tools, 1):
            logger.debug(f"Tool {i}: {tool.metadata.name}")
    
    def _create_agent(self):
        """Create the ReAct agent with custom system prompt"""
        logger.info("Creating ReAct agent")
        
        try:
            self.agent = ReActAgent(
                tools=self.tools,
                llm=self.llm,
                verbose=self.config.verbose,
                system_prompt=self.system_prompt,
                max_iterations=10
            )
            
            logger.info(f"Agent created successfully with {len(self.tools)} tools")
            logger.debug(f"System prompt length: {len(self.system_prompt)} characters")
            
        except Exception as e:
            logger.error(f"Error creating agent: {str(e)}", exc_info=True)
            raise
    
    async def _run_agent_async(self, user_message: str, ctx: Context) -> str:
        """Run agent asynchronously with event streaming and logging"""
        logger.debug("Starting async agent execution")
        
        try:
            # Run agent and get handler
            handler = self.agent.run(user_message, ctx=ctx)
            logger.debug("Agent handler created, streaming events...")
            
            # Stream events and collect response
            full_response = ""
            async for ev in handler.stream_events():
                if isinstance(ev, AgentStream):
                    delta = ev.delta
                    full_response += delta
                    print(f"{delta}", end="", flush=True)
            
            # Wait for final response
            response = await handler
            agent_response = str(response)
            
            logger.info(f"Agent execution completed successfully")
            logger.debug(f"Response length: {len(agent_response)} characters")
            
            return agent_response
            
        except Exception as e:
            logger.error(f"Error during async agent execution: {str(e)}", exc_info=True)
            raise
    
    def chat(self, user_message: str) -> str:
        """
        Send a message to the agent and get a response with full logging
        
        Args:
            user_message: User's input message
        
        Returns:
            Agent's response
        """
        timestamp = datetime.now().isoformat()
        
        logger.info("=" * 80)
        logger.info(f"USER MESSAGE [{timestamp}]: {user_message}")
        logger.info("=" * 80)
        
        try:
            # Create context for this conversation turn
            ctx = Context(self.agent)
            
            # Run agent asynchronously
            response = asyncio.run(self._run_agent_async(user_message, ctx))
            
            # Store in conversation history
            self.conversation_history.append({
                "timestamp": timestamp,
                "role": "user",
                "content": user_message
            })
            self.conversation_history.append({
                "timestamp": datetime.now().isoformat(),
                "role": "assistant",
                "content": response
            })
            
            logger.info("=" * 80)
            logger.info(f"AGENT RESPONSE: {response}")
            logger.info("=" * 80)
            
            return response
            
        except Exception as e:
            error_msg = f"Error during chat: {str(e)}"
            logger.error(error_msg, exc_info=True)
            return error_msg
    
    def reset_conversation(self):
        """Reset conversation memory"""
        logger.info("Resetting conversation history")
        self.conversation_history = []
        logger.debug("Conversation history cleared")
    
    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the full conversation history"""
        logger.debug(f"Retrieving conversation history ({len(self.conversation_history)} messages)")
        return self.conversation_history
    
    def get_system_prompt(self) -> str:
        """Get current system prompt"""
        return self.system_prompt
    
    def set_system_prompt(self, prompt: str):
        """Update system prompt and recreate agent"""
        logger.info("Updating system prompt")
        logger.debug(f"New prompt length: {len(prompt)} characters")
        
        self.system_prompt = prompt
        self._create_agent()
        
        logger.info("System prompt updated and agent recreated")
    
    def update_config(self, **kwargs):
        """Update configuration and recreate components as needed"""
        logger.info(f"Updating configuration with: {list(kwargs.keys())}")
        
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                old_value = getattr(self.config, key)
                setattr(self.config, key, value)
                logger.debug(f"Config updated: {key} = {value} (was {old_value})")
            else:
                logger.warning(f"Unknown config key: {key}")
        
        # Recreate components if needed
        if any(key in kwargs for key in ['model', 'temperature', 'max_tokens', 'top_p']):
            self._create_llm()
            self._create_agent()
            logger.info("LLM and agent recreated due to config changes")
    
    def print_agent_info(self):
        """Print detailed agent configuration"""
        logger.info("Agent Configuration Summary:")
        logger.info(f"  Model: {self.config.model}")
        logger.info(f"  Temperature: {self.config.temperature}")
        logger.info(f"  Max Tokens: {self.config.max_tokens}")
        logger.info(f"  Tools: {len(self.tools)}")
        logger.info(f"  System Prompt Length: {len(self.system_prompt)} chars")
        logger.info(f"  Conversation Turns: {len(self.conversation_history)}")
