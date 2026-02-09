#!/usr/bin/env python3
"""
Helper script to generate password hash for Streamlit app authentication
"""
import hashlib
import sys

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

if __name__ == "__main__":
    if len(sys.argv) > 1:
        password = sys.argv[1]
    else:
        password = input("Enter password: ")

    hashed = hash_password(password)
    print(f"\nPassword hash:")
    print(hashed)
    print(f"\nAdd this to your .streamlit/secrets.toml:")
    print(f'app_password_hash = "{hashed}"')
