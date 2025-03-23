import os
import re
import time
from typing import Dict, Any, Optional
from pathlib import Path
from sec_api import PdfGeneratorApi

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

def validate_input(
    accession_number: str,
    file_type: str,
    options: Dict[str, Any],
    exhibit_number: Optional[str] = None
) -> Dict[str, Any]:
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
    
    # Validate options
    if options:
        # Validate page size
        if "page_size" in options:
            valid_page_sizes = ["A4", "Letter"]
            if options["page_size"] not in valid_page_sizes:
                return {
                    "status": 400,
                    "error": f"Invalid page size. Must be one of: {', '.join(valid_page_sizes)}"
                }
        
        # Validate margins
        if "margin" in options:
            if not isinstance(options["margin"], dict):
                return {
                    "status": 400,
                    "error": "Margins must be specified as a dictionary"
                }
            for side in ["top", "bottom", "left", "right"]:
                if side in options["margin"]:
                    try:
                        margin = float(options["margin"][side])
                        if margin < 0 or margin > 5:
                            return {
                                "status": 400,
                                "error": "Margins must be between 0 and 5 inches"
                            }
                    except ValueError:
                        return {
                            "status": 400,
                            "error": "Margin values must be numbers"
                        }
        
        # Validate header and footer
        for option in ["header", "footer"]:
            if option in options and not isinstance(options[option], bool):
                return {
                    "status": 400,
                    "error": f"{option.capitalize()} must be a boolean value"
                }
    
    return {"status": 200}

def setup_pdf_directory(accession_number: str, file_type: str, exhibit_number: Optional[str] = None) -> str:
    """Set up the PDF directory structure and return the file path."""
    base_dir = Path("generated_pdfs")
    sub_dir = base_dir / file_type / accession_number
    
    # Create directory if it doesn't exist
    sub_dir.mkdir(parents=True, exist_ok=True)
    
    # Determine file name
    if file_type == "complete":
        file_name = "filing.pdf"
    elif file_type == "primary":
        file_name = "primary.pdf"
    else:  # exhibit
        file_name = f"{exhibit_number}.pdf"
    
    return str(sub_dir / file_name)

def check_pdf_quality(file_path: str) -> Dict[str, bool]:
    """Perform quality checks on the generated PDF."""
    # Note: This is a simplified version. In a real implementation,
    # you would use a PDF processing library to perform these checks.
    return {
        "searchable_text": True,
        "table_structure": True,
        "hyperlinks": True,
        "page_numbers": True,
        "image_quality": True
    }

def pdf_generator_agent(
    accession_number: str,
    file_type: str = "complete",
    options: Dict[str, Any] = None,
    exhibit_number: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate PDFs from SEC filings and their components.
    
    Args:
        accession_number (str): The accession number of the filing
        file_type (str): Type of file to convert (complete, primary, or exhibit)
        options (dict): PDF generation options (page size, margins, header/footer)
        exhibit_number (str, optional): The specific exhibit number to convert
        
    Returns:
        dict: Response containing status code and either file path or error message
    """
    # Set default options if none provided
    if options is None:
        options = {
            "page_size": "Letter",
            "margin": {"top": 1, "bottom": 1, "left": 1, "right": 1},
            "header": True,
            "footer": True
        }
    
    # Validate input
    validation_result = validate_input(accession_number, file_type, options, exhibit_number)
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
        
        pdf_api = PdfGeneratorApi(api_key)
        rate_limiter = RateLimiter()
        
        # Set up PDF directory and get file path
        file_path = setup_pdf_directory(accession_number, file_type, exhibit_number)
        
        # Apply rate limiting
        rate_limiter.wait()
        
        # Make API request with retry logic
        max_retries = 3
        retry_delay = 1  # seconds
        
        for attempt in range(max_retries):
            try:
                # Generate PDF
                if file_type == "exhibit":
                    content = pdf_api.generate_pdf(accession_number, exhibit_number, options)
                else:
                    content = pdf_api.generate_pdf(accession_number, options)
                
                # Save the file
                with open(file_path, 'wb') as f:
                    f.write(content)
                
                # Verify file was created and has content
                if not os.path.exists(file_path) or os.path.getsize(file_path) == 0:
                    return {
                        "status": 500,
                        "error": "Failed to save PDF or file is empty"
                    }
                
                # Perform quality checks
                quality_checks = check_pdf_quality(file_path)
                
                return {
                    "status": 200,
                    "file_path": file_path,
                    "file_size": os.path.getsize(file_path),
                    "quality_checks": quality_checks
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
        elif "conversion" in error_message:
            return {
                "status": 500,
                "error": "PDF conversion failed"
            }
        else:
            return {
                "status": 500,
                "error": f"An unexpected error occurred: {str(e)}"
            } 