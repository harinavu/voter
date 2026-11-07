#!/usr/bin/env python3
"""
change_password.py
──────────────────
Run this script to generate a new password hash.
Then paste the hash into auth.js → AUTH_PASSWORD_HASH.

Usage:
    python3 change_password.py
"""
import hashlib
import getpass

print("═" * 50)
print("  Sakhavaram Voter Search — Change Password")
print("═" * 50)
print()

password = getpass.getpass("Enter new password: ")
confirm  = getpass.getpass("Confirm new password: ")

if password != confirm:
    print("\n❌  Passwords do not match. Try again.")
    raise SystemExit(1)

if len(password) < 6:
    print("\n❌  Password must be at least 6 characters.")
    raise SystemExit(1)

hash_hex = hashlib.sha256(password.encode()).hexdigest()

print()
print("✅  New password hash generated!")
print()
print("  Copy this hash and paste it into auth.js")
print("  Replace the value of: AUTH_PASSWORD_HASH")
print()
print(f"  AUTH_PASSWORD_HASH = '{hash_hex}'")
print()
print("  Then commit and push auth.js to GitHub.")
print()
