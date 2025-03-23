# SEC Filing Analysis System: Agent Architecture Plan

## Project Overview

The SEC Filing Analysis System is designed to help users extract and analyze information from SEC filings by leveraging the extensive SEC-API set of endpoints. The system employs an agent-based architecture using LangGraph, with a clear separation between a "smart" planner agent and "dumb" tool agents that interface with specific SEC-API endpoints.

## Design Philosophy

This architecture follows a strict agent-based approach with:

1. **Smart Planner Agent**: Acts as the user proxy, interprets queries, plans execution steps, and orchestrates the tool agents.
2. **Dumb Tool Agents**: Each represents a single SEC-API endpoint with no reasoning capabilities.
3. **Clear Responsibility Separation**: The planner makes all decisions; tool agents simply execute.

## Why This Approach Works

This design offers several advantages:

- **Modularity**: Each tool agent is a simple wrapper around a specific SEC-API endpoint, making it easy to add/remove/update capabilities.
- **Efficiency**: Only the planner uses LLM capabilities; tool agents are lightweight function wrappers.
- **Maintainability**: Simple interfaces between components make debugging and extending the system straightforward.
- **Clarity**: Each component has a single responsibility, making the system easier to understand.
- **Testability**: Each agent can be tested independently with clearly defined inputs and outputs.

## Core Principles

### Avoid Fallbacks

**IMPORTANT**: This system explicitly AVOIDS fallbacks. If an agent cannot complete its task with the provided parameters, it should fail clearly and explicitly. This approach:

- Reveals gaps in our understanding rather than hiding them
- Ensures consistent behavior (no silent defaults)
- Makes the planner responsible for handling failures
- Provides clear signals about what needs improvement

### No Rigid Rules in Tool Agents

Tool agents should NOT contain:
- Decision logic
- Parameter interpretation
- Defaults or assumed values
- Recovery strategies

Instead, tool agents should be pure functions that:
- Accept exactly specified parameters
- Execute a single API call
- Return results exactly as provided by the API
- Include clear status information

### Planner Intelligence

The planner agent is the ONLY component permitted to:
- Interpret user queries
- Choose appropriate tools
- Format parameters
- Handle errors
- Adapt strategies
- Make decisions

## LangGraph Integration

The system will leverage LangGraph for orchestrating the multi-agent workflow. This implementation focuses on core functionality for the POC without over-engineering.

### State Management

Define a simple state schema for tracking agent interactions:

```python
# Define state that tracks information between agents
state_schema = {
    "user_query": str,  # Original user question
    "company_info": Optional[Dict],  # Company resolution results
    "filings": Optional[List[Dict]],  # Filing search results
    "current_filing": Optional[Dict],  # Current filing being analyzed
    "extracted_content": Optional[Dict],  # Extracted section content
    "current_status": str,  # Current status of the workflow
    "errors": List[Dict],  # Any errors encountered
    "final_response": Optional[str]  # Final answer to user
}
```

### Agent Graph Structure

Implement a directed graph structure using LangGraph:

```python
from langgraph.graph import StateGraph
import operator

# Create the graph
workflow = StateGraph(state_schema)

# Add nodes for each agent
workflow.add_node("planner", planner_agent)
workflow.add_node("company_resolution", company_resolution_node)
workflow.add_node("filing_search", filing_search_node)
workflow.add_node("section_extraction", section_extraction_node)
workflow.add_node("summarizer", summarizer_node)

# Define the entry point
workflow.set_entry_point("planner")

# Add conditional edges based on planner decisions
workflow.add_conditional_edges(
    "planner",
    lambda state: state["next_step"],
    {
        "resolve_company": "company_resolution",
        "search_filings": "filing_search",
        "extract_section": "section_extraction",
        "summarize": "summarizer",
        "complete": "end"
    }
)

# Each agent reports back to the planner after execution
workflow.add_edge("company_resolution", "planner")
workflow.add_edge("filing_search", "planner")
workflow.add_edge("section_extraction", "planner")
workflow.add_edge("summarizer", "planner")

# Compile the graph
sec_analysis_app = workflow.compile()
```

