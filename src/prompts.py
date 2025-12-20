"""
Prompts, schemas, and tool definitions for the Sales Analyst Agent.
"""

from typing import Annotated
from pydantic import BaseModel, Field
from langchain.tools import tool


# ============================================================================
# SYSTEM PROMPTS
# ============================================================================

SYSTEM_PROMPT = """You are an expert Sales Data Analyst AI assistant specialized in analyzing sales data and providing business insights.

**Your Responsibilities:**
1. Query the sales database to retrieve relevant data
2. Analyze sales trends, customer behavior, and product performance
3. Provide actionable business insights and recommendations
4. Generate visualizations when requested
5. Handle casual conversation and greetings

**How You Work:**
- You have access to tools for querying databases and generating visualizations
- Always think step-by-step and explain your reasoning
- When analyzing data, provide both raw numbers and business context
- Ask clarifying questions if requests are ambiguous
- Be conversational but maintain a professional tone

**Available Tools:**
- `query_sales_database`: Query the sales database using natural language
- `generate_visualization`: Create charts and visualizations
- `analyze_metrics`: Perform calculations and metric analysis

**Important Guidelines:**
- Start by understanding what the user is asking
- Use the appropriate tool to retrieve or analyze data
- Provide clear, actionable insights
- Always cite the data you're using in your analysis"""


# ============================================================================
# TOOL SCHEMAS & DEFINITIONS
# ============================================================================

class DatabaseQuery(BaseModel):
    """Schema for database query operations"""
    query: str = Field(description="Natural language query about sales data")
    query_type: str = Field(
        default="general",
        description="Type of query: general, aggregation, trend, or comparison"
    )


class VisualizationRequest(BaseModel):
    """Schema for visualization requests"""
    title: str = Field(description="Title for the visualization")
    chart_type: str = Field(
        description="Type of chart: bar, line, pie, scatter, histogram"
    )
    data_description: str = Field(description="Description of data to visualize")
    x_axis: str = Field(default="", description="Label for X axis")
    y_axis: str = Field(default="", description="Label for Y axis")


class MetricsAnalysis(BaseModel):
    """Schema for metrics analysis"""
    metric_type: str = Field(
        description="Type of metric: KPI, ratio, growth_rate, or comparison"
    )
    description: str = Field(description="Description of what to analyze")
    time_period: str = Field(default="current", description="Time period for analysis")


# ============================================================================
# TOOL DEFINITIONS
# ============================================================================

@tool
def query_sales_database(query: str, query_type: str = "general") -> str:
    """
    Query the sales database using natural language.
    
    This tool converts natural language questions into SQL queries and executes them
    against the sales database. It can retrieve data about sales, customers, products,
    employees, and geographic information.
    
    Args:
        query: Natural language question about the sales data
        query_type: Type of query (general, aggregation, trend, comparison)
    
    Returns:
        Query results as formatted text
    
    Examples:
        - "What are the total sales by product category?"
        - "Show me the top 10 customers by revenue"
        - "What is the sales trend over the last 12 months?"
    """
    # This will be implemented in agent_workflow.py
    pass


@tool
def generate_visualization(
    title: str,
    chart_type: str,
    data_description: str,
    x_axis: str = "",
    y_axis: str = ""
) -> str:
    """
    Generate a visualization based on data description.
    
    Creates charts to help visualize sales data and trends.
    
    Args:
        title: Title for the visualization
        chart_type: Type of chart (bar, line, pie, scatter, histogram)
        data_description: Description of what data to visualize
        x_axis: Label for X axis (optional)
        y_axis: Label for Y axis (optional)
    
    Returns:
        Information about the generated visualization
    
    Examples:
        - "Sales by Product Category" as a bar chart
        - "Monthly Revenue Trend" as a line chart
        - "Customer Segmentation" as a pie chart
    """
    # This will be implemented in agent_workflow.py
    pass


@tool
def analyze_metrics(
    metric_type: str,
    description: str,
    time_period: str = "current"
) -> str:
    """
    Analyze business metrics and provide calculations.
    
    Performs calculations on sales data to derive business metrics,
    KPIs, growth rates, and comparative analysis.
    
    Args:
        metric_type: Type of metric (KPI, ratio, growth_rate, comparison)
        description: Description of what to analyze
        time_period: Time period for analysis (current, last_month, last_quarter, last_year)
    
    Returns:
        Analysis results and insights
    
    Examples:
        - "Calculate the average order value"
        - "What is the month-over-month growth rate?"
        - "Compare this quarter's sales to last quarter"
    """
    # This will be implemented in agent_workflow.py
    pass


# ============================================================================
# GRAPH STATE SCHEMA
# ============================================================================

class AgentState(BaseModel):
    """State schema for the agent graph"""
    messages: list = Field(description="List of messages in the conversation")
    current_node: str = Field(default="", description="Current node being executed")
    query_result: str = Field(default="", description="Result from last database query")
    analysis_result: str = Field(default="", description="Result from last analysis")
    visualization_data: dict = Field(default_factory=dict, description="Data for visualization")
    
    class Config:
        arbitrary_types_allowed = True


# ============================================================================
# TOOL DESCRIPTIONS FOR AGENT
# ============================================================================

TOOL_DESCRIPTIONS = {
    "query_sales_database": {
        "name": "query_sales_database",
        "description": """Query the sales database using natural language.

Available data:
- Sales transactions: id, amount, date, customer_id, product_id, employee_id
- Customers: name, email, city, country, contact info
- Products: name, category, price, supplier
- Employees: name, department, location, sales region
- Geographic: cities, countries, regions

Use this tool to retrieve any specific data from the database."""
    },
    "generate_visualization": {
        "name": "generate_visualization",
        "description": """Create visualizations and charts.

Supported chart types: bar, line, pie, scatter, histogram, box plot

Use this when the user asks to visualize, plot, show, or chart data."""
    },
    "analyze_metrics": {
        "name": "analyze_metrics",
        "description": """Analyze metrics and provide business insights.

Can calculate: KPIs, growth rates, comparisons, averages, totals, ratios

Use this to perform calculations and provide business analysis."""
    }
}