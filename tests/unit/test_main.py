import unittest
from unittest.mock import Mock

from src.bot.main import (
    build_gmail_app_link,
    build_gmail_mobile_link,
    build_gmail_web_link,
    build_text_link_entity,
    notify_and_label,
)


class TestMain(unittest.TestCase):
    def test_build_gmail_links_use_thread_id(self):
        app_link = build_gmail_app_link('msg123', thread_id='thread456')
        mobile_link = build_gmail_mobile_link('msg123', thread_id='thread456')
        web_link = build_gmail_web_link('msg123', thread_id='thread456')

        self.assertEqual(app_link, 'googlegmail:///cv=thread456/accountId=1')
        self.assertEqual(
            web_link,
            'https://mail.google.com/mail/u/pedrolucazxmesquita%40gmail.com/#all/thread456',
        )
        self.assertEqual(
            mobile_link,
            'https://pedrolucazx.github.io/job-status-bot/gmail-redirect.html?'
            'to=googlegmail%3A%2F%2F%2Fcv%3Dthread456%2FaccountId%3D1&'
            'fallback=https%3A%2F%2Fmail.google.com%2Fmail%2Fu%2Fpedrolucazxmesquita%2540gmail.com%2F%23all%2Fthread456',
        )
        self.assertNotIn('rfc822msgid', app_link)
        self.assertNotIn('rfc822msgid', mobile_link)
        self.assertNotIn('rfc822msgid', web_link)

    def test_notify_and_label_sends_thread_link(self):
        gmail_client = Mock()
        notifier = Mock()
        result = {
            'job_related': True,
            'empresa': 'Digital Growth',
            'cargo': 'Desenvolvedor(a) Fullstack Pleno',
            'resultado': 'avancou',
            'proxima_etapa': 'entrevista técnica com o time',
        }

        notify_and_label(result, gmail_client, notifier, 'msg123', simulate=True, thread_id='thread456')

        expected_message = (
            '✅ Avançou de etapa — Digital Growth (Desenvolvedor(a) Fullstack Pleno)\n'
            'Próxima etapa: entrevista técnica com o time\n'
            'Abrir no Gmail app (pedrolucazxmesquita@gmail.com)\n'
            'Web/PC: https://mail.google.com/mail/u/pedrolucazxmesquita%40gmail.com/#all/thread456'
        )
        app_label = 'Abrir no Gmail app (pedrolucazxmesquita@gmail.com)'
        notifier.send_message.assert_called_once_with(
            expected_message,
            entities=[
                build_text_link_entity(
                    expected_message,
                    app_label,
                    'https://pedrolucazx.github.io/job-status-bot/gmail-redirect.html?'
                    'to=googlegmail%3A%2F%2F%2Fcv%3Dthread456%2FaccountId%3D1&'
                    'fallback=https%3A%2F%2Fmail.google.com%2Fmail%2Fu%2Fpedrolucazxmesquita%2540gmail.com%2F%23all%2Fthread456',
                )
            ],
        )
        gmail_client.apply_label.assert_not_called()


if __name__ == '__main__':
    unittest.main()
