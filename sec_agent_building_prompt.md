"""
# SEC-API Agent Implementation Prompt

Use this prompt to implement standardized tool agents for SEC-API endpoints. Each agent should follow the exact structure defined below to ensure consistency, proper error handling, and seamless integration.

## Standardized Agent Development Workflow

For each SEC-API endpoint, follow this consistent development process:

1. **Document API Capabilities (Planning Phase)**
   - Create `{api_name}_agent_plan.md` with:
     - Complete list of ALL methods and functionalities the API offers
     - Parameter descriptions, types, and whether they're required or optional
     - Response format and field descriptions
     - ALL relevant documentation text from SEC-API-Python
     - Example usage patterns and code snippets
     - Error scenarios and expected handling
   - This document serves as the comprehensive reference and contract for implementation
   - The plan MUST be complete before moving to test creation

2. **Create Test File Based on Plan**
   - Create `test_{api_name}_agent.py` that verifies:
     - EVERY method and functionality documented in the plan
     - ALL parameter combinations specified in the plan
     - EVERY error scenario outlined in the plan
     - Response format consistency as defined in the plan
   - Tests should be written against the plan's specifications
   - NO implementation details should be assumed beyond what's in the plan
   - Tests serve as executable documentation of the plan's requirements

3. **Implement Agent Following Plan and Tests**
   - Create `{api_name}_agent.py` implementing:
     - ALL functionality documented in the plan
     - Passing ALL tests created from the plan
     - Following the exact structure shown in this document
     - Maintaining consistent error handling
   - Implementation should satisfy both plan and tests
   - NO functionality should be added that isn't in the plan

4. **Verification and Documentation**
   - Run tests to verify implementation matches plan requirements
   - Update plan document with any discovered limitations
   - Document implementation decisions in the plan
   - Ensure all three files remain in sync

This workflow ensures that:
- The plan serves as the single source of truth
- Tests verify the plan's requirements
- Implementation satisfies both plan and tests
- All components remain aligned

## Agent Structure Requirements

Create a Python function with this exact signature pattern:

```python
def {api_name}_agent(
    # Required parameters based on API documentation
    {required_param1}: {type},
    {required_param2}: {type},
    # Optional parameters
    {optional_param1}: {type} = None,
    {optional_param2}: {type} = None,
    # Standard parameters for all agents
    api_key: Optional[str] = None,
    proxies: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Agent for the {SEC-API Name} endpoint.
    
    This agent {one-sentence description of what the agent does}.
    
    Args:
        {required_param1}: {description of parameter}
        {required_param2}: {description of parameter}
        {optional_param1}: {description of parameter}
        {optional_param2}: {description of parameter}
        api_key: Optional API key that overrides the environment variable
        proxies: Optional proxy configuration for corporate networks
        
    Returns:
        Dictionary with the following standardized fields:
        - status: int (HTTP status code - 200 for success, error code otherwise)
        - data: Any (the primary payload when successful, None when unsuccessful)
        - error: Optional[str] (error message when unsuccessful, None when successful)
        - metadata: Dict (contextual information about the response)
    
    Raises:
        No exceptions - all errors are captured and returned in the response
    """
    # Initialize metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "api_endpoint": "{exact_api_endpoint_name}",
        "params": {
            "{required_param1}": str({required_param1}),
            # Include other parameter names without values for privacy
            "{optional_param1}": "provided" if {optional_param1} is not None else "not provided"
        }
    }
    
    # Validate required parameters
    if {required_param1} is None:
        return {
            "status": 400,
            "data": None,
            "error": "{required_param1} is required",
            "metadata": metadata
        }
    
    # Additional validation if needed
    
    try:
        # Initialize the SEC-API client
        from sec_api import {OriginalApiClass}
        client = {OriginalApiClass}(api_key=api_key, proxies=proxies)
        
        # Call the SEC-API endpoint with appropriate parameters
        result = client.{method_name}({params})
        
        # Return standardized success response
        return {
            "status": 200,
            "data": result,
            "error": None,
            "metadata": metadata
        }
    except Exception as e:
        # Determine appropriate error code
        error_code = 500
        if "rate limit" in str(e).lower():
            error_code = 429
        elif "not found" in str(e).lower():
            error_code = 404
        elif "invalid" in str(e).lower() or "bad request" in str(e).lower():
            error_code = 400
            
        # Return standardized error response
        return {
            "status": error_code,
            "data": None,
            "error": str(e),
            "metadata": {
                **metadata,
                "exception_type": type(e).__name__
            }
        }
