import unittest
from unittest.mock import patch, Mock, MagicMock
from src.bot.gmail_client import GmailClient

class TestGmailClient(unittest.TestCase):

    @patch('src.bot.gmail_client.get_credentials')
    @patch('src.bot.gmail_client.build')
    def test_get_new_emails(self, mock_build, mock_get_credentials):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_service.users.return_value.labels.return_value.list.return_value.execute.return_value = {
            'labels': [{'name': 'jobbot-processado', 'id': 'Label_1'}]
        }
        mock_service.users.return_value.messages.return_value.list.return_value.execute.return_value = {
            'messages': [{'id': 'msg1'}]
        }
        mock_service.users.return_value.messages.return_value.get.return_value.execute.return_value = {
            'id': 'msg1',
            'payload': {
                'headers': [
                    {'name': 'Subject', 'value': 'Test Subject'},
                    {'name': 'From', 'value': 'test@example.com'}
                ],
                'body': {
                    'data': 'VGVzdCBlbWFpbCBib2R5'
                },
                'mimeType': 'text/plain'
            }
        }

        client = GmailClient()
        emails = client.get_new_emails()

        self.assertEqual(len(emails), 1)
        self.assertEqual(emails[0]['id'], 'msg1')
        self.assertEqual(emails[0]['subject'], 'Test Subject')
        self.assertEqual(emails[0]['sender'], 'test@example.com')
        self.assertEqual(emails[0]['body'], 'Test email body')

    @patch('src.bot.gmail_client.get_credentials')
    @patch('src.bot.gmail_client.build')
    def test_apply_label(self, mock_build, mock_get_credentials):
        mock_service = MagicMock()
        mock_build.return_value = mock_service

        mock_service.users.return_value.labels.return_value.list.return_value.execute.return_value = {
            'labels': [{'name': 'jobbot-processado', 'id': 'Label_1'}]
        }

        client = GmailClient()
        client.apply_label('msg1', 'jobbot-processado')

        mock_service.users.return_value.messages.return_value.modify.assert_called_once_with(
            userId='me',
            id='msg1',
            body={'addLabelIds': ['Label_1'], 'removeLabelIds': []}
        )

if __name__ == '__main__':
    unittest.main()
