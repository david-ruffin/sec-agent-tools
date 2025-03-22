"""
SEC Filing Analysis System with LangGraph

A more robust implementation of the SEC filing analysis tool
using LangGraph's Plan-and-Execute pattern.
"""

import os
import logging
from typing import Dict, Any, List, Sequence, TypedDict, Optional, Union
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain.tools import StructuredTool
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
from sec_api import QueryApi, ExtractorApi, XbrlApi
from mapping_api.mapping_api import SECMappingAPI
import sec_api_knowledge

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure environment
load_dotenv()
SEC_API_KEY = os.getenv("SEC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

if not SEC_API_KEY or not OPENAI_API_KEY:
    logger.error("SEC_API_KEY or OPENAI_API_KEY not found in .env file")
    raise ValueError("API keys not found. Please add them to your .env file.")

# Initialize API clients
query_api = QueryApi(api_key=SEC_API_KEY)
extractor_api = ExtractorApi(api_key=SEC_API_KEY)
xbrl_api = XbrlApi(api_key=SEC_API_KEY)
mapping_api = SECMappingAPI()  # Using our enhanced implementation

# Type definitions
class AgentState(TypedDict):
    query: str
    action_plan: List[Dict[str, Any]]
    current_step: int
    step_results: List[Dict[str, Any]]
    context: Dict[str, Any]
    error: Union[str, None]
    company_cache: Dict[str, Dict[str, Any]]  # Add cache to state

#################################################
# Tool 1: Company Resolution
#################################################
def resolve_company_info(
    parameter_type: str,
    value: str,
    state: Optional[AgentState] = None
) -> Dict[str, Any]:
    """
    Resolve a company identifier to standardized information.
    
    Args:
        parameter_type: One of 'ticker', 'cik', 'cusip', 'name', 'exchange', 'sector', 'industry'
        value: The value to resolve
        state: Current agent state for caching
    
    Returns:
        Dictionary containing company information or error
    """
    try:
        # Check if we already have a successful resolution in context
        if state and state.get("context", {}).get("company_info"):
            logger.info("Using existing company info from context")
            return {
                "success": True,
                "data": state["context"]["company_info"],
                "message": "Using existing company info"
            }

        # Use our enhanced mapping API implementation
        result = mapping_api.resolve_company(parameter_type, value)
        
        # Handle successful resolution
        if result and (isinstance(result, list) and result or not isinstance(result, list)):
            company_info = result[0].__dict__ if isinstance(result, list) else result.__dict__
            
            # Store in context if we have state
            if state:
                if state.get("context") is None:
                    state["context"] = {}
                state["context"]["company_info"] = company_info
            
            return {
                "success": True,
                "data": company_info,
                "message": "Company resolved successfully"
            }
            
        # Handle no results found
        return {
            "success": False,
            "data": None,
            "message": f"No company found for {parameter_type}: {value}"
        }
        
    except Exception as e:
        logger.error(f"Error in resolve_company_info: {str(e)}")
        return {
            "success": False,
            "data": None,
            "message": f"API error: {str(e)}"
        }

#################################################
# Tool 2: SEC Query API
#################################################
def search_sec_filings(
    ticker: Optional[str] = None,
    cik: Optional[str] = None,
    company_name: Optional[str] = None,
    form_type: Optional[str] = None,
    from_date: Optional[str] = None,
    to_date: Optional[str] = None,
    size: str = "1"
) -> str:
    """
    Search SEC filings using the Query API.
    
    Args:
        ticker: Company ticker symbol
        cik: Company CIK number
        company_name: Company name
        form_type: Filing form type (e.g., '10-K', '10-Q')
        from_date: Start date in YYYY-MM-DD format
        to_date: End date in YYYY-MM-DD format
        size: Number of results to return
        
    Returns:
        Formatted search results or error message
    """
    try:
        # Build query
        query_parts = []
        
        if ticker:
            query_parts.append(f'ticker:"{ticker}"')
        elif cik:
            query_parts.append(f'cik:"{cik}"')
        elif company_name:
            query_parts.append(f'companyName:"{company_name}"')
            
        if form_type:
            query_parts.append(f'formType:"{form_type}"')
            
        if from_date and to_date:
            query_parts.append(f'filedAt:[{from_date} TO {to_date}]')
        elif from_date:
            query_parts.append(f'filedAt:[{from_date} TO 2099-12-31]')
        elif to_date:
            query_parts.append(f'filedAt:[1900-01-01 TO {to_date}]')
            
        # Join query parts with AND
        query = " AND ".join(query_parts)
        
        # Search parameters
        search_params = {
            "query": query,
            "from": "0",
            "size": size,
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        
        # Execute search
        filings = query_api.get_filings(search_params)
        
        if not filings or "filings" not in filings or not filings["filings"]:
            return "No results found matching your criteria."
        
        # Format results
        total_filings = filings.get("total", {}).get("value", 0)
        
        if int(size) == 1:
            # For single filing, return detailed info
            filing = filings["filings"][0]
            return f"""
Most Recent Filing:
Company: {filing.get('companyName', 'N/A')} (Ticker: {filing.get('ticker', 'N/A')})
Form Type: {filing.get('formType', 'N/A')}
Filed At: {filing.get('filedAt', 'N/A')}
Filing URL: {filing.get('linkToFilingDetails', filing.get('linkToHtml', 'N/A'))}
"""
        else:
            # For multiple filings, return summary list
            formatted_results = [f"Found {total_filings} total filings. Showing most recent {min(int(size), len(filings['filings']))}:"]
            
            for i, filing in enumerate(filings.get("filings", []), 1):
                formatted_results.append(f"\nFiling {i}:")
                formatted_results.append(f"Company: {filing.get('companyName', 'N/A')} (Ticker: {filing.get('ticker', 'N/A')})")
                formatted_results.append(f"Form Type: {filing.get('formType', 'N/A')}")
                formatted_results.append(f"Filed At: {filing.get('filedAt', 'N/A')}")
                formatted_results.append(f"Filing URL: {filing.get('linkToFilingDetails', filing.get('linkToHtml', 'N/A'))}")
            
            return "\n".join(formatted_results)
        
    except Exception as e:
        logger.error(f"Error in search_sec_filings: {str(e)}")
        return f"Error searching SEC filings: {str(e)}"

#################################################
# Tool 3: SEC Extractor API
#################################################
def extract_section(
    filing_url: str, 
    section_id: str
) -> Dict[str, Any]:
    """
    Extract a specific section from an SEC filing.
    
    Args:
        filing_url: URL to the SEC filing (must be a sec.gov URL)
        section_id: Section identifier (e.g., "1A", "7", "part1item2")
        
    Returns:
        Dictionary containing either the extracted section or error information
    """
    try:
        # Validate filing URL
        if not filing_url.startswith("https://www.sec.gov/"):
            return {
                "is_error": True,
                "error": "Invalid URL. Must be an SEC.gov URL.",
                "content": None
            }
            
        # Get form type from URL to validate section ID
        form_type = None
        if "10-k" in filing_url.lower() or "10k" in filing_url.lower():
            form_type = "10-K"
            valid_sections = sec_api_knowledge.SECTION_IDS_10K
        elif "10-q" in filing_url.lower() or "10q" in filing_url.lower():
            form_type = "10-Q"
            valid_sections = sec_api_knowledge.SECTION_IDS_10Q
        elif "8-k" in filing_url.lower() or "8k" in filing_url.lower():
            form_type = "8-K"
            valid_sections = sec_api_knowledge.SECTION_IDS_8K
        else:
            # Try to infer from section_id format
            if section_id.startswith("part"):
                form_type = "10-Q"
                valid_sections = sec_api_knowledge.SECTION_IDS_10Q
            elif "." in section_id:
                form_type = "8-K"
                valid_sections = sec_api_knowledge.SECTION_IDS_8K
            else:
                form_type = "10-K"
                valid_sections = sec_api_knowledge.SECTION_IDS_10K
        
        # Validate section ID
        if section_id not in valid_sections:
            return {
                "is_error": True,
                "error": f"Invalid section ID '{section_id}' for {form_type}. Valid sections are: {', '.join(valid_sections.keys())}",
                "content": None,
                "form_type": form_type
            }
            
        # Extract section
        section_content = extractor_api.get_section(filing_url, section_id, "text")
        
        if not section_content or len(section_content.strip()) < 10:
            return {
                "is_error": True,
                "error": f"Section {section_id} appears to be empty or not available in this filing.",
                "content": None,
                "section_id": section_id,
                "section_name": valid_sections.get(section_id, "Unknown Section"),
                "form_type": form_type
            }
        
        return {
            "is_error": False,
            "content": section_content,
            "section_id": section_id,
            "section_name": valid_sections.get(section_id, "Unknown Section"),
            "form_type": form_type
        }
    
    except Exception as e:
        logger.error(f"Error in extract_section: {str(e)}")
        return {
            "is_error": True,
            "error": str(e),
            "content": None,
            "section_id": section_id
        }

#################################################
# Tool 4: SEC XBRL API
#################################################
def xbrl_to_json(
    filing_url: str
) -> Dict[str, Any]:
    """
    Extract financial data from a filing using XBRL.
    
    Args:
        filing_url: URL to the SEC filing
        
    Returns:
        Dictionary containing either the XBRL data or error information
    """
    try:
        # Check for valid URL format
        if not filing_url.startswith("https://www.sec.gov/"):
            return {
                "is_error": True,
                "error": "Invalid URL format. Must be an SEC.gov URL.",
                "data": None
            }
            
        # Extract XBRL data
        xbrl_data = xbrl_api.xbrl_to_json(htm_url=filing_url)
        
        if not xbrl_data:
            return {
                "is_error": True,
                "error": "No XBRL data found for this filing.",
                "data": None
            }
        
        # Extract key financial information
        financial_data = {
            "statements": [],
            "key_metrics": {}
        }
        
        # Find statements
        for key in xbrl_data.keys():
            if key.startswith("Statements") or key == "CoverPage":
                financial_data["statements"].append(key)
        
        # Extract key metrics
        if "CoverPage" in xbrl_data:
            cover_data = xbrl_data["CoverPage"]
            if "EntityCommonStockSharesOutstanding" in cover_data:
                financial_data["key_metrics"]["shares_outstanding"] = cover_data["EntityCommonStockSharesOutstanding"]
            if "EntityPublicFloat" in cover_data:
                financial_data["key_metrics"]["public_float"] = cover_data["EntityPublicFloat"]
            if "DocumentFiscalPeriodFocus" in cover_data:
                financial_data["key_metrics"]["fiscal_period"] = cover_data["DocumentFiscalPeriodFocus"]
            if "DocumentFiscalYearFocus" in cover_data:
                financial_data["key_metrics"]["fiscal_year"] = cover_data["DocumentFiscalYearFocus"]
        
        # Check for revenue data
        if "StatementsOfIncome" in xbrl_data:
            income_data = xbrl_data["StatementsOfIncome"]
            
            # Look for common revenue field names from our knowledge base
            for field in sec_api_knowledge.FINANCIAL_METRICS["revenue"]:
                if field in income_data:
                    financial_data["key_metrics"]["revenue"] = income_data[field]
                    break
            
            # Look for net income
            for field in sec_api_knowledge.FINANCIAL_METRICS["net_income"]:
                if field in income_data:
                    financial_data["key_metrics"]["net_income"] = income_data[field]
                    break
            
            # Look for EPS
            for field in sec_api_knowledge.FINANCIAL_METRICS["earnings_per_share"]:
                if field in income_data:
                    financial_data["key_metrics"]["earnings_per_share"] = income_data[field]
                    break
        
        # Check for balance sheet data
        if "BalanceSheets" in xbrl_data:
            balance_data = xbrl_data["BalanceSheets"]
            
            # Look for asset data
            for field in sec_api_knowledge.FINANCIAL_METRICS["assets"]:
                if field in balance_data:
                    financial_data["key_metrics"]["assets"] = balance_data[field]
                    break
            
            # Look for liability data
            for field in sec_api_knowledge.FINANCIAL_METRICS["liabilities"]:
                if field in balance_data:
                    financial_data["key_metrics"]["liabilities"] = balance_data[field]
                    break
        
        return {
            "is_error": False,
            "error": None,
            "data": xbrl_data,
            "summary": financial_data
        }
    
    except Exception as e:
        logger.error(f"Error in xbrl_to_json: {str(e)}")
        return {
            "is_error": True,
            "error": str(e),
            "data": None
        }

#################################################
# Agent Steps
#################################################
def create_planning_agent():
    """Create an agent for planning steps."""
    # Format section info as readable strings
    form_10k_sections = "\n".join([f"* \"{section_id}\" - {section_name}" for section_id, section_name in sec_api_knowledge.FORM_10K_SECTIONS.items()])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a planning agent for SEC filing analysis.
        Create a detailed plan to answer questions about SEC filings.
        
        Available Tools:
        - ResolveCompany: Get company info from name/ticker
        - SECQueryAPI: Search for SEC filings
        - SECExtractSection: Get specific sections from filings
        - SECFinancialData: Extract XBRL financial data
        
        10-K SECTIONS:
        {form_10k_sections}
        
        For example:
        - Use "7" for Management's Discussion and Analysis
        - Use "1A" for Risk Factors
        
        Your output MUST follow this exact format for each step:
        
        ### Step N: [Step Name]
        #### What Information is Needed:
        [List required info]
        #### Tool to Use:
        [Tool name and parameters]
        #### Expected Output:
        [What we expect from this step]
        """),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    llm = ChatOpenAI(model="gpt-4-turbo-preview")
    agent = create_openai_tools_agent(llm, [], prompt)
    
    return AgentExecutor(agent=agent, tools=[], verbose=True)

def create_execution_agent(tools: Sequence[StructuredTool]):
    """Create an agent for executing steps."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are an execution agent for SEC filing analysis.
        Execute individual steps of the analysis plan EXACTLY as specified.
        
        When using tools:
        1. Check the response's "success" field
        2. If success is false, report the error message and stop
        3. If success is true, use the data for next steps
        4. Use existing company info from context when available
        """),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    llm = ChatOpenAI(model="gpt-4-turbo-preview")
    agent = create_openai_tools_agent(llm, tools, prompt)
    
    return AgentExecutor(agent=agent, tools=tools, verbose=True)

def create_response_agent():
    """Create an agent for generating the final response."""
    prompt = ChatPromptTemplate.from_messages([
        ("system", """You are a response agent for SEC filing analysis.
        Your job is to synthesize the results of multiple analysis steps
        into a clear, concise answer.
        
        Guidelines:
        - Be concise and direct, focusing on the answer to the user's question
        - Include relevant financial figures when available
        - Format financial data in an easy-to-read manner
        - Include important context but avoid unnecessary details
        - If information is missing or unavailable, clearly state that
        """),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    llm = ChatOpenAI(model="gpt-4-turbo-preview")
    agent = create_openai_tools_agent(llm, [], prompt)
    
    return AgentExecutor(agent=agent, tools=[], verbose=True)

#################################################
# Graph Nodes
#################################################
def planning_step(state: AgentState) -> AgentState:
    """Create a plan for analysis based on the query."""
    planning_agent = create_planning_agent()
    
    try:
        # Get query context for enhanced planning
        query_context = sec_api_knowledge.analyze_query_for_tools(state["query"])
        tool_recommendation = {
            "tool": query_context["recommended_tools"][0],
            "explanation": f"Based on query analysis, starting with {query_context['recommended_tools'][0]}"
        }
        
        planning_input = {
            "input": f"""
Query: {state["query"]}

Query Analysis:
- Form Type: {query_context['form_type']}
- Is Financial Query: {query_context['requires_financial_data']}
- Is Textual Query: {query_context['requires_section_extraction']}
- Recommended Tool: {tool_recommendation['tool']}
- Reason: {tool_recommendation['explanation']}

Create a detailed step-by-step plan to answer this query.
"""
        }
        
        # Execute planning agent
        planning_result = planning_agent.invoke(planning_input)
        
        # Parse plan into steps
        plan_text = planning_result["output"]
        steps = []
        
        for step_block in plan_text.split("### Step")[1:]:
            try:
                step_name = step_block.split("\n")[0].strip()
                info_needed = step_block.split("#### What Information is Needed:")[1].split("\n")[0].strip()
                tool = step_block.split("#### Tool to Use:")[1].split("\n")[0].strip()
                expected_output = step_block.split("#### Expected Output:")[1].split("\n")[0].strip()
                
                current_step = {
                    "step": step_name,
                    "info_needed": info_needed,
                    "tool": tool,
                    "expected_output": expected_output
                }
                
                steps.append(current_step)
            except Exception as e:
                logger.error(f"Error parsing step: {str(e)}")
                continue
        
        return {
            "action_plan": steps,
            "current_step": 0,
            "error": None,
            "context": {
                "query_context": query_context,
                "tool_recommendation": tool_recommendation
            }
        }
    
    except Exception as e:
        logger.error(f"Error in planning step: {str(e)}")
        return {
            "error": f"Planning error: {str(e)}"
        }

def execution_step(state: AgentState) -> AgentState:
    """Execute the current step in the plan."""
    if state.get("error"):
        return state
    
    current_step = state["action_plan"][state["current_step"]]
    context = state.get("context", {})
    
    # Create execution agent with tools
    tools = [
        StructuredTool.from_function(
            func=lambda parameter_type, value: resolve_company_info(parameter_type, value, state),
            name="ResolveCompany",
            description="Resolve company information to get ticker/CIK. Input types: 'ticker', 'cik', 'cusip', 'name', 'exchange', 'sector', 'industry'"
        ),
        StructuredTool.from_function(
            func=search_sec_filings,
            name="SECQueryAPI",
            description="Search SEC filings by providing company name and form type (e.g., companyName: Microsoft Corporation, formType: 10-K)"
        ),
        StructuredTool.from_function(
            func=extract_section,
            name="SECExtractSection",
            description="Extract a specific section from an SEC filing"
        ),
        StructuredTool.from_function(
            func=xbrl_to_json,
            name="SECFinancialData",
            description="Extract financial data from a filing"
        )
    ]
    
    execution_agent = create_execution_agent(tools)
    
    try:
        # Create a structured prompt for the execution agent
        prompt = f"""
        Execute the following step in our SEC analysis plan:
        
        Step: {current_step['step']}
        Information Needed: {current_step.get('info_needed', 'N/A')}
        Tool to Use: {current_step.get('tool', 'N/A')}
        Expected Output: {current_step.get('expected_output', 'N/A')}
        
        Current Context:
        {context}
        
        Original Query: {state["query"]}
        
        Please use the appropriate tool to execute this step and provide the results.
        Remember to use information from previous steps stored in the context.
        """
        
        result = execution_agent.invoke({
            "input": prompt,
            "context": context
        })
        
        # Extract and store important information in context
        if "ResolveCompany" in current_step.get('tool', ''):
            # Store company info in context
            context["company_info"] = result["output"]
            if isinstance(result["output"], dict) and "ticker" in result["output"]:
                context["ticker"] = result["output"]["ticker"]
        elif "SECQueryAPI" in current_step.get('tool', ''):
            # Store filing info in context
            context["filing_info"] = result["output"]
            if "Filing URL:" in result["output"]:
                context["filing_url"] = result["output"].split("Filing URL:")[1].strip()
        elif "SECFinancialData" in current_step.get('tool', ''):
            # Store financial data in context
            context["financial_data"] = result["output"]
        elif "SECExtractSection" in current_step.get('tool', ''):
            # Store section content in context
            context["section_content"] = result["output"]
        
        # Store results and update state
        return {
            "step_results": [{
                "step": current_step,
                "output": result["output"]
            }],
            "current_step": state["current_step"] + 1,
            "context": context
        }
    
    except Exception as e:
        logger.error(f"Error in execution step: {str(e)}")
        return {
            "error": f"Execution error: {str(e)}"
        }

def response_step(state: AgentState) -> AgentState:
    """Generate the final response based on the execution results."""
    if state.get("error"):
        return state
    
    response_agent = create_response_agent()
    
    try:
        # Prepare execution results
        execution_results = ""
        for step_result in state.get("step_results", []):
            execution_results += f"\nStep: {step_result['step'].get('step', 'Unknown')}\n"
            execution_results += f"Output: {step_result['output']}\n"
            execution_results += "---\n"
        
        # Create prompt for response agent
        prompt = f"""
        Original Query: {state["query"]}
        
        Execution Results:
        {execution_results}
        
        Context Information:
        {state.get("context", {})}
        
        Please synthesize these results into a clear, concise answer to the user's query.
        """
        
        result = response_agent.invoke({
            "input": prompt
        })
        
        # Return final answer
        return {
            "answer": result["output"]
        }
    
    except Exception as e:
        logger.error(f"Error in response step: {str(e)}")
        return {
            "error": f"Response generation error: {str(e)}"
        }

def should_continue(state: AgentState) -> str:
    """Determine whether to continue to the next step or end."""
    if state.get("error"):
        return "end"
    elif "answer" in state:
        return "end"
    elif state.get("current_step", 0) >= len(state.get("action_plan", [])):
        return "respond"
    else:
        return "execute"

#################################################
# LangGraph Setup
#################################################
def create_graph():
    """Create and return a LangGraph for SEC analysis."""
    # Create a new graph
    workflow = StateGraph(AgentState)
    
    # Add nodes to the graph
    workflow.add_node("plan", planning_step)
    workflow.add_node("execute", execution_step)
    workflow.add_node("respond", response_step)
    
    # Add edges for execution flow
    workflow.add_edge("plan", "execute")
    workflow.add_conditional_edges(
        "execute",
        should_continue,
        {
            "execute": "execute",
            "respond": "respond",
            "end": END
        }
    )
    workflow.add_edge("respond", END)
    
    # Set the entry point
    workflow.set_entry_point("plan")
    
    # Compile the graph
    return workflow.compile()

#################################################
# Entry Point
#################################################
def process_query(query: str) -> str:
    """Process a user query using the SEC analysis graph."""
    app = create_graph()
    
    # Create initial state
    initial_state = {
        "query": query,
        "action_plan": [],
        "current_step": 0,
        "step_results": [],
        "context": {},
        "error": None,
        "company_cache": {}
    }
    
    try:
        # Execute the graph
        final_state = app.invoke(initial_state)
        
        # Check for errors
        if final_state.get("error"):
            return f"Error: {final_state['error']}"
        
        # Return the answer
        return final_state.get("answer", "No answer generated.")
    
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return f"An unexpected error occurred: {str(e)}"

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Process command line query
        query = " ".join(sys.argv[1:])
        print(process_query(query))
    else:
        # Interactive mode
        print("SEC Filing Analysis System with LangGraph")
        print("Type 'exit' to quit")
        while True:
            query = input("\nEnter your question: ")
            if query.lower() in ['exit', 'quit']:
                break
            print("\n" + process_query(query)) 