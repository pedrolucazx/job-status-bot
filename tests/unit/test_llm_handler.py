import os
import unittest
from unittest.mock import patch, Mock
from src.bot.llm_handler import LLMHandler, validate_decision

class TestLLMHandler(unittest.TestCase):

    @patch.dict(os.environ, {'GEMINI_API_KEY': 'fake-key-for-tests'})
    @patch('google.generativeai.GenerativeModel')
    def test_extract_info(self, mock_genai_model):
        mock_model_instance = Mock()
        mock_model_instance.generate_content.return_value = Mock(
            text='{"job_related": true, "empresa": "TechCorp", "cargo": "Backend", "resultado": "rejeitado", "proxima_etapa": "", "evidencia": "This is a test email."}'
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
                 '{"id": "1", "job_related": true, "empresa": "TechCorp", "cargo": "Backend", "resultado": "rejeitado", "proxima_etapa": "", "evidencia": "This is a test email."},'
                 '{"id": "2", "job_related": false, "empresa": "", "cargo": "", "resultado": "indefinido", "proxima_etapa": "", "evidencia": "This is a test email."}'
                 ']'
        )
        mock_genai_model.return_value = mock_model_instance

        llm_handler = LLMHandler()
        emails = [
            {"id": "1", "sender": "a@gupy.io", "subject": "Feedback", "body": "This is a test email."},
            {"id": "2", "sender": "friend@gmail.com", "subject": "Oi", "body": "This is a test email."},
        ]

        results = llm_handler.classify_batch(emails)

        mock_model_instance.generate_content.assert_called_once()
        self.assertEqual(results["1"]["resultado"], "rejeitado")
        self.assertFalse(results["2"]["job_related"])

class TestDecisionEvidence(unittest.TestCase):
    def test_confirmation_is_silent(self):
        result = {'job_related': True, 'resultado': 'indefinido', 'evidencia': ''}
        self.assertEqual(validate_decision(result, 'Sua inscrição foi recebida.'), result)

    def test_missing_and_invented_evidence_rejected(self):
        for evidence in ('', None, 'Você passou!'):
            with self.subTest(evidence=evidence), self.assertRaises(ValueError):
                validate_decision({'job_related': True, 'resultado': 'avancou', 'evidencia': evidence}, 'Inscrição recebida')

    def test_whitespace_in_evidence_is_normalized(self):
        result = {'job_related': True, 'resultado': 'rejeitado', 'evidencia': 'Seguimos com outros candidatos.'}
        self.assertEqual(validate_decision(result, 'Seguimos com\n outros candidatos.'), result)


    def test_case_accents_and_punctuation_are_not_invention(self):
        result = {'job_related': True, 'resultado': 'rejeitado', 'evidencia': '"Optamos por nao avancar"'}
        self.assertEqual(validate_decision(result, 'Neste momento, optamos por não avançar com sua candidatura.'), result)
        with self.assertRaises(ValueError):
            validate_decision({**result, 'evidencia': 'optamos por avançar'}, 'optamos por não avançar')


class TestBatchEvidence(unittest.TestCase):
    @patch.dict(os.environ, {'GEMINI_API_KEY': 'fake'})
    @patch('google.generativeai.GenerativeModel')
    def test_invalid_decision_does_not_block_other_emails(self, model):
        handler = LLMHandler()
        handler._generate_with_retry = Mock(return_value=[
            {'id': 'bad', 'job_related': True, 'resultado': 'avancou', 'evidencia': 'Inventado'},
            {'id': 'good', 'job_related': True, 'resultado': 'rejeitado', 'evidencia': 'Não vamos seguir.'},
        ])
        emails = [
            {'id': 'bad', 'subject': 'Inscrição recebida', 'body': 'Obrigado por se candidatar'},
            {'id': 'good', 'subject': 'Retorno', 'body': 'Não vamos seguir.'},
        ]
        results = handler.classify_batch(emails)
        self.assertTrue(results['bad']['invalid'])  # kept, so main labels it for review instead of retrying
        self.assertNotIn('invalid', results['good'])
        self.assertEqual(results['good']['resultado'], 'rejeitado')


if __name__ == '__main__':
    unittest.main()
