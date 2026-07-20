import base64
import re
from html.parser import HTMLParser
from googleapiclient.discovery import build
from src.utils.auth import get_credentials

_URL_RE = re.compile(r'https?://\S+')
_TEMPLATE_RE = re.compile(r'email_[a-zA-Z0-9_]+')

def _content_length(text):
    """Length of the text with URLs stripped — long footers are mostly
    tracking links, so raw length alone can't tell real content from
    boilerplate."""
    return len(_URL_RE.sub('', text))

class _HTMLTextExtractor(HTMLParser):
    _SKIP_TAGS = {'script', 'style', 'head'}
    _BLOCK_TAGS = {'p', 'div', 'br', 'tr', 'li', 'h1', 'h2', 'h3', 'h4', 'h5', 'h6'}

    def __init__(self):
        super().__init__()
        self._chunks = []
        self._skip_depth = 0

    def handle_starttag(self, tag, attrs):
        if tag in self._SKIP_TAGS:
            self._skip_depth += 1
        elif tag in self._BLOCK_TAGS:
            self._chunks.append('\n')

    def handle_endtag(self, tag):
        if tag in self._SKIP_TAGS:
            self._skip_depth = max(0, self._skip_depth - 1)

    def handle_data(self, data):
        if self._skip_depth == 0:
            self._chunks.append(data)

    def text(self):
        return '\n'.join(line.strip() for line in ''.join(self._chunks).splitlines() if line.strip())


def html_to_text(html):
    parser = _HTMLTextExtractor()
    parser.feed(html)
    return parser.text()


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

        return [self._email_data_from_message(message) for message in messages]

    def get_email_by_rfc822_msgid(self, rfc822_msgid):
        clean_msgid = rfc822_msgid.strip().strip('<>')
        messages = self.service.users().messages().list(
            userId='me', q=f'rfc822msgid:{clean_msgid}'
        ).execute().get('messages', [])
        if not messages:
            return None
        return self._email_data_from_message(messages[0])

    def _email_data_from_message(self, message):
        msg = self.service.users().messages().get(userId='me', id=message['id']).execute()
        payload = msg['payload']
        email_data = {
            'id': msg.get('id', message['id']),
            'thread_id': msg.get('threadId', message.get('threadId', message['id'])),
        }
        for header in payload['headers']:
            if header['name'] == 'Subject':
                email_data['subject'] = header['value']
            if header['name'] == 'From':
                email_data['sender'] = header['value']
            if header['name'] == 'List-Unsubscribe':
                match = _TEMPLATE_RE.search(header['value'])
                if match:
                    email_data['template_hint'] = match.group(0)

        email_data['body'] = self._extract_body(payload)
        return email_data

    def _extract_body(self, payload):
        parts_by_type = {}
        self._collect_parts(payload, parts_by_type)

        plain = parts_by_type.get('text/plain', '')
        html = parts_by_type.get('text/html')
        html_text = html_to_text(html) if html else ''

        # Pick whichever alternative has more actual content once tracking
        # URLs are stripped out — a plaintext part that's mostly footer
        # links can still be longer in raw characters than the real
        # message, so length alone isn't a reliable signal.
        if _content_length(html_text) > _content_length(plain):
            return html_text
        return plain

    def _collect_parts(self, payload, parts_by_type):
        mime_type = payload.get('mimeType', '')
        data = payload.get('body', {}).get('data')
        if data and mime_type in ('text/plain', 'text/html') and mime_type not in parts_by_type:
            parts_by_type[mime_type] = base64.urlsafe_b64decode(data).decode('utf-8', errors='replace')
        for part in payload.get('parts', []):
            self._collect_parts(part, parts_by_type)

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
