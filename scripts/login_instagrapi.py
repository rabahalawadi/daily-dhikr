"""
Interactive Login Script for Instagram via instagrapi.
Logs in, prompts for 2FA/verification code if requested by Instagram,
and saves session.json for automated publishing.
"""

import getpass
import json
import os
import sys
from pathlib import Path

# Ensure UTF-8 stdout
if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.config import settings
from instagrapi import Client
from instagrapi.exceptions import (
    BadPassword,
    TwoFactorRequired,
    ChallengeRequired,
    PleaseWaitFewMinutes,
)


def login_flow():
    print("=" * 70)
    print("  INSTAGRAM DIRECT LOGIN SETUP (instagrapi)")
    print("=" * 70)
    print("This will authenticate your Instagram account on your local machine")
    print("and create a session.json file so future posts publish without passwords.\n")

    cl = Client()
    cl.delay_range = [2, 4]

    # Bypass timeline feed simulation which often triggers Instagram 500 error on new sessions
    cl.login_flow = lambda: True

    session_file = Path(settings.INSTAGRAM_SESSION_PATH)

    # Check existing session
    if session_file.exists():
        print(f"Found existing session file: {session_file}")
        try:
            cl.load_settings(str(session_file))
            if cl.user_id:
                print("Verifying saved session...")
                user_info = cl.user_info(cl.user_id)
                print(f"\n[SUCCESS] Already logged in as: @{user_info.username} ({user_info.full_name})")
                choice = input("\nDo you want to re-authenticate with another account? (y/N): ").strip().lower()
                if choice != "y":
                    return
        except Exception as e:
            print(f"Existing session invalid or expired: {e}. Proceeding with fresh login.")

    # Get credentials
    username = settings.INSTAGRAM_USERNAME
    if not username:
        username = input("Enter your Instagram username: ").strip()

    password = settings.INSTAGRAM_PASSWORD
    if not password:
        password = getpass.getpass("Enter your Instagram password: ")

    print(f"\nAttempting login for @{username}...")

    try:
        cl.login(username, password)
    except TwoFactorRequired:
        print("\n[Two-Factor Authentication Detected]")
        code = input("Enter the 2FA code sent to your phone/authenticator app: ").strip()
        cl.login(username, password, verification_code=code)
    except ChallengeRequired:
        print("\n[Security Challenge Required by Instagram]")
        choice = input("Send verification code via (1) SMS or (2) Email? [1/2]: ").strip()
        choice_type = 0 if choice == "1" else 1
        cl.challenge_resolve(cl.last_json, choice=choice_type)
        code = input("Enter the security code you received: ").strip()
        cl.challenge_code_handler(code)
    except BadPassword:
        print("\n[ERROR] Incorrect password. Please check your credentials.")
        sys.exit(1)
    except PleaseWaitFewMinutes:
        print("\n[WARNING] Instagram rate limited this attempt. Please wait a few minutes before trying again.")
        sys.exit(1)
    except Exception as e:
        if cl.user_id:
            print(f"\n[INFO] Primary authentication succeeded (user_id: {cl.user_id}). Post-login check notice: {e}")
        else:
            print(f"\n[ERROR] Login failed: {e}")
            sys.exit(1)

    # Save session
    cl.dump_settings(str(session_file))
    print(f"\n[SUCCESS] Login verified! Session saved to: {session_file.resolve()}")

    user_info = cl.user_info(cl.user_id)
    print(f"Logged in account: @{user_info.username} ({user_info.full_name})")

    # Read serialized session for GitHub Actions instructions
    with open(session_file, "r", encoding="utf-8") as f:
        session_json_str = f.read()

    print("\n" + "=" * 70)
    print("GITHUB ACTIONS SECRET SETUP (OPTIONAL - FOR CLOUD AUTOMATION)")
    print("=" * 70)
    print("If you run the daily automation on GitHub Actions:")
    print("1. Go to: https://github.com/rabahalawadi/daily-dhikr/settings/secrets/actions")
    print("2. Add a new repository secret:")
    print("   Name:  INSTAGRAM_SESSION_DATA")
    print("   Value: (Paste the contents of your session.json file)")
    print("=" * 70)


if __name__ == "__main__":
    login_flow()
