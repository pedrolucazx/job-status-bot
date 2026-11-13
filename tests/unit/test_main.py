import unittest
from unittest.mock import Mock, patch
from urllib.parse import unquote
from src.bot.main import build_gmail_web_link, notify_and_label, process_batch


@patch('src.bot.main.GMAIL_ACCOUNT', 'user@example.com')
class TestMain(unittest.TestCase):
    def test_exact_message_search(self):
        link = build_gmail_web_link('internal', 'abc+123@example.org')
        self.assertEqual(unquote(link), 'https://mail.google.com/mail/?authuser=user@example.com#search/in:anywhere rfc822msgid:abc+123@example.org')
        self.assertNotIn('googlegmail', link)

    def test_missing_message_id_fallback(self):
        self.assertTrue(build_gmail_web_link('msg123').endswith('#all/msg123'))

    def test_only_decisions_notify(self):
        for status in ('indefinido', '', None, 'inscricao', 'rejeitado', 'avancou'):
            with self.subTest(status=status):
                gmail, notifier = Mock(), Mock()
                notify_and_label({'job_related': True, 'resultado': status}, gmail, notifier, 'msg')
                self.assertEqual(notifier.send_message.call_count, int(status in ('rejeitado', 'avancou')))
                gmail.apply_label.assert_called_once_with('msg', 'jobbot-processado')

    def test_unrelated_email_never_notifies(self):
        notifier = Mock()
        notify_and_label({'job_related': False, 'resultado': 'avancou'}, Mock(), notifier, 'msg')
        notifier.send_message.assert_not_called()

    def test_readable_notification_and_exact_link(self):
        notifier, gmail = Mock(), Mock()
        result = {'job_related': True, 'resultado': 'avancou', 'empresa': 'Acme',
                  'cargo': 'Backend', 'proxima_etapa': 'entrevista técnica',
                  'evidencia': 'Você foi selecionado para entrevista.'}
        notify_and_label(result, gmail, notifier, 'msg', rfc822_msgid='abc@example.org')
        message = notifier.send_message.call_args.args[0]
        self.assertIn('✅ Você avançou de etapa\n\nEmpresa: Acme\nVaga: Backend', message)
        self.assertIn('Próxima etapa: entrevista técnica', message)
        self.assertIn('rfc822msgid:abc@example.org', message)
        self.assertEqual(notifier.send_message.call_args.kwargs['email_url'], build_gmail_web_link('msg', 'abc@example.org'))

    def test_delivery_failure_keeps_email_unlabeled(self):
        gmail, notifier = Mock(), Mock()
        notifier.send_message.side_effect = RuntimeError('delivery failed')
        with self.assertRaises(RuntimeError):
            notify_and_label({'job_related': True, 'resultado': 'rejeitado'}, gmail, notifier, 'msg')
        gmail.apply_label.assert_not_called()

    def test_missing_classification_remains_unlabeled(self):
        gmail, llm, notifier = Mock(), Mock(), Mock()
        llm.classify_batch.return_value = {}
        process_batch([{'id': 'msg'}], gmail, llm, notifier)
        gmail.apply_label.assert_not_called()
        notifier.send_message.assert_not_called()

    def test_batch_passes_message_id(self):
        gmail, llm, notifier = Mock(), Mock(), Mock()
        llm.classify_batch.return_value = {'msg': {'job_related': True, 'resultado': 'rejeitado'}}
        process_batch([{'id': 'msg', 'rfc822_msgid': 'abc@example.org'}], gmail, llm, notifier)
        self.assertIn('abc%40example.org', notifier.send_message.call_args.kwargs['email_url'])

    def test_rejection_omits_next_step_and_simulation_does_not_label(self):
        gmail, notifier = Mock(), Mock()
        notify_and_label({'job_related': True, 'resultado': 'rejeitado', 'proxima_etapa': 'irrelevant'},
                         gmail, notifier, 'msg', simulate=True)
        self.assertNotIn('Próxima etapa', notifier.send_message.call_args.args[0])
        gmail.apply_label.assert_not_called()

    def test_failed_delivery_does_not_block_next_email(self):
        gmail, llm, notifier = Mock(), Mock(), Mock()
        decision = {'job_related': True, 'resultado': 'rejeitado'}
        llm.classify_batch.return_value = {'bad': decision, 'good': decision}
        notifier.send_message.side_effect = [RuntimeError('failed'), None]
        process_batch([{'id': 'bad'}, {'id': 'good'}], gmail, llm, notifier)
        self.assertEqual(notifier.send_message.call_count, 2)
        gmail.apply_label.assert_called_once_with('good', 'jobbot-processado')


class TestReviewAndExclusions(unittest.TestCase):
    def test_invalid_verdict_is_labeled_for_review_and_not_retried(self):
        gmail, llm, notifier = Mock(), Mock(), Mock()
        llm.classify_batch.return_value = {'x': {'job_related': True, 'resultado': 'avancou', 'invalid': True}}
        process_batch([{'id': 'x'}], gmail, llm, notifier)
        notifier.send_message.assert_not_called()
        labels = [c.args[1] for c in gmail.apply_label.call_args_list]
        self.assertEqual(labels, ['jobbot-revisar', 'jobbot-processado'])

    def test_missing_review_label_still_marks_processed(self):
        gmail, llm = Mock(), Mock()
        gmail.apply_label.side_effect = [ValueError('missing'), None]
        llm.classify_batch.return_value = {'x': {'job_related': True, 'resultado': 'avancou', 'invalid': True}}
        process_batch([{'id': 'x'}], gmail, llm, Mock())
        self.assertEqual(gmail.apply_label.call_args_list[-1].args, ('x', 'jobbot-processado'))

    def test_linkedin_stats_skip_gemini(self):
        from src.bot.main import is_excluded
        self.assertTrue(is_excluded('LinkedIn <notifications-noreply@linkedin.com>'))
        self.assertFalse(is_excluded('LinkedIn <jobs-noreply@linkedin.com>'))  # Easy Apply verdicts come from here