### Agent Implementation Types

For the POC, we'll implement three specific types of agent nodes:

1. **Tool Nodes**: Simple wrappers around SEC-API endpoints
   ```python
   def company_resolution_node(state):
       """Node that calls the company_resolution_agent with parameters from state"""
       try:
           # Extract parameters from state
           identifier_type = state.get("identifier_type", "name")
           identifier_value = state.get("company_name")
           
           # Call the agent
           result = company_resolution_agent(identifier_type, identifier_value)
           
           # Update state with results
           return {
               "company_info": result["data"],
               "current_status": f"Company resolution: {result['status']}",
               "errors": state["errors"] + [result["error"]] if result["error"] else state["errors"]
           }
       except Exception as e:
           return {
               "errors": state["errors"] + [{"source": "company_resolution", "error": str(e)}],
               "current_status": "Error in company resolution"
           }
   ```

2. **Planner Node**: Directs the workflow based on the current state and user query
   ```python
   def planner_agent(state):
       """Analyzes the current state and determines next steps"""
       # For the POC, use a simple OpenAI call to determine the next step
       messages = [
           {"role": "system", "content": "You are planning the steps to answer a user's question about SEC filings."},
           {"role": "user", "content": f"User query: {state['user_query']}\nCurrent state: {state}"}
       ]
       
       response = openai_client.chat.completions.create(
           model="gpt-4",
           messages=messages,
           functions=[
               {
                   "name": "plan_next_step",
                   "description": "Plan the next step in the SEC analysis workflow",
                   "parameters": {
                       "type": "object",
                       "properties": {
                           "next_step": {
                               "type": "string", 
                               "enum": ["resolve_company", "search_filings", "extract_section", "summarize", "complete"]
                           },
                           "reasoning": {"type": "string"}
                       },
                       "required": ["next_step", "reasoning"]
                   }
               }
           ],
           function_call={"name": "plan_next_step"}
       )
       
       # Extract function call arguments
       function_args = json.loads(response.choices[0].message.function_call.arguments)
       
       # Return updated state with next step
       return {
           "next_step": function_args["next_step"],
           "current_status": f"Planning: {function_args['reasoning']}"
       }
   ```

3. **Summarizer Node**: Formats the final response to the user (only uses LLM capabilities)
   ```python
   def summarizer_node(state):
       """Creates a final response based on extracted information"""
       # Only runs when we have content to summarize
       if not state.get("extracted_content"):
           return {
               "errors": state["errors"] + [{"source": "summarizer", "error": "No content to summarize"}],
               "current_status": "Error in summarization"
           }
       
       # Use OpenAI to generate a summary
       messages = [
           {"role": "system", "content": "You are summarizing SEC filing information based on a user query."},
           {"role": "user", "content": f"Query: {state['user_query']}\nExtracted content: {state['extracted_content']}"}
       ]
       
       response = openai_client.chat.completions.create(
           model="gpt-4",
           messages=messages
       )
       
       # Return final response
       return {
           "final_response": response.choices[0].message.content,
           "current_status": "Completed",
           "next_step": "complete"
       }
   ```

## Complete Tool Agent Catalog

Based on the SEC-API documentation, here are all available tool agents:

### EDGAR Filing Search & Download Agents

#### 1. Filing Search Agent (QueryApi)

**SEC-API Endpoint**: `QueryApi.get_filings()`  
**Description**: Searches for SEC filings based on parameters like CIK, form type, date range.  
**Input Format**:
```python
{
  "query": "cik:1326801 AND formType:\"10-K\"",  # Required
  "from": "0",                                   # Optional
  "size": "10",                                  # Optional
  "sort": [{"filedAt": {"order": "desc"}}]      # Optional
}
```
**Output Format**:
```python
{
  "status": 200,
  "data": {
    "filings": [
      {
        "cik": "1326801",
        "ticker": "META",
        "companyName": "Meta Platforms Inc",
        "formType": "10-K",
        "filedAt": "2023-02-01",
        "accessionNo": "0001326801-23-000013",
        "linkToFilingDetails": "https://www.sec.gov/...",
        # Other filing metadata
      },
      # More filings
    ],
    "total": 42
  },
  "error": None,
  "metadata": {"timestamp": "2023-06-01T12:34:56"}
}
```

