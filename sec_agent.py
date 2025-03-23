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
    This implementation directly follows the approach in sec.py"""
    
    # Format section info for the prompt
    form_10k_sections = "\n".join([f"* \"{section_id}\" - {section_name}" 
                                 for section_id, section_name in sec_api_knowledge.FORM_10K_SECTIONS.items()])
    
    # Format tool registry for the prompt
    tools_description = "\n".join([
        f"* {tool['name']}: {tool['description']}" for _, tool in TOOL_REGISTRY.items()
    ])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a planning agent for SEC filing analysis.
        
        Available SEC-API Tools:
        {tools_description}
        
        10-K Sections Available:
        {form_10k_sections}
        
        For each query about SEC filings, create a detailed step-by-step plan.
        Each step should include:
        
        ### Step N: [Step Name]
        #### What Information is Needed:
        [List required info - max 20 words]
        #### Tool to Use:
        [Tool name with exact parameters]
        #### Expected Output:
        [What we expect - max 20 words]
        """),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    llm = ChatOpenAI(model="gpt-4-turbo-preview")
    agent = create_openai_tools_agent(llm, [], prompt)
    
    return AgentExecutor(agent=agent, tools=[], verbose=True)

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

def planning_node(state: State) -> State:
    """Planning node that analyzes queries and creates execution plans.
    This directly follows the approach in sec.py's planning_step function."""
    try:
        print("\nStep 1: Planning - Started")
        query = state["user_query"]
        
        # First analyze query using sec_api_knowledge
        query_analysis = sec_api_knowledge.analyze_query_for_tools(query)
        
        # Print analysis details
        print(f"Analyzing query: {query}")
        if "company_name" in query_analysis:
            print(f"Identified company: {query_analysis['company_name']}")
        else:
            print("No company name identified in query")
            
            # If no company name found, use GPT-4 to extract it
            llm = ChatOpenAI(model="gpt-4-turbo-preview")
            company_extraction_prompt = f"""
            Extract the company name from this query about SEC filings. 
            Return ONLY the company name, nothing else.
            If no company is mentioned, respond with "Unknown".
            
            Query: {query}
            """
            company_response = llm.invoke(company_extraction_prompt)
            company_name = company_response.content.strip()
            if company_name and company_name != "Unknown":
                query_analysis["company_name"] = company_name
                print(f"Identified company (via GPT-4): {company_name}")
                
        print(f"Form type: {query_analysis['form_type']}")
        print(f"Requires financial data: {query_analysis['requires_financial_data']}")
        print(f"Requires section extraction: {query_analysis['requires_section_extraction']}")
        
        # Create a detailed step-by-step plan using the planning agent
        planning_agent = create_planning_agent()
        planning_result = planning_agent.invoke({
            "input": f"""
Query: {query}

Analysis:
- Form Type: {query_analysis['form_type']}
- Company Name: {query_analysis.get('company_name', 'Unknown')}
- Date Range: {query_analysis.get('date_range', 'Most recent')}
- Section Needed: {query_analysis.get('section_name', 'N/A')}
- Financial Data: {"Yes" if query_analysis.get('requires_financial_data') else "No"}

Create a detailed step-by-step plan to answer this query.
"""
        })
        
        # Parse plan into steps
        plan_text = planning_result["output"]
        action_plan = []
        
        # Split into step blocks and skip the first empty one
        step_blocks = [s for s in plan_text.split("### Step") if s.strip()]
        
        for step_block in step_blocks:
            try:
                # Extract step name (everything until the first newline)
                step_name = step_block.split("\n")[0].strip()
                
                # Extract sections using more robust splitting
                sections = step_block.split("####")
                
                # Parse each section
                info_needed = ""
                tool = ""
                expected_output = ""
                
                for section in sections:
                    section = section.strip()
                    if section.startswith("What Information is Needed:"):
                        info_needed = section.replace("What Information is Needed:", "").strip()
                    elif section.startswith("Tool to Use:"):
                        tool = section.replace("Tool to Use:", "").strip()
                    elif section.startswith("Expected Output:"):
                        expected_output = section.replace("Expected Output:", "").strip()
                
                if not all([info_needed, tool, expected_output]):
                    raise ValueError("Missing required step information")
                
                # Extract tool name and parameters from the tool string
                tool_info = {
                    "step": step_name,
                    "info_needed": info_needed,
                    "tool": tool,
                    "expected_output": expected_output
                }
                
                action_plan.append(tool_info)
                
            except Exception as e:
                logger.error(f"Failed to parse step: {str(e)}")
                print(f"Error parsing step: {str(e)}")
                continue
        
        if not action_plan:
            raise ValueError("No valid steps found in plan")
            
        # Log the action plan
        print("\nAction Plan:")
        for i, step in enumerate(action_plan, 1):
            print(f"\nStep {i}: {step['step']}")
            print(f"Info Needed: {step['info_needed']}")
            print(f"Tool: {step['tool']}")
            print(f"Expected Output: {step['expected_output']}")
        
        print("\nStep 1: Planning - Complete")
        
        # Update state with plan and analysis
        return {
            **state,
            "query_analysis": query_analysis,
            "action_plan": action_plan,
            "current_step_index": 0
        }
        
    except Exception as e:
        print(f"\nStep 1: Planning - Failed: {str(e)}")
        logger.error(f"Planning failed: {str(e)}")
        return {
            **state,
            "errors": state["errors"] + [{"source": "planning", "message": str(e)}]
        }

