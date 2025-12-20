"""
FastAPI server for Sales Analyst Agent with LangGraph.
Includes lifespan context management and streaming support.
"""

import asyncio
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import StreamingResponse, JSONResponse
from pydantic import BaseModel, Field
from langchain_core.messages import HumanMessage, BaseMessage

from src.agent_workflow import initialize_agent
from src.logger import setup_logging

from dotenv import load_dotenv
load_dotenv()


# Initialize logger
logger = setup_logging("SalesAnalystAPI")


# ============================================================================
# STATE MANAGEMENT
# ============================================================================

class AppState:
    """Application state holder"""
    def __init__(self):
        self.graph = None
        self.agent = None
        self.llm = None
        self.conversation_history: dict = {}
    
    def get_session_history(self, session_id: str) -> List[BaseMessage]:
        """Get conversation history for a session"""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        return self.conversation_history[session_id]
    
    def add_message(self, session_id: str, message: BaseMessage):
        """Add message to session history"""
        if session_id not in self.conversation_history:
            self.conversation_history[session_id] = []
        self.conversation_history[session_id].append(message)


# Global state
app_state = AppState()


# ============================================================================
# LIFESPAN CONTEXT MANAGER
# ============================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI.
    Handles startup and shutdown of the agent.
    
    Reference: https://fastapi.tiangolo.com/advanced/events/#lifespan
    """
    
    # STARTUP
    logger.info("=" * 80)
    logger.info("APPLICATION STARTUP")
    logger.info("=" * 80)
    
    try:
        logger.info("Initializing Sales Analyst Agent...")
        
        # Initialize the agent
        graph, agent, llm = initialize_agent(
            db_path="sales_data.db",
            tables_folder="./data",
            model_name="gpt-5-nano",
            temperature=0.0
        )
        
        # Store in app state
        app_state.graph = graph
        app_state.agent = agent
        app_state.llm = llm
        
        logger.info("Agent initialized successfully")
        logger.info("Application ready to accept requests")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Failed to initialize agent: {str(e)}", exc_info=True)
        raise
    
    # YIELD (server runs)
    yield
    
    # SHUTDOWN
    logger.info("=" * 80)
    logger.info("APPLICATION SHUTDOWN")
    logger.info("=" * 80)
    
    try:
        logger.info("Cleaning up resources...")
        
        # Close database connections
        if app_state.agent and app_state.agent.engine:
            app_state.agent.engine.dispose()
            logger.info("Database connections closed")
        
        # Clear conversation history
        app_state.conversation_history.clear()
        logger.info("Conversation history cleared")
        
        logger.info("Shutdown complete")
        logger.info("=" * 80)
        
    except Exception as e:
        logger.error(f"Error during shutdown: {str(e)}", exc_info=True)


# ============================================================================
# FASTAPI APP INITIALIZATION
# ============================================================================

app = FastAPI(
    title="Sales Analyst Agent",
    description="AI-powered sales data analysis with LangGraph",
    version="1.0.0",
    lifespan=lifespan
)


# ============================================================================
# REQUEST/RESPONSE MODELS
# ============================================================================

class ChatRequest(BaseModel):
    """Request model for chat endpoint"""
    message: str = Field(..., description="User message")
    session_id: str = Field(default="default", description="Session identifier")
    stream: bool = Field(default=True, description="Enable streaming response")


class ChatResponse(BaseModel):
    """Response model for chat endpoint"""
    session_id: str
    response: str
    message_count: int


class HealthResponse(BaseModel):
    """Health check response"""
    status: str
    agent_ready: bool
    message: str


# ============================================================================
# HEALTH CHECK ENDPOINT
# ============================================================================

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint.
    Verifies that the agent is initialized and ready.
    """
    logger.info("Health check requested")
    
    if app_state.graph is None:
        logger.warning("Agent not initialized")
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    return HealthResponse(
        status="healthy",
        agent_ready=True,
        message="Sales Analyst Agent is running"
    )


