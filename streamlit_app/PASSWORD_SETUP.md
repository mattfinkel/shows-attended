# Password Protection Setup

This app includes optional password protection to restrict access.

## How It Works

- **Password is optional**: If no password is set, the app is accessible to anyone
- **Session-based**: Once you log in on a device, you stay logged in until you logout or clear browser data
- **Secure**: Password is hashed using SHA-256, not stored in plain text

## Setting Up a Password

### For Local Development

1. **Generate a password hash:**
   ```bash
   python generate_password_hash.py "your-secure-password"
   ```

2. **Add the hash to `.streamlit/secrets.toml`:**
   ```toml
   app_password_hash = "your-generated-hash-here"
   ```

3. **Restart the Streamlit app**

### For Streamlit Cloud Deployment

1. **Generate your password hash locally** (as above)

2. **Add to Streamlit Cloud secrets:**
   - Go to your app settings on https://share.streamlit.io
   - Click "Secrets"
   - Add the line:
     ```toml
     app_password_hash = "your-generated-hash-here"
     ```

3. **Save and redeploy**

## Disabling Password Protection

Simply remove or comment out the `app_password_hash` line from your secrets:

```toml
# app_password_hash = "..."
```

The app will be accessible without authentication.

## Security Notes

- Never commit your password or hash to Git
- `.streamlit/secrets.toml` is in `.gitignore` by default
- Use a strong, unique password
- On Streamlit Cloud, secrets are encrypted and never exposed

## Logout

When password protection is enabled, a "🚪 Logout" button appears in the sidebar. Click it to logout and require re-authentication.
