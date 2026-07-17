import os
import unittest
from unittest.mock import patch, Mock
from src.bot.llm_handler import LLMHandler

class TestLLMHandler(unittest.TestCase):

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'fake-key-for-tests'})
    @patch('google.generativeai.GenerativeModel')
    def test_extract_info(self, mock_genai_model):
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = Mock(
            text='{"job_related": true, "empresa": "TechCorp", "cargo": "Backend", "resultado": "rejeitado"}'
        )
        mock_genai_model.return_value = mock_model_instance

        llm_handler = LLMHandler()
        email_body = "This is a test email."

        llm_handler.extract_info(email_body)

        mock_model_instance.generate_content.assert_called_once()

if __name__ == '__main__':
    unittest.main()
