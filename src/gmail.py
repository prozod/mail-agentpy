import time
import html
import base64
from bs4 import BeautifulSoup
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# delete token.json if u modify scopes
SCOPES = [
    "https://www.googleapis.com/auth/gmail.readonly",
    "https://www.googleapis.com/auth/calendar"
]
LAST_PROCESSED_MAIL_ID = None
USER_ID = 'me'
POLLING_INTERVAL_SECONDS = 10
MAX_RESULTS = 1

def find_mime_part(payload, mime_type):
    """
    search recursively the message payload for a part with the given MIME type
    and returns its body data (base64 encoded string)
    """
    if payload.get('mimeType') == mime_type and payload.get('body', {}).get('data'):
        return payload['body']['data']
    if 'parts' in payload:
        for part in payload['parts']:
            result = find_mime_part(part, mime_type)
            if result:
                return result
    return None

def get_message_body(payload):
    """
    recursively extract email body.
    returns clean plain text (stripped HTML if needed).
    prefers text/plain; if empty, falls back to text/html.
    """
    plain_text = None
    html_text = None

    def recurse(part):
        nonlocal plain_text, html_text

        mime = part.get('mimeType', '')
        body = part.get('body', {}).get('data')

        if mime == 'text/plain' and body and not plain_text:
            plain_text = body
        elif mime == 'text/html' and body and not html_text:
            html_text = body

        for sub in part.get('parts', []):
            recurse(sub)

    recurse(payload)

    data = plain_text or html_text
    if not data:
        return ""

    # fix base64 padding
    missing_padding = len(data) % 4
    if missing_padding:
        data += '=' * (4 - missing_padding)

    # decode base64
    decoded = base64.urlsafe_b64decode(data.encode('utf-8')).decode('utf-8', errors='ignore')
    decoded = html.unescape(decoded)

    # if HTML fallback, strip tags
    if not plain_text and html_text:
        decoded = BeautifulSoup(decoded, "html.parser").get_text(separator='\n')

    return decoded


def get_latest_email(service):
    """
    get the single latest message
    """
    try:
        response = service.users().messages().list(
            userId=USER_ID,
            maxResults=MAX_RESULTS,
            q="in:inbox"
            #q="in:inbox OR in:spam"
        ).execute()

        messages = response.get('messages', [])

        if not messages:
            return None, None

        latest_msg_id = messages[0]['id']
        
        # get la toate detaliile din mail (inclusiv ID)
        msg_details = service.users().messages().get(
            userId=USER_ID,
            id=latest_msg_id,
            format='full',  # full msg payload
            metadataHeaders=['Subject', 'From', 'Date']
        ).execute()

        # mail headers
        payload = msg_details['payload']
        headers = payload.get('headers', [])
        subject = next((h['value'] for h in headers if h['name'] == 'Subject'), 'No Subject')
        sender = next((h['value'] for h in headers if h['name'] == 'From'), 'Unknown Sender')
        date = next((h['value'] for h in headers if h['name'] == 'Date'), 'Unknown Date')

        # mail body
        body_content = get_message_body(payload)
        
        # categoria/labelul (INBOX or SPAM)
        labels = msg_details.get('labelIds', [])
        location = 'INBOX' #if 'INBOX' in labels else ('SPAM' if 'SPAM' in labels else 'OTHER')

        email_details = {
            'id': latest_msg_id,
            'subject': subject,
            'from': sender,
            'date': date,
            'location': location,
            'body_snippet': msg_details.get('snippet', 'No snippet available.'),
            'full_body': body_content
        }

        return latest_msg_id, email_details

    except Exception as e:
        print(f"An error occurred: {e}")
        return None, None

def start_polling(service):
    global LAST_PROCESSED_MAIL_ID
    print("-----> Polling started (INBOX) <----")

    while True:
        timestamp = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime())
        print(f"\n-----> Checking Gmail at: {timestamp}...")

        latest_id, latest_email_details = get_latest_email(service)

        if latest_id is None:
            print("Mailbox empty sau avem eroare.")

        elif latest_id != LAST_PROCESSED_MAIL_ID:
            print(f"-----> NEW E-MAIL DETECTED! Found in: {latest_email_details['location']}")
            LAST_PROCESSED_MAIL_ID = latest_id
            yield latest_email_details

        else:
            print("-----> No new e-mails received since the last check.")

        print(f"\n-----> Waiting for {POLLING_INTERVAL_SECONDS} seconds... ^(-_-)^")
        time.sleep(POLLING_INTERVAL_SECONDS)
