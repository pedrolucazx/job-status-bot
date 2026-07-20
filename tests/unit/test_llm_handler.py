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
            text='{"job_related": true, "empresa": "TechCorp", "cargo": "Backend", "resultado": "rejeitado", "proxima_etapa": ""}'
        )
        mock_genai_model.return_value = mock_model_instance

        llm_handler = LLMHandler()
        email_body = "This is a test email."

        llm_handler.extract_info(email_body)

        mock_model_instance.generate_content.assert_called_once()

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'fake-key-for-tests'})
    @patch('google.generativeai.GenerativeModel')
    def test_classify_batch(self, mock_genai_model):
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = Mock(
            text='['
                 '{"id": "1", "job_related": true, "empresa": "TechCorp", "cargo": "Backend", "resultado": "rejeitado", "proxima_etapa": ""},'
                 '{"id": "2", "job_related": false, "empresa": "", "cargo": "", "resultado": "indefinido", "proxima_etapa": ""}'
                 ']'
        )
        mock_genai_model.return_value = mock_model_instance

        llm_handler = LLMHandler()
        emails = [
            {"id": "1", "sender": "a@gupy.io", "subject": "Feedback", "body": "..."},
            {"id": "2", "sender": "friend@gmail.com", "subject": "Oi", "body": "..."},
        ]

        results = llm_handler.classify_batch(emails)

        mock_model_instance.generate_content.assert_called_once()
        self.assertEqual(results["1"]["resultado"], "rejeitado")
        self.assertFalse(results["2"]["job_related"])

if __name__ == '__main__':
    unittest.main()
