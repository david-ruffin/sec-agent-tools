import os
import logging
from dotenv import load_dotenv
from langgraph.graph import StateGraph, END
from langchain.agents import AgentExecutor, create_openai_tools_agent
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI
import sec_api_knowledge

# Configure environment
load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Configure logging
logging.basicConfig(level=logging.INFO, 
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def create_planning_agent():
    """Create an agent for planning steps."""
    # Format section info as readable strings instead of raw dictionaries
    form_10k_sections = "\n".join([f"* \"{section_id}\" - {section_name}" for section_id, section_name in sec_api_knowledge.FORM_10K_SECTIONS.items()])
    form_10q_sections = "\n".join([f"* \"{section_id}\" - {section_name}" for section_id, section_name in sec_api_knowledge.FORM_10Q_SECTIONS.items()])
    form_8k_sections = "\n".join([f"* \"{section_id}\" - {section_name}" for section_id, section_name in sec_api_knowledge.FORM_8K_ITEMS.items()])
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are a planning agent for SEC filing analysis.
        Create a detailed plan to answer questions about SEC filings.
        
        USE THESE EXACT SECTION IDs - DO NOT USE DESCRIPTIVE NAMES:
        
        10-K SECTIONS:
        {form_10k_sections}
        
        10-Q SECTIONS:
        {form_10q_sections}
        
        8-K SECTIONS:
        {form_8k_sections}
        
        For example:
        - Use "7" for Management's Discussion and Analysis in 10-K
        - Use "1A" for Risk Factors in 10-K
        - Use "part2item1a" for Risk Factors in 10-Q
        
        IMPORTANT RULES FOR TOOL SELECTION:
        1. For Financial Data (revenue, assets, earnings, etc.):
           - ALWAYS use SECFinancialData (XBRL API) for financial metrics
           - NEVER try to extract financial data from text sections
           - If XBRL data is unavailable, clearly state this limitation
           - Common financial metrics: revenue, assets, liabilities, earnings, shares
        
        2. For Textual Analysis (risk factors, MD&A, etc.):
           - Use SECExtractSection for specific sections
           - Use section IDs exactly as shown above
        
        3. For Company Information:
           - Always start with ResolveCompany to get accurate ticker/CIK
           - Use parameter_type="name" for company names
           - Use parameter_type="ticker" for ticker symbols
        
        4. For Finding Filings:
           - Use SECQueryAPI with proper filters
           - Include date ranges when specified
           - Default to most recent if no date given
        
        IMPORTANT: Each step description MUST be 10 words or less.
        
        Your output MUST follow this exact format for each step:
        
        ### Step N: [Step Name - MAX 10 WORDS]
        #### What Information is Needed:
        [One line, MAX 10 words]
        #### Tool to Use:
        [Specific tool name and parameters]
        #### Expected Output:
        [One line, MAX 10 words]
        
        Remember: Keep ALL descriptions to 10 words or less.
        """),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    
    llm = ChatOpenAI(model="gpt-4-turbo-preview")
    agent = create_openai_tools_agent(llm, [], prompt)
    
    return AgentExecutor(agent=agent, tools=[], verbose=True)

if __name__ == "__main__":
    # Create the planning agent
    planning_agent = create_planning_agent()
    
    # Test with the query that previously failed
    query = "Summarize the Management Discussion and Analysis section of Microsoft's 2023 10-K"
    
    # Execute the planning agent
    try:
        result = planning_agent.invoke({"input": query})
        
        # Save output to a file
        os.makedirs("output", exist_ok=True)
        with open("output/output2.txt", "w") as f:
            f.write(f"Query: {query}\n\n")
            f.write(f"Planning Result:\n{result['output']}")
            
        print("Planning complete! Results saved to output/output2.txt")
    except Exception as e:
        logger.error(f"Error: {str(e)}")
        print(f"Error: {str(e)}") 