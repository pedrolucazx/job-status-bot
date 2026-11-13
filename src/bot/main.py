import argparse
import os
from urllib.parse import quote
from dotenv import load_dotenv
from src.bot.gmail_client import GmailClient
from src.bot.llm_handler import LLMHandler
from src.bot.notifier import Notifier
from src.bot.notion_tracker import NotionTracker

load_dotenv()

# Senders that are pure noise (no application ever involved) — kept as a
# small, stable optimization to skip them for free. Relevance for
# everything else is judged by the LLM itself, not a keyword/domain list,
# so this never needs updating for a new ATS or a foreign-language email.
EXCLUDED_SENDERS = [
    "jobalerts-noreply@linkedin.com",
    "notifications-noreply@linkedin.com",  # weekly post stats, never a verdict
    "avisovagas@catho.com.br",
]
REVIEW_LABEL = 'jobbot-revisar'  # Gemini claimed a verdict it couldn't quote

BATCH_SIZE = 10
GMAIL_ACCOUNT = os.getenv('GMAIL_ACCOUNT', '0')


def is_excluded(sender):
    sender_lower = sender.lower()
    return any(addr in sender_lower for addr in EXCLUDED_SENDERS)


def build_gmail_web_link(message_id, rfc822_msgid=None):
    account = quote(GMAIL_ACCOUNT or '0', safe='')
    if rfc822_msgid:
        query = quote(f"in:anywhere rfc822msgid:{rfc822_msgid}", safe='')
        return f"https://mail.google.com/mail/?authuser={account}#search/{query}"
    return f"https://mail.google.com/mail/?authuser={account}#all/{quote(message_id, safe='')}"


def next_step_text(result):
    proxima_etapa = result.get('proxima_etapa')
    if proxima_etapa is None:
        return 'não informada'

    proxima_etapa = str(proxima_etapa).strip()
    return proxima_etapa or 'não informada'


def send_status_notification(notifier, status_line, result, message_id, rfc822_msgid=None, notion_line=None):
    lines = [status_line, '',
             f"Empresa: {result.get('empresa') or 'não informada'}",
             f"Vaga: {result.get('cargo') or 'não informada'}"]
    if result.get('resultado') == 'avancou':
        lines.extend(['', f"Próxima etapa: {next_step_text(result)}"])
    if result.get('evidencia'):
        lines.extend(['', f"Trecho do e-mail: {' '.join(result['evidencia'].split())[:700]}"])
    if notion_line:
        lines.extend(['', notion_line])
    if rfc822_msgid:
        lines.extend(['', 'Se o link não abrir no app, copie esta busca no Gmail:',
                      f"in:anywhere rfc822msgid:{rfc822_msgid}"])
    notifier.send_message(
        "\n".join(lines),
        email_url=build_gmail_web_link(message_id, rfc822_msgid),
    )


def notify_and_label(result, gmail_client, notifier, message_id, simulate=False, rfc822_msgid=None, tracker=None):
    if result.get('job_related') is not True:
        print(f"Email {message_id} is not job-related. Applying label and skipping.")
    else:
        resultado = result.get('resultado')
        # Notion first, so the message can say what happened there. Never raises.
        notion_line = tracker.update(result, message_id=message_id) if tracker and resultado in ('rejeitado', 'avancou') else None

        if resultado == 'rejeitado':
            send_status_notification(
                notifier,
                "❌ Reprovação",
                result,
                message_id,
                rfc822_msgid,
                notion_line,
            )
        elif resultado == 'avancou':
            send_status_notification(
                notifier,
                "✅ Você avançou de etapa",
                result,
                message_id,
                rfc822_msgid,
                notion_line,
            )
        else:
            print(f"Email {message_id} resultado is '{resultado}'. No notification sent.")

    if not simulate:
        gmail_client.apply_label(message_id, 'jobbot-processado')
    else:
        print("Simulating applying 'jobbot-processado' label.")


def process_batch(batch, gmail_client, llm_handler, notifier, simulate=False, tracker=None):
    results = llm_handler.classify_batch(batch)
    for email in batch:
        result = results.get(email['id'])
        if result is None:
            print(f"Email {email['id']} missing from batch response, leaving unlabeled for retry.")
            continue
        if result.get('invalid'):
            if not simulate:
                try:
                    gmail_client.apply_label(email['id'], REVIEW_LABEL)
                except ValueError:
                    print(f"Label {REVIEW_LABEL} missing in Gmail; create it to see these e-mails.")
                gmail_client.apply_label(email['id'], 'jobbot-processado')
            print(f"Email {email['id']} labeled {REVIEW_LABEL}; no notification, no retry.")
            continue
        try:
            notify_and_label(result, gmail_client, notifier, email['id'],
                             simulate=simulate, rfc822_msgid=email.get('rfc822_msgid'), tracker=tracker)
        except Exception:
            # Isolate delivery/label failures; later emails still need processing.
            # Exception text can contain credential-bearing request URLs.
            print(f"Email {email['id']} failed during delivery or labeling; will retry.")


def chunk(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def main():
    parser = argparse.ArgumentParser(description='Job Status Bot')
    parser.add_argument('--local-email', type=str, help='Path to a local email file for testing.')
    parser.add_argument('--resend-rfc822-msgid', type=str, help='Resend notification for a specific Gmail RFC822 Message-ID.')
    args = parser.parse_args()

    if args.local_email:
        print(f"Running in local mode with email file: {args.local_email}")
        with open(args.local_email, 'r') as f:
            content = f.read()

        lines = content.split('\n')
        sender = ''
        subject = ''
        for line in lines:
            if line.lower().startswith('from:'):
                sender = line[5:].strip()
            elif line.lower().startswith('subject:'):
                subject = line[8:].strip()

        body_start = 0
        for i, line in enumerate(lines):
            if line.strip() == '' and i > 0:
                body_start = i + 1
                break
        body = '\n'.join(lines[body_start:]) if body_start else content

        llm_handler = LLMHandler()
        notifier = Notifier()

        result = llm_handler.extract_info(body)
        notify_and_label(result, None, notifier, 'local', simulate=True)

        print("Local test complete.")
    else:
        print("Running in live mode.")
        gmail_client = GmailClient()
        llm_handler = LLMHandler()
        notifier = Notifier()
        tracker = NotionTracker()
        print(f"Notion tracker {'enabled' if tracker.enabled else 'disabled (no NOTION_TOKEN/NOTION_DATA_SOURCE_ID)'}.")

        if args.resend_rfc822_msgid:
            email = gmail_client.get_email_by_rfc822_msgid(args.resend_rfc822_msgid)
            if not email:
                raise SystemExit(f"Email with RFC822 Message-ID {args.resend_rfc822_msgid!r} not found.")
            print(f"Resending notification for email {email['id']}.")
            # Resend is a preview: never write to Notion again.
            process_batch([email], gmail_client, llm_handler, notifier, simulate=True)
            return

        emails = gmail_client.get_new_emails()
        print(f"Found {len(emails)} new email(s).")

        to_classify = []
        for email in emails:
            if is_excluded(email.get('sender', '')):
                print(f"Email {email.get('id', '')} from excluded sender. Applying label and skipping.")
                gmail_client.apply_label(email.get('id', ''), 'jobbot-processado')
            else:
                to_classify.append(email)

        for batch in chunk(to_classify, BATCH_SIZE):
            try:
                process_batch(batch, gmail_client, llm_handler, notifier, tracker=tracker)
            except Exception as e:
                ids = [e_.get('id', '') for e_ in batch]
                print(f"Error processing batch {ids}: {e}. Leaving unlabeled for retry next run.")

if __name__ == '__main__':
    main()
