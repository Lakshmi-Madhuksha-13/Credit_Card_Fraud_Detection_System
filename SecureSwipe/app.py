import streamlit as st
import pandas as pd
import numpy as np
import json
import os
import re 
from datetime import datetime

# --- 1. DATA PERSISTENCE LAYER ---
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

if 'db' not in st.session_state:
    st.session_state.db = load_data()

# --- 2. VALIDATION LOGIC ---
def validate_registration(username, email, password):
    if "_" not in username:
        return False, "Username must contain an underscore (_)."
    if not email.lower().endswith("@gmail.com"):
        return False, "Only @gmail.com addresses are accepted."
    if len(password) < 6:
        return False, "Password must be at least 6 characters long."
    if not (re.search(r"[A-Z]", password) and re.search(r"[a-z]", password) and 
            re.search(r"[0-9]", password) and re.search(r"[!@#$%^&*(),.?\":{}|<>|]", password)):
        return False, "Password must contain Mixed Case, Number, and Special Character."
    return True, ""

# --- 3. AI ENGINE ---
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
    st.markdown("<h3 style='text-align:center;'>Smart protection for every transaction.</h3>", unsafe_allow_html=True)
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
        e = st.text_input("Email (@gmail.com)")
        p = st.text_input("Password", type="password")
        vp = st.text_input("Verify Password", type="password")
        if st.form_submit_button("CREATE ACCOUNT"):
            valid, msg = validate_registration(u, e, p)
            if not fn: st.error("Name required.")
            elif not valid: st.error(msg)
            elif p != vp: st.error("Passwords mismatch.")
            elif u in st.session_state.db: st.error("Username taken.")
            else:
                st.session_state.db[u] = {"full_name": fn, "pw": p, "email": e, "type": acc_type, "cards": {}, "history": []}
                save_data(st.session_state.db)
                st.success("Success! Please Login.")
    if st.button("Already have an account? Login"): nav("Login")

# --- 7. PAGE: LOGIN ---
elif st.session_state.page == "Login":
    st.title("Secure Access")
    l_u = st.text_input("Username")
    l_p = st.text_input("Password", type="password")
    if st.button("ENTER SYSTEM"):
        if l_u in st.session_state.db and st.session_state.db[l_u]['pw'] == l_p:
            st.session_state.user = l_u
            nav("Dashboard")
        else: st.error("Invalid credentials.")
    if st.button("Forgot Password?"): nav("ForgotPassword")
    if st.button("Need an account? Register"): nav("Register")

# --- 8. PAGE: FORGOT PASSWORD ---
elif st.session_state.page == "ForgotPassword":
    st.title("Reset Password")
    f_u = st.text_input("Username")
    f_e = st.text_input("Email")
    new_p = st.text_input("New Password", type="password")
    if st.button("Update"):
        if f_u in st.session_state.db and st.session_state.db[f_u]['email'] == f_e:
            st.session_state.db[f_u]['pw'] = new_p
            save_data(st.session_state.db)
            st.success("Updated!")
            nav("Login")
        else: st.error("Details mismatch.")
    if st.button("Back to Login"): nav("Login")

# --- 9. PAGE: DASHBOARD ---
elif st.session_state.page == "Dashboard":
    u = st.session_state.user
    u_data = st.session_state.db[u]
    st.title(f"🛡️ Welcome, {u_data.get('full_name', u)}")
    
    # Sidebar
    st.sidebar.button("LOGOUT", on_click=lambda: nav("Home"))
    if st.sidebar.button("❌ DELETE ACCOUNT"):
        del st.session_state.db[u]
        save_data(st.session_state.db)
        st.session_state.user = None
        nav("Home")

    t1, t2, t3 = st.tabs(["💳 My Cards", "🔍 AI Scanner", "📜 History"])
    
    with t1:
        st.subheader("Manage Secure Assets")
        with st.expander("➕ Add New Card"):
            c_num = st.text_input("Card Number (Last 4 digits)", max_chars=4)
            c_lim = st.number_input("Transaction Limit ($)", min_value=1.0, value=500.0)
            if st.button("Secure This Card"):
                st.session_state.db[u]['cards'][c_num] = c_lim
                save_data(st.session_state.db)
                st.success(f"Card {c_num} protected with ${c_lim} limit.")
        
        # Display Cards visually
        cols = st.columns(2)
        for i, (num, lim) in enumerate(st.session_state.db[u]['cards'].items()):
            with cols[i % 2]:
                st.markdown(f"""
                <div style="background: linear-gradient(45deg, #1a237e, #3949ab); padding: 20px; border-radius: 15px; color: white; margin-bottom: 10px;">
                    <p style="font-size: 0.8em; margin: 0;">SECURE SWIPE ASSET</p>
                    <h2 style="margin: 10px 0;">**** **** **** {num}</h2>
                    <p style="margin: 0; font-size: 0.9em;">LIMIT: ${lim}</p>
                    <p style="text-align: right; font-size: 0.7em; color: #81c784;">● ACTIVE PROTECTION</p>
                </div>
                """, unsafe_allow_html=True)

    with t2:
        st.subheader("Real-Time Security Scan")
        selected_card = st.selectbox("Select Card for Scan", list(st.session_state.db[u]['cards'].keys()))
        v14 = st.number_input("Anomaly Factor (V14)", value=0.0)
        amt = st.number_input("Transaction Amount ($)", min_value=0.01)
        
        if st.button("RUN SECURITY CHECK"):
            limit = st.session_state.db[u]['cards'][selected_card]
            status = ""
            
            # Check Limit First
            if amt > limit:
                st.error(f"🚨 ALERT: Transaction of ${amt} exceeds your set limit of ${limit}!")
                status = "DECLINED (Limit Exceeded)"
            else:
                feats = np.zeros(29); feats[13], feats[28] = v14, amt
                if model.predict([feats])[0] == 1:
                    st.error("🚨 FRAUD DETECTED: Pattern analysis suggests high risk.")
                    status = "DECLINED (AI Fraud)"
                else:
                    st.success("✅ TRANSACTION VERIFIED: Within safe parameters.")
                    status = "APPROVED"
            
            # Save to History
            st.session_state.db[u]['history'].append({
                "time": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "card": f"**** {selected_card}",
                "amount": f"${amt}",
                "status": status
            })
            save_data(st.session_state.db)

    with t3:
        st.subheader("Activity Log")
        if st.session_state.db[u]['history']:
            df_hist = pd.DataFrame(st.session_state.db[u]['history'])
            st.table(df_hist.iloc[::-1]) # Show newest first
        else:
            st.info("No transaction history yet.")
