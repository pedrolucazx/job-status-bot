import unittest
from unittest.mock import patch, Mock
import requests
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

    @patch('requests.post')
    def test_send_message_with_entities(self, mock_post):
        notifier = Notifier()
        notifier.bot_token = 'fake_token'
        notifier.chat_id = 'fake_chat_id'

        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        message = "Open Gmail"
        entities = [{"type": "text_link", "offset": 0, "length": 10, "url": "googlegmail:///cv=thread/accountId=1"}]
        notifier.send_message(message, entities=entities)

        expected_url = "https://api.telegram.org/botfake_token/sendMessage"
        expected_payload = {
            "chat_id": "fake_chat_id",
            "text": message,
            "entities": entities,
        }

        mock_post.assert_called_once_with(expected_url, json=expected_payload)
        mock_response.raise_for_status.assert_called_once()

    @patch('requests.post')
    def test_send_message_retries_without_entities_when_telegram_rejects_link(self, mock_post):
        notifier = Notifier()
        notifier.bot_token = 'fake_token'
        notifier.chat_id = 'fake_chat_id'

        rejected_response = Mock()
        rejected_response.raise_for_status.side_effect = requests.exceptions.HTTPError("bad link")
        fallback_response = Mock()
        fallback_response.raise_for_status = Mock()
        mock_post.side_effect = [rejected_response, fallback_response]

        message = "Open Gmail"
        entities = [{"type": "text_link", "offset": 0, "length": 10, "url": "googlegmail:///cv=thread/accountId=1"}]
        notifier.send_message(message, entities=entities)

        expected_url = "https://api.telegram.org/botfake_token/sendMessage"
        self.assertEqual(mock_post.call_count, 2)
        mock_post.assert_any_call(expected_url, json={
            "chat_id": "fake_chat_id",
            "text": message,
            "entities": entities,
        })
        mock_post.assert_any_call(expected_url, json={
            "chat_id": "fake_chat_id",
            "text": message,
        })
        rejected_response.raise_for_status.assert_called_once()
        fallback_response.raise_for_status.assert_called_once()

if __name__ == '__main__':
    unittest.main()