def company_resolution_node(state: State) -> State:
    """Node for resolving company information."""
    try:
        print("\nStep 2: Company Resolution - Started")
        
        # Get company name from query analysis
        query_analysis = state["query_analysis"]
        company_name = query_analysis.get("company_name")
        
        if not company_name:
            raise ValueError("No company name found in query")
            
        print(f"Resolving company: {company_name}")
        result = company_resolution_agent(
            identifier_type="name",
            identifier_value=company_name
        )
        
        if result["status"] != 200:
            raise ValueError(f"Company resolution failed: {result.get('error')}")
        
        # Get company data
        company_data = result.get("data", result)
        if isinstance(company_data, list) and len(company_data) > 0:
            # If we got a list of companies, take the first one (most relevant match)
            company_data = company_data[0]
        
        # Create a standardized company object
        standardized_company = {
            "name": company_data.get("name", company_name),
            "cik": company_data.get("cik", ""),
            "ticker": company_data.get("ticker", ""),
            "sic": company_data.get("sic", ""),
            "sic_description": company_data.get("sicDescription", "")
        }
            
        print(f"Company resolved: {standardized_company['name']} (CIK: {standardized_company['cik']}, Ticker: {standardized_company['ticker']})")
        print("\nStep 2: Company Resolution - Complete")
        
        return {
            **state,
            "company_info": standardized_company,
            "current_step_index": state["current_step_index"] + 1
        }
        
    except Exception as e:
        print(f"\nStep 2: Company Resolution - Failed: {str(e)}")
        logger.error(f"Company resolution failed: {str(e)}")
        return {
            **state,
            "errors": state["errors"] + [{"source": "company_resolution", "message": str(e)}]
        }

def filing_search_node(state: State) -> State:
    """Node for searching SEC filings."""
    try:
        print("\nStep 3: Filing Search - Started")
        
        company_info = state["company_info"]
        if not company_info:
            raise ValueError("No company information available")
            
        query_analysis = state["query_analysis"]
        form_type = query_analysis.get("form_type", "10-K")
        
        # Build the query with strict form type matching
        query_string = f'cik:{company_info["cik"]} AND formType:"{form_type}"'
        
        # Add date range if specified
        if "date_range" in query_analysis and query_analysis["date_range"]:
            start_date, end_date = query_analysis["date_range"]
            query_string += f' AND filedAt:[{start_date} TO {end_date}]'
        
        print(f"Searching with query: {query_string}")
        print(f"Searching for {form_type} filings for {company_info['name']} (CIK: {company_info['cik']})")
        
        result = filing_search_agent(
            query={"query": query_string, "from": "0", "size": "10", "sort": [{"filedAt": {"order": "desc"}}]}
        )
        
        if result["status"] != 200:
            raise ValueError(f"Filing search failed: {result.get('error')}")
            
        # Process filing results
        filing_data = result.get("data", {})
        all_filings = filing_data.get("filings", [])
        
        # Filter to ensure we only get the exact form type
        filings = [f for f in all_filings if f["formType"] == form_type]
        
        if filings:
            print(f"Found {len(filings)} {form_type} filings")
            print(f"Most recent: {filings[0]['formType']} filed on {filings[0]['filedAt']}")
            print(f"Link: {filings[0]['linkToFilingDetails']}")
            filing_info = filings[0]
        else:
            print(f"No {form_type} filings found")
            raise ValueError(f"No {form_type} filings found for {company_info['name']}")
            
        print("\nStep 3: Filing Search - Complete")
        
        # Determine next step based on query analysis
        next_step_index = state["current_step_index"] + 1
            
        return {
            **state,
            "filing_info": filing_info,
            "current_step_index": next_step_index
        }
        
    except Exception as e:
        print(f"\nStep 3: Filing Search - Failed: {str(e)}")
        logger.error(f"Filing search failed: {str(e)}")
        return {
            **state,
            "errors": state["errors"] + [{"source": "filing_search", "message": str(e)}]
        }

