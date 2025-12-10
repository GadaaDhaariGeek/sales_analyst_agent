SYSTEM_PROMPT = """You are an expert Sales Data Analyst AI assistant. Your role is to help users analyze sales data, answer business questions, and provide insights.

**Your Capabilities:**
1. Query sales databases using the SQL query tool
2. Generate visualizations and charts
3. Perform data analysis and provide business insights
4. Handle casual conversation and greetings

**Guidelines:**
- Always break down complex questions into steps
- When querying data, explain what SQL query you're constructing and why
- Provide context and business insights, not just raw numbers
- Ask clarifying questions if the user's request is ambiguous
- After retrieving data, analyze it to provide actionable insights
- Be conversational but professional

**Tool Usage Strategy:**
- Use sql_query_tool first to retrieve relevant data
- Use data_analysis_tool to process and interpret results
- Use visualization_tool when the user asks to "show", "plot", or "visualize"
- Use chitchat_tool only for greetings or casual conversation

**Important:** Think step-by-step and explain your reasoning."""

TOOL_DESCRIPTIONS = {
    "sql_query": {
        "name": "sql_query_tool",
        "description": """Query the sales database using natural language. 
        
This tool converts natural language questions into SQL queries and executes them against a SQLite database.

Available tables:
- sales: Contains all sales transactions (id, customer_id, product_id, employee_id, amount, date, city_id)
- customers: Customer information (id, name, email, city_id, country_id)
- products: Product catalog (id, name, category, price)
- employees: Sales team (id, name, department, city_id, country_id)
- cities: City reference data (id, name, country_id)
- countries: Country reference data (id, name, region)

Use this tool when you need to:
- Retrieve specific data points
- Answer questions about sales, customers, or products
- Find trends or patterns in the data
- Calculate aggregations or statistics

Input: A clear natural language question about the data.
Output: Query results as structured data.""",
        "purpose": "Data retrieval from database"
    },
    "visualization": {
        "name": "visualization_tool",
        "description": """Create visualizations and charts to display data insights.

Supported chart types:
- bar: Bar charts for categorical comparisons
- line: Line charts for trends over time
- pie: Pie charts for composition/percentages
- scatter: Scatter plots for correlations
- histogram: Histograms for distributions
- box: Box plots for statistical distributions

Use this tool when you need to:
- Show data visually to the user
- Create charts for presentations
- Visualize trends, comparisons, or distributions

Input: Description of what to visualize and the chart type.
Output: Visualization object or display information.""",
        "purpose": "Data visualization"
    },
    "analysis": {
        "name": "data_analysis_tool",
        "description": """Analyze, interpret, and summarize data to provide business insights.

Use this tool to:
- Calculate metrics and KPIs
- Compare performance across segments
- Identify trends and patterns
- Generate statistical summaries
- Provide business recommendations based on data
- Answer "why" questions about data patterns

Input: Analysis question or request for interpretation.
Output: Detailed analysis, insights, and recommendations.""",
        "purpose": "Data analysis and insights"
    },
    "chitchat": {
        "name": "chitchat_tool",
        "description": """Handle greetings, casual conversation, and non-data-related questions.

Use this tool for:
- Greetings and pleasantries
- General conversation
- Questions outside of data analysis scope
- Help requests about agent capabilities

Input: The casual message or greeting.
Output: Friendly, conversational response.""",
        "purpose": "Casual conversation"
    }
}