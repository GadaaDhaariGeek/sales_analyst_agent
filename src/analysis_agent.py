import sqlite3
import pandas as pd
from pathlib import Path
from typing import List, Dict, Any
import json
from llama_index.core import SQLDatabase
from llama_index.core.query_engine import NLSQLTableQueryEngine
from llama_index.core.tools import QueryEngineTool, FunctionTool
from llama_index.llms.openai import OpenAI
from llama_index.core.agent.workflow import ReActAgent
from llama_index.core.workflow import Context
from sqlalchemy import create_engine, text
import plotly.graph_objects as go
import plotly.express as px

from dotenv import load_dotenv
load_dotenv()


class SalesDataAnalyst:
    """Agentic AI Sales Data Analyst using LlamaIndex"""
    
    def __init__(self, tables_folder: str = "Tables", db_path: str = "sales.db"):
        self.tables_folder = Path(tables_folder)
        self.db_path = db_path
        self.engine = None
        self.sql_database = None
        self.agent = None
        self.context = None  # Agent context for conversation
        self.conversation_history = []
        
        # Initialize components
        self._setup_database()
        self._create_tools()
        self._create_agent()
    
    def _setup_database(self):
        """Load CSV files into SQLite database"""
        print("Setting up database...")
        
        # Create SQLite connection
        conn = sqlite3.connect(self.db_path)
        
        # Load each CSV file into the database
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
                print(f"Loaded {table_name}: {len(df)} rows")
            else:
                print(f"Warning: {csv_file} not found")
        
        conn.close()
        
        # Create SQLAlchemy engine for LlamaIndex
        self.engine = create_engine(f"sqlite:///{self.db_path}")
        self.sql_database = SQLDatabase(self.engine)
        print("Database setup complete!\n")
    
    def _create_sql_query_tool(self) -> QueryEngineTool:
        """Create SQL query tool for data retrieval"""
        
        # Create NL-to-SQL query engine
        sql_query_engine = NLSQLTableQueryEngine(
            sql_database=self.sql_database,
            tables=["cities", "countries", "customers", "employees", "products", "sales"],
            verbose=True
        )
        
        # Wrap as a tool
        sql_tool = QueryEngineTool.from_defaults(
            query_engine=sql_query_engine,
            name="sql_query_tool",
            description=(
                "Useful for querying the sales database to retrieve data. "
                "Can answer questions about sales, customers, products, employees, cities, and countries. "
                "Input should be a natural language question about the data. "
                "The tool will generate and execute the appropriate SQL query."
            )
        )
        
        return sql_tool
    
    def _create_visualization_tool(self) -> FunctionTool:
        """Create visualization generation tool"""
        
        def generate_visualization(
            data_description: str,
            chart_type: str = "bar"
        ) -> str:
            """
            Generate a visualization based on data description.
            
            Args:
                data_description: Description of what data to visualize
                chart_type: Type of chart (bar, line, pie, scatter)
            
            Returns:
                Information about the generated visualization
            """
            # In a real implementation, this would generate actual charts
            # For now, we'll return a description
            return f"Generated {chart_type} chart for: {data_description}. Chart would be displayed in the UI."
        
        viz_tool = FunctionTool.from_defaults(
            fn=generate_visualization,
            name="visualization_tool",
            description=(
                "Useful for creating visualizations like bar charts, line charts, pie charts, or scatter plots. "
                "Input should describe what data to visualize and optionally the chart type. "
                "Use this when the user asks to 'show', 'visualize', 'plot', or 'chart' something."
            )
        )
        
        return viz_tool
    
    def _create_data_analysis_tool(self) -> FunctionTool:
        """Create data analysis and summarization tool"""
        
        def analyze_data(query: str) -> str:
            """
            Analyze and summarize data based on the query.
            
            Args:
                query: Analysis question or request
            
            Returns:
                Analysis summary and insights
            """
            # This is a placeholder - in practice, the LLM will handle this
            return f"Analyzing: {query}. The LLM will provide detailed insights based on the data retrieved."
        
        analysis_tool = FunctionTool.from_defaults(
            fn=analyze_data,
            name="data_analysis_tool",
            description=(
                "Useful for analyzing and summarizing data, calculating metrics, "
                "comparing performance, and generating insights. "
                "Use this after retrieving data to provide business intelligence."
            )
        )
        
        return analysis_tool
    
    def _create_chitchat_tool(self) -> FunctionTool:
        """Create chitchat handler tool"""
        
        def handle_chitchat(message: str) -> str:
            """
            Handle casual conversation and greetings.
            
            Args:
                message: The chitchat message
            
            Returns:
                Friendly response
            """
            greetings = ["hello", "hi", "hey", "greetings"]
            message_lower = message.lower()
            
            if any(greeting in message_lower for greeting in greetings):
                return "Hello! I'm your AI Sales Data Analyst. I can help you analyze sales data, answer questions about customers, products, and employees. What would you like to know?"
            
            return "I'm here to help you analyze sales data. Feel free to ask me questions about sales, customers, products, or employees!"
        
        chitchat_tool = FunctionTool.from_defaults(
            fn=handle_chitchat,
            name="chitchat_tool",
            description=(
                "Useful for handling greetings, small talk, and casual conversation. "
                "Use this when the user is just saying hello or making casual conversation "
                "not related to data analysis."
            )
        )
        
        return chitchat_tool
    
    def _create_tools(self):
        """Create all agent tools"""
        print("Creating agent tools...")
        
        self.tools = [
            self._create_sql_query_tool(),
            self._create_visualization_tool(),
            self._create_data_analysis_tool(),
            self._create_chitchat_tool()
        ]
        
        print(f"Created {len(self.tools)} tools\n")
    
    def _create_agent(self):
        """Create the ReAct agent"""
        print("Creating agent...")
        
        # Initialize LLM
        llm = OpenAI(model="gpt-5-nano", temperature=0)
        
        # Create ReAct agent (no memory parameter needed - it's built-in)
        self.agent = ReActAgent(
            tools=self.tools,
            llm=llm,
            verbose=True
        )
        
        # Create context for the agent (stores conversation state)
        self.context = Context(self.agent)
        
        print("Agent created successfully!\n")
    
    def chat(self, user_message: str) -> str:
        """
        Send a message to the agent and get a response.
        
        Args:
            user_message: User's input message
        
        Returns:
            Agent's response
        """
        print(f"\n{'='*60}")
        print(f"USER: {user_message}")
        print(f"{'='*60}\n")
        
        try:
            import asyncio
            
            # Run the agent with context - this is the sync wrapper
            async def run_agent():
                handler = self.agent.run(user_message, ctx=self.context)
                
                # Stream the events
                async for ev in handler.stream_events():
                    from llama_index.core.agent.workflow import AgentStream
                    if isinstance(ev, AgentStream):
                        print(f"{ev.delta}", end="", flush=True)
                
                return await handler
            
            # Run synchronously
            response = asyncio.run(run_agent())
            agent_response = str(response)
            
            # Store in conversation history
            self.conversation_history.append({
                "role": "user",
                "content": user_message
            })
            self.conversation_history.append({
                "role": "assistant",
                "content": agent_response
            })
            
            print(f"\n\n{'='*60}")
            print(f"FINAL ANSWER: {agent_response}")
            print(f"{'='*60}\n")
            
            return agent_response
            
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"\n{error_msg}\n")
            import traceback
            traceback.print_exc()
            return error_msg
    
    def reset_conversation(self):
        """Reset conversation memory"""
        self.context = Context(self.agent)
        self.conversation_history = []
        print("Conversation reset.\n")
    
    def get_conversation_history(self) -> List[Dict[str, str]]:
        """Get the full conversation history"""
        return self.conversation_history


