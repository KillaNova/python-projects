"""
Email Auto-Responder / Filter
Connects via IMAP (read) + SMTP (send).
Configure credentials and rules in config.json (see config.example.json).

Usage:
  python main.py --run          # process inbox once
  python main.py --run --loop   # check every N seconds (set in config)
  python main.py --list-rules   # show active rules
"""

import argparse
import email
import imaplib
import json
import os
import smtplib
import time
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from pathlib import Path

CONFIG_PATH = Path(__file__).parent / "config.json"
EXAMPLE_CONFIG = {
    "imap": {
        "host": "imap.gmail.com",
        "port": 993,
        "username": "you@gmail.com",
        "password": "your-app-password"
    },
    "smtp": {
        "host": "smtp.gmail.com",
        "port": 587,
        "username": "you@gmail.com",
        "password": "your-app-password"
    },
    "check_interval_seconds": 60,
    "rules": [
        {
            "name": "Vacation reply",
            "match": {"subject_contains": ["vacation", "out of office"]},
            "action": "reply",
            "reply_body": "Thanks for reaching out! I'm currently out of office and will reply soon."
        },
        {
            "name": "Spam filter",
            "match": {"from_contains": ["noreply@spam.example.com"]},
            "action": "move",
            "target_folder": "Junk"
        },
        {
            "name": "Label newsletters",
            "match": {"subject_contains": ["newsletter", "unsubscribe"]},
            "action": "label",
            "label": "Newsletters"
        }
    ]
}


def load_config() -> dict:
    if not CONFIG_PATH.exists():
        example_path = CONFIG_PATH.parent / "config.example.json"
        with open(example_path, "w") as f:
            json.dump(EXAMPLE_CONFIG, f, indent=2)
        raise FileNotFoundError(
            f"config.json not found. A template was written to {example_path}.\n"
            "Fill in your credentials and rename it to config.json."
        )
    with open(CONFIG_PATH) as f:
        return json.load(f)


def matches_rule(msg: email.message.Message, rule: dict) -> bool:
    conditions = rule.get("match", {})
    subject = (msg.get("Subject") or "").lower()
    sender = (msg.get("From") or "").lower()

    if "subject_contains" in conditions:
        if not any(kw.lower() in subject for kw in conditions["subject_contains"]):
            return False
    if "from_contains" in conditions:
        if not any(kw.lower() in sender for kw in conditions["from_contains"]):
            return False
    return True


def send_reply(smtp_cfg: dict, original: email.message.Message, body: str) -> None:
    reply_to = original.get("Reply-To") or original.get("From")
    subject = "Re: " + (original.get("Subject") or "")

    msg = MIMEMultipart()
    msg["From"] = smtp_cfg["username"]
    msg["To"] = reply_to
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "plain"))

    with smtplib.SMTP(smtp_cfg["host"], smtp_cfg["port"]) as server:
        server.starttls()
        server.login(smtp_cfg["username"], smtp_cfg["password"])
        server.sendmail(smtp_cfg["username"], reply_to, msg.as_string())

    print(f"  [REPLY] Sent to {reply_to}")


def process_inbox(config: dict) -> None:
    imap_cfg = config["imap"]
    smtp_cfg = config["smtp"]
    rules = config.get("rules", [])
    replied_ids: set[str] = set()

    with imaplib.IMAP4_SSL(imap_cfg["host"], imap_cfg["port"]) as imap:
        imap.login(imap_cfg["username"], imap_cfg["password"])
        imap.select("INBOX")

        _, data = imap.search(None, "UNSEEN")
        uids = data[0].split()
        print(f"[{datetime.now():%H:%M:%S}] Found {len(uids)} unread message(s).")

        for uid in uids:
            _, raw = imap.fetch(uid, "(RFC822)")
            msg = email.message_from_bytes(raw[0][1])
            msg_id = msg.get("Message-ID", uid.decode())
            subject = msg.get("Subject", "(no subject)")
            sender = msg.get("From", "unknown")
            print(f"\n  From: {sender}\n  Subject: {subject}")

            for rule in rules:
                if not matches_rule(msg, rule):
                    continue

                action = rule["action"]
                print(f"  Rule matched: '{rule['name']}' → action={action}")

                if action == "reply" and msg_id not in replied_ids:
                    try:
                        send_reply(smtp_cfg, msg, rule["reply_body"])
                        replied_ids.add(msg_id)
                    except Exception as e:
                        print(f"  [ERROR] Reply failed: {e}")

                elif action == "move":
                    folder = rule.get("target_folder", "Junk")
                    imap.copy(uid, folder)
                    imap.store(uid, "+FLAGS", "\\Deleted")
                    print(f"  [MOVE] → {folder}")

                elif action == "label":
                    label = rule.get("label", "AutoLabel")
                    # Gmail uses IMAP flags via X-GM-LABELS; for standard IMAP create folder
                    try:
                        imap.create(label)
                    except Exception:
                        pass
                    imap.copy(uid, label)
                    print(f"  [LABEL] → {label}")

        imap.expunge()


def main():
    parser = argparse.ArgumentParser(description="Email auto-responder and filter")
    parser.add_argument("--run", action="store_true", help="Process inbox")
    parser.add_argument("--loop", action="store_true", help="Keep running on interval")
    parser.add_argument("--list-rules", action="store_true", help="Print active rules")
    args = parser.parse_args()

    try:
        config = load_config()
    except FileNotFoundError as e:
        print(e)
        return

    if args.list_rules:
        rules = config.get("rules", [])
        print(f"{len(rules)} rule(s) configured:")
        for i, r in enumerate(rules, 1):
            print(f"  {i}. [{r['action'].upper()}] {r['name']} — match: {r['match']}")
        return

    if args.run:
        if args.loop:
            interval = config.get("check_interval_seconds", 60)
            print(f"Looping every {interval}s. Ctrl+C to stop.")
            while True:
                try:
                    process_inbox(config)
                except Exception as e:
                    print(f"[ERROR] {e}")
                time.sleep(interval)
        else:
            try:
                process_inbox(config)
            except Exception as e:
                print(f"[ERROR] {e}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
