"""
Clinical Trial Eligibility Matcher - Authentication Module
Provides secure, session-based authentication with:
- SQLite persistent user store with PBKDF2-HMAC-SHA256 password hashing + salt
- Pre-seeded synthetic clinician accounts for testing
- Sign In form (email + password)
- Sign Up form (name, email, password, confirm password)
- Password Reset form (email + new password workflow)
- High-contrast, medical-tech styled UI isolated in its own CSS namespace
"""

import sqlite3
import os
import hashlib
import secrets
from typing import Optional, Dict, Any

try:
    import streamlit as st
except ImportError:
    st = None

DB_PATH = os.path.join(os.path.dirname(__file__), "clinical_trial_users.db")

# -----------------------------------------------------------------------------
# Database Initialization & Security Helpers
# -----------------------------------------------------------------------------

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_auth_db():
    """Initializes SQLite user table and pre-seeds a demo clinician account."""
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL COLLATE NOCASE,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()

    # Pre-seed demo user if empty
    cursor.execute("SELECT COUNT(*) as count FROM users")
    count = cursor.fetchone()["count"]
    if count == 0:
        demo_users = [
            ("Dr. Sarah Lin, MD", "doctor@oncology.org", "ClinicalTrial2026!"),
            ("Dr. James Reed, PhD", "researcher@trials.org", "Matcher2026!"),
        ]
        for name, email, password in demo_users:
            pwd_hash, salt = hash_password(password)
            cursor.execute(
                "INSERT INTO users (name, email, password_hash, salt) VALUES (?, ?, ?, ?)",
                (name, email, pwd_hash, salt)
            )
        conn.commit()
    conn.close()

def hash_password(password: str, salt: Optional[str] = None) -> tuple[str, str]:
    """Hashes password using standard library PBKDF2-HMAC-SHA256 with 100,000 rounds."""
    if not salt:
        salt = secrets.token_hex(16)
    pwd_bytes = password.encode("utf-8")
    salt_bytes = salt.encode("utf-8")
    pwd_hash = hashlib.pbkdf2_hmac("sha256", pwd_bytes, salt_bytes, 100000).hex()
    return pwd_hash, salt

def verify_password(password: str, salt: str, expected_hash: str) -> bool:
    """Constant-time verification of supplied password against stored hash."""
    computed_hash, _ = hash_password(password, salt)
    return secrets.compare_digest(computed_hash, expected_hash)

# -----------------------------------------------------------------------------
# User Repository Operations
# -----------------------------------------------------------------------------

def get_user_by_email(email: str) -> Optional[Dict[str, Any]]:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE email = ?", (email.strip(),))
    row = cursor.fetchone()
    conn.close()
    if row:
        return dict(row)
    return None

def register_user(name: str, email: str, password: str) -> tuple[bool, str]:
    name = name.strip()
    email = email.strip().lower()

    if not name or len(name) < 2:
        return False, "Please provide a valid full name."
    if not email or "@" not in email or "." not in email:
        return False, "Please enter a valid email address."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."

    if get_user_by_email(email) is not None:
        return False, f"An account with email '{email}' already exists. Please sign in."

    pwd_hash, salt = hash_password(password)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO users (name, email, password_hash, salt) VALUES (?, ?, ?, ?)",
            (name, email, pwd_hash, salt)
        )
        conn.commit()
        conn.close()
        return True, "Account registered successfully! You can now sign in."
    except Exception as e:
        return False, f"Database error: {str(e)}"

def authenticate_user(email: str, password: str) -> tuple[bool, Optional[Dict[str, Any]], str]:
    email = email.strip().lower()
    user = get_user_by_email(email)
    if not user:
        return False, None, "Invalid email or password."
    
    if verify_password(password, user["salt"], user["password_hash"]):
        return True, user, "Authentication successful."
    return False, None, "Invalid email or password."

def reset_user_password(email: str, new_password: str) -> tuple[bool, str]:
    email = email.strip().lower()
    user = get_user_by_email(email)
    if not user:
        return False, f"No registered account found for '{email}'."
    if len(new_password) < 6:
        return False, "New password must be at least 6 characters long."

    pwd_hash, salt = hash_password(new_password)
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        cursor.execute(
            "UPDATE users SET password_hash = ?, salt = ? WHERE email = ?",
            (pwd_hash, salt, email)
        )
        conn.commit()
        conn.close()
        return True, "Password has been successfully updated! You can now log in."
    except Exception as e:
        return False, f"Failed to update password: {str(e)}"