```

## Critical Implementation Rules

1. **NO FALLBACKS** - Never add default values or fallbacks for required parameters. If a parameter is required and not provided, return a 400 error immediately.

2. **NO PARAMETER INTERPRETATION** - Never attempt to interpret, modify, or augment the input parameters. Pass them exactly as provided to the SEC-API.

3. **NO DECISION LOGIC** - Never add business logic, filtering, or decision-making to the agent. It should be a pure wrapper around the SEC-API endpoint.

4. **CONSISTENT ERROR HANDLING** - Always catch all exceptions and return them in the standardized format with appropriate status codes.

5. **COMPREHENSIVE PARAMETER VALIDATION** - Validate all required parameters at the beginning of the function.

6. **EXACT SEC-API MAPPING** - Map directly to the SEC-API methods without adding layers of abstraction.

7. **TRANSPARENCY** - Always include metadata with timestamp, endpoint name, and parameter presence information.

8. **SIMPLICITY OVER COMPLEXITY** - Prefer implementations with fewer conditionals and special cases. Use the exact methods shown in documentation.

9. **LITERAL INTERPRETATION** - Follow the API documentation examples exactly, even if you think there might be a "better" way to do it.

## How to Determine Parameters from SEC-API Documentation

1. **Required Parameters**: 
   - Any parameter marked as "Required" in the documentation
   - The primary identifier parameters (query string, CIK, ticker, etc.)
   - Parameters with no default values in example code

2. **Optional Parameters**:
   - Parameters with default values in example code
   - Pagination parameters (from, size)
   - Sorting parameters
   - Format parameters (output type)

3. **Standardized Return Structure**:
   - Always wrap the SEC-API response in the standard response format
   - Don't modify or filter the original API response data
   - Include all metadata even for error responses

## Example Implementation for Company Resolution Agent

```python
def company_resolution_agent(
    identifier_type: str,
    identifier_value: str,
    api_key: Optional[str] = None,
    proxies: Optional[Dict[str, str]] = None
) -> Dict[str, Any]:
    """Agent for the Mapping API endpoint.
    
    This agent resolves company identifiers (name, CIK, ticker) to full company details.
    
    Args:
        identifier_type: Type of identifier ('name', 'cik', or 'ticker')
        identifier_value: Value of the identifier to resolve
        api_key: Optional API key that overrides the environment variable
        proxies: Optional proxy configuration for corporate networks
        
    Returns:
        Dictionary with the following standardized fields:
        - status: int (HTTP status code - 200 for success, error code otherwise)
        - data: Any (company information when successful, None when unsuccessful)
        - error: Optional[str] (error message when unsuccessful, None when successful)
        - metadata: Dict (contextual information about the response)
    """
    # Initialize metadata
    metadata = {
        "timestamp": datetime.now().isoformat(),
        "api_endpoint": "MappingApi.resolve",
        "params": {
            "identifier_type": identifier_type,
            "identifier_value": identifier_value
        }
    }
    
    # Validate required parameters
    if identifier_type is None:
        return {
            "status": 400,
            "data": None,
            "error": "identifier_type is required",
            "metadata": metadata
        }
        
    if identifier_value is None:
        return {
            "status": 400,
            "data": None,
            "error": "identifier_value is required",
            "metadata": metadata
        }
        
    # Validate identifier_type values
    if identifier_type not in ["name", "cik", "ticker"]:
        return {
            "status": 400,
            "data": None,
            "error": "identifier_type must be one of: name, cik, ticker",
            "metadata": metadata
        }
    
    try:
        # Initialize the SEC-API client
        from sec_api import MappingApi
        mapping_api = MappingApi(api_key=api_key, proxies=proxies)
        
        # Use resolve() method for all identifier types
        result = mapping_api.resolve(identifier_type, identifier_value)
        
        # Return standardized success response
        return {
            "status": 200,
            "data": result,
            "error": None,
            "metadata": metadata
        }
    except Exception as e:
        # Determine appropriate error code
        error_code = 500
        if "rate limit" in str(e).lower():
            error_code = 429
        elif "not found" in str(e).lower():
            error_code = 404
        elif "invalid" in str(e).lower() or "bad request" in str(e).lower():
            error_code = 400
            
        # Return standardized error response
        return {
            "status": error_code,
            "data": None,
            "error": str(e),
            "metadata": {
                **metadata,
                "exception_type": type(e).__name__
            }
        }
