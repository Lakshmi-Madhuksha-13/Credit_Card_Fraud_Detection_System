import streamlit as st
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier

# --- 1. AI ENGINE ---
@st.cache_resource
def load_secure_swipe_ai():
    url = "https://raw.githubusercontent.com/nsethi31/Kaggle-Data-Credit-Card-Fraud-Detection/master/creditcard.csv"
    df = pd.read_csv(url)

    fraud = df[df['Class'] == 1]
    normal = df[df['Class'] == 0].sample(len(fraud) * 3, random_state=42)
    df_balanced = pd.concat([fraud, normal])

    X = df_balanced.drop(['Time', 'Class'], axis=1)
    y = df_balanced['Class']

    model = RandomForestClassifier(n_estimators=50, random_state=42)
    model.fit(X, y)
    return model

model = load_secure_swipe_ai()

# --- SESSION STATE ---
if 'db' not in st.session_state: st.session_state.db = {}
if 'page' not in st.session_state: st.session_state.page = "Home"
if 'user' not in st.session_state: st.session_state.user = None
if 'cards' not in st.session_state: st.session_state.cards = {}

def nav(page):
    st.session_state.page = page
    st.rerun()

# --- HOME ---
if st.session_state.page == "Home":
    st.markdown("<h1 style='text-align:center;color:#1a237e;'>🛡️ SECURE SWIPE</h1>", unsafe_allow_html=True)
    st.markdown("### Smart protection for every transaction")
    st.write("AI-powered fraud detection for online & offline card transactions.")

    col1, col2 = st.columns(2)
    with col1:
        if st.button("LOGIN"): nav("Login")
    with col2:
        if st.button("REGISTER"): nav("Register")

# --- REGISTER ---
elif st.session_state.page == "Register":
    st.title("Create Account")
    acc_type = st.radio("Account Type", ["User", "Institution"], horizontal=True)

    with st.form("register"):
        username = st.text_input("Username")
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        confirm = st.text_input("Confirm Password", type="password")

        if st.form_submit_button("Register"):
            if password == confirm and username not in st.session_state.db:
                st.session_state.db[username] = {
                    "pw": password,
                    "email": email,
                    "type": acc_type
                }
                st.session_state.cards[username] = []
                st.success("Account created successfully")
            else:
                st.error("Registration failed")

    if st.button("Back"): nav("Home")

# --- LOGIN ---
elif st.session_state.page == "Login":
    st.title("Login")

    username = st.text_input("Username")
    email = st.text_input("Email")
    password = st.text_input("Password", type="password")

    if st.button("Login"):
        if username in st.session_state.db:
            user = st.session_state.db[username]
            if user["pw"] == password and user["email"] == email:
                st.session_state.user = username
                nav("Dashboard")
            else:
                st.error("Invalid credentials")
        else:
            st.error("User not found")

    if st.button("Back"): nav("Home")

# --- DASHBOARD ---
elif st.session_state.page == "Dashboard":
    user = st.session_state.user
    st.title("Secure Swipe Dashboard")

    st.sidebar.button("Logout", on_click=lambda: nav("Home"))

    tab1, tab2 = st.tabs(["💳 Cards", "🔍 AI Scan"])

    with tab1:
        card = st.text_input("Add Card (Last 4 digits)")
        if st.button("Add Card"):
            st.session_state.cards[user].append(card)
            st.success("Card protected")

        st.write("Protected Cards:", st.session_state.cards[user])

    with tab2:
        v14 = st.number_input("Anomaly Score (V14)")
        amount = st.number_input("Transaction Amount")

        if st.butt