# -----------------------------------------------------------------------------
# Isolated High-Contrast Styling for Login & Signup
# -----------------------------------------------------------------------------

AUTH_CSS = """
<style>
/* Isolated Authentication Screen Theme */
.auth-wrapper {
  max-width: 480px;
  margin: 40px auto 20px auto;
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}


.auth-card {
  background-color: #FFFFFF;
  border: 1px solid #E2E8F0;
  border-radius: 16px;
  padding: 32px 28px;
  box-shadow: 0 4px 20px rgba(11, 25, 44, 0.08);
}

.auth-header-badge {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  background-color: #F0FDFA;
  color: #0F766E;
  border: 1px solid #CCFBF1;
  padding: 4px 12px;
  border-radius: 9999px;
  font-size: 11.5px;
  font-weight: 700;
  letter-spacing: 0.5px;
  text-transform: uppercase;
  margin-bottom: 12px;
}

.auth-title {
  font-family: 'Outfit', sans-serif;
  color: #F8FAFC !important;
  font-size: 24px !important;
  font-weight: 700 !important;
  margin: 0 0 6px 0 !important;
  letter-spacing: -0.02em;
}

.auth-subtitle {
  color: #CBD5E1;
  font-size: 13.5px;
  margin: 0 0 24px 0;
  line-height: 1.5;
}

.demo-account-box {
  background-color: #F8FAFC;
  border: 1px dashed #CBD5E1;
  border-radius: 10px;
  padding: 12px 14px;
  margin-bottom: 20px;
  font-size: 12px;
  color: #334155;
}

.demo-account-box strong {
  color: #0F766E;
}

/* Explicit high-contrast input styling for Auth page */
div[data-testid="stForm"] .stTextInput input {
  background-color: #FFFFFF !important;
  color: #0F172A !important;
  border: 1.5px solid #CBD5E1 !important;
  border-radius: 8px !important;
  padding: 10px 14px !important;
  font-size: 14px !important;
  font-weight: 500 !important;
}

div[data-testid="stForm"] .stTextInput input:focus {
  border-color: #0D9488 !important;
  box-shadow: 0 0 0 3px rgba(13, 148, 136, 0.18) !important;
}

div[data-testid="stForm"] .stTextInput input::placeholder {
  color: #94A3B8 !important;
  font-weight: 400 !important;
}

/* Form primary action button */
div[data-testid="stForm"] .stButton button {
  width: 100% !important;
  background: linear-gradient(135deg, #0D9488 0%, #0F766E 100%) !important;
  color: #FFFFFF !important;
  font-weight: 700 !important;
  font-size: 15px !important;
  border: none !important;
  border-radius: 8px !important;
  padding: 10px 20px !important;
  box-shadow: 0 4px 12px rgba(13, 148, 136, 0.25) !important;
  margin-top: 8px !important;
}

div[data-testid="stForm"] .stButton button:hover {
  background: linear-gradient(135deg, #0F766E 0%, #115E59 100%) !important;
  box-shadow: 0 6px 16px rgba(13, 148, 136, 0.35) !important;
}
</style>
"""

# -----------------------------------------------------------------------------
# Auth Page Rendering Component
# -----------------------------------------------------------------------------

