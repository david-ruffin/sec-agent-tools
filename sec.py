"""
SEC Filing Analysis System V2 - Planning Phase Only
Focus: Parse query and create execution plan
"""

import os
import sys
import logging
from typing import Dict, Any, List, Union
from dotenv import load_dotenv
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import sec_api_knowledge
from sec_apis.query import QueryApi
from sec_apis.extractor import ExtractorApi
from sec_apis.mapping import MappingApi
import requests.exceptions
import urllib3.exceptions
from sec_apis.mapping import SECMappingAPI

# Configure logging with more specific format
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - [%(levelname)s] - %(message)s'
)
logger = logging.getLogger(__name__)

# Configure environment
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
SEC_API_KEY = os.getenv("SEC_API_KEY")

if not OPENAI_API_KEY:
    raise ValueError("[ENV ERROR] OPENAI_API_KEY not found in .env file")
if not SEC_API_KEY:
    raise ValueError("[ENV ERROR] SEC_API_KEY not found in .env file")

# Initialize SEC API client
query_api = QueryApi(api_key=SEC_API_KEY)

def create_planning_agent():
    """Create an agent for planning steps."""
    # Format section info and XBRL metrics as readable strings
    form_10k_sections = "\n".join([f"* \"{section_id}\" - {section_name}" 
                                 for section_id, section_name in sec_api_knowledge.FORM_10K_SECTIONS.items()])
    
    xbrl_metrics = "\n".join([f"* {metric}: {', '.join(tags[:2])}..." 
                             for metric, tags in sec_api_knowledge.XBRL_METRICS.items()])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a planning agent for SEC filing analysis.
        
        Available SEC-API Tools and Parameters:

        1. ResolveCompany:
           - Input: Company name exactly as provided in the query
           - Output: Company details including CIK and ticker
           - IMPORTANT: Do not guess or modify company names

        2. SECQueryAPI (Filing Search):
           - Date Format: [YYYY-MM-DD TO YYYY-MM-DD]
           - Form Types: 10-K, 10-Q, 8-K
           - Example: filedAt:[2023-01-01 TO 2023-12-31] AND formType:"10-K"

        3. SECExtractSection (Section Extractor):
           10-K SECTIONS:
           {form_10k_sections}
           
        4. SECFinancialData (XBRL Data):
           FINANCIAL METRICS:
           {xbrl_metrics}

        RULES FOR EACH STEP:
        1. MUST use exact SEC-API parameters (section IDs, date formats)
        2. MUST be clear and concise (max 20 words per step)
        3. MUST follow this format:
           ### Step N: [Step Name]
           #### What Information is Needed:
           [List required info - max 20 words]
           #### Tool to Use:
           [Tool name with exact parameters]
           #### Expected Output:
           [What we expect - max 20 words]

        Example Step:
        ### Step 1: Get Company Information
        #### What Information is Needed:
        Company name: Microsoft Corporation
        #### Tool to Use:
        ResolveCompany with name="Microsoft Corporation"
        #### Expected Output:
        Company details including CIK and ticker
        """),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    # Use GPT-4 for better planning
    llm = ChatOpenAI(model="gpt-4-turbo-preview")
    agent = create_openai_tools_agent(llm, [], prompt)
    
    return AgentExecutor(agent=agent, tools=[], verbose=True)

def planning_step(query: str) -> Dict[str, Any]:
    """Step 1: Planning Phase"""
    try:
        # First analyze query using sec_api_knowledge
        query_context = sec_api_knowledge.analyze_query_for_tools(query)
        
        # Get tool recommendation
        tool_recommendation = {
            "tool": "SECQueryAPI and SECExtractSection",
            "explanation": "Need to search for filing and extract section"
        }
        
        # Extract date filter and section info
        date_filter = query_context.get("date_range", "")
        section_info = query_context.get("section_name", "")
        financial_info = "Yes" if query_context.get("requires_financial_data") else "No"
        
        # Create and execute planning agent
        try:
            planning_agent = create_planning_agent()
            planning_result = planning_agent.invoke({
                "input": f"""
