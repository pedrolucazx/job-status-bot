import unittest
from unittest.mock import patch, Mock
import requests
from src.bot.notifier import Notifier


class TestNotifier(unittest.TestCase):
    @patch('src.bot.notifier.requests.post')
    def test_button_and_no_preview(self, post):
        post.return_value.json.return_value = {'ok': True}
        Notifier().send_message('✅ Avanço', email_url='https://mail.google.com/')
        payload = post.call_args.kwargs['json']
        self.assertEqual(payload['reply_markup']['inline_keyboard'][0][0]['url'], 'https://mail.google.com/')
        self.assertEqual(payload['link_preview_options'], {'is_disabled': True})
        self.assertEqual(post.call_args.kwargs['timeout'], 30)

    @patch('src.bot.notifier.requests.post')
    def test_failures_propagate_without_secret_or_silent_fallback(self, post):
        for error in (requests.Timeout('secret'), requests.HTTPError('secret')):
            with self.subTest(error=error):
                post.reset_mock()
                post.side_effect = error
                with self.assertRaisesRegex(RuntimeError, 'Telegram delivery failed') as caught:
                    Notifier().send_message('test')
                self.assertNotIn('secret', str(caught.exception))
                self.assertEqual(post.call_count, 1)

    @patch('src.bot.notifier.requests.post')
    def test_api_error_is_not_success(self, post):
        post.return_value.json.return_value = {'ok': False}
        with self.assertRaises(RuntimeError):
            Notifier().send_message('test')