def section_extraction_node(state: State) -> State:
    """Node for extracting sections from filings."""
    try:
        print("\nStep 4: Section Extraction - Started")
        
        filing_info = state["filing_info"]
        if not filing_info:
            raise ValueError(f"No filings of the requested type available")
            
        query_analysis = state["query_analysis"]
        section_id = query_analysis.get("section_id")
        
        if not section_id:
            # Use sec_api_knowledge to get the section ID
            form_type = query_analysis.get("form_type", "10-K")
            query = state["user_query"]
            
            # Let sec_api_knowledge determine the section ID
            if "section_name" in query_analysis:
                section_name = query_analysis["section_name"]
                section_id = sec_api_knowledge.get_section_id(form_type, section_name)
                
            # If still no section ID, raise an error instead of using defaults
            if not section_id:
                raise ValueError(f"Could not determine which section to extract from {form_type}. The query requires section extraction but no specific section was identified in the query analysis or planning steps.")
        
        print(f"Extracting section {section_id} from {filing_info['formType']} filing")
        print(f"Filing URL: {filing_info['linkToFilingDetails']}")
        
        result = section_extraction_agent(
            filing_url=filing_info["linkToFilingDetails"],
            section=section_id
        )
        
        if result["status"] != 200:
            raise ValueError(f"Section extraction failed: {result.get('error')}")
            
        section_content = result.get("data", "No content extracted")
        display_content = section_content[:500] + "..." if len(section_content) > 500 else section_content
        print(f"Extracted {len(section_content)} characters from section {section_id}")
        print(f"Preview: {display_content[:100]}...")
        
        print("\nStep 4: Section Extraction - Complete")
            
        return {
            **state,
            "section_content": {"section_id": section_id, "content": section_content},
            "current_step_index": state["current_step_index"] + 1
        }
        
    except Exception as e:
        print(f"\nStep 4: Section Extraction - Failed: {str(e)}")
        logger.error(f"Section extraction failed: {str(e)}")
        return {
            **state,
            "errors": state["errors"] + [{"source": "section_extraction", "message": str(e)}]
        }

