"""
SEC Filing Analysis Agent with Chunking Strategy

A LangChain agent that uses SEC-API tools to analyze SEC filings.
Implements a contextual chunking strategy for handling large documents.
"""

import os
import logging
from typing import Dict, Any, Optional, List
from dotenv import load_dotenv
from sec_api import QueryApi, ExtractorApi, XbrlApi
from langchain.agents import AgentType, initialize_agent
from langchain.tools import StructuredTool
from langchain_openai import ChatOpenAI

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Configure environment
load_dotenv()
SEC_API_KEY = os.getenv("SEC_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4")

if not SEC_API_KEY or not OPENAI_API_KEY:
    logger.error("SEC_API_KEY or OPENAI_API_KEY not found in .env file")
    raise ValueError("API keys not found. Please add them to your .env file.")

# Initialize API clients
query_api = QueryApi(api_key=SEC_API_KEY)
extractor_api = ExtractorApi(api_key=SEC_API_KEY)
xbrl_api = XbrlApi(api_key=SEC_API_KEY)

#################################################
# Tool 1: SEC Query API
#################################################
def search_sec_filings(
    query: str,
    from_param: str = "0",
    size: str = "10"
) -> str:
    """
    Search SEC filings using the Query API.
    
    Args:
        query: Search query in SEC-API format (e.g., 'ticker:MSFT AND formType:"10-K"')
        from_param: Starting position for pagination
        size: Number of results to return
        
    Returns:
        Formatted search results
    """
    try:
        # Build query parameters
        search_params = {
            "query": query,
            "from": from_param,
            "size": size,
            "sort": [{"filedAt": {"order": "desc"}}]
        }
        
        # Call the API
        filings = query_api.get_filings(search_params)
        
        if not filings or "filings" not in filings or not filings["filings"]:
            return "No results found matching your criteria."
        
        # Format results
        total_filings = filings.get("total", {}).get("value", 0)
        formatted_results = [f"Found {total_filings} results. Showing top {min(5, len(filings['filings']))}:"]
        
        for i, filing in enumerate(filings.get("filings", [])[:5], 1):
            formatted_results.append(f"\nResult {i}:")
            formatted_results.append(f"Company: {filing.get('companyName', 'N/A')} (Ticker: {filing.get('ticker', 'N/A')})")
            formatted_results.append(f"Form Type: {filing.get('formType', 'N/A')}")
            formatted_results.append(f"Filed At: {filing.get('filedAt', 'N/A')}")
            formatted_results.append(f"Accession Number: {filing.get('accessionNo', 'N/A')}")
            formatted_results.append(f"Filing URL: {filing.get('linkToFilingDetails', filing.get('linkToHtml', 'N/A'))}")
            
            # Add items for 8-K filings
            if filing.get('formType') == '8-K' and filing.get('items'):
                formatted_results.append(f"Items: {filing.get('items', 'N/A')}")
        
        return "\n".join(formatted_results)
    
    except Exception as e:
        logger.error(f"Error in search_sec_filings: {str(e)}")
        return f"An error occurred while searching SEC filings: {str(e)}"

