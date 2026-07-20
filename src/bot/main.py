import argparse
from urllib.parse import quote
from dotenv import load_dotenv
from src.bot.gmail_client import GmailClient
from src.bot.llm_handler import LLMHandler
from src.bot.notifier import Notifier

load_dotenv()

# Senders that are pure noise (no application ever involved) — kept as a
# small, stable optimization to skip them for free. Relevance for
# everything else is judged by the LLM itself, not a keyword/domain list,
# so this never needs updating for a new ATS or a foreign-language email.
EXCLUDED_SENDERS = [
    "jobalerts-noreply@linkedin.com",
    "avisovagas@catho.com.br",
]

BATCH_SIZE = 10
GMAIL_ACCOUNT = "pedrolucazxmesquita@gmail.com"


def is_excluded(sender):
    sender_lower = sender.lower()
    return any(addr in sender_lower for addr in EXCLUDED_SENDERS)


def build_gmail_link(message_id, thread_id=None):
    conversation_id = thread_id or message_id
    account = quote(GMAIL_ACCOUNT, safe='')
    return f"https://mail.google.com/mail/?authuser={account}#all/{quote(conversation_id, safe='')}"


def notify_and_label(result, gmail_client, notifier, message_id, simulate=False, thread_id=None):
    if not result.get('job_related'):
        print(f"Email {message_id} is not job-related. Applying label and skipping.")
    else:
        resultado = result.get('resultado')
        empresa = result.get('empresa', 'Unknown')
        cargo = result.get('cargo', 'Unknown')
        email_link = build_gmail_link(message_id, thread_id)

        if resultado == 'rejeitado':
            message = f"❌ Rejeitado — {empresa} ({cargo})\n{email_link}"
            print(f"Sending notification to Telegram: {message}")
            notifier.send_message(message)
        elif resultado == 'avancou':
            message = f"✅ Avançou de etapa — {empresa} ({cargo})\n{email_link}"
            print(f"Sending notification to Telegram: {message}")
            notifier.send_message(message)
        else:
            print(f"Email {message_id} resultado is '{resultado}'. No notification sent.")

    if not simulate:
        gmail_client.apply_label(message_id, 'jobbot-processado')
    else:
        print("Simulating applying 'jobbot-processado' label.")


def process_batch(batch, gmail_client, llm_handler, notifier, simulate=False):
    results = llm_handler.classify_batch(batch)
    for email in batch:
        result = results.get(email['id'])
        if result is None:
            print(f"Email {email['id']} missing from batch response, leaving unlabeled for retry.")
            continue
        notify_and_label(result, gmail_client, notifier, email['id'], simulate=simulate, thread_id=email.get('thread_id'))


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

        if args.resend_rfc822_msgid:
            email = gmail_client.get_email_by_rfc822_msgid(args.resend_rfc822_msgid)
            if not email:
                raise SystemExit(f"Email with RFC822 Message-ID {args.resend_rfc822_msgid!r} not found.")
            print(f"Resending notification for email {email['id']}.")
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
                process_batch(batch, gmail_client, llm_handler, notifier)
            except Exception as e:
                ids = [e_.get('id', '') for e_ in batch]
                print(f"Error processing batch {ids}: {e}. Leaving unlabeled for retry next run.")

if __name__ == '__main__':
    main()