def xbrl_extraction_node(state: State) -> State:
    """Node for extracting XBRL financial data."""
    try:
        print("\nStep 4: XBRL Financial Data Extraction - Started")
        
        filing_info = state["filing_info"]
        if not filing_info:
            raise ValueError(f"No filings of the requested type available")
            
        query_analysis = state["query_analysis"]
        
        # Check for financial metrics
        financial_metrics = query_analysis.get("financial_metrics", [])
        if not financial_metrics and "requires_financial_data" in query_analysis and query_analysis["requires_financial_data"]:
            # Default to revenue if no specific metrics identified
            financial_metrics = ["revenue"]
            
        print(f"Extracting financial metrics: {', '.join(financial_metrics)}")
        print(f"Filing URL: {filing_info['linkToFilingDetails']}")
        
        # Get accession number from filing URL
        accession_no = filing_info.get("accessionNo", "")
        if not accession_no:
            # Try to extract from URL
            try:
                accession_no = filing_info["linkToFilingDetails"].split("/")[-2]
            except:
                raise ValueError("Could not determine accession number from filing")
        
        # Fixed function call to use htm_url instead of filing_url
        result = xbrl_converter_agent(
            accession_no=accession_no,
            htm_url=filing_info["linkToFilingDetails"]
        )
        
        if result["status"] != 200:
            raise ValueError(f"XBRL extraction failed: {result.get('error')}")
            
        # Get full financial data
        financial_data = result.get("data", {})
        
        # XBRL tag mappings for common financial metrics
        xbrl_metric_mappings = {
            "revenue": [
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "Revenues", 
                "SalesRevenueNet", 
                "RevenueNet",
                "TotalRevenuesAndOtherIncome"
            ],
            "net_income": [
                "NetIncomeLoss",
                "ProfitLoss",
                "NetIncomeLossAvailableToCommonStockholdersBasic"
            ],
            "total_assets": [
                "Assets",
                "AssetsCurrent",
                "AssetsNoncurrent"
            ],
            "cash": [
                "CashAndCashEquivalentsAtCarryingValue",
                "CashAndCashEquivalentsPeriodIncreaseDecrease"
            ],
            "eps": [
                "EarningsPerShareBasic",
                "EarningsPerShareDiluted"
            ]
        }
        
        # Financial statement mappings
        financial_statement_types = [
            "StatementsOfIncome",
            "BalanceSheets",
            "StatementsOfCashFlows",
            "StatementsOfComprehensiveIncome",
            "StatementsOfShareholdersEquity"
        ]
        
        # Extract specific metrics using the mappings
        extracted_metrics = {}
        
        for metric in financial_metrics:
            # Get the list of potential XBRL tags for this metric
            possible_tags = xbrl_metric_mappings.get(metric, [metric])
            
            # Check each financial statement type for the metric
            for statement_type in financial_statement_types:
                if statement_type not in financial_data:
                    continue
                
                statement_data = financial_data[statement_type]
                
                # Check each possible tag in this statement
                for tag in possible_tags:
                    if tag in statement_data:
                        # Take the most recent value
                        values = statement_data[tag]
                        if values and isinstance(values, list) and len(values) > 0:
                            # Get the most recent period's value
                            latest_value = values[0]
                            extracted_metrics[metric] = {
                                "value": latest_value.get("value"),
                                "unit": latest_value.get("unitRef", ""),
                                "period": latest_value.get("period", {}),
                                "source": f"{statement_type}.{tag}"
                            }
                            break  # Found this metric, move to next
                
                # If we found this metric, no need to check other statement types
                if metric in extracted_metrics:
                    break
                    
        print(f"Extracted financial data for {len(extracted_metrics)} metrics")
        print(f"Financial data preview: {str(extracted_metrics)[:200]}...")
        
        print("\nStep 4: XBRL Financial Data Extraction - Complete")
            
        return {
            **state,
            "financial_data": extracted_metrics,
            "current_step_index": state["current_step_index"] + 1
        }
        
    except Exception as e:
        print(f"\nStep 4: XBRL Financial Data Extraction - Failed: {str(e)}")
        logger.error(f"XBRL extraction failed: {str(e)}")
        return {
            **state,
            "errors": state["errors"] + [{"source": "xbrl_extraction", "message": str(e)}]
        }

def answer_generation_node(state: State) -> State:
    """Node for generating the final answer."""
    try:
        print("\nStep 5: Answer Generation - Started")
        
        query = state["user_query"]
        context = ""
        
        # Build context from available data
        if state.get("section_content"):
            section = state["section_content"]
            context += f"Section {section['section_id']} content: {section['content'][:2000]}...\n\n"
            
        if state.get("financial_data"):
            context += f"Financial data: {json.dumps(state['financial_data'], indent=2)}\n\n"
            
        if state.get("filing_info"):
            filing = state["filing_info"]
            context += f"Filing information: {filing['formType']} filed on {filing['filedAt']}\n\n"
        
        if state.get("company_info"):
            company = state["company_info"]
            context += f"Company: {company['name']} (CIK: {company['cik']}, Ticker: {company['ticker']})\n\n"
        
        print(f"Generating answer for query: {query}")
        
        # Use GPT-4 to generate answer
        llm = ChatOpenAI(model="gpt-4-turbo-preview")
        response = llm.invoke(f"""
        Based on the following information from SEC filings:
        {context}
        
        Answer this question accurately and concisely: {query}
        """)
        
        final_answer = response.content
        print(f"Generated answer: {final_answer[:200]}...")
        
        print("\nStep 5: Answer Generation - Complete")
        
        return {
            **state,
            "final_answer": final_answer,
            "current_step_index": state["current_step_index"] + 1
        }
        
    except Exception as e:
        print(f"\nStep 5: Answer Generation - Failed: {str(e)}")
        logger.error(f"Answer generation failed: {str(e)}")
        return {
            **state,
            "errors": state["errors"] + [{"source": "answer_generation", "message": str(e)}]
        }