#################################################
# Tool 2: SEC Extractor API
#################################################
def extract_section(
    filing_url: str,
    section_id: str,
    output_format: str = "text"
) -> Dict[str, Any]:
    """
    Extract a section from an SEC filing with enhanced error handling.
    
    Args:
        filing_url: URL to the SEC filing (must be a sec.gov URL ending in .htm or .html)
        section_id: Section identifier (e.g., "7", "1A", "part2item1a")
        output_format: Either "text" or "html" format
        
    Returns:
        Dictionary with section content and metadata
    """
    try:
        # Section ID mappings for common sections
        section_name_mapping = {
            "1": "Business",
            "1A": "Risk Factors",
            "1B": "Unresolved Staff Comments",
            "1C": "Cybersecurity",
            "2": "Properties",
            "3": "Legal Proceedings",
            "4": "Mine Safety",
            "5": "Market Information",
            "6": "Selected Financial Data",
            "7": "Management Discussion and Analysis",
            "7A": "Market Risk",
            "8": "Financial Statements",
            "9": "Accountant Changes",
            "9A": "Controls and Procedures",
            "9B": "Other Information",
            "10": "Directors and Officers",
            "11": "Executive Compensation",
            "12": "Security Ownership",
            "13": "Related Transactions",
            "14": "Principal Accountant Fees",
            # 10-Q Sections
            "part1item1": "Financial Statements",
            "part1item2": "Management Discussion",
            "part1item3": "Market Risk",
            "part1item4": "Controls and Procedures",
            "part2item1": "Legal Proceedings",
            "part2item1a": "Risk Factors",
            "part2item2": "Unregistered Sales",
            "part2item3": "Defaults",
            "part2item4": "Mine Safety",
            "part2item5": "Other Information",
            "part2item6": "Exhibits"
        }
        
        # Fix section_id format - strip any "item_" prefix
        if section_id.startswith("item_"):
            logger.info(f"Converting section ID format from '{section_id}' to '{section_id[5:]}'")
            section_id = section_id[5:]  # Remove "item_" prefix
        
        # Verify URL format
        if not filing_url.startswith("https://www.sec.gov/") or not (filing_url.endswith('.htm') or filing_url.endswith('.html')):
            return {
                "is_error": True,
                "error": "Invalid URL format. Must be a sec.gov URL ending in .htm or .html",
                "content": None,
                "section_id": section_id,
                "section_name": section_name_mapping.get(section_id, "Unknown Section")
            }
        
        # Extract section
        section_content = extractor_api.get_section(filing_url, section_id, output_format)
        
        if not section_content or len(section_content.strip()) < 10:
            return {
                "is_error": False,
                "error": None,
                "content": None,
                "is_empty": True,
                "section_id": section_id,
                "section_name": section_name_mapping.get(section_id, "Unknown Section"),
                "status": "Section exists but appears to be empty or not available"
            }
        
        return {
            "is_error": False,
            "error": None,
            "content": section_content,
            "is_empty": False,
            "section_id": section_id,
            "section_name": section_name_mapping.get(section_id, "Unknown Section"),
            "status": "Success"
        }
    
    except Exception as e:
        logger.error(f"Error in extract_section: {str(e)}")
        return {
            "is_error": True,
            "error": str(e),
            "content": None,
            "section_id": section_id,
            "section_name": section_name_mapping.get(section_id, "Unknown Section"),
            "status": "Error"
        }

