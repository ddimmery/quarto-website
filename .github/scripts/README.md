# Newsletter Scripts

This directory contains scripts for managing and sending newsletters from your Quarto blog.

## Setup

### 1. Install Dependencies

The newsletter functionality requires Python with these packages (installed automatically in the GitHub Action):
- `pyyaml`
- `beautifulsoup4` 
- `html2text`

### 2. Create Email List

Create your subscriber list:

```bash
# Create a sample email list to start with
python .github/scripts/manage_email_list.py sample

# Add subscribers manually
python .github/scripts/manage_email_list.py add subscriber@example.com --name "John Doe"
python .github/scripts/manage_email_list.py add another@example.com

# View current subscribers
python .github/scripts/manage_email_list.py list
```

### 3. Encrypt Email List

Encrypt the email list for secure storage in your repository:

```bash
# This will prompt for a passphrase - remember this!
python .github/scripts/manage_email_list.py encrypt
```

This creates `.github/email_list.gpg` which is safe to commit to your repository.

### 4. Set Up GitHub Secrets

Add these secrets to your GitHub repository (Settings > Secrets and variables > Actions):

**Email Service Settings:**
- `SMTP_SERVER`: Your SMTP server (e.g., `smtp.gmail.com`)
- `SMTP_PORT`: SMTP port (usually `587` for TLS)
- `SMTP_USERNAME`: Your email username
- `SMTP_PASSWORD`: Your email password or app password
- `FROM_EMAIL`: The "from" email address
- `FROM_NAME`: The "from" name (e.g., "Drew Dimmery")

**Email List Encryption:**
- `EMAIL_LIST_PASSPHRASE`: The passphrase you used to encrypt the email list
- `EMAIL_LIST_GPG_KEY`: Base64-encoded GPG private key (see below)

**Testing:**
- `TEST_EMAIL`: Your email address for testing

### 5. Generate GPG Key for Email List

```bash
# Generate a new GPG key (use a strong passphrase)
gpg --full-generate-key

# Export the private key and encode as base64
gpg --export-secret-keys YOUR_KEY_ID | base64 > private_key_base64.txt
```

Add the contents of `private_key_base64.txt` as the `EMAIL_LIST_GPG_KEY` secret.

## Usage

### Sending a Newsletter

1. **Render your site first** (this creates the HTML files):
   ```bash
   quarto render
   ```

2. **Send via GitHub Actions**:
   - Go to Actions tab in your GitHub repository
   - Find "Send Newsletter" workflow
   - Click "Run workflow"
   - Enter the path to your rendered HTML file (e.g., `_site/posts/my-new-post/index.html`)
   - Optionally override the email subject
   - Choose test mode for testing

### Managing Subscribers

```bash
# Add a subscriber
python .github/scripts/manage_email_list.py add new@example.com --name "New Subscriber"

# Remove a subscriber  
python .github/scripts/manage_email_list.py remove old@example.com

# List all subscribers
python .github/scripts/manage_email_list.py list

# Re-encrypt after making changes
python .github/scripts/manage_email_list.py encrypt
```

Remember to commit the updated `.github/email_list.gpg` file after making changes.

## Email Providers

### Gmail Setup
1. Enable 2-factor authentication
2. Generate an App Password: Google Account > Security > 2-Step Verification > App passwords
3. Use these settings:
   - `SMTP_SERVER`: `smtp.gmail.com`
   - `SMTP_PORT`: `587`
   - `SMTP_USERNAME`: your gmail address
   - `SMTP_PASSWORD`: the app password (not your regular password)

### Other Providers
- **Outlook/Hotmail**: `smtp-mail.outlook.com:587`
- **Yahoo**: `smtp.mail.yahoo.com:587`
- **SendGrid**: `smtp.sendgrid.net:587`

## Security Notes

- The email list is encrypted with GPG before being stored in the repository
- All sensitive credentials are stored as GitHub Secrets
- The workflow only runs manually (never automatically)
- Decrypted email list is cleaned up after each run
- Test mode allows you to verify everything works before sending to all subscribers