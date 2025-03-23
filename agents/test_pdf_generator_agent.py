import pytest
import os
import shutil
from unittest.mock import Mock, patch
from pdf_generator_agent import pdf_generator_agent

@pytest.fixture
def cleanup():
    yield
    # Clean up test generated PDFs after tests
    base_dir = "generated_pdfs"
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)

@pytest.fixture(autouse=True)
def mock_env_api_key():
    with patch.dict(os.environ, {"SEC_API_KEY": "mock_api_key"}):
        yield

@patch('pdf_generator_agent.PdfGeneratorApi')
def test_generate_complete_filing_pdf(mock_pdf_api, cleanup):
    # Configure mock to return sample content
    mock_instance = Mock()
    mock_pdf_api.return_value = mock_instance
    mock_instance.generate_pdf.return_value = b"%PDF-1.5\nSample PDF content"
    
    response = pdf_generator_agent(
        accession_number="0001640147-23-000089",
        file_type="complete",
        options={
            "page_size": "Letter",
            "margin": {"top": 1, "bottom": 1, "left": 1, "right": 1},
            "header": True,
            "footer": True
        }
    )
    
    assert response["status"] == 200
    assert response["file_path"].endswith("filing.pdf")
    assert os.path.exists(response["file_path"])
    assert os.path.getsize(response["file_path"]) > 0
    
    # Verify API was called with correct parameters
    mock_instance.generate_pdf.assert_called_once_with(
        "0001640147-23-000089", 
        {
            "page_size": "Letter",
            "margin": {"top": 1, "bottom": 1, "left": 1, "right": 1},
            "header": True,
            "footer": True
        }
    )

@patch('pdf_generator_agent.PdfGeneratorApi')
def test_generate_primary_document_pdf(mock_pdf_api, cleanup):
    # Configure mock to return sample content
    mock_instance = Mock()
    mock_pdf_api.return_value = mock_instance
    mock_instance.generate_pdf.return_value = b"%PDF-1.5\nSample PDF content"
    
    response = pdf_generator_agent(
        accession_number="0001640147-23-000089",
        file_type="primary",
        options={
            "page_size": "A4",
            "watermark": "CONFIDENTIAL"
        }
    )
    
    assert response["status"] == 200
    assert response["file_path"].endswith("primary.pdf")
    assert os.path.exists(response["file_path"])
    assert os.path.getsize(response["file_path"]) > 0
    
    # Verify API was called with correct parameters
    mock_instance.generate_pdf.assert_called_once_with(
        "0001640147-23-000089", 
        {
            "page_size": "A4",
            "watermark": "CONFIDENTIAL"
        }
    )

@patch('pdf_generator_agent.PdfGeneratorApi')
def test_generate_exhibit_pdf(mock_pdf_api, cleanup):
    # Configure mock to return sample content
    mock_instance = Mock()
    mock_pdf_api.return_value = mock_instance
    mock_instance.generate_pdf.return_value = b"%PDF-1.5\nSample PDF content"
    
    response = pdf_generator_agent(
        accession_number="0001640147-23-000089",
        file_type="exhibit",
        exhibit_number="EX-10.1",
        options={
            "page_size": "Letter",
            "header": False,
            "footer": True
        }
    )
    
    assert response["status"] == 200
    assert response["file_path"].endswith("EX-10.1.pdf")
    assert os.path.exists(response["file_path"])
    assert os.path.getsize(response["file_path"]) > 0
    
    # Verify API was called with correct parameters
    mock_instance.generate_pdf.assert_called_once_with(
        "0001640147-23-000089", 
        "EX-10.1",
        {
            "page_size": "Letter",
            "header": False,
            "footer": True
        }
    )

def test_invalid_accession_number():
    response = pdf_generator_agent(
        accession_number="invalid-format",
        file_type="complete"
    )
    
    assert response["status"] == 400
    assert "error" in response
    assert "invalid accession number format" in response["error"].lower()

def test_invalid_file_type():
    response = pdf_generator_agent(
        accession_number="0001640147-23-000089",
        file_type="invalid"
    )
    
    assert response["status"] == 400
    assert "error" in response
    assert "invalid file type" in response["error"].lower()

