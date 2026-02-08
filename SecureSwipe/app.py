import streamlit as st
import pandas as pd
import numpy as np
import json
import os

# --- 1. DATA PERSISTENCE LAYER ---
USER_DB = "users_data.json"

def load_data():
    if os.path.exists(USER_DB):
        with open(USER_DB, "r") as f:
            return json.load(f)
    return {}

def save_data(data):
    with open(USER_DB, "w") as f:
        json.dump(data, f)

# Initialize data
if 'db' not in st.session_state:
    st.session_state.db = load_data()

# --- 2. AI ENGINE (Original Code) ---
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

# --- 3. STATE MANAGEMENT ---
if 'page' not in st.session_state: st.session_state.page = "Home"
if 'user' not in st.session_state: st.session_state.user = None

def nav(target):
    st.session_state.page = target
    st.rerun()

# --- 4. PAGE: HOME ---
if st.session_state.page == "Home":
    st.markdown("<h1 style='text-align:center; color:#1a237e;'>🛡️ SECURE SWIPE</h1>", unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800")
    st.markdown("### **Smart protection for every transaction.**")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("LOGIN", use_container_width=True): nav("Login")
    with col2:
        if st.button("REGISTER", use_container_width=True): nav("Register")

# --- 5. PAGE: REGISTER ---
elif st.session_state.page == "Register":
    st.title("Join Secure Swipe")
    acc_type = st.radio("Account Type", ["User", "Institution"], horizontal=True)
    
    with st.form("reg_form"):
        u = st.text_input("Username")
        e = st.text_input("Email Address")
        p = st.text_input("Password", type="password")
        vp = st.text_input("Verify Password", type="password")
        
        if st.form_submit_button("CREATE ACCOUNT"):
            if p == vp and u not in st.session_state.db:
                st.session_state.db[u] = {"pw": p, "email": e, "type": acc_type, "cards": []}
                save_data(st.session_state.db)
                st.success("Account created! You can now login anytime.")
            else:
                st.error("User exists or passwords mismatch.")
    
    if st.button("Already have an account? Login here"): nav("Login")
    if st.button("← Back to Home"): nav("Home")

# --- 6. PAGE: LOGIN ---
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

# --- 7. PAGE: FORGOT PASSWORD ---
elif st.session_state.page == "ForgotPassword":
    st.title("Reset Password")
    f_u = st.text_input("Enter Username")
    f_e = st.text_input("Enter Registered Email")
    new_p = st.text_input("New Password", type="password")
    
    if st.button("Update Password"):
        if f_u in st.session_state.db and st.session_state.db[f_u]['email'] == f_e:
            st.session_state.db[f_u]['pw'] = new_p
            save_data(st.session_state.db)
            st.success("Password updated! Please login.")
            nav("Login")
        else:
            st.error("Username and Email do not match our records.")
    if st.button("← Back to Login"): nav("Login")

# --- 8. PAGE: DASHBOARD ---
elif st.session_state.page == "Dashboard":
    u = st.session_state.user
    u_data = st.session_state.db[u]
    st.title(f"🛡️ {u_data['type']} Dashboard")
    
    # Sidebar
    st.sidebar.write(f"Logged in: **{u}**")
    if st.sidebar.button("LOGOUT"):
        st.session_state.user = None
        nav("Home")
    
    if st.sidebar.button("❌ DELETE ACCOUNT", help="Permanent Action"):
        del st.session_state.db[u]
        save_data(st.session_state.db)
        st.session_state.user = None
        nav("Home")

    t1, t2 = st.tabs(["Cards", "Scanner"])
    with t1:
        c_add = st.text_input("Add Card (Last 4 digits)")
        if st.button("Protect"):
            st.session_state.db[u]['cards'].append(c_add)
            save_data(st.session_state.db)
            st.success("Card Saved Permanently.")
        st.write("Your Cards:", st.session_state.db[u]['cards'])
        
    with t2:
        v14 = st.number_input("Anomaly Factor", value=0.0)
        amt = st.number_input("Amount", value=0.0)
        if st.button("VALIDATE"):
            # Original AI prediction logic remains exactly the same
            feats = np.zeros(29); feats[13], feats[28] = v14, amt
            if model.predict([feats])[0] == 1:
                st.error("🚨 FRAUD DETECTED!")
            else:
                st.success("✅ SAFE")
