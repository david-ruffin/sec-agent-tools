# test_full_text_search_tool.py
import unittest
from unittest.mock import patch
from full_text_search_tool import full_text_search_tool

class TestFullTextSearchTool(unittest.TestCase):
    @patch('full_text_search_tool.FullTextSearchApi')
    def test_full_text_search_success(self, mock_api_class):
        # Create a fake response that the API might return.
        fake_response = {
            "filings": [
                {
                    "accessionNo": "0000000000-23-000001",
                    "formType": "8-K",
                    "filedAt": "2023-01-15T00:00:00-04:00",
                }
            ]
        }
        
        # Configure the mock instance to return our fake response.
        mock_api_instance = mock_api_class.return_value
        mock_api_instance.get_filings.return_value = fake_response
        
        # Call our function with sample parameters.
        result = full_text_search_tool(
            query='"Example Query"',
            form_types="8-K,10-Q",
            start_date="2023-01-01",
            end_date="2023-06-30"
        )
        
        # Assert that our function returns the expected fake response.
        self.assertEqual(result, fake_response)
        # Also ensure that the API was called with the correct parameters.
        expected_form_types = ["8-K", "10-Q"]
        mock_api_instance.get_filings.assert_called_once_with({
            "query": '"Example Query"',
            "formTypes": expected_form_types,
            "startDate": "2023-01-01",
            "endDate": "2023-06-30"
        })

if __name__ == '__main__':
    unittest.main()