#### 2. Full Text Search Agent (FullTextSearchApi)

**SEC-API Endpoint**: `FullTextSearchApi.get_filings()`  
**Description**: Searches the full text of SEC filings and their attachments.  
**Input Format**:
```python
{
  "query": "climate risk",                   # Required
  "formTypes": ["10-K", "10-Q"],            # Optional
  "startDate": "2023-01-01",                # Optional
  "endDate": "2023-12-31",                  # Optional
  "ciks": ["1326801"],                      # Optional
  "tickers": [],                            # Optional
  "sics": [],                               # Optional
  "from": 0,                                # Optional
  "size": 10,                               # Optional
  "sortBy": "relevance"                     # Optional
}
```
**Output Format**: Similar to Filing Search Agent

#### 3. Filing Download Agent (RenderApi)

**SEC-API Endpoint**: `RenderApi.get_file()`  
**Description**: Downloads any SEC filing, exhibit, or attached file in its original format.  
**Input Format**:
```python
{
  "url": "https://www.sec.gov/Archives/edgar/data/...",  # Required
  "return_binary": False                                 # Optional
}
```
**Output Format**:
```python
{
  "status": 200,
  "data": "<!DOCTYPE html>...",  # HTML content or binary data
  "error": None,
  "metadata": {"timestamp": "2023-06-01T12:34:56"}
}
```

#### 4. PDF Generator Agent (PdfGeneratorApi)

**SEC-API Endpoint**: `PdfGeneratorApi.get_pdf()`  
**Description**: Converts SEC filings or exhibits to PDF format.  
**Input Format**:
```python
{
  "url": "https://www.sec.gov/Archives/edgar/data/..."  # Required
}
```
**Output Format**:
```python
{
  "status": 200,
  "data": b"<binary PDF data>",  # Binary PDF data
  "error": None,
  "metadata": {"timestamp": "2023-06-01T12:34:56"}
}
```

#### 5. Real-Time Filing Stream Agent (StreamApi)

**SEC-API Endpoint**: WebSocket connection  
**Description**: Provides real-time stream of newly published SEC filings.  
**Input Format**: WebSocket connection parameters  
**Output Format**: Stream of filing data events

### Converter & Extractor Agents

#### 6. Section Extraction Agent (ExtractorApi)

**SEC-API Endpoint**: `ExtractorApi.get_section()`  
**Description**: Extracts specific sections from SEC filings.  
**Input Format**:
```python
{
  "filing_url": "https://www.sec.gov/...",  # Required
  "section_id": "1A",                       # Required (section ID like "1A", "7", "part2item1a")
  "output_format": "text"                   # Optional ("text" or "html")
}
```
**Output Format**:
```python
{
  "status": 200,
  "data": "Section content as text or HTML...",
  "error": None,
  "metadata": {
    "timestamp": "2023-06-01T12:34:56",
    "section_id": "1A",
    "section_name": "Risk Factors"
  }
}
```

#### 7. XBRL-to-JSON Agent (XbrlApi)

**SEC-API Endpoint**: `XbrlApi.xbrl_to_json()`  
**Description**: Converts XBRL financial data to structured JSON.  
**Input Format**:
```python
{
  "htm_url": "https://www.sec.gov/...",  # Either htm_url or xbrl_url is required
  "xbrl_url": None,
  "json_dir": None                       # Optional
}
```
**Output Format**:
```python
{
  "status": 200,
  "data": {
    "FinancialStatements": {
      "BalanceSheets": {...},
      "IncomeStatements": {...},
      "CashFlows": {...},
      # Other financial data
    }
  },
  "error": None,
  "metadata": {"timestamp": "2023-06-01T12:34:56"}
}
```

### Investment Adviser Agents

#### 8. Form ADV Firms Agent (FormAdvApi.get_firms)

