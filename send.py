import argparse
import base64
from datetime import datetime, timedelta
from email.message import EmailMessage
from pathlib import Path

from jinja2 import Template

from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

import db

TEMPLATES = {
    0: Path('templates/initial_email.txt'),
    1: Path('templates/followup_1.txt'),
    2: Path('templates/followup_2.txt'),
}

SUBJECTS = {
    0: 'Initial Email',
    1: 'Follow-up #1',
    2: 'Follow-up #2',
}

FOLLOWUP_DELAYS = {
    1: timedelta(days=3),
    2: timedelta(days=7),
}

SCOPES = ['https://www.googleapis.com/auth/gmail.send']
API_CREDENTIALS_PATH = Path('credentials/credentials.json')
TOKEN_PATH = Path('credentials/token.json')


def render_template(path, context):
    text = path.read_text()
    return Template(text).render(**context)


def get_gmail_service():
    creds = None
    if TOKEN_PATH.exists():
        creds = Credentials.from_authorized_user_file(TOKEN_PATH, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(
                API_CREDENTIALS_PATH, SCOPES
            )
            creds = flow.run_local_server(port=0)
        TOKEN_PATH.write_text(creds.to_json())
    return build('gmail', 'v1', credentials=creds)


def send_email(to_email, subject, body, service=None):
    if service is None:
        service = get_gmail_service()

    message = EmailMessage()
    message['To'] = to_email
    message['From'] = 'me'
    message['Subject'] = subject
    message.set_content(body)

    encoded = base64.urlsafe_b64encode(message.as_bytes()).decode()

    try:
        service.users().messages().send(
            userId='me', body={'raw': encoded}
        ).execute()
    except HttpError as error:
        raise RuntimeError(f'API error: {error}')


def send_step(step, dry_run=False):
    contacts = db.get_contacts_by_step(step)
    now = datetime.utcnow()
    service = None if dry_run else get_gmail_service()
    for c in contacts:
        if step > 0 and not c['followups_enabled']:
            continue
        if step > 0 and c['last_sent']:
            last_sent = datetime.fromisoformat(c['last_sent'])
            delay = FOLLOWUP_DELAYS.get(step, timedelta())
            if now - last_sent < delay:
                continue
        context = {'name': c['name'], 'email': c['email']}
        body = render_template(TEMPLATES[step], context)
        if dry_run:
            print(f"[DRY RUN] Would send step {step} to {c['email']}")
            continue
        try:
            send_email(c['email'], SUBJECTS[step], body, service)
            db.log_email(c['id'], TEMPLATES[step].name, 'sent')
            db.update_contact_step(c['id'], step + 1)
            print(f"Sent step {step} to {c['email']}")
        except Exception as e:
            db.log_email(c['id'], TEMPLATES[step].name, f'error:{e}')
            print(f"Error sending to {c['email']}: {e}")


def main():
    parser = argparse.ArgumentParser(description='Email automation CLI')
    parser.add_argument('--import', dest='import_file', help='Import contacts CSV')
    parser.add_argument('--send', action='store_true', help='Send emails')
    parser.add_argument('--step', type=int, help='Which step to send')
    parser.add_argument('--dry-run', action='store_true', help='Dry run')
    parser.add_argument('--toggle-followup', action='store_true', help='Toggle followups for a contact')
    parser.add_argument('--email', help='Email address for toggle')
    parser.add_argument('--on', action='store_true', help='Enable followups')
    parser.add_argument('--off', action='store_true', help='Disable followups')

    args = parser.parse_args()

    db.init_db()

    if args.import_file:
        db.import_contacts(args.import_file)
        print('Contacts imported.')

    if args.toggle_followup and args.email:
        if args.on == args.off:
            parser.error('Specify --on or --off')
        db.toggle_followups(args.email, args.on)
        state = 'enabled' if args.on else 'disabled'
        print(f'Follow-ups {state} for {args.email}')

    if args.send:
        if args.step is None:
            parser.error('--step required with --send')
        send_step(args.step, dry_run=args.dry_run)


if __name__ == '__main__':
    main()
