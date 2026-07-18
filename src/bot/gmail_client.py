from googleapiclient.discovery import build
from src.utils.auth import get_credentials

class GmailClient:
    def __init__(self):
        self.creds = get_credentials()
        self.service = build('gmail', 'v1', credentials=self.creds)

    def get_new_emails(self):
        label_id = self._get_label_id('jobbot-processado')
        if not label_id:
            raise ValueError("Label 'jobbot-processado' not found.")

        # Recent mail first, so new applications aren't stuck behind an
        # old backlog while it's still draining under the LLM rate limit.
        recent = self.service.users().messages().list(
            userId='me', q='-label:jobbot-processado newer_than:2d'
        ).execute().get('messages', [])
        backlog = self.service.users().messages().list(
            userId='me', q='-label:jobbot-processado'
        ).execute().get('messages', [])

        seen = set()
        messages = []
        for m in recent + backlog:
            if m['id'] not in seen:
                seen.add(m['id'])
                messages.append(m)
        
        emails = []
        for message in messages:
            msg = self.service.users().messages().get(userId='me', id=message['id']).execute()
            email_data = {'id': message['id']}
            headers = msg['payload']['headers']
            for header in headers:
                if header['name'] == 'Subject':
                    email_data['subject'] = header['value']
                if header['name'] == 'From':
                    email_data['sender'] = header['value']
            
            if 'parts' in msg['payload']:
                for part in msg['payload']['parts']:
                    if part['mimeType'] == 'text/plain':
                        import base64
                        email_data['body'] = base64.urlsafe_b64decode(part['body']['data']).decode('utf-8')
                        break
            else:
                 import base64
                 email_data['body'] = base64.urlsafe_b64decode(msg['payload']['body']['data']).decode('utf-8')

            emails.append(email_data)
        
        return emails

    def _get_label_id(self, label_name):
        results = self.service.users().labels().list(userId='me').execute()
        labels = results.get('labels', [])
        for label in labels:
            if label['name'] == label_name:
                return label['id']
        return None


    def apply_label(self, message_id, label_name):
        label_id = self._get_label_id(label_name)
        if not label_id:
            raise ValueError(f"Label '{label_name}' not found.")

        body = {
            'addLabelIds': [label_id],
            'removeLabelIds': []
        }
        self.service.users().messages().modify(userId='me', id=message_id, body=body).execute()