**SEC-API Endpoint**: `FormAdvApi.get_firms()`  
**Description**: Retrieves information about investment adviser firms.  
**Input Format**:
```python
{
  "query": "Info.FirmCrdNb:361",                    # Required
  "from": "0",                                      # Optional
  "size": "10",                                     # Optional
  "sort": [{"Info.FirmCrdNb": {"order": "desc"}}]  # Optional
}
```
**Output Format**: Standardized response with firm data

#### 9. Form ADV Individuals Agent (FormAdvApi.get_individuals)

**SEC-API Endpoint**: `FormAdvApi.get_individuals()`  
**Description**: Retrieves information about individual investment advisers.  
**Input Format**: Similar to Form ADV Firms Agent  
**Output Format**: Standardized response with individual adviser data

#### 10. Form ADV Brochures Agent (FormAdvApi.get_brochures)

**SEC-API Endpoint**: `FormAdvApi.get_brochures()`  
**Description**: Retrieves Form ADV brochures.  
**Input Format**: Similar to Form ADV Firms Agent  
**Output Format**: Standardized response with brochure data

### Ownership Data Agents

#### 11. Insider Trading Agent (InsiderTradingApi)

**SEC-API Endpoint**: `InsiderTradingApi.get_data()`  
**Description**: Accesses insider buy/sell transactions from Forms 3/4/5.  
**Input Format**:
```python
{
  "query": "issuer.tradingSymbol:TSLA",       # Required
  "from": "0",                                # Optional
  "size": "10",                               # Optional
  "sort": [{"filedAt": {"order": "desc"}}]    # Optional
}
```
**Output Format**: Standardized response with insider trading data

#### 12. 13F Holdings Agent (Form13FHoldingsApi)

**SEC-API Endpoint**: `Form13FHoldingsApi.get_data()`  
**Description**: Accesses Form 13F holdings data from institutional investors.  
**Input Format**:
```python
{
  "query": "cik:1350694 AND periodOfReport:2024-03-31",  # Required
  "from": "0",                                           # Optional
  "size": "10",                                          # Optional
  "sort": [{"filedAt": {"order": "desc"}}]              # Optional
}
```
**Output Format**: Standardized response with 13F holdings data

#### 13. 13F Cover Pages Agent (Form13FCoverPagesApi)

**SEC-API Endpoint**: `Form13FCoverPagesApi.get_data()`  
**Description**: Accesses cover page data from Form 13F filings.  
**Input Format**: Similar to 13F Holdings Agent  
**Output Format**: Standardized response with 13F cover page data

#### 14. 13D/G Ownership Agent (Form13DGApi)

**SEC-API Endpoint**: `Form13DGApi.get_data()`  
**Description**: Accesses Form 13D/G filings for significant ownership stakes.  
**Input Format**:
```python
{
  "query": "owners.name:Point72 AND owners.amountAsPercent:[10 TO *]",  # Required
  "from": "0",                                                           # Optional
  "size": "50",                                                          # Optional
  "sort": [{"filedAt": {"order": "desc"}}]                              # Optional
}
```
**Output Format**: Standardized response with 13D/G ownership data

#### 15. N-PORT Holdings Agent (FormNportApi)

**SEC-API Endpoint**: `FormNportApi.get_data()`  
**Description**: Accesses Form N-PORT filings from investment companies.  
**Input Format**:
```python
{
  "query": "fundInfo.totAssets:[100000000 TO *]",  # Required
  "from": "0",                                     # Optional
  "size": "10",                                    # Optional
  "sort": [{"filedAt": {"order": "desc"}}]        # Optional
}
```
**Output Format**: Standardized response with N-PORT holdings data

### Proxy Voting Agents

#### 16. N-PX Proxy Voting Records Agent (FormNPXApi)

**SEC-API Endpoint**: `FormNPXApi.get_voting_records()`  
**Description**: Accesses proxy voting records from investment companies.  
**Input Format**:
```python
{
  "query": "cik:884546",                        # Required
  "from": "0",                                  # Optional
  "size": "1",                                  # Optional
  "sort": [{"filedAt": {"order": "desc"}}]      # Optional
}
```
**Output Format**: Standardized response with N-PX voting records

