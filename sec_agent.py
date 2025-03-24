"""
SEC Filing Analysis System using LangGraph
Implements a smart orchestrator with tool agents for SEC-API.io
"""

import os
import sys
import json
import logging
from typing import Dict, Any, List, Optional, TypedDict, Annotated, Callable, Literal
from dotenv import load_dotenv
from langgraph.graph import StateGraph
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from langchain.tools import StructuredTool

import sec_api_knowledge
from agents.mapping_agent import company_resolution_agent
from agents.filing_search_agent import filing_search_agent
from agents.section_extraction_agent import section_extraction_agent
from agents.xbrl_converter_agent import xbrl_converter_agent

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SEC_API_KEY = os.getenv("SEC_API_KEY")

if not OPENAI_API_KEY or not SEC_API_KEY:
    raise ValueError("Missing required API keys in .env file")

# Define state schema for LangGraph using TypedDict
class State(TypedDict):
    user_query: str                      # Original user question
    query_analysis: Dict[str, Any]       # Analysis of the query from sec_api_knowledge
    action_plan: List[Dict[str, Any]]    # Steps to execute from the planning agent
    current_step_index: int              # Current step index in the action plan
    company_info: Optional[Dict]         # Company resolution results
    filing_info: Optional[Dict]          # Filing search results
    section_content: Optional[Dict]      # Section extraction results
    financial_data: Optional[Dict]       # XBRL financial data results
    errors: List[Dict]                   # Error tracking
    final_answer: Optional[str]          # Final answer to user

# Define tool registry with consistent schema
TOOL_REGISTRY = {
    "company_resolution": {
        "name": "ResolveCompany",
        "description": "Resolves company names to CIK numbers and tickers",
        "function": company_resolution_agent,
        "params": ["identifier_type", "identifier_value"]
    },
    "filing_search": {
        "name": "SECQueryAPI",
        "description": "Searches for SEC filings by CIK, form type, and date",
        "function": filing_search_agent,
        "params": ["query"]
    },
    "section_extraction": {
        "name": "SECExtractSection",
        "description": "Extracts specific sections from SEC filings",
        "function": section_extraction_agent,
        "params": ["filing_url", "section"]
    },
    "xbrl_conversion": {
        "name": "SECFinancialData",
        "description": "Extracts financial data from XBRL in SEC filings",
        "function": xbrl_converter_agent,
        "params": ["accession_no", "htm_url"]
    }
}

