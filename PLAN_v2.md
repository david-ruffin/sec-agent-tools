# SEC-API LangGraph Implementation Plan

## Project Overview

This project implements a Plan-and-Execute pattern using LangGraph to create an intelligent agent for SEC filing analysis. The agent first plans its approach, then executes each step, with the ability to revise plans based on results.

## Core Components

1. **Tools**: SEC-API endpoints wrapped as Python functions
   - Query API: Search filings
   - Full Text Search: Semantic search
   - Extractor API: Get filing sections
   - EDGAR Entities: Company information
   - XBRL-to-JSON: Financial data

2. **Planning Agent**: Creates multi-step plans for queries
   - Identifies required information
   - Determines optimal tool sequence
   - Handles dependencies between steps
   - Plans fallback strategies

3. **Execution Agent**: Carries out individual steps
   - Executes tool calls
   - Processes results
   - Handles errors gracefully
   - Summarizes information

4. **State Management**: Tracks progress and context
   - Current plan status
   - Execution history
   - Intermediate results
   - Error states

## Implementation Steps

### 1. Tool Setup
```python
from langgraph.prebuilt import create_agent_executor
from langchain_openai import ChatOpenAI

# Define tools with clear input/output schemas
tools = [
    Tool(
        name="SECQueryAPI",
        description="Search SEC filings by ticker, form type, date range",
        function=query_tool.search_filings,
    ),
    # ... other tools
]
```

### 2. Planning Agent
```python
from langgraph.graph import StateGraph, END

def create_planning_agent():
    return create_agent_executor(
        llm=ChatOpenAI(model="gpt-4-turbo-preview"),
        tools=[],  # No tools needed for planning
        system_message="""Plan steps to answer questions about SEC filings.
        For each step, specify:
        1. What information is needed
        2. Which tool to use
        3. Expected output
        4. Potential fallbacks
        """
    )

def planning_step(state):
    # Generate plan based on query
    planning_agent = create_planning_agent()
    plan = planning_agent.invoke({
        "input": state["query"],
        "context": state.get("context", {})
    })
    return {"plan": plan["steps"]}
```

### 3. Execution Agent
```python
def create_execution_agent():
    return create_agent_executor(
        llm=ChatOpenAI(model="gpt-3.5-turbo"),
        tools=tools,
        system_message="""Execute individual steps of the SEC analysis plan.
        For each step:
        1. Use the specified tool
        2. Verify the results
        3. Format the output
        4. Handle any errors
        """
    )

def execution_step(state):
    execution_agent = create_execution_agent()
    current_step = state["plan"][state["current_step_index"]]
    
    result = execution_agent.invoke({
        "input": current_step,
        "context": state.get("context", {})
    })
    
    return {
        "step_result": result,
        "current_step_index": state["current_step_index"] + 1
    }
```

### 4. Graph Construction
```python
def create_sec_graph():
    workflow = StateGraph()
    
    # Add nodes
    workflow.add_node("plan", planning_step)
    workflow.add_node("execute", execution_step)
    workflow.add_node("replan", replan_step)
    
    # Add edges
    workflow.add_edge("plan", "execute")
    workflow.add_edge("execute", "replan")
    workflow.add_conditional_edges(
        "replan",
        should_continue,
        {
            True: "execute",
            False: END
        }
    )
    
    return workflow.compile()
```

## Test Cases

### Basic Queries
1. "What are the risk factors mentioned in Tesla's most recent 10-K?"
   ```python
   expected_plan = [
       "Find Tesla's most recent 10-K using Query API",
       "Extract risk factors section using Extractor API",
       "Summarize key points from extracted text"
   ]
   ```

2. "Find the most recent 10-K filing for Apple Inc."
   ```python
   expected_plan = [
       "Search for Apple's filings using Query API",
       "Filter for most recent 10-K",
       "Return filing details and URL"
   ]
   ```

### Financial Data Queries
3. "What was Amazon's revenue in 2022?"
   ```python
   expected_plan = [
       "Find Amazon's 2022 10-K using Query API",
       "Extract financial data using XBRL-to-JSON API",
       "If XBRL fails, extract Income Statement using Extractor API",
       "Locate and return revenue figure"
   ]
   ```

4. "What is the total assets value on Tesla's balance sheet for 2021?"
   ```python
   expected_plan = [
       "Find Tesla's 2021 10-K using Query API",
       "Get balance sheet data using XBRL-to-JSON API",
       "If XBRL fails, extract balance sheet using Extractor API",
       "Locate and return total assets value"
   ]
   ```

### Complex Analysis
5. "Extract the Management Discussion and Analysis section from Microsoft's latest quarterly report"
   ```python
   expected_plan = [
       "Find Microsoft's latest 10-Q using Query API",
       "Extract MD&A section using Extractor API",
       "Format and summarize the content"
   ]
   ```

6. "Who are the executive officers of Google?"
   ```python
   expected_plan = [
       "Get Google's company info using EDGAR Entities API",
       "Find latest 10-K using Query API",
       "Extract executive officers section using Extractor API",
       "Format officer information"
   ]
   ```

### Advanced Analysis
7. "Compare risk factors between Tesla and Ford's latest 10-K filings"
   ```python
   expected_plan = [
       "Find latest 10-Ks for both companies using Query API",
       "Extract risk factors sections using Extractor API",
       "Analyze and compare the content",
       "Highlight key similarities and differences"
   ]
   ```

8. "Track mentions of 'artificial intelligence' in Apple's quarterly reports throughout 2023"
   ```python
   expected_plan = [
       "Find all Apple 10-Qs from 2023 using Query API",
       "Search each filing for 'artificial intelligence' using Full Text Search",
       "Extract relevant sections using Extractor API",
       "Analyze mention frequency and context"
   ]
   ```

## Success Criteria

1. **Accuracy**: All test queries return correct information
2. **Robustness**: Handles missing data and API errors gracefully
3. **Efficiency**: Minimizes API calls through smart planning
4. **Clarity**: Provides clear, well-formatted responses
5. **Adaptability**: Can modify plans based on intermediate results

## Next Steps

1. Implement core LangGraph components
2. Create comprehensive test suite
3. Add monitoring and logging
4. Document API patterns and examples
5. Create user guide with best practices 