### Security Offerings Agents

#### 17. S-1/424B4 Agent (Form_S1_424B4_Api)

**SEC-API Endpoint**: `Form_S1_424B4_Api.get_data()`  
**Description**: Accesses S-1 registration statements and 424B4 prospectuses.  
**Input Format**:
```python
{
  "query": "ticker:V",                          # Required
  "from": "0",                                  # Optional
  "size": "50",                                 # Optional
  "sort": [{"filedAt": {"order": "desc"}}]      # Optional
}
```
**Output Format**: Standardized response with S-1/424B4 data

#### 18. Crowdfunding Agent (FormCApi)

**SEC-API Endpoint**: `FormCApi.get_data()`  
**Description**: Accesses Form C filings for crowdfunding campaigns.  
**Input Format**:
```python
{
  "query": "id:*",                              # Required
  "from": "0",                                  # Optional
  "size": "10",                                 # Optional
  "sort": [{"filedAt": {"order": "desc"}}]      # Optional
}
```
**Output Format**: Standardized response with Form C data

#### 19. Private Offerings Agent (FormDApi)

**SEC-API Endpoint**: `FormDApi.get_data()`  
**Description**: Accesses Form D filings for private securities offerings.  
**Input Format**:
```python
{
  "query": "offeringData.offeringSalesAmounts.totalOfferingAmount:[1000000 TO *]",  # Required
  "from": "0",                                                                     # Optional
  "size": "10",                                                                    # Optional
  "sort": [{"filedAt": {"order": "desc"}}]                                        # Optional
}
```
**Output Format**: Standardized response with Form D data

### Form 8-K Event Agents

#### 20. 8-K Auditor Changes Agent (Form_8K_Item_X_Api - 4.01)

**SEC-API Endpoint**: `Form_8K_Item_X_Api.get_data()`  
**Description**: Accesses auditor and accountant change disclosures.  
**Input Format**:
```python
{
  "query": "item4_01:* AND filedAt:[2024-01-01 TO 2024-12-31]",  # Required
  "from": "0",                                                   # Optional
  "size": "50",                                                  # Optional
  "sort": [{"filedAt": {"order": "desc"}}]                      # Optional
}
```
**Output Format**: Standardized response with 8-K Item 4.01 data

#### 21. 8-K Financial Restatements Agent (Form_8K_Item_X_Api - 4.02)

**SEC-API Endpoint**: `Form_8K_Item_X_Api.get_data()`  
**Description**: Accesses financial restatement disclosures.  
**Input Format**: Similar to 8-K Auditor Changes Agent but with "item4_02:*"  
**Output Format**: Standardized response with 8-K Item 4.02 data

#### 22. 8-K Leadership Changes Agent (Form_8K_Item_X_Api - 5.02)

**SEC-API Endpoint**: `Form_8K_Item_X_Api.get_data()`  
**Description**: Accesses disclosures about changes in directors, executives, and board members.  
**Input Format**: Similar to 8-K Auditor Changes Agent but with "item5_02:*"  
**Output Format**: Standardized response with 8-K Item 5.02 data

### Company Information Agents

#### 23. Directors & Board Members Agent (DirectorsBoardMembersApi)

**SEC-API Endpoint**: `DirectorsBoardMembersApi.get_data()`  
**Description**: Accesses information about company directors and board members.  
**Input Format**:
```python
{
  "query": "ticker:AMZN",                    # Required
  "from": 0,                                 # Optional
  "size": 50,                                # Optional
  "sort": [{"filedAt": {"order": "desc"}}]   # Optional
}
```
**Output Format**: Standardized response with directors and board members data

#### 24. Executive Compensation Agent (ExecCompApi)

**SEC-API Endpoint**: `ExecCompApi.get_data()`  
**Description**: Accesses standardized compensation data for key executives.  
**Input Format**:
```python
{
  "ticker_or_cik": "TSLA"  # Required (can be ticker or CIK)
}
```
**Output Format**: Standardized response with executive compensation data