```

## Implementation Checklist for Each Agent

When implementing an agent for any SEC-API endpoint:

1. [ ] Define function name as lowercase with snake_case and "_agent" suffix
2. [ ] Include all required parameters from documentation
3. [ ] Add optional parameters with appropriate defaults
4. [ ] Include api_key and proxies parameters
5. [ ] Validate all required parameters before API call
6. [ ] Use typed parameters with appropriate Python types
7. [ ] Properly document the function with comprehensive docstring
8. [ ] Catch and handle all exceptions without letting them propagate
9. [ ] Return standardized response format with status, data, error, and metadata
10. [ ] Set appropriate status codes for different error scenarios
11. [ ] Include timestamp and API endpoint info in metadata
12. [ ] Verify the API method exists in the SEC-API documentation before using it
13. [ ] Test with real API calls before finalizing

## Linting and Testing Framework

### Linting Configuration

We recommend using the following linting tools and configuration:

```python
# .flake8
[flake8]
max-line-length = 100
extend-ignore = E203
exclude = .git,__pycache__,build,dist

# pyproject.toml
[tool.black]
line-length = 100
target-version = ['py38']
include = '\.pyi?$'
exclude = '''
/(
    \.git
  | \.hg
  | \.mypy_cache
  | \.tox
  | \.venv
  | _build
  | buck-out
  | build
  | dist
)/
'''

[tool.isort]
profile = "black"
line_length = 100
```

### Test-Driven Development Approach

Each agent should have corresponding tests that verify:

1. **Parameter Validation**: Tests that the agent correctly validates and rejects invalid parameters
2. **Error Handling**: Tests that the agent properly catches and formats different types of errors
3. **Success Cases**: Tests that the agent correctly passes parameters to the SEC-API and formats successful responses

### Example Test Structure (Using pytest)

```python
# test_agents.py

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime

# Import your agent
from agents.company_agent import company_resolution_agent

# Fixtures
@pytest.fixture
def mock_mapping_api():
    with patch('sec_api.MappingApi') as mock:
        instance = mock.return_value
        instance.resolve.return_value = {"name": "Test Company", "cik": "123456", "ticker": "TEST"}
        yield instance

# Tests
class TestCompanyResolutionAgent:
    def test_missing_identifier_type(self):
        result = company_resolution_agent(identifier_type=None, identifier_value="TEST")
        assert result["status"] == 400
        assert "identifier_type is required" in result["error"]
        assert result["data"] is None
        
    def test_missing_identifier_value(self):
        result = company_resolution_agent(identifier_type="ticker", identifier_value=None)
        assert result["status"] == 400
        assert "identifier_value is required" in result["error"]
        assert result["data"] is None
        
    def test_invalid_identifier_type(self):
        result = company_resolution_agent(identifier_type="invalid", identifier_value="TEST")
        assert result["status"] == 400
        assert "identifier_type must be one of" in result["error"]
        assert result["data"] is None
        
    def test_successful_lookup(self, mock_mapping_api):
        result = company_resolution_agent(identifier_type="ticker", identifier_value="TEST")
        assert result["status"] == 200
        assert result["data"] == {"name": "Test Company", "cik": "123456", "ticker": "TEST"}
        assert result["error"] is None
        mock_mapping_api.resolve.assert_called_once_with("ticker", "TEST")
        
    def test_api_error_handling(self, mock_mapping_api):
        mock_mapping_api.resolve.side_effect = Exception("API rate limit exceeded")
        result = company_resolution_agent(identifier_type="ticker", identifier_value="TEST")
        assert result["status"] == 429
        assert "API rate limit exceeded" in result["error"]
        assert result["data"] is None
        assert result["metadata"]["exception_type"] == "Exception"
```

### Simplified Testing Approach

For initial testing, you can use a simple script:

```python
# test_company_resolution_agent.py
from company_resolution_agent import company_resolution_agent