def create_sample_data():
    """Create sample CSV files for testing"""
    tables_folder = Path("Tables")
    tables_folder.mkdir(exist_ok=True)
    
    # Sample data
    cities_data = pd.DataFrame({
        'city_id': [1, 2, 3, 4, 5],
        'city_name': ['New York', 'London', 'Tokyo', 'Paris', 'Mumbai'],
        'country': ['USA', 'UK', 'Japan', 'France', 'India'],
        'region': ['North America', 'Europe', 'Asia', 'Europe', 'Asia']
    })
    
    countries_data = pd.DataFrame({
        'country_id': [1, 2, 3, 4, 5],
        'country_name': ['USA', 'UK', 'Japan', 'France', 'India'],
        'region': ['North America', 'Europe', 'Asia', 'Europe', 'Asia']
    })
    
    customers_data = pd.DataFrame({
        'customer_id': [1, 2, 3, 4, 5],
        'customer_name': ['Acme Corp', 'TechGlobal', 'Innovate Ltd', 'DataCo', 'CloudNet'],
        'city_id': [1, 2, 3, 4, 5],
        'contact_email': ['contact@acme.com', 'info@techglobal.com', 'sales@innovate.com', 'hello@dataco.com', 'info@cloudnet.com']
    })
    
    employees_data = pd.DataFrame({
        'employee_id': [1, 2, 3, 4],
        'employee_name': ['John Smith', 'Sarah Johnson', 'Mike Chen', 'Emily Davis'],
        'role': ['Sales Rep', 'Sales Rep', 'Sales Manager', 'Sales Rep'],
        'city_id': [1, 1, 2, 3]
    })
    
    products_data = pd.DataFrame({
        'product_id': [1, 2, 3, 4, 5],
        'product_name': ['Laptop Pro', 'Desktop Ultra', 'Mouse Wireless', 'Keyboard Mech', 'Monitor 4K'],
        'category': ['Electronics', 'Electronics', 'Accessories', 'Accessories', 'Electronics'],
        'price': [1200, 1500, 50, 120, 800]
    })
    
    sales_data = pd.DataFrame({
        'sale_id': range(1, 21),
        'sale_date': pd.date_range('2023-01-01', periods=20, freq='15D'),
        'customer_id': [1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5, 1, 2, 3, 4, 5],
        'product_id': [1, 2, 3, 4, 5, 2, 1, 5, 3, 4, 1, 3, 2, 5, 4, 3, 1, 4, 2, 5],
        'quantity': [2, 1, 10, 5, 3, 1, 2, 2, 8, 4, 3, 12, 1, 2, 6, 15, 1, 3, 2, 1],
        'employee_id': [1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4, 1, 2, 3, 4]
    })
    
    # Calculate revenue
    sales_data['revenue'] = sales_data.apply(
        lambda row: row['quantity'] * products_data.loc[products_data['product_id'] == row['product_id'], 'price'].values[0],
        axis=1
    )
    
    # Save to CSV
    cities_data.to_csv(tables_folder / 'cities.csv', index=False)
    countries_data.to_csv(tables_folder / 'countries.csv', index=False)
    customers_data.to_csv(tables_folder / 'customers.csv', index=False)
    employees_data.to_csv(tables_folder / 'employees.csv', index=False)
    products_data.to_csv(tables_folder / 'products.csv', index=False)
    sales_data.to_csv(tables_folder / 'sales.csv', index=False)
    
    print("Sample data created in Tables folder!\n")


def main():
    """Main conversation loop"""
    
    print("\n" + "="*60)
    print("AGENTIC AI SALES DATA ANALYST")
    print("="*60 + "\n")
    
    # Create sample data if needed
    if not Path("Tables").exists():
        print("Creating sample data...")
        create_sample_data()
    
    # Initialize the analyst
    analyst = SalesDataAnalyst()
    
    print("\n" + "="*60)
    print("Ready! Type 'quit' to exit, 'reset' to clear conversation")
    print("="*60 + "\n")
    
    # Conversation loop
    while True:
        try:
            user_input = input("\nYou: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("\nGoodbye! Thanks for using the Sales Data Analyst.\n")
                break
            
            if user_input.lower() == 'reset':
                analyst.reset_conversation()
                continue
            
            # Get agent response
            analyst.chat(user_input)
            
        except KeyboardInterrupt:
            print("\n\nGoodbye!\n")
            break
        except Exception as e:
            print(f"\nError: {e}\n")


if __name__ == "__main__":
    main()