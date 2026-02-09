"""
Simple password authentication for Streamlit app
Password is stored in secrets.toml (optional)
"""
import streamlit as st
import hashlib

def hash_password(password):
    """Hash password using SHA-256"""
    return hashlib.sha256(password.encode()).hexdigest()

def check_password():
    """
    Returns True if the user has entered the correct password.
    Uses session state to keep user logged in.

    If no password is set in secrets, returns True (no auth required).
    """
    # Check if password protection is enabled
    try:
        app_password_hash = st.secrets.get("app_password_hash", None)
        if not app_password_hash:
            # No password set, allow access
            return True
    except (KeyError, FileNotFoundError):
        # No secrets file or no password set
        return True

    # Initialize session state
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    # If already authenticated, return True
    if st.session_state.authenticated:
        return True

    # Show login form
    st.markdown("## 🔐 Login")
    st.markdown("Please enter the password to access the app.")

    password = st.text_input("Password", type="password", key="login_password")

    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("Login", type="primary"):
            if hash_password(password) == app_password_hash:
                st.session_state.authenticated = True
                st.rerun()
            else:
                st.error("❌ Incorrect password")

    with col2:
        if st.button("Cancel"):
            st.stop()

    return False

def logout():
    """Logout the current user"""
    st.session_state.authenticated = False
    st.rerun()

def show_logout_button():
    """Show logout button in sidebar if password protection is enabled"""
    try:
        app_password_hash = st.secrets.get("app_password_hash", None)
        if app_password_hash and st.session_state.get("authenticated", False):
            with st.sidebar:
                st.divider()
                if st.button("🚪 Logout", use_container_width=True):
                    logout()
    except (KeyError, FileNotFoundError):
        pass
