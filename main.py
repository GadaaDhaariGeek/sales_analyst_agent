# ============================================================================
# EXAMPLE USAGE
# ============================================================================

from src.analysis_agent import AgentConfig, EnhancedSalesDataAnalyst
from src.prompts import SYSTEM_PROMPT, TOOL_DESCRIPTIONS
from src.logger import logger

if __name__ == "__main__":
    # Custom configuration
    config = AgentConfig(
        model="gpt-5-nano",
        temperature=0.0,
        max_tokens=2048,
        db_path="sales_data.db",
        verbose=True
    )
    
    # Initialize agent
    analyst = EnhancedSalesDataAnalyst(
        tables_folder="./data",
        config=config,
        system_prompt=SYSTEM_PROMPT
    )
    
    # Print agent info
    analyst.print_agent_info()
    
    # Example conversation loop
    try:
        while True:
            user_input = input("\n📊 You: ").strip()
            
            if not user_input:
                continue
            
            if user_input.lower() in ['exit', 'quit', 'bye']:
                logger.info("User exited conversation")
                break
            
            if user_input.lower() == 'reset':
                analyst.reset_conversation()
                print("✅ Conversation reset")
                continue
            
            if user_input.lower() == 'history':
                history = analyst.get_conversation_history()
                print(f"\n📝 Conversation History ({len(history)} messages):")
                for msg in history:
                    print(f"  [{msg['role'].upper()}] {msg['content'][:100]}...")
                continue
            
            # Get response from agent
            response = analyst.chat(user_input)
            print(f"\n")
    
    except KeyboardInterrupt:
        logger.info("Agent interrupted by user")
        print("\n\nGoodbye!")