#### 25. Outstanding Shares & Float Agent (FloatApi)

**SEC-API Endpoint**: `FloatApi.get_float()`  
**Description**: Accesses information on outstanding shares and public float.  
**Input Format**:
```python
{
  "ticker": "GOOGL"  # Required
}
```
**Output Format**: Standardized response with float data

#### 26. Subsidiary Agent (SubsidiaryApi)

**SEC-API Endpoint**: `SubsidiaryApi.get_data()`  
**Description**: Accesses information about company subsidiaries.  
**Input Format**:
```python
{
  "query": "ticker:TSLA",                    # Required
  "from": "0",                               # Optional
  "size": "50",                              # Optional
  "sort": [{"filedAt": {"order": "desc"}}]   # Optional
}
```
**Output Format**: Standardized response with subsidiary data

### Enforcement & Regulatory Agents

#### 27. SEC Enforcement Actions Agent (SecEnforcementActionsApi)

**SEC-API Endpoint**: `SecEnforcementActionsApi.get_data()`  
**Description**: Accesses SEC enforcement actions data.  
**Input Format**:
```python
{
  "query": "releasedAt:[2024-01-01 TO 2024-12-31]",  # Required
  "from": "0",                                       # Optional
  "size": "50",                                      # Optional
  "sort": [{"releasedAt": {"order": "desc"}}]       # Optional
}
```
**Output Format**: Standardized response with enforcement actions data

#### 28. SEC Litigation Releases Agent (SecLitigationsApi)

**SEC-API Endpoint**: `SecLitigationsApi.get_data()`  
**Description**: Accesses SEC litigation releases.  
**Input Format**: Similar to SEC Enforcement Actions Agent  
**Output Format**: Standardized response with litigation releases data

#### 29. SEC Administrative Proceedings Agent (SecAdministrativeProceedingsApi)

**SEC-API Endpoint**: `SecAdministrativeProceedingsApi.get_data()`  
**Description**: Accesses SEC administrative proceedings.  
**Input Format**: Similar to SEC Enforcement Actions Agent  
**Output Format**: Standardized response with administrative proceedings data

#### 30. AAER Agent (AaerApi)

**SEC-API Endpoint**: `AaerApi.get_data()`  
**Description**: Accesses Accounting and Auditing Enforcement Releases.  
**Input Format**:
```python
{
  "query": "dateTime:[2012-01-01 TO 2020-12-31]",  # Required
  "from": "0",                                     # Optional
  "size": "50",                                    # Optional
  "sort": [{"dateTime": {"order": "desc"}}]       # Optional
}
```
**Output Format**: Standardized response with AAER data

#### 31. SRO Filings Agent (SroFilingsApi)

**SEC-API Endpoint**: `SroFilingsApi.get_data()`  
**Description**: Accesses filings from Self-Regulatory Organizations.  
**Input Format**:
```python
{
  "query": "sro:NASDAQ",                       # Required
  "from": "0",                                 # Optional
  "size": "10",                                # Optional
  "sort": [{"issueDate": {"order": "desc"}}]   # Optional
}
```
**Output Format**: Standardized response with SRO filings data

### Utility Agents

#### 32. Company Resolution Agent (MappingApi)

**SEC-API Endpoint**: `MappingApi.resolve()`  
**Description**: Resolves company identifiers (name, CIK, ticker).  
**Input Format**:
```python
{
  "identifier_type": "name",      # Required ("name", "cik", or "ticker")
  "identifier_value": "Facebook"  # Required
}
```
**Output Format**:
```python
{
  "status": 200,
  "data": [
    {
      "name": "Meta Platforms Inc",
      "cik": "1326801",
      "ticker": "META",
      "sic": "7370",
      "sic_industry": "Services-Computer Programming, Data Processing, Etc."
    }
  ],
  "error": None,
  "metadata": {"timestamp": "2023-06-01T12:34:56"}
}
```

#### 33. EDGAR Entities Agent (EdgarEntitiesApi)

