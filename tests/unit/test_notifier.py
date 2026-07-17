import unittest
from unittest.mock import patch, Mock
from src.bot.notifier import Notifier

class TestNotifier(unittest.TestCase):

    @patch('requests.post')
    def test_send_message(self, mock_post):
        notifier = Notifier()
        notifier.bot_token = 'fake_token'
        notifier.chat_id = 'fake_chat_id'
        
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        message = "Test message"
        notifier.send_message(message)

        expected_url = "https://api.telegram.org/botfake_token/sendMessage"
        expected_payload = {
            "chat_id": "fake_chat_id",
            "text": message
        }

        mock_post.assert_called_once_with(expected_url, json=expected_payload)
        mock_response.raise_for_status.assert_called_once()

if __name__ == '__main__':
    unittest.main()
