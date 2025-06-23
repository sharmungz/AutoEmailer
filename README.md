# AutoEmailer
# Email Automation Application

This repository contains a local Python application for automating personalized email campaigns via Gmail. It provides a command‑line interface (CLI) to send initial outreach emails, schedule follow‑up messages, and track all sends and status in a local SQLite database.

---

## Features

* **One‑off email sending**: Send a templated first email to a list of contacts.
* **Automated follow‑ups**: Define multiple follow‑up drafts and delays; send them conditionally based on contact settings.
* **Toggle per‑contact**: Enable or disable follow‑up sequences on a per‑recipient basis.
* **Tracking & logging**: All sent messages (initial and follow‑ups) are recorded with timestamp and status in SQLite.
* **Dry‑run mode**: Preview which emails *would* be sent without actually transmitting.
* **Customizable templates**: Store email bodies as plain text with `{{placeholder}}` tokens.

---

## Tech Stack

* **Language**: Python 3.9+
* **Database**: SQLite (via the built‑in `sqlite3` module)
* **Templating**: [Jinja2](https://palletsprojects.com/p/jinja/) or Python’s `string.Template`
* **Email transport**:

  * Option A: Gmail SMTP (`smtplib` + App Password)
  * Option B: Gmail API (`google-api-python-client` + OAuth2)
* **CLI framework**: `argparse` (built‑in) or `click`
* **Dependencies**: Listed in `requirements.txt`

---

## Project Structure

```
email-automation/
├── send.py                   # Main CLI entry point
├── db.py                     # Database schema and helper functions
├── templates/                # Email template files
│   ├── initial_email.txt     # First outreach message
│   ├── followup_1.txt        # Follow‑up #1 message
│   └── followup_2.txt        # Follow‑up #2 message
├── email_db.sqlite           # Local SQLite database (auto‑generated)
├── credentials/              # OAuth2 tokens or App Password storage
│   └── gmail_creds.json
├── requirements.txt          # Python dependencies
└── README.md                 # This documentation
```

---

## Prerequisites

1. **Python** 3.9 or higher installed
2. **Gmail account** with one of the following:

   * App Password (recommended for simplicity)
   * OAuth2 credentials (requires Google Cloud Project setup)
3. **Access** to a terminal/console on your local machine

---

## Installation

1. Clone this repository:

   ```bash
   git clone https://github.com/<your‑username>/email-automation.git
   cd email-automation
   ```
2. Create and activate a virtual environment:

   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

---

## Configuration

### 1. Email Credentials

* **SMTP + App Password**:

  1. Enable 2‑Step Verification on your Google Account.
  2. Generate an App Password for “Mail.”
  3. Save it in `credentials/gmail_creds.json`:

     ```json
     {
       "email": "you@gmail.com",
       "app_password": "abcd efgh ijkl mnop"
     }
     ```

* **Gmail API + OAuth2** (optional):

  1. Create a Google Cloud Project with Gmail API enabled.
  2. Download `credentials.json` from OAuth2 consent setup.
  3. Place it in `credentials/` and follow the first‑run instructions in `send.py` to generate tokens.

### 2. Contact Import

Convert your contacts spreadsheet to CSV and load into the database:

```bash
python send.py --import contacts.csv
```

This will populate `contacts` table with name, email, and default settings.

---

## Usage

### Send initial emails

```bash
python send.py --send --step 0
```

Sends the first template (`initial_email.txt`) to all contacts with `step = 0`.

### Send follow‑ups

```bash
python send.py --send --step 1
python send.py --send --step 2
```

Sends follow‑up #1 or #2 to contacts whose `step` matches and whose `followups_enabled` flag is true, provided the configured delay has elapsed.

### Dry‑run

```bash
python send.py --dry-run --send --step 0
```

Prints which emails would be sent, without actually sending.

### Toggle follow‑ups

Use the CLI to enable/disable follow‑ups for a specific contact:

```bash
python send.py --toggle-followup --email alice@example.com --off
```

---

## Database Schema

* **contacts** (`id`, `name`, `email`, `followups_enabled`, `step`, `last_sent`)
* **log** (`id`, `contact_id`, `template`, `timestamp`, `status`)

---

## Contributing

Contributions welcome! Feel free to open issues or submit pull requests.

---

## License

[MIT License](LICENSE)