def render_auth_page():
    """Renders the standalone Login / Signup / Reset Password gatekeeper interface."""
    init_auth_db()
    st.markdown(AUTH_CSS, unsafe_allow_html=True)

    st.markdown("""
    <div class="auth-wrapper">
      <div style="text-align: center; margin-bottom: 20px;">
        <div style="font-size: 38px; line-height: 1; margin-bottom: 8px;">🔬</div>
        <div class="auth-header-badge">Clinical Trial Eligibility Matcher</div>
        <h1 class="auth-title">Applied Oncology Portal</h1>
        <p class="auth-subtitle">
          Sign in or create a research credential to access the GenAI trial adjudication pipeline.
        </p>
      </div>
    </div>
    """, unsafe_allow_html=True)

    col1, col2, col3 = st.columns([1, 2.2, 1])
    with col2:
        tab_login, tab_signup, tab_reset = st.tabs([
            "🔑 Sign In",
            "✨ Create Account",
            "🔄 Reset Password"
        ])

        # -------------------- TAB 1: SIGN IN --------------------
        with tab_login:
            st.markdown("""
            <div class="demo-account-box">
              <strong>Quick Test Account:</strong><br>
              Email: <code>doctor@oncology.org</code> &bull; Password: <code>ClinicalTrial2026!</code>
            </div>
            """, unsafe_allow_html=True)

            with st.form("signin_form", clear_on_submit=False):
                email_input = st.text_input(
                    "Work / Institutional Email",
                    value="",
                    placeholder="doctor@oncology.org",
                    key="login_email"
                )
                password_input = st.text_input(
                    "Password",
                    value="",
                    type="password",
                    placeholder="••••••••••••",
                    key="login_password"
                )
                submit_login = st.form_submit_button("Sign In to Portal", use_container_width=True)

                if submit_login:
                    if not email_input or not password_input:
                        st.error("Please enter both email and password.")
                    else:
                        success, user, msg = authenticate_user(email_input, password_input)
                        if success and user:
                            st.session_state["authenticated"] = True
                            st.session_state["user_email"] = user["email"]
                            st.session_state["user_name"] = user["name"]
                            st.success(f"Welcome back, {user['name']}! Redirecting...")
                            st.rerun()
                        else:
                            st.error(msg)

        # -------------------- TAB 2: SIGN UP --------------------
        with tab_signup:
            with st.form("signup_form", clear_on_submit=False):
                new_name = st.text_input(
                    "Full Name & Credential",
                    value="",
                    placeholder="Dr. Jane Doe, MD",
                    key="signup_name"
                )
                new_email = st.text_input(
                    "Institutional Email",
                    value="",
                    placeholder="jane.doe@cancercenter.org",
                    key="signup_email"
                )
                new_password = st.text_input(
                    "Create Password",
                    value="",
                    type="password",
                    placeholder="Minimum 6 characters",
                    key="signup_password"
                )
                confirm_password = st.text_input(
                    "Confirm Password",
                    value="",
                    type="password",
                    placeholder="Re-enter password",
                    key="signup_confirm_password"
                )
                submit_signup = st.form_submit_button("Create Research Account", use_container_width=True)

                if submit_signup:
                    if new_password != confirm_password:
                        st.error("Passwords do not match. Please verify and retry.")
                    else:
                        ok, msg = register_user(new_name, new_email, new_password)
                        if ok:
                            st.success(msg)
                            # Auto-login the new user
                            user = get_user_by_email(new_email)
                            if user:
                                st.session_state["authenticated"] = True
                                st.session_state["user_email"] = user["email"]
                                st.session_state["user_name"] = user["name"]
                                st.rerun()
                        else:
                            st.error(msg)

        # -------------------- TAB 3: RESET PASSWORD --------------------
        with tab_reset:
            with st.form("reset_form", clear_on_submit=False):
                reset_email = st.text_input(
                    "Account Email",
                    value="",
                    placeholder="registered.email@oncology.org",
                    key="reset_email"
                )
                new_pwd = st.text_input(
                    "New Password",
                    value="",
                    type="password",
                    placeholder="Enter new password (min 6 chars)",
                    key="reset_new_pwd"
                )
                confirm_new_pwd = st.text_input(
                    "Confirm New Password",
                    value="",
                    type="password",
                    placeholder="Re-enter new password",
                    key="reset_confirm_pwd"
                )
                submit_reset = st.form_submit_button("Update Password", use_container_width=True)

                if submit_reset:
                    if not reset_email:
                        st.error("Please provide your account email address.")
                    elif new_pwd != confirm_new_pwd:
                        st.error("New passwords do not match.")
                    else:
                        ok, msg = reset_user_password(reset_email, new_pwd)
                        if ok:
                            st.success(msg)
                        else:
                            st.error(msg)


def render_logout_button():
    """Renders a clean logout widget in the sidebar showing logged-in status."""
    if st.session_state.get("authenticated", False):
        user_name = st.session_state.get("user_name", "Clinical Investigator")
        user_email = st.session_state.get("user_email", "")

        st.markdown(f"""
        <div style="background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 10px; padding: 12px; margin-bottom: 16px;">
          <div style="font-size: 11px; text-transform: uppercase; letter-spacing: 0.5px; color: #0D9488; font-weight: 700;">
            Authenticated Session
          </div>
          <div style="font-size: 13.5px; font-weight: 700; color: #0F172A; margin-top: 2px;">
            {user_name}
          </div>
          <div style="font-size: 11.5px; color: #64748B;">
            {user_email}
          </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button("🚪 Sign Out", key="sidebar_logout_btn", use_container_width=True):
            st.session_state["authenticated"] = False
            st.session_state["user_email"] = None
            st.session_state["user_name"] = None
            st.rerun()
