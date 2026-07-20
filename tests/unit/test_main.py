import unittest
from unittest.mock import Mock

from src.bot.main import build_gmail_app_link, build_gmail_web_link, notify_and_label


class TestMain(unittest.TestCase):
    def test_build_gmail_links_use_thread_id(self):
        app_link = build_gmail_app_link('msg123', thread_id='thread456')
        web_link = build_gmail_web_link('msg123', thread_id='thread456')

        self.assertEqual(app_link, 'googlegmail:///cv=thread456/accountId=1')
        self.assertEqual(
            web_link,
            'https://mail.google.com/mail/?authuser=pedrolucazxmesquita%40gmail.com#all/thread456',
        )
        self.assertNotIn('rfc822msgid', app_link)
        self.assertNotIn('rfc822msgid', web_link)

    def test_notify_and_label_sends_thread_link(self):
        gmail_client = Mock()
        notifier = Mock()
        result = {
            'job_related': True,
            'empresa': 'Digital Growth',
            'cargo': 'Desenvolvedor(a) Fullstack Pleno',
            'resultado': 'avancou',
        }

        notify_and_label(result, gmail_client, notifier, 'msg123', simulate=True, thread_id='thread456')

        notifier.send_message.assert_called_once_with(
            '✅ Avançou de etapa — Digital Growth (Desenvolvedor(a) Fullstack Pleno)\n'
            'Gmail app: googlegmail:///cv=thread456/accountId=1\n'
            'Web/PC: https://mail.google.com/mail/?authuser=pedrolucazxmesquita%40gmail.com#all/thread456'
        )
        gmail_client.apply_label.assert_not_called()


if __name__ == '__main__':
    unittest.main()