def test_company_resolution_agent():
    # Test with valid parameters
    print("\nTesting with company name...")
    result = company_resolution_agent("name", "Microsoft")
    print(f"Status: {result['status']}")
    if result['status'] == 200:
        print(f"Data: {result['data']}")
    else:
        print(f"Error: {result['error']}")
    
    # Test with invalid parameters
    print("\nTesting with invalid identifier type...")
    result = company_resolution_agent("invalid", "test")
    print(f"Status: {result['status']}")
    print(f"Error: {result['error']}")

if __name__ == "__main__":
    test_company_resolution_agent()
```

### Running Tests

Run tests with code coverage to ensure all agents are thoroughly tested:

```bash
pytest --cov=agents tests/ --cov-report=term-missing
```

### CI Integration

Add these checks to your CI pipeline to ensure quality:

```yaml
# .github/workflows/python-tests.yml
name: Python Tests

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Set up Python
      uses: actions/setup-python@v2
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install pytest pytest-cov flake8 black isort
        if [ -f requirements.txt ]; then pip install -r requirements.txt; fi
    - name: Lint with flake8
      run: |
        flake8 . --count --select=E9,F63,F7,F82 --show-source --statistics
        flake8 . --count --exit-zero --max-complexity=10 --statistics
    - name: Check formatting with black
      run: |
        black --check .
    - name: Check imports with isort
      run: |
        isort --check --profile black .
    - name: Test with pytest
      run: |
        pytest --cov=agents tests/ --cov-report=xml
```

## Is TDD and Linting Overkill?

For a system with 30+ agents that need consistent implementation and error handling, Test-Driven Development and linting are essential, not overkill. Here's why:

1. **Consistency**: With so many similar agents, TDD ensures they all behave consistently and follow the same patterns

2. **Error Detection**: Tests catch problems early before they impact the planner agent or user experience

3. **Documentation**: Tests serve as executable documentation of how each agent should behave

4. **Refactoring Confidence**: As the system evolves, tests provide confidence that changes won't break existing functionality

5. **Quality Assurance**: Linting ensures code style consistency across all agents

The investment in setting up TDD and linting will save significant time in debugging and maintenance as the system grows. 

# SEC Agent Building Guidelines

## Agent Structure
Each SEC API agent should consist of three files in the `agents` directory:

1. **Plan File** (`*_agent_plan.md`):
   - API overview and capabilities
   - Available methods and parameters
   - Response format documentation
   - Implementation requirements
   - Error handling guidelines

2. **Agent File** (`*_agent.py`):
   - Clean, focused implementation
   - Full API functionality exposed
   - Consistent error handling
   - Standard response format
   - Input validation

3. **Test File** (`test_*_agent.py`):
   - Comprehensive test cases
   - Error condition testing
   - Response validation
   - Example usage

## Implementation Guidelines

1. **Start with the Plan**:
   - Document API capabilities
   - Define required methods
   - Specify response formats
   - List error conditions
   - Note implementation requirements

2. **Create the Agent**:
   - Follow the plan exactly
   - Implement all documented methods
   - Use consistent error handling
   - Return standardized responses
   - Add helpful docstrings

3. **Write Tests**:
   - Test all documented methods
   - Cover error conditions
   - Validate responses
   - Include usage examples
   - Test edge cases

## Standard Response Format
All agents should return responses in this format:

```python
{
    "status": int,  # HTTP status code
    "error": str,   # Error message if status != 200
    "data": Any,    # Response data if status == 200
    "metadata": {   # Request/response metadata
        "timestamp": str,
        "endpoint": str,
        "params": dict
    }
}
```

## Error Handling
All agents should handle:

1. Invalid inputs
2. Missing required parameters
3. Network errors
4. API rate limits
5. Authentication failures

## Documentation
All agents should include:

1. Clear docstrings
2. Parameter descriptions
3. Return value documentation
4. Error condition descriptions
5. Usage examples

## Testing
All tests should verify:

1. Successful API calls
2. Error conditions
3. Response format
4. Data validation
5. Edge cases

Remember: Each agent should be a "dumb" tool that exposes the full functionality of its SEC-API endpoint while maintaining consistent error handling and response structure. 