#################################################
# Tool 3: SEC XBRL API (Financial Data)
#################################################
def xbrl_to_json(
    htm_url: Optional[str] = None,
    xbrl_url: Optional[str] = None,
    accession_no: Optional[str] = None
) -> Dict[str, Any]:
    """
    Convert XBRL to JSON and extract financial data.
    
    Args:
        htm_url: URL to the filing HTML
        xbrl_url: URL to the XBRL file
        accession_no: Filing accession number
        
    Returns:
        Dictionary containing either the XBRL data or error information
    """
    try:
        # Validate inputs
        input_count = sum(x is not None for x in [htm_url, xbrl_url, accession_no])
        if input_count == 0:
            return {
                "is_error": True,
                "error": "At least one of htm_url, xbrl_url, or accession_no must be provided",
                "data": None
            }
        if input_count > 1:
            return {
                "is_error": True,
                "error": "Please provide only one of htm_url, xbrl_url, or accession_no",
                "data": None
            }
        
        # Call appropriate API method
        if htm_url:
            xbrl_data = xbrl_api.xbrl_to_json(htm_url=htm_url)
        elif xbrl_url:
            xbrl_data = xbrl_api.xbrl_to_json(xbrl_url=xbrl_url)
        else:
            xbrl_data = xbrl_api.xbrl_to_json(accession_no=accession_no)
        
        if not xbrl_data:
            return {
                "is_error": True,
                "error": "No XBRL data found or could not parse XBRL",
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
            # Look for common revenue field names
            revenue_fields = [
                "RevenueFromContractWithCustomerExcludingAssessedTax",
                "Revenues",
                "SalesRevenueNet",
                "RevenueNet"
            ]
            for field in revenue_fields:
                if field in income_data:
                    financial_data["key_metrics"]["revenue"] = income_data[field]
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
# New Tool 4: Section Extraction with Chunking
#################################################
def extract_section_with_chunking(
    filing_url: str,
    section_id: str,
    output_format: str = "text",
    chunk_size: int = 8000,  # Characters per chunk
    chunk_overlap: int = 500  # Overlap between chunks for context
) -> Dict[str, Any]:
    """
    Extract a section from an SEC filing and split into manageable chunks if needed.
    Uses a contextual retrieval approach for chunking.
    
    Args:
        filing_url: URL to the SEC filing (must be a sec.gov URL ending in .htm or .html)
        section_id: Section identifier (e.g., "7", "1A", "part2item1a")
        output_format: Either "text" or "html" format
        chunk_size: Maximum size of each chunk in characters
        chunk_overlap: Number of characters to overlap between chunks
        
    Returns:
        Dictionary with section content (potentially chunked) and metadata
    """
    try:
        # First get the full section using the existing extract_section function
        result = extract_section(filing_url, section_id, output_format)
        
        # Return immediately if there was an error or empty content
        if result["is_error"] or result.get("is_empty", True) or not result["content"]:
            return result
            
        content = result["content"]
        
        # Only apply chunking if content exceeds chunk_size
        if len(content) <= chunk_size:
            result["chunked"] = False
            result["chunk_count"] = 1
            return result
            
        # Split content into paragraphs (respecting document structure)
        paragraphs = []
        for block in content.split('\n\n'):
            # Further split if paragraphs are very long
            if len(block) > chunk_size:
                # Split on sentences for long paragraphs
                sentences = []
                for sentence in block.replace('\n', ' ').split('. '):
                    if sentence:
                        sentences.append(sentence + ('.' if not sentence.endswith('.') else ''))
                paragraphs.extend(sentences)
            else:
                paragraphs.append(block)
        
        # Create chunks with overlap
        chunks = []
        current_chunk = ""
        current_length = 0
        
        for paragraph in paragraphs:
            # If adding this paragraph would exceed chunk_size, finalize the chunk
            if current_length + len(paragraph) + 2 > chunk_size and current_length > 0:
                chunks.append(current_chunk)
                
                # Start new chunk with overlap
                overlap_point = max(0, len(current_chunk) - chunk_overlap)
                current_chunk = current_chunk[overlap_point:] + "\n\n" + paragraph
                current_length = len(current_chunk)
            else:
                # Add paragraph to current chunk
                if current_length > 0:
                    current_chunk += "\n\n" + paragraph
                else:
                    current_chunk = paragraph
                current_length = len(current_chunk)
        
        # Add the last chunk if not empty
        if current_length > 0:
            chunks.append(current_chunk)
        
        # Update result with chunks
        result["content"] = chunks
        result["chunked"] = True
        result["chunk_count"] = len(chunks)
        result["original_length"] = len(content)
        
        # Create chunk metadata
        result["chunks_metadata"] = []
        for i, chunk in enumerate(chunks):
            # Extract key headings or first few lines for each chunk
            lines = chunk.split('\n')
            headings = [line for line in lines if line.isupper() or line.startswith('#') or line.startswith('##')]
            
            first_lines = lines[:min(3, len(lines))]
            
            result["chunks_metadata"].append({
                "chunk_index": i,
                "length": len(chunk),
                "headings": headings[:3],  # First 3 headings
                "preview": " ".join(first_lines)[:100] + "..."  # Preview of first 100 chars
            })
        
        return result
    
    except Exception as e:
        logger.error(f"Error in extract_section_with_chunking: {str(e)}")
        return {
            "is_error": True,
            "error": f"Error in chunking process: {str(e)}",
            "content": None,
            "section_id": section_id,
            "status": "Error"
        }

#################################################
# New Tool 5: Analyze Section with Chunking
#################################################
def analyze_section_chunks(
    filing_url: str,
    section_id: str,
    analysis_objective: str = "Summarize key points and trends",
    chunk_size: int = 8000,
    chunk_overlap: int = 500
) -> Dict[str, Any]:
    """
    Extract and analyze a section by breaking it into manageable chunks.
    
    Args:
        filing_url: URL to the SEC filing
        section_id: Section ID to extract
        analysis_objective: What to analyze in the section
        chunk_size: Maximum size of each chunk
        chunk_overlap: Overlap between chunks
        
    Returns:
        Analysis results with metadata
    """
    # First extract the section with chunking
    result = extract_section_with_chunking(
        filing_url=filing_url,
        section_id=section_id,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap
    )
    
    if result["is_error"] or result.get("is_empty", True):
        return {
            "is_error": True,
            "error": result.get("error", "Failed to extract section"),
            "analysis": None,
            "section_id": section_id
        }
    
    # Create an agent for analysis
    llm = ChatOpenAI(
        temperature=0,
        model=OPENAI_MODEL
    )
    
    # If not chunked, analyze the whole section
    if not result.get("chunked", False):
        # Create a simple prompt for small sections
        content = result["content"]
        prompt = f"""Analyze this {result.get('section_name', section_id)} section with the objective: {analysis_objective}
        
        CONTENT:
        {content[:12000]}  # Limit content length for LLM
        
        Provide a concise analysis focusing on the objective.
        """
        try:
            analysis = llm.invoke(prompt)
            
            return {
                "is_error": False,
                "analysis": analysis.content,
                "section_id": section_id,
                "section_name": result.get("section_name", "Unknown Section"),
                "chunked": False
            }
        except Exception as e:
            logger.error(f"Error in section analysis: {str(e)}")
            return {
                "is_error": True,
                "error": f"Error analyzing section: {str(e)}",
                "section_id": section_id
            }
    
    # For chunked content, analyze each chunk and then synthesize
    chunks = result["content"]
    chunk_analyses = []
    
    # Analyze each chunk
    for i, chunk in enumerate(chunks):
        chunk_prompt = f"""Analyze part {i+1} of {len(chunks)} from {result.get('section_name', section_id)} section with objective: {analysis_objective}
        
        CONTENT CHUNK {i+1}/{len(chunks)}:
        {chunk[:12000]}  # Limit chunk size for LLM
        
        Provide an analysis of this chunk only. Focus on key points and insights.
        Remember this is part {i+1} of {len(chunks)}, so focus on what's in this specific chunk.
        """
        try:
            chunk_analysis = llm.invoke(chunk_prompt)
            chunk_analyses.append({
                "chunk_index": i,
                "analysis": chunk_analysis.content
            })
        except Exception as e:
            logger.error(f"Error analyzing chunk {i}: {str(e)}")
            chunk_analyses.append({
                "chunk_index": i,
                "analysis": f"Error analyzing this chunk: {str(e)}"
            })
    
    # Now synthesize the full analysis
    synthesis_prompt = f"""Synthesize the following analyses of {result.get('section_name', section_id)} section into a cohesive summary.
    
    ANALYSIS OBJECTIVE: {analysis_objective}
    
    INDIVIDUAL CHUNK ANALYSES:
    """
    
    for ca in chunk_analyses:
        synthesis_prompt += f"\n\nCHUNK {ca['chunk_index']+1} ANALYSIS:\n{ca['analysis']}"
    
    synthesis_prompt += "\n\nSynthesize these analyses into one cohesive summary that addresses the original objective. Avoid repetition and focus on the most important insights across all chunks."
    
    try:
        final_analysis = llm.invoke(synthesis_prompt)
        
        return {
            "is_error": False,
            "analysis": final_analysis.content,
            "section_id": section_id,
            "section_name": result.get("section_name", "Unknown Section"),
            "chunked": True,
            "chunk_count": len(chunks),
            "chunk_analyses": chunk_analyses,
            "original_length": result.get("original_length", 0)
        }
    except Exception as e:
        logger.error(f"Error in final synthesis: {str(e)}")
        
        # Fallback: just combine the individual analyses
        combined_analysis = "ANALYSIS SUMMARY (Error in final synthesis):\n\n"
        for ca in chunk_analyses:
            combined_analysis += f"PART {ca['chunk_index']+1} INSIGHTS:\n{ca['analysis']}\n\n"
        
        return {
            "is_error": False,
            "analysis": combined_analysis,
            "section_id": section_id,
            "section_name": result.get("section_name", "Unknown Section"),
            "chunked": True,
            "chunk_count": len(chunks),
            "synthesis_error": str(e)
        }

#################################################
# System Prompt
#################################################
SYSTEM_PROMPT = """You are an expert SEC filing analyst with access to SEC data tools.

Follow these guidelines when using SEC-API tools:

1. Query API: Use for finding specific filings
   - Format: ticker:TSLA AND formType:"10-K"
   - Include date ranges: filedAt:[2020-01-01 TO 2023-12-31]
   - Common form types: 10-K (annual), 10-Q (quarterly), 8-K (current events)

2. Extractor API: Use for getting specific sections
   - Requires proper SEC.gov URLs ending in .htm or .html
   - IMPORTANT: Use ONLY these exact section IDs (without any prefixes):
     * "7" for Management Discussion and Analysis
     * "1A" for Risk Factors
     * "1C" for Cybersecurity
     * "8" for Financial Statements and Notes
     * For 10-Q sections, use proper format: "part1item2" for MD&A

3. XBRL API: Use for financial data
   - Extract shares outstanding, revenue, etc.
   - Requires valid filing URL or accession number

4. Section Analysis with Chunking: Use for analyzing large sections
   - Automatically breaks large sections into manageable chunks
   - Analyzes each chunk and synthesizes a complete analysis
   - Ideal for MD&A and Risk Factors sections that may be very long

Process for common tasks:
1. For section analysis: First find the filing with Query API, then use Section Analysis with Chunking
2. For financial data: Find the filing, then use XBRL API
3. For comparisons: Retrieve and analyze multiple filings to compare corresponding sections

When providing your analysis:
- Be concise but thorough
- Quote relevant text when appropriate
- Format financial data clearly
- For comparisons, highlight key differences
"""

#################################################
# LangChain Setup
#################################################
def create_agent():
    """Create and return a LangChain agent with SEC tools"""
    # Create tools
    tools = [
        StructuredTool.from_function(
            func=search_sec_filings,
            name="SECQueryAPI",
            description="Search SEC filings using exact query syntax (e.g., ticker:MSFT AND formType:\"10-K\")"
        ),
        StructuredTool.from_function(
            func=extract_section,
            name="SECExtractSection",
            description="Extract a specific section from an SEC filing using a valid SEC.gov URL. Use section IDs like '7' for Management Discussion and Analysis, '1A' for Risk Factors, without any prefixes."
        ),
        StructuredTool.from_function(
            func=xbrl_to_json,
            name="SECFinancialData",
            description="Extract financial data from a filing using the XBRL API"
        ),
        StructuredTool.from_function(
            func=analyze_section_chunks,
            name="SECAnalyzeSectionWithChunking",
            description="Extract and analyze a section from an SEC filing using a chunking strategy for handling large documents. Ideal for analyzing MD&A (section '7') or Risk Factors (section '1A')."
        )
    ]
    
    # Create LLM
    llm = ChatOpenAI(
        temperature=0,
        model=OPENAI_MODEL
    )
    
    # Create agent
    agent = initialize_agent(
        tools=tools,
        llm=llm,
        agent=AgentType.STRUCTURED_CHAT_ZERO_SHOT_REACT_DESCRIPTION,
        verbose=True,
        handle_parsing_errors=True,
        system_message=SYSTEM_PROMPT
    )
    
    return agent

#################################################
# Main Functionality
#################################################
def process_query(query: str) -> str:
    """Process a user query using the SEC agent"""
    agent = create_agent()
    try:
        return agent.invoke(query)["output"]
    except Exception as e:
        logger.error(f"Error processing query: {str(e)}")
        return f"An error occurred: {str(e)}"

#################################################
# Entry Point
#################################################
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Process command line query
        query = " ".join(sys.argv[1:])
        print(process_query(query))
    else:
        # Interactive mode
        print("SEC Filing Analysis Agent with Chunking (type 'exit' to quit)")
        print("This version includes contextual chunking for handling large documents")
        while True:
            query = input("\nEnter your question: ")
            if query.lower() in ['exit', 'quit']:
                break
            print("\n" + process_query(query))