import argparse
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


def is_excluded(sender):
    sender_lower = sender.lower()
    return any(addr in sender_lower for addr in EXCLUDED_SENDERS)


def notify_and_label(result, gmail_client, notifier, message_id, simulate=False, rfc822_msgid=None):
    if not result.get('job_related'):
        print(f"Email {message_id} is not job-related. Applying label and skipping.")
    else:
        resultado = result.get('resultado')
        empresa = result.get('empresa', 'Unknown')
        cargo = result.get('cargo', 'Unknown')
        # Gmail's API message id isn't the id its own web UI uses in links —
        # linking by the email's RFC822 Message-ID via rfc822msgid: search
        # is what actually resolves. Using the account's email address
        # instead of a positional /u/N/ index too, since that index depends
        # on login order in the browser and varies by device/session.
        if rfc822_msgid:
            email_link = f"https://mail.google.com/mail/u/pedrolucazxmesquita@gmail.com/#search/rfc822msgid:{rfc822_msgid}"
        else:
            email_link = f"https://mail.google.com/mail/u/pedrolucazxmesquita@gmail.com/#all/{message_id}"

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
        notify_and_label(result, gmail_client, notifier, email['id'], simulate=simulate, rfc822_msgid=email.get('rfc822_msgid'))


def chunk(items, size):
    for i in range(0, len(items), size):
        yield items[i:i + size]


def main():
    parser = argparse.ArgumentParser(description='Job Status Bot')
    parser.add_argument('--local-email', type=str, help='Path to a local email file for testing.')
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