Query: {query}

Analysis:
- Form Type: {query_context['form_type']}
- Company ID Type: {query_context['company_identifier_type']}
- Date Filter: {date_filter if date_filter else 'Most recent'}
- Section Needed: {section_info if section_info else 'N/A'}
- Financial Data: {financial_info if financial_info else 'N/A'}
- Recommended Tool: {tool_recommendation['tool']}
- Reason: {tool_recommendation['explanation']}

Create a detailed step-by-step plan to answer this query.
"""
            })
        except Exception as e:
            logger.error(f"[OPENAI ERROR] Planning agent failed: {str(e)}")
            return {
                "status": 500,
                "error": f"[OPENAI ERROR] Failed to create plan: {str(e)}",
                "query": query
            }
            
        if not planning_result or "output" not in planning_result:
            return {
                "status": 500,
                "error": "[OPENAI ERROR] No valid output from planning agent",
                "query": query
            }
            
        # Parse plan into steps
        plan_text = planning_result["output"]
        steps = []
        
        # Split into step blocks and skip the first empty one
        step_blocks = [s for s in plan_text.split("### Step") if s.strip()]
        
        # Extract company name from first step
        first_step = step_blocks[0] if step_blocks else ""
        company_name = None
        if "Company name:" in first_step:
            company_name = first_step.split("Company name:")[1].split("\n")[0].strip()
            # Add company name to query context
            query_context["company_name"] = company_name
        
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
                
                # Validate step content length (20 words)
                for content, name in [(info_needed, "info"), (tool, "tool"), (expected_output, "output")]:
                    if len(content.split()) > 20:
                        logger.warning(f"[VALIDATION WARNING] Step {name} exceeds 20 words: {content}")
                
                if not all([info_needed, tool, expected_output]):
                    raise ValueError("Missing required step information")
                
                current_step = {
                    "step": step_name,
                    "info_needed": info_needed,
                    "tool": tool,
                    "expected_output": expected_output
                }
                
                steps.append(current_step)
                
            except Exception as e:
                logger.error(f"[PARSING ERROR] Failed to parse step: {str(e)}")
                return {
                    "status": 500,
                    "error": f"[PARSING ERROR] Failed to parse plan step: {str(e)}",
                    "query": query
                }
        
        if not steps:
            return {
                "status": 500,
                "error": "[VALIDATION ERROR] No valid steps found in plan",
                "query": query
            }
        
        # Return success with plan
        return {
            "status": 200,
            "action_plan": steps,
            "current_step": 0,
            "context": {
                "query_context": query_context,
                "tool_recommendation": tool_recommendation
            }
        }
        
    except Exception as e:
        logger.error(f"[SYSTEM ERROR] Planning step failed: {str(e)}")
        return {
            "status": 500,
            "error": f"[SYSTEM ERROR] Planning failed: {str(e)}",
            "query": query
        }

def company_resolution_step(plan_result: Dict[str, Any]) -> Dict[str, Any]:
    """Step 2: Company Resolution
    Use MappingAPI to resolve company information from the query context"""
    try:
        # Get company name from query context
        query_context = plan_result["context"]["query_context"]
        company_name = query_context.get("company_name")
        
        if not company_name:
            logger.error("[VALIDATION ERROR] No company name found in query context")
            return {
                "status": 500,
                "error": "[VALIDATION ERROR] No company name found in query context",
                "query": plan_result.get("query", "Unknown query")
            }
            
        # Initialize MappingAPI
        mapping_api = SECMappingAPI()
        
        try:
            # Resolve company using exact name from query
            company_matches = mapping_api.get_company_by_name(company_name)
            
            if not company_matches:
                logger.error(f"[SEC-API ERROR] No company found with name: {company_name}")
                return {
                    "status": 500,
                    "error": f"[SEC-API ERROR] Company not found: {company_name}",
                    "query": plan_result.get("query", "Unknown query")
                }
                
            # Use first match (most relevant)
            company_info = company_matches[0]
            
            # Format company info for response
            company_data = {
                "name": company_info.name,
                "cik": company_info.cik,
                "ticker": company_info.ticker,
                "sic": company_info.sic,
                "sicDescription": company_info.sic_industry
            }
            
            logger.info(f"[SEC-API SUCCESS] Found company: {company_data['name']} (CIK: {company_data['cik']}, Ticker: {company_data['ticker']})")
            
            # Return success with company info
            return {
                "status": 200,
                "company_info": company_data,
                "context": plan_result["context"]
            }
            
        except Exception as e:
            logger.error(f"[SEC-API ERROR] Company resolution failed: {str(e)}")
            return {
                "status": 500,
                "error": f"[SEC-API ERROR] Failed to resolve company: {str(e)}",
                "query": plan_result.get("query", "Unknown query")
            }
            
    except Exception as e:
        logger.error(f"[SYSTEM ERROR] Company resolution failed: {str(e)}")
        return {
            "status": 500,
            "error": f"[SYSTEM ERROR] Company resolution failed: {str(e)}",
            "query": plan_result.get("query", "Unknown query")
        }

def filing_search_step(company_result: Dict[str, Any]) -> Dict[str, Any]:
    """Step 3: Filing Search
    Search for specific filing using company info and query context"""
    try:
        # Get context from previous step
        query_context = company_result["context"]["query_context"]
        company_info = company_result["company_info"]
        
        # Build SEC-API query
        sec_query = f"cik:{company_info['cik']} AND formType:\"{query_context['form_type']}\""
        
        # Add date range if specified
        if query_context.get('date_range'):
            start_date, end_date = query_context['date_range']
            if start_date and end_date:
                sec_query += f" AND filedAt:[{start_date} TO {end_date}]"
        
        # Query SEC-API
        query = {
            "query": sec_query,
            "from": "0",
            "size": "1",
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        
        logger.info(f"[SEC-API REQUEST] Querying with: {query}")
        filing_result = query_api.get_filings(query)
        
        if not filing_result or "filings" not in filing_result or not filing_result["filings"]:
            return {
                "status": 500,
                "error": f"[SEC-API ERROR] No {query_context['form_type']} filings found for {company_info['name']}",
                "query": query
            }
            
        # Get first (most recent) filing
        filing = filing_result["filings"][0]
        filing_info = {
            "accessionNo": filing.get("accessionNo"),
            "filedAt": filing.get("filedAt"),
            "form": filing.get("formType"),
            "description": filing.get("description"),
            "linkToFilingDetails": filing.get("linkToFilingDetails")
        }
        
        logger.info(f"[SEC-API SUCCESS] Found filing: {filing_info['form']} filed on {filing_info['filedAt']}")
        
        # Return success with filing info
        return {
            "status": 200,
            "filing_info": filing_info,
            "company_info": company_info,
            "context": company_result["context"]
        }
        
    except Exception as e:
        logger.error(f"[SYSTEM ERROR] Filing search failed: {str(e)}")
        return {
            "status": 500,
            "error": f"[SYSTEM ERROR] Filing search failed: {str(e)}",
            "query": str(query)
        }

def section_extraction_step(filing_result: Dict[str, Any]) -> Dict[str, Any]:
    """Step 4: Section Extraction
    Extract specific section from filing using ExtractorApi"""
    try:
        # Get filing info from previous step
        filing_info = filing_result["filing_info"]
        
        # Get section ID directly from action plan step 3
        extraction_step = [step for step in filing_result["action_plan"] if "SECExtractSection" in step["tool"]][0]
        section_id = extraction_step["tool"].split('section="')[1].split('"')[0]
            
        # Initialize ExtractorApi
        extractor_api = ExtractorApi(api_key=SEC_API_KEY)
        filing_url = filing_info["linkToFilingDetails"]
        
        logger.info(f"[SEC-API REQUEST] Extracting section {section_id} from {filing_url}")
        
        try:
            # Extract section using ExtractorApi with URL - no fallbacks
            section_text = extractor_api.get_section(filing_url, section_id, "text")
            
            if not section_text or len(section_text) < 10:
                return {
                    "status": 500,
                    "error": f"[SEC-API ERROR] Section {section_id} not found or empty in filing",
                    "filing_info": filing_info
                }
                
            # Get section content
            section_content = section_text
            
            # For very long sections, truncate to first 5000 chars for display
            display_content = section_content[:5000] + "..." if len(section_content) > 5000 else section_content
            
            logger.info(f"[SEC-API SUCCESS] Extracted section {section_id} ({len(section_content)} chars)")
            
            # Return success with section content
            return {
                "status": 200,
                "section_id": section_id,
                "section_content": section_content,
                "display_content": display_content,
                "filing_info": filing_info,
                "company_info": filing_result["company_info"]
            }
            
        except requests.exceptions.ConnectionError as e:
            logger.error(f"[NETWORK ERROR] SEC-API extraction failed: {str(e)}")
            return {
                "status": 500,
                "error": f"[NETWORK ERROR] Failed to connect to SEC-API: {str(e)}",
                "filing_info": filing_info
            }
        except Exception as e:
            logger.error(f"[SEC-API ERROR] Section extraction failed: {str(e)}")
            return {
                "status": 500,
                "error": f"[SEC-API ERROR] Section extraction failed: {str(e)}",
                "filing_info": filing_info
            }
            
    except Exception as e:
        logger.error(f"[SYSTEM ERROR] Section extraction failed: {str(e)}")
        return {
            "status": 500,
            "error": f"[SYSTEM ERROR] Section extraction failed: {str(e)}",
            "filing_info": filing_result.get("filing_info", {})
        }

if __name__ == "__main__":
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
    
    # Step 1: Planning
    plan_result = planning_step(query)
    if plan_result["status"] != 200:
        print(f"\n{plan_result['error']}")
        sys.exit(1)
        
    print("\nStep 1: Planning - Complete")
    print("\nAction Plan:")
    for i, step in enumerate(plan_result["action_plan"], 1):
        print(f"\nStep {i}: {step['step']}")
        print(f"Info Needed: {step['info_needed']}")
        print(f"Tool: {step['tool']}")
        print(f"Expected Output: {step['expected_output']}")
    
    # Add action plan to next step
    plan_result["action_plan"] = plan_result["action_plan"]
    
    # Step 2: Company Resolution
    company_result = company_resolution_step(plan_result)
    if company_result["status"] != 200:
        print(f"\n{company_result['error']}")
        sys.exit(1)
        
    print("\nStep 2: Company Resolution - Complete")
    print(f"Company: {company_result['company_info']['name']}")
    print(f"CIK: {company_result['company_info']['cik']}")
    print(f"Ticker: {company_result['company_info']['ticker']}")
    
    # Add action plan to next step
    company_result["action_plan"] = plan_result["action_plan"]
    
    # Step 3: Filing Search
    filing_result = filing_search_step(company_result)
    if filing_result["status"] != 200:
        print(f"\n{filing_result['error']}")
        sys.exit(1)
        
    print("\nStep 3: Filing Search - Complete")
    print(f"Found: {filing_result['filing_info']['form']} filed on {filing_result['filing_info']['filedAt']}")
    print(f"Link: {filing_result['filing_info']['linkToFilingDetails']}")
    
    # Add action plan to next step
    filing_result["action_plan"] = plan_result["action_plan"]
    
    # Step 4: Section Extraction
    section_result = section_extraction_step(filing_result)
    if section_result["status"] != 200:
        print(f"\n{section_result['error']}")
        sys.exit(1)
        
    print("\nStep 4: Section Extraction - Complete")
    print(f"Extracted: Section {section_result['section_id']} from {section_result['filing_info']['form']}")
    print(f"\nPreview (first 500 chars):\n{section_result['display_content'][:500]}...")
    
    # Write section content to output file
    output_file = f"output_{section_result['company_info']['ticker']}_{section_result['filing_info']['form']}_{section_result['section_id']}.txt"
    with open(output_file, "w") as f:
        f.write(section_result['section_content'])
    
    print(f"\nFull content written to {output_file}")
    
    # Exit with success
    sys.exit(0) 