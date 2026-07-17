import argparse
import json
import os
import base64
from dotenv import load_dotenv
from src.bot.gmail_client import GmailClient
from src.bot.llm_handler import LLMHandler
from src.bot.notifier import Notifier

load_dotenv()

def process_email(email_body, sender, subject, gmail_client, llm_handler, notifier, message_id, simulate=False):
    ats_domains = load_ats_domains()
    keywords = ["processo seletivo", "sua candidatura", "feedback", "retorno sobre a vaga"]

    sender_domain = sender.split('@')[-1].lower() if '@' in sender else ''
    matches_ats = any(domain in sender_domain for domain in ats_domains)
    matches_keyword = any(kw in subject.lower() for kw in keywords)

    if not matches_ats and not matches_keyword:
        print(f"Email {message_id} does not match cheap filter. Applying label and skipping.")
        if not simulate:
            gmail_client.apply_label(message_id, 'jobbot-processado')
        else:
            print("Simulating applying 'jobbot-processado' label.")
        return

    extracted = llm_handler.extract_info(email_body)

    if not extracted.get('job_related'):
        print(f"Email {message_id} is not job-related. Applying label and skipping.")
        if not simulate:
            gmail_client.apply_label(message_id, 'jobbot-processado')
        else:
            print("Simulating applying 'jobbot-processado' label.")
        return

    resultado = extracted.get('resultado')
    empresa = extracted.get('empresa', 'Unknown')
    cargo = extracted.get('cargo', 'Unknown')

    if resultado == 'rejeitado':
        message = f"❌ Rejeitado — {empresa} ({cargo})"
        print(f"Sending notification to Telegram: {message}")
        notifier.send_message(message)
    elif resultado == 'avancou':
        message = f"✅ Avançou de etapa — {empresa} ({cargo})"
        print(f"Sending notification to Telegram: {message}")
        notifier.send_message(message)
    else:
        print(f"Email {message_id} resultado is '{resultado}'. No notification sent.")

    if not simulate:
        gmail_client.apply_label(message_id, 'jobbot-processado')
    else:
        print("Simulating applying 'jobbot-processado' label.")

def load_ats_domains():
    path = os.path.join(os.path.dirname(__file__), '..', 'config', 'ats_domains.txt')
    with open(path, 'r') as f:
        return [line.strip() for line in f if line.strip()]

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

        process_email(body, sender, subject, None, llm_handler, notifier, 'local', simulate=True)

        print("Local test complete.")
    else:
        print("Running in live mode.")
        gmail_client = GmailClient()
        llm_handler = LLMHandler()
        notifier = Notifier()

        emails = gmail_client.get_new_emails()
        print(f"Found {len(emails)} new email(s).")

        for email in emails:
            process_email(
                email.get('body', ''),
                email.get('sender', ''),
                email.get('subject', ''),
                gmail_client,
                llm_handler,
                notifier,
                email.get('id', '')
            )

if __name__ == '__main__':
    main()