def create_planning_agent():
    """Create the planning agent with knowledge of SEC filing analysis.
    This agent is responsible for planning and executing the entire workflow."""
    
    # Format section info for the prompt
    form_10k_sections = "\n".join([f"* \"{section_id}\" - {section_name}" 
                                 for section_id, section_name in sec_api_knowledge.FORM_10K_SECTIONS.items()])
    
    # Format tool registry for the prompt and create tool list
    tools_description = []
    tools = []
    
    for tool_id, tool_info in TOOL_REGISTRY.items():
        tools_description.append(f"* {tool_info['name']}: {tool_info['description']}")
        
        # Create a wrapper function that handles the parameter mapping
        def create_tool_fn(tool_func, param_names):
            def wrapped(**kwargs):
                # Ensure all required parameters are present
                missing_params = [p for p in param_names if p not in kwargs]
                if missing_params:
                    raise ValueError(f"Missing required parameters: {', '.join(missing_params)}")
                
                # Map the parameters to what the function expects
                mapped_params = {name: kwargs[name] for name in param_names}
                result = tool_func(**mapped_params)
                return result  # Return the raw result without json.dumps()
            return wrapped
        
        # Create the tool with proper schema
        tool = StructuredTool(
            name=tool_info['name'],
            description=tool_info['description'],
            func=create_tool_fn(tool_info['function'], tool_info['params']),
            args_schema={
                "type": "object",
                "properties": {param: {"type": "string"} for param in tool_info['params']},
                "required": tool_info['params']
            }
        )
        tools.append(tool)
    
    tools_description = "\n".join(tools_description)
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are an intelligent SEC filing analysis agent that can plan and execute queries.
        You have access to these tools:
        
        {tools_description}
        
        10-K Sections Available for Extraction:
        {form_10k_sections}
        
        Your job is to:
        1. Understand what information is needed to answer the query
        2. Use the appropriate tools to gather that information
        3. Keep track of what information you have and what you still need
        4. Generate a final answer when you have all needed information
        
        IMPORTANT: When constructing SEC-API queries, you MUST use the correct field names:
        - Use "formType" (not "form_type") for the form type
        - Use "filedAt" (not "filed_at") for filing date
        - Use "cik" for the company identifier
        
        For example, a correct query would be:
        "ticker:AAPL AND formType:\"10-K\" AND filedAt:[2022-01-01 TO 2022-12-31]"
        
        For each step:
        1. THINK about what information you need and what tool can provide it
        2. Choose the appropriate tool and execute it
        3. Analyze the result and decide what to do next
        4. When you have all needed information, provide the final answer
        
        Always format your response as:
        THOUGHT: Your reasoning about what to do next
        ACTION: The tool to use (or "Final Answer" if ready to respond)
        ACTION INPUT: The parameters to pass to the tool
        
        After each tool returns, you'll receive the result and should plan your next step.
        
        Remember:
        - You can use tools multiple times if needed
        - You should verify information before using it
        - Some queries may need multiple pieces of information
        - Only provide a Final Answer when you have everything needed
        """),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    llm = ChatOpenAI(model="gpt-4-turbo-preview")
    agent = create_openai_tools_agent(llm, tools, prompt)
    
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

def initialize_state(query: str) -> State:
    """Initialize the graph state with user query"""
    return {
        "user_query": query,
        "query_analysis": {},
        "action_plan": [],
        "current_step_index": 0,
        "company_info": None,
        "filing_info": None,
        "section_content": None,
        "financial_data": None,
        "errors": [],
        "final_answer": None
    }

def format_response(raw_answer: str, state: State) -> str:
    """Return SEC-API response directly."""
    # SEC-API responses are already properly formatted
    # Financial data comes as XBRL-JSON
    # Company info comes as EDGAR entity format
    # Filing info comes as SEC-API query format
    # Section content comes as raw text
    return raw_answer

def process_query(query: str) -> Dict[str, Any]:
    """Process a user query about SEC filings using LangGraph."""
    try:
        # Initialize state
        state = initialize_state(query)
        
        # Create workflow
        workflow = StateGraph(State)
        
        def planning_and_execution_node(state: State) -> State:
            """Single node that handles both planning and execution."""
            # Create or get the planning agent
            planning_agent = create_planning_agent()
            
            # Let the agent decide what to do next
            result = planning_agent.invoke({"input": state["user_query"]})
            
            # Parse the agent's response and execute the chosen tool
            # The tool responses are already in SEC-API format
            state["final_answer"] = result["output"]
            return state
            
        # Add the single node that handles everything
        workflow.add_node("planning_and_execution", planning_and_execution_node)
        
        # Add conditional edges
        def should_continue(state: State) -> Literal["continue", "complete", "error"]:
            if state.get("errors"):
                return "error"
            if state.get("final_answer") is not None:
                return "complete"
            return "continue"
        
        workflow.add_conditional_edges(
            "planning_and_execution",
            should_continue,
            {
                "continue": "planning_and_execution",
                "complete": "complete",
                "error": "error"
            }
        )
        
        # Add simple complete and error nodes
        def complete_node(state: State) -> State:
            return state
            
        def error_node(state: State) -> State:
            """Node for handling errors in the workflow."""
            if not state.get("errors"):
                raise ValueError("Error node called without error information")
            
            error = state["errors"][-1]
            return {
                **state,
                "final_answer": f"Error in {error['source']}: {error['message']}"
            }
            
        workflow.add_node("complete", complete_node)
        workflow.add_node("error", error_node)
        
        # Set entry point
        workflow.set_entry_point("planning_and_execution")
        
        # Compile workflow
        app = workflow.compile()
        
        # Execute workflow
        final_state = app.invoke(state)
        
        # Return standardized output
        return {
            "status": "success" if not final_state.get("errors") else "error",
            "answer": final_state.get("final_answer", ""),
            "context": {
                "company_info": final_state.get("company_info"),
                "filing_info": final_state.get("filing_info"),
                "section_content": final_state.get("section_content"),
                "financial_data": final_state.get("financial_data"),
                "errors": final_state.get("errors", [])
            }
        }
        
    except Exception as e:
        logger.error(f"Query processing failed: {str(e)}")
        return {
            "status": "error",
            "answer": f"Failed to process query: {str(e)}",
            "context": {}
        }

if __name__ == "__main__":
    # Check if query is provided in command line arguments
    if len(sys.argv) > 1:
        # Get query from command line arguments
        query = " ".join(sys.argv[1:])
    else:
        # Interactive mode
        print("SEC Filing Analysis System")
        print("Type 'exit' to quit")
        query = input("\nEnter your question: ")
        if query.lower() in ['exit', 'quit']:
            sys.exit(0)
    
    print(f"\nProcessing query: {query}")
    
    # Process the query
    result = process_query(query)
    
    # Display final result
    print("\n" + "="*50)
    print("FINAL RESULT:")
    print("="*50)
    print(f"Status: {result['status']}")
    print(f"\nAnswer: {result['answer']}")
    
    # Exit with appropriate code
    sys.exit(0 if result['status'] == 'success' else 1) 