import os
import re
import time
from typing import Dict, Any, Optional
from pathlib import Path
from sec_api import RenderApi

class RateLimiter:
    def __init__(self, max_requests_per_second: int = 10):
        self.last_request_time = 0
        self.min_interval = 1.0 / max_requests_per_second

    def wait(self):
        current_time = time.time()
        time_since_last_request = current_time - self.last_request_time
        if time_since_last_request < self.min_interval:
            time.sleep(self.min_interval - time_since_last_request)
        self.last_request_time = time.time()

def validate_input(accession_number: str, file_type: str, exhibit_number: Optional[str] = None) -> Dict[str, Any]:
    """Validate the input parameters."""
    # Validate accession number format (XXXXXXXXXX-YY-ZZZZZZ)
    if not re.match(r'^\d{10}-\d{2}-\d{6}$', accession_number):
        return {
            "status": 400,
            "error": "Invalid accession number format. Expected format: XXXXXXXXXX-YY-ZZZZZZ"
        }
    
    # Validate file type
    valid_file_types = ["complete", "primary", "exhibit"]
    if file_type not in valid_file_types:
        return {
            "status": 400,
            "error": f"Invalid file type. Must be one of: {', '.join(valid_file_types)}"
        }
    
    # Validate exhibit number if file type is exhibit
    if file_type == "exhibit":
        if not exhibit_number:
            return {
                "status": 400,
                "error": "Exhibit number required when file type is 'exhibit'"
            }
        if not re.match(r'^EX-\d+(\.\d+)?$', exhibit_number):
            return {
                "status": 400,
                "error": "Invalid exhibit number format. Expected format: EX-XX.X"
            }
    
    return {"status": 200}

def setup_download_directory(accession_number: str, file_type: str, exhibit_number: Optional[str] = None) -> str:
    """Set up the download directory structure and return the file path."""
    base_dir = Path("downloads")
    sub_dir = base_dir / file_type / accession_number
    
    # Create directory if it doesn't exist
    sub_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine file name
    if file_type == "complete":
        file_name = "filing.html"
    elif file_type == "primary":
        file_name = "primary.html"
    else:  # exhibit
        file_name = f"{exhibit_number}.html"
    
    return str(sub_dir / file_name)

def download_agent(
    accession_number: str,
    file_type: str = "complete",
    exhibit_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Download SEC filings and their components.
    
    Args:
        accession_number (str): The accession number of the filing
        file_type (str): Type of file to download (complete, primary, or exhibit)
        exhibit_number (str, optional): The specific exhibit number to download
        
    Returns:
        dict: Response containing status code and either file path or error message
    """
    # Validate input
    validation_result = validate_input(accession_number, file_type, exhibit_number)
    if validation_result["status"] != 200:
        return validation_result
    
    try:
        # Initialize API client with rate limiting
        api_key = os.getenv("SEC_API_KEY")
        if not api_key:
            return {
                "status": 401,
                "error": "API key not found in environment variables"
            }
        
        render_api = RenderApi(api_key)
        rate_limiter = RateLimiter()
        
        # Set up download directory and get file path
        file_path = setup_download_directory(accession_number, file_type, exhibit_number)
        
        # Apply rate limiting
        rate_limiter.wait()
        
        # Make API request with retry logic
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                # Download the file using the appropriate RenderApi method
                if file_type == "exhibit":
                    content = render_api.get_filing(accession_number, exhibit_number)
                else:
                    content = render_api.get_filing(accession_number)
                
                # Save the file
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                # Verify file was created and has content
                if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                    return {
                        "status": 500,
                        "error": "Failed to save file or file is empty"
                    }
                
                return {
                    "status": 200,
                    "file_path": file_path,
                    "file_size": os.path.getsize(file_path)
                }
                
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise e
        
    except Exception as e:
        error_message = str(e).lower()
        
        if "rate limit" in error_message:
            return {
                "status": 429,
                "error": "Rate limit exceeded. Please try again later."
            }
        elif "api key" in error_message or "unauthorized" in error_message:
            return {
                "status": 401,
                "error": "Invalid API key or unauthorized access"
            }
        elif "not found" in error_message:
            return {
                "status": 404,
                "error": "Requested filing or exhibit not found"
            }
        else:
            return {
                "status": 500,
                "error": f"An unexpected error occurred: {str(e)}"
            } 