**SEC-API Endpoint**: `EdgarEntitiesApi.get_data()`  
**Description**: Accesses information on EDGAR filing entities.  
**Input Format**:
```python
{
  "query": "cik:1318605",                           # Required
  "from": "0",                                      # Optional
  "size": "50",                                     # Optional
  "sort": [{"cikUpdatedAt": {"order": "desc"}}]     # Optional
}
```
**Output Format**: Standardized response with EDGAR entities data

## Implementation Plan

### Phase 1: Foundation (Core Tool Agents)

**Milestone 1: Basic Tool Agents**
- Create wrapper functions for the core agents:
  - Company Resolution Agent (MappingApi)
  - Filing Search Agent (QueryApi)
  - Section Extraction Agent (ExtractorApi)
- Ensure clean input/output interfaces
- Test each function independently with sample inputs
- Success Criteria: Each agent correctly interfaces with its SEC-API endpoint

**Milestone 2: Tool Agent Integration**
- Create a simple orchestration function that can call tools in sequence
- Test with hardcoded parameters
- Success Criteria: Multi-step workflow from company name to section extraction works

### Phase 2: Smart Planner Development

**Milestone 3: Basic Planner Agent**
- Create initial planner agent that can interpret simple queries
- Implement logic to extract company names, form types, and section needs
- Success Criteria: Planner correctly identifies needed steps for simple queries

**Milestone 4: Query Analysis Enhancement**
- Improve planner's ability to understand more complex queries
- Add support for date ranges, multiple sections, and financial data requests
- Success Criteria: Planner correctly interprets a wide range of query types

### Phase 3: LangGraph Integration

**Milestone 5: Basic Graph Structure**
- Set up LangGraph state management
- Define nodes for each agent
- Create simple linear graph for basic queries
- Success Criteria: End-to-end workflow using LangGraph for simple queries

**Milestone 6: Advanced Graph Structure**
- Implement conditional branching in the graph
- Add error handling paths
- Success Criteria: System gracefully handles errors and adapts workflow

### Phase 4: Refinement and Expansion

**Milestone 7: Additional Tool Agents**
- Add remaining SEC-API endpoints as needed
- Test each independently
- Success Criteria: Full coverage of required SEC-API functionality

**Milestone 8: Planner Enhancements**
- Implement more sophisticated planning strategies
- Add memory for context across multiple queries
- Success Criteria: Planner handles complex, multi-step queries

## Sample User Journeys

### Basic Journey: Extract Risk Factors

```
User: "What are Apple's risk factors in their latest 10-K?"

Planner → Company Agent: company_agent(identifier_type="name", identifier_value="Apple")
Company Agent → Planner: {status: 200, data: [{cik: "320193", ticker: "AAPL", ...}], ...}

Planner → Filing Agent: filing_agent(query="cik:320193 AND formType:\"10-K\"", size="1", ...)
Filing Agent → Planner: {status: 200, data: {filings: [{url: "https://www.sec.gov/...", ...}]}, ...}

Planner → Extractor Agent: extractor_agent(filing_url="https://www.sec.gov/...", section_id="1A", ...)
Extractor Agent → Planner: {status: 200, data: "<section text content>", ...}

Planner → User: "<formatted answer about Apple's risk factors>"
```

### Complex Journey: Financial Analysis

```
User: "Compare Facebook and Google's revenue growth over the last 3 years"

Planner → Company Agent: company_agent(identifier_type="name", identifier_value="Facebook")
Company Agent → Planner: {status: 200, data: [{cik: "1326801", ticker: "META", ...}], ...}

Planner → Company Agent: company_agent(identifier_type="name", identifier_value="Google")
Company Agent → Planner: {status: 200, data: [{cik: "1652044", ticker: "GOOGL", ...}], ...}

Planner → Filing Agent: filing_agent(query="cik:1326801 AND formType:\"10-K\"", size="3", ...)
Filing Agent → Planner: {status: 200, data: {filings: [...]}, ...}

Planner → Filing Agent: filing_agent(query="cik:1652044 AND formType:\"10-K\"", size="3", ...)
Filing Agent → Planner: {status: 200, data: {filings: [...]}, ...}

Planner → XBRL Agent: xbrl_agent(htm_url="https://www.sec.gov/...")
XBRL Agent → Planner: {status: 200, data: {...}, ...}

... (repeat for each filing)

Planner → User: "<formatted comparison of revenue growth>"
```