def test_invalid_options():
    response = pdf_generator_agent(
        accession_number="0001640147-23-000089",
        file_type="complete",
        options={
            "page_size": "InvalidSize",
            "margin": {"invalid": 1}
        }
    )
    
    assert response["status"] == 400
    assert "error" in response
    assert "invalid" in response["error"].lower()

def test_missing_exhibit_number():
    response = pdf_generator_agent(
        accession_number="0001640147-23-000089",
        file_type="exhibit"
    )
    
    assert response["status"] == 400
    assert "error" in response
    assert "exhibit number required" in response["error"].lower()

@patch('pdf_generator_agent.PdfGeneratorApi')
def test_file_not_found(mock_pdf_api):
    # Configure mock to raise an exception
    mock_instance = Mock()
    mock_pdf_api.return_value = mock_instance
    mock_instance.generate_pdf.side_effect = Exception("Not found")
    
    response = pdf_generator_agent(
        accession_number="0001640147-99-999999",
        file_type="complete"
    )
    
    assert response["status"] == 404
    assert "error" in response
    assert "not found" in response["error"].lower()

@patch('pdf_generator_agent.PdfGeneratorApi')
def test_rate_limit_handling(mock_pdf_api):
    # Configure mock to raise a rate limit exception
    mock_instance = Mock()
    mock_pdf_api.return_value = mock_instance
    mock_instance.generate_pdf.side_effect = Exception("Rate limit exceeded")
    
    response = pdf_generator_agent(
        accession_number="0001640147-23-000089",
        file_type="complete"
    )
    
    assert response["status"] == 429
    assert "error" in response
    assert "rate limit" in response["error"].lower()

@patch('pdf_generator_agent.PdfGeneratorApi')
def test_authentication_error(mock_pdf_api):
    # Configure mock to raise an authentication error
    mock_instance = Mock()
    mock_pdf_api.return_value = mock_instance
    mock_instance.generate_pdf.side_effect = Exception("Invalid API key")
    
    response = pdf_generator_agent(
        accession_number="0001640147-23-000089",
        file_type="complete"
    )
    
    assert response["status"] == 401
    assert "error" in response
    assert "api key" in response["error"].lower()

@patch('pdf_generator_agent.PdfGeneratorApi')
def test_large_file_generation(mock_pdf_api, cleanup):
    # Mock a large PDF response
    large_content = b"%PDF-1.5\n" + b"x" * (10 * 1024 * 1024) + b"\n%%EOF"  # 10MB
    
    mock_instance = Mock()
    mock_pdf_api.return_value = mock_instance
    mock_instance.generate_pdf.return_value = large_content
    
    response = pdf_generator_agent(
        accession_number="0001640147-23-000089",
        file_type="complete"
    )
    
    assert response["status"] == 200
    assert os.path.exists(response["file_path"])
    assert os.path.getsize(response["file_path"]) == len(large_content)

@patch('pdf_generator_agent.PdfGeneratorApi')
@patch('pdf_generator_agent.check_pdf_quality')
def test_pdf_quality_checks(mock_quality_check, mock_pdf_api, cleanup):
    # Configure mocks
    mock_instance = Mock()
    mock_pdf_api.return_value = mock_instance
    mock_instance.generate_pdf.return_value = b"%PDF-1.5\nSample PDF content"
    
    mock_quality_result = {
        "searchable_text": True,
        "table_structure": True,
        "hyperlinks": True,
        "page_numbers": True,
        "image_quality": True
    }
    mock_quality_check.return_value = mock_quality_result
    
    response = pdf_generator_agent(
        accession_number="0001640147-23-000089",
        file_type="complete",
        options={
            "page_size": "Letter",
            "margin": {"top": 1, "bottom": 1, "left": 1, "right": 1},
            "header": True,
            "footer": True
        }
    )
    
    assert response["status"] == 200
    assert response["quality_checks"] == mock_quality_result
    mock_quality_check.assert_called_once() 