# ============================================================================
# CHAT ENDPOINT - NON-STREAMING
# ============================================================================

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Chat endpoint for non-streaming responses.
    
    Args:
        request: ChatRequest with message and session_id
    
    Returns:
        ChatResponse with agent response
    """
    
    logger.info(f"Chat request received - Session: {request.session_id}")
    logger.debug(f"Message: {request.message}")
    
    if app_state.graph is None:
        logger.error("Agent not initialized")
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    try:
        # Get or create session history
        history = app_state.get_session_history(request.session_id)
        
        # Create input state
        input_state = {
            "messages": history + [HumanMessage(content=request.message)]
        }
        
        logger.debug(f"Input messages count: {len(input_state['messages'])}")
        
        # Run the graph
        logger.info("Invoking agent graph")
        output = await asyncio.to_thread(app_state.graph.invoke, input_state)
        
        # Extract response
        response_messages = output.get("messages", [])
        final_response = ""
        
        if response_messages:
            last_message = response_messages[-1]
            final_response = last_message.content if hasattr(last_message, 'content') else str(last_message)
        
        logger.info(f"Agent response generated - Length: {len(final_response)}")
        
        # Update session history
        app_state.add_message(request.session_id, HumanMessage(content=request.message))
        app_state.add_message(request.session_id, output["messages"][-1])
        
        return ChatResponse(
            session_id=request.session_id,
            response=final_response,
            message_count=len(app_state.get_session_history(request.session_id))
        )
    
    except Exception as e:
        logger.error(f"Error processing chat: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")


# ============================================================================
# CHAT ENDPOINT - STREAMING
# ============================================================================

@app.post("/chat/stream")
async def chat_stream(request: ChatRequest):
    """
    Streaming chat endpoint.
    Returns chunked responses for real-time streaming.
    
    Args:
        request: ChatRequest with message and session_id
    
    Returns:
        StreamingResponse with agent output
    """
    
    logger.info(f"Streaming chat request - Session: {request.session_id}")
    
    if app_state.graph is None:
        raise HTTPException(status_code=503, detail="Agent not initialized")
    
    async def generate():
        """Generator function for streaming response"""
        try:
            # Get session history
            history = app_state.get_session_history(request.session_id)
            
            # Create input state
            input_state = {
                "messages": history + [HumanMessage(content=request.message)]
            }
            
            logger.info("Starting stream generation")
            
            # Stream from graph
            async for event in app_state.graph.astream(input_state):
                logger.debug(f"Stream event: {list(event.keys())}")
                
                # Yield each event as JSON
                yield f"data: {event}\n\n"
            
            logger.info("Stream generation complete")
        
        except Exception as e:
            logger.error(f"Error during streaming: {str(e)}", exc_info=True)
            yield f"data: {{'error': '{str(e)}'}}\n\n"
    
    return StreamingResponse(generate(), media_type="application/x-ndjson")


# ============================================================================
# SESSION MANAGEMENT ENDPOINTS
# ============================================================================

@app.get("/sessions/{session_id}")
async def get_session_history(session_id: str):
    """
    Get conversation history for a session.
    
    Args:
        session_id: Session identifier
    
    Returns:
        List of messages in the session
    """
    
    logger.info(f"Fetching history for session: {session_id}")
    
    history = app_state.get_session_history(session_id)
    
    return {
        "session_id": session_id,
        "message_count": len(history),
        "messages": [
            {
                "role": msg.type if hasattr(msg, 'type') else "unknown",
                "content": msg.content if hasattr(msg, 'content') else str(msg)
            }
            for msg in history
        ]
    }


@app.delete("/sessions/{session_id}")
async def clear_session(session_id: str):
    """
    Clear conversation history for a session.
    
    Args:
        session_id: Session identifier
    
    Returns:
        Confirmation message
    """
    
    logger.info(f"Clearing session: {session_id}")
    
    if session_id in app_state.conversation_history:
        del app_state.conversation_history[session_id]
        logger.info(f"Session {session_id} cleared")
    
    return {"message": f"Session {session_id} cleared", "session_id": session_id}


# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions with logging"""
    logger.error(f"HTTP Error {exc.status_code}: {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions with logging"""
    logger.error(f"Unhandled exception: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error"}
    )


# ============================================================================
# ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    import uvicorn
    
    logger.info("Starting FastAPI server")
    
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8000,
        log_level="info",
        reload=False  # Set to True for development
    )