### Additional Example Queries

The system is designed to handle a wide range of queries about SEC filings, such as:

1. **Section Analysis**: "Summarize the Management Discussion and Analysis section of Microsoft's 2023 10-K"
2. **Financial Data Extraction**: "How many shares outstanding did Immix Biopharma have as of 12/31/23?"
3. **Trend Analysis**: "What did Immix Biopharma report as revenue for the quarter ended September 30, 2024?"
4. **Cross-Filing Comparison**: "Identify and list risk factors that are similar across Apple's four most recent quarterly (10-Q) filings"
5. **Change Detection**: "Identify new significant accounting policies introduced in Amazon's latest quarterly report compared to the previous four quarterly reports"
6. **Topic-Specific Analysis**: "Detect and analyze new footnote disclosures related to cybersecurity in Tesla's most recent quarterly report (10-Q)"
7. **Time Series Analysis**: "How many stock options, on average, have been granted each quarter over the past eight quarters for Coca-Cola?"
8. **Policy Extraction**: "What did Microsoft list as the recent accounting guidance on their last 10-K?"
9. **Industry Comparison**: "What did the largest companies in the farming industry report as their revenue recognition policy in their 2024 10-K?"

## Technical Considerations

### Agent Implementation Template

All agents should be implemented using this exact template:

```python
def agent_name(param1: Type, param2: Type, ..., api_key: Optional[str] = None, proxies: Optional[Dict] = None) -> Dict[str, Any]:
    """Short description of what this agent does.
    
    Args:
        param1: Description of parameter 1
        param2: Description of parameter 2
        ...
        api_key: Optional API key (overrides environment variable)
        proxies: Optional proxy configuration
        
    Returns:
        Dictionary with standardized fields:
        - status: int (200 for success, error code otherwise)
        - data: Any (the primary payload, when successful)
        - error: str (error message, when unsuccessful)
        - metadata: Dict (additional information about the response)
    """
    try:
        # Initialize the API client
        api_client = SecApiClient(api_key, proxies)
        
        # Validate parameters if needed
        if param1 is None:
            return {
                "status": 400,
                "data": None,
                "error": "param1 is required",
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "api_endpoint": "endpoint_name"
                }
            }
        
        # Call the SEC-API endpoint
        result = api_client.endpoint_method(param1, param2, ...)
        
        # Return standardized success response
        return {
            "status": 200,
            "data": result,
            "error": None,
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "api_endpoint": "endpoint_name",
                # Add any other useful metadata
            }
        }
    except Exception as e:
        # Return standardized error response
        return {
            "status": 500,  # Or more specific code if available
            "data": None,
            "error": str(e),
            "metadata": {
                "timestamp": datetime.now().isoformat(),
                "api_endpoint": "endpoint_name",
                "exception_type": type(e).__name__
            }
        }
```

### Planner Agent Implementation

The planner should use an LLM with a prompt template that includes:

1. **System Context**: Detailed information about available tools and their parameters
2. **Task Description**: Instructions for planning and orchestration
3. **Examples**: Sample queries and how to break them down
4. **Output Format**: Clear structure for tool selection and parameter formatting

## Simple Testing Strategy

For the POC, we'll use a simplified testing approach:

1. **Manual Function Testing**: Test each agent function independently with real API calls
2. **Logging**: Implement detailed logging for debugging
3. **Status Codes**: Use HTTP-style status codes to track success/failure

This will provide sufficient validation while avoiding over-engineering.

## Conclusion

This architecture provides a clean, maintainable approach to SEC filing analysis with a clear separation of concerns. By keeping tool agents simple and focusing complexity in the planner, we ensure maintainability while maximizing flexibility for handling diverse user queries.

The key to success is ensuring the planner agent is well-designed and capable of understanding user intent, while keeping tool agents as direct wrappers around SEC-API endpoints without unnecessary complexity. 