def error_handling_node(state: State) -> State:
    """Node for handling errors in the workflow."""
    errors = state.get("errors", [])
    error_message = errors[-1]['message'] if errors else "Unknown error"
    
    logger.error(f"Workflow error: {error_message}")
    print(f"\nError: {error_message}")
    
    return {
        **state,
        "final_answer": f"Sorry, I encountered an error: {error_message}"
    }

def decide_next_node(state: State) -> Literal["planning", "company_resolution", "filing_search", "section_extraction", "xbrl_extraction", "answer_generation", "error", "complete"]:
    """Decide which node to execute next based on the current state."""
    
    # If we have errors, go to error handling
    if state.get("errors") and len(state.get("errors")) > 0:
        return "error"
    
    # If we already have a final answer, we're done
    if state.get("final_answer"):
        return "complete"
    
    # Get current step index
    current_index = state.get("current_step_index", 0)
    
    # Get the action plan
    action_plan = state.get("action_plan", [])
    
    # If we haven't planned yet, start with planning
    if not action_plan:
        return "planning"
    
    # If we're at the end of the plan, go to answer generation
    if current_index >= len(action_plan):
        return "answer_generation"
    
    # Check what the current step is
    if current_index < len(action_plan):
        current_step = action_plan[current_index]
        tool_string = current_step.get("tool", "").lower()
        
        # Check which tool the current step uses
        if "resolvecompany" in tool_string or "company" in tool_string:
            return "company_resolution"
        elif "query" in tool_string or "search" in tool_string or "filing" in tool_string:
            return "filing_search"
        elif "extract" in tool_string or "section" in tool_string:
            return "section_extraction"
        elif "xbrl" in tool_string or "financial" in tool_string:
            return "xbrl_extraction"
    
    # Default to answer generation if we can't determine the next step
    return "answer_generation"

def process_query(query: str) -> Dict[str, Any]:
    """Process a user query about SEC filings using LangGraph."""
    try:
        # Initialize state
        state = initialize_state(query)
        
        # Create workflow
        workflow = StateGraph(State)
        
        # Add nodes
        workflow.add_node("planning", planning_node)
        workflow.add_node("company_resolution", company_resolution_node)
        workflow.add_node("filing_search", filing_search_node)
        workflow.add_node("section_extraction", section_extraction_node)
        workflow.add_node("xbrl_extraction", xbrl_extraction_node)
        workflow.add_node("answer_generation", answer_generation_node)
        workflow.add_node("error", error_handling_node)
        
        # Add a simple complete node that just returns the state
        def complete_node(state: State) -> State:
            return state
            
        workflow.add_node("complete", complete_node)
        
        # Add conditional edges from each node to the decision function
        workflow.add_conditional_edges(
            "planning",
            decide_next_node,
            {
                "company_resolution": "company_resolution",
                "error": "error",
                "complete": "complete"
            }
        )
        
        workflow.add_conditional_edges(
            "company_resolution",
            decide_next_node,
            {
                "filing_search": "filing_search",
                "error": "error",
                "complete": "complete"
            }
        )
        
        workflow.add_conditional_edges(
            "filing_search",
            decide_next_node,
            {
                "section_extraction": "section_extraction",
                "xbrl_extraction": "xbrl_extraction",
                "answer_generation": "answer_generation",
                "error": "error",
                "complete": "complete"
            }
        )
        
        workflow.add_conditional_edges(
            "section_extraction",
            decide_next_node,
            {
                "answer_generation": "answer_generation",
                "error": "error",
                "complete": "complete"
            }
        )
        
        workflow.add_conditional_edges(
            "xbrl_extraction",
            decide_next_node,
            {
                "answer_generation": "answer_generation",
                "error": "error",
                "complete": "complete"
            }
        )
        
        workflow.add_conditional_edges(
            "answer_generation",
            decide_next_node,
            {
                "complete": "complete",
                "error": "error"
            }
        )
        
        workflow.add_conditional_edges(
            "error",
            lambda _: "complete",
            {
                "complete": "complete"
            }
        )
        
        # Set entry point
        workflow.set_entry_point("planning")
        
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