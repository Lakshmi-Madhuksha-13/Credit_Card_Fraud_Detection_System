import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import re 

# --- 1. DATA PERSISTENCE LAYER ---
# This ensures users don't have to register every time
USER_DB = "users_data.json"

def load_data():
    if os.path.exists(USER_DB):
        try:
            with open(USER_DB, "r") as f:
                return json.load(f)
        except:
            return {}
    return {}

def save_data(data):
    with open(USER_DB, "w") as f:
        json.dump(data, f)

# Initialize database in session state
if 'db' not in st.session_state:
    st.session_state.db = load_data()

# --- 2. VALIDATION LOGIC ---
def validate_registration(username, email, password):
    # Username check: must contain an underscore
    if "_" not in username:
        return False, "Username must contain an underscore (_)."
    
    # Email check: must end with @gmail.com
    if not email.lower().endswith("@gmail.com"):
        return False, "Only @gmail.com addresses are accepted."
    
    # Password checks: Min 6 chars, Uppercase, Lowercase, Number, Special Char
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter."
    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter."
    # RECTIFIED: Corrected regex for number detection
    if not re.search(r"[0-9]", password):
        return False, "Password must contain at least one number."
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>|]", password):
        return False, "Password must contain at least one special character."
    
    return True, ""

# --- 3. AI ENGINE (SECURE SWIPE CORE) ---
@st.cache_resource
def load_secure_swipe_ai():
    url = "https://raw.githubusercontent.com/nsethi31/Kaggle-Data-Credit-Card-Fraud-Detection/master/creditcard.csv"
    df = pd.read_csv(url)
    fraud = df[df['Class'] == 1]
    normal = df[df['Class'] == 0].sample(len(fraud) * 3)
    df_balanced = pd.concat([fraud, normal])
    X = df_balanced.drop(['Time', 'Class'], axis=1)
    y = df_balanced['Class']
    from sklearn.ensemble import RandomForestClassifier
    return RandomForestClassifier(n_estimators=50, random_state=42).fit(X, y)

model = load_secure_swipe_ai()

# --- 4. STATE MANAGEMENT ---
if 'page' not in st.session_state: st.session_state.page = "Home"
if 'user' not in st.session_state: st.session_state.user = None

def nav(target):
    st.session_state.page = target
    st.rerun()

# --- 5. PAGE: HOME ---
if st.session_state.page == "Home":
    st.markdown("<h1 style='text-align:center; color:#1a237e;'>🛡️ SECURE SWIPE</h1>", unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800")
    st.markdown("### **Smart protection for every transaction.**")
    st.write("Register once, stay protected forever.")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("LOGIN", use_container_width=True): nav("Login")
    with col2:
        if st.button("REGISTER", use_container_width=True): nav("Register")

# --- 6. PAGE: REGISTER ---
elif st.session_state.page == "Register":
    st.title("Join Secure Swipe")
    acc_type = st.radio("Account Type", ["User", "Institution"], horizontal=True)
    
    with st.form("reg_form"):
        fn = st.text_input("Full Name")
        u = st.text_input("Username (must include '_')")
        e = st.text_input("Email Address (@gmail.com only)")
        p = st.text_input("Password (min 6 chars, A-z, 0-9, !@#)", type="password")
        vp = st.text_input("Verify Password", type="password")
        
        if st.form_submit_button("CREATE ACCOUNT"):
            is_valid, error_msg = validate_registration(u, e, p)
            if not fn:
                st.error("Please enter your Full Name.")
            elif not is_valid:
                st.error(error_msg)
            elif p != vp:
                st.error("Passwords do not match.")
            elif u in st.session_state.db:
                st.error("Username already exists.")
            else:
                st.session_state.db[u] = {
                    "full_name": fn,
                    "pw": p, 
                    "email": e, 
                    "type": acc_type, 
                    "cards": []
                }
                save_data(st.session_state.db)
                st.success("Account created successfully! You can now login.")
    
    if st.button("Already have an account? Login here"): nav("Login")
    if st.button("← Back to Home"): nav("Home")

# --- 7. PAGE: LOGIN ---
elif st.session_state.page == "Login":
    st.title("Secure Access")
    l_u = st.text_input("Username")
    l_p = st.text_input("Password", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("ENTER SYSTEM"):
            if l_u in st.session_state.db and st.session_state.db[l_u]['pw'] == l_p:
                st.session_state.user = l_u
                nav("Dashboard")
            else: st.error("Invalid Credentials.")
    with col2:
        if st.button("Forgot Password?"): nav("ForgotPassword")
            
    st.divider()
    if st.button("Need an account? Register here"): nav("Register")
    if st.button("← Back"): nav("Home")

# --- 8. PAGE: FORGOT PASSWORD ---
elif st.session_state.page == "ForgotPassword":
    st.title("Reset Password")
    f_u = st.text_input("Enter Username")
    f_e = st.text_input("Enter Registered Email")
    new_p = st.text_input("New Password", type="password")
    
    if st.button("Update Password"):
        is_valid, error_msg = validate_registration(f_u, f_e, new_p)
        if not is_valid:
            st.error(error_msg)
        elif f_u in st.session_state.db and st.session_state.db[f_u]['email'] == f_e:
            st.session_state.db[f_u]['pw'] = new_p
            save_data(st.session_state.db)
            st.success("Password updated! Go to login.")
            nav("Login")
        else:
            st.error("Account details do not match.")
    if st.button("← Back to Login"): nav("Login")

# --- 9. PAGE: DASHBOARD ---
elif st.session_state.page == "Dashboard":
    u = st.session_state.user
    u_data = st.session_state.db[u]
    st.title(f"🛡️ Welcome, {u_data.get('full_name', u)}")
    
    st.sidebar.write(f"Account: **{u}**")
    if st.sidebar.button("LOGOUT"):
        st.session_state.user = None
        nav("Home")
    
    if st.sidebar.button("❌ DELETE ACCOUNT"):
        del st.session_state.db[u]
        save_data(st.session_state.db)
        st.session_state.user = None
        st.warning("Account Deleted.")
        nav("Home")

    t1, t2 = st.tabs(["Cards", "Scanner"])
    with t1:
        c_add = st.text_input("Add Card (Last 4 digits)")
        if st.button("Protect"):
            st.session_state.db[u]['cards'].append(c_add)
            save_data(st.session_state.db)
            st.success("Card Saved Permanently.")
        st.write("Protected Cards:", st.session_state.db[u]['cards'])
        
    with t2:
        st.subheader("AI Fraud Scan")
        v14 = st.number_input("Anomaly Factor (V14)", value=0.0)
        amt = st.number_input("Amount ($)", value=0.0)
        if st.button("VALIDATE"):
            feats = np.zeros(29); feats[13], feats[28] = v14, amt
            if model.predict([feats])[0] == 1:
                st.error("🚨 FRAUD DETECTED!")
            else:
                st.success("✅ SAFE")
