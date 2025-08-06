#!/usr/bin/env python3
"""
Email list management script for newsletter functionality.
Encrypts and decrypts the email subscriber list.
"""

import os
import sys
import json
import argparse
import subprocess
import getpass
from pathlib import Path
from typing import List, Dict


def encrypt_email_list(email_list_path: str, output_path: str, passphrase: str):
    """Encrypt the email list file using GPG."""
    if not os.path.exists(email_list_path):
        print(f"Error: Email list file {email_list_path} not found.")
        sys.exit(1)
    
    try:
        cmd = [
            'gpg', '--batch', '--yes', '--passphrase', passphrase,
            '--symmetric', '--cipher-algo', 'AES256',
            '--output', output_path, email_list_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"Email list encrypted successfully to {output_path}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error encrypting file: {e}")
        print(f"GPG stderr: {e.stderr.decode() if e.stderr else 'No error output'}")
        sys.exit(1)


def decrypt_email_list(encrypted_path: str, output_path: str, passphrase: str):
    """Decrypt the email list file using GPG."""
    if not os.path.exists(encrypted_path):
        print(f"Error: Encrypted file {encrypted_path} not found.")
        sys.exit(1)
    
    try:
        cmd = [
            'gpg', '--batch', '--yes', '--passphrase', passphrase,
            '--decrypt', '--output', output_path, encrypted_path
        ]
        
        subprocess.run(cmd, check=True, capture_output=True)
        print(f"Email list decrypted successfully to {output_path}")
        
    except subprocess.CalledProcessError as e:
        print(f"Error decrypting file: {e}")
        print(f"GPG stderr: {e.stderr.decode() if e.stderr else 'No error output'}")
        sys.exit(1)


def add_subscriber(email_list_path: str, email: str, name: str = None):
    """Add a new subscriber to the email list."""
    subscribers = []
    
    # Load existing list if it exists
    if os.path.exists(email_list_path):
        with open(email_list_path, 'r') as f:
            try:
                subscribers = json.load(f)
            except json.JSONDecodeError:
                print("Warning: Invalid JSON in email list, starting fresh.")
                subscribers = []
    
    # Check if email already exists
    for subscriber in subscribers:
        if subscriber.get('email', '').lower() == email.lower():
            print(f"Email {email} already exists in the list.")
            return
    
    # Add new subscriber
    new_subscriber = {'email': email}
    if name:
        new_subscriber['name'] = name
    
    subscribers.append(new_subscriber)
    
    # Save updated list
    with open(email_list_path, 'w') as f:
        json.dump(subscribers, f, indent=2)
    
    print(f"Added {email} to the email list.")


def remove_subscriber(email_list_path: str, email: str):
    """Remove a subscriber from the email list."""
    if not os.path.exists(email_list_path):
        print(f"Email list file {email_list_path} not found.")
        return
    
    with open(email_list_path, 'r') as f:
        try:
            subscribers = json.load(f)
        except json.JSONDecodeError:
            print("Error: Invalid JSON in email list.")
            return
    
    # Find and remove subscriber
    original_count = len(subscribers)
    subscribers = [s for s in subscribers if s.get('email', '').lower() != email.lower()]
    
    if len(subscribers) == original_count:
        print(f"Email {email} not found in the list.")
        return
    
    # Save updated list
    with open(email_list_path, 'w') as f:
        json.dump(subscribers, f, indent=2)
    
    print(f"Removed {email} from the email list.")


def list_subscribers(email_list_path: str):
    """List all subscribers in the email list."""
    if not os.path.exists(email_list_path):
        print(f"Email list file {email_list_path} not found.")
        return
    
    with open(email_list_path, 'r') as f:
        try:
            subscribers = json.load(f)
        except json.JSONDecodeError:
            print("Error: Invalid JSON in email list.")
            return
    
    if not subscribers:
        print("No subscribers found.")
        return
    
    print(f"Total subscribers: {len(subscribers)}")
    print("=" * 40)
    
    for i, subscriber in enumerate(subscribers, 1):
        email = subscriber.get('email', 'No email')
        name = subscriber.get('name', '')
        if name:
            print(f"{i}. {email} ({name})")
        else:
            print(f"{i}. {email}")


def create_sample_list(email_list_path: str):
    """Create a sample email list file."""
    sample_data = [
        {
            "email": "subscriber1@example.com",
            "name": "John Doe"
        },
        {
            "email": "subscriber2@example.com", 
            "name": "Jane Smith"
        }
    ]
    
    with open(email_list_path, 'w') as f:
        json.dump(sample_data, f, indent=2)
    
    print(f"Created sample email list at {email_list_path}")
    print("Please replace with your actual subscriber data.")


def main():
    parser = argparse.ArgumentParser(description='Manage encrypted email subscriber list')
    parser.add_argument('--email-list', default='email_list.json', help='Path to email list JSON file')
    parser.add_argument('--encrypted-file', default='.github/email_list.gpg', help='Path to encrypted file')
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Encrypt command
    encrypt_parser = subparsers.add_parser('encrypt', help='Encrypt the email list')
    
    # Decrypt command  
    decrypt_parser = subparsers.add_parser('decrypt', help='Decrypt the email list')
    
    # Add subscriber command
    add_parser = subparsers.add_parser('add', help='Add a subscriber')
    add_parser.add_argument('email', help='Email address to add')
    add_parser.add_argument('--name', help='Subscriber name (optional)')
    
    # Remove subscriber command
    remove_parser = subparsers.add_parser('remove', help='Remove a subscriber')
    remove_parser.add_argument('email', help='Email address to remove')
    
    # List subscribers command
    list_parser = subparsers.add_parser('list', help='List all subscribers')
    
    # Create sample command
    sample_parser = subparsers.add_parser('sample', help='Create a sample email list')
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    if args.command == 'encrypt':
        passphrase = getpass.getpass("Enter passphrase for encryption: ")
        encrypt_email_list(args.email_list, args.encrypted_file, passphrase)
        
    elif args.command == 'decrypt':
        passphrase = getpass.getpass("Enter passphrase for decryption: ")
        decrypt_email_list(args.encrypted_file, args.email_list, passphrase)
        
    elif args.command == 'add':
        add_subscriber(args.email_list, args.email, args.name)
        
    elif args.command == 'remove':
        remove_subscriber(args.email_list, args.email)
        
    elif args.command == 'list':
        list_subscribers(args.email_list)
        
    elif args.command == 'sample':
        create_sample_list(args.email_list)


if __name__ == "__main__":
    main()