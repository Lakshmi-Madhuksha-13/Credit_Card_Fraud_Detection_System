import streamlit as st
import pandas as pd
import numpy as np
import re
from sklearn.ensemble import RandomForestClassifier

# --- 1. APP CONFIGURATION ---
st.set_page_config(page_title="Secure Swipe AI", page_icon="🛡️", layout="wide")

# --- 2. AI ENGINE (Initialization) ---
@st.cache_resource
def load_secure_swipe_ai():
    # Creating a lightweight model for real-time validation
    model = RandomForestClassifier(n_estimators=10, random_state=42)
    # Dummy training data to initialize the model (29 features)
    model.fit(np.zeros((10, 29)), np.random.randint(0, 2, 10))
    return model

model = load_secure_swipe_ai()

# --- 3. UNIFIED VALIDATION LOGIC ---
def validate_email(email):
    return email.lower().endswith("@gmail.com")

def validate_username(username):
    return "_" in username

def validate_password(password):
    # Constraint: 6+ chars, 1 Upper, 1 Lower, 1 Number, 1 Special Char
    if len(password) < 6:
        return False
    if not re.search(r"[a-z]", password): return False
    if not re.search(r"[A-Z]", password): return False
    if not re.search(r"[0-9]", password): return False
    # Using raw string and single quotes to handle double quotes in regex safely
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password): return False
    return True

# --- 4. SESSION STATE (Database) ---
if 'db' not in st.session_state: st.session_state.db = {} 
if 'page' not in st.session_state: st.session_state.page = "Home"
if 'user' not in st.session_state: st.session_state.user = None
if 'cards' not in st.session_state: st.session_state.cards = {} # {username: [list of cards]}
if 'card_limits' not in st.session_state: st.session_state.card_limits = {} # {card_id: limit}
if 'card_status' not in st.session_state: st.session_state.card_status = {} # {card_id: "Active"/"Blocked"}

def nav(target):
    st.session_state.page = target
    st.rerun()

# --- 5. PAGE: HOME ---
if st.session_state.page == "Home":
    st.markdown("<h1 style='text-align:center; color:#1a237e;'>🛡️ SECURE SWIPE</h1>", unsafe_allow_html=True)
    st.image("https://images.unsplash.com/photo-1563013544-824ae1b704d3?w=800")
    st.markdown("### **Smart protection for every transaction.**")
    
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
        if acc_type == "User":
            st.text_input("Full Name")
            st.selectbox("Gender", ["Male", "Female", "Other"])
        else:
            st.text_input("Institution Name")
            st.text_input("Registration ID")

        phone = st.text_input("Phone Number")
        u = st.text_input("Username (must contain '_')")
        e = st.text_input("Email Address (must be @gmail.com)")
        p = st.text_input("Create Password", type="password", help="6+ chars, Upper, Lower, Number, Special")
        vp = st.text_input("Confirm Password", type="password")
        
        if st.form_submit_button("CREATE ACCOUNT"):
            if u in st.session_state.db:
                st.error("Username already exists.")
            elif not validate_username(u):
                st.error("Username must contain an underscore (_).")
            elif not validate_email(e):
                st.error("Email must be a @gmail.com address.")
            elif not validate_password(p):
                st.error("Password must be 6+ characters with Upper, Lower, Number, and Special Char.")
            elif p != vp:
                st.error("Passwords do not match.")
            else:
                st.session_state.db[u] = {"pw": p, "email": e, "type": acc_type, "phone": phone}
                st.session_state.cards[u] = []
                st.success("Account created! Redirecting to login...")
                nav("Login")
    if st.button("← Back to Home"): nav("Home")

# --- 7. PAGE: LOGIN ---
elif st.session_state.page == "Login":
    st.title("Secure Access")
    l_mode = st.selectbox("Account Type", ["User", "Institution"])
    l_u = st.text_input("Username")
    l_e = st.text_input("Email")
    l_p = st.text_input("Password", type="password")
    
    if st.button("ENTER SYSTEM"):
        # Verifying constraints during login as requested
        if not validate_username(l_u) or not validate_email(l_e) or not validate_password(l_p):
            st.error("Invalid input format. Check your username (_), email (@gmail.com), and password requirements.")
        elif l_u in st.session_state.db:
            data = st.session_state.db[l_u]
            if data['pw'] == l_p and data['email'] == l_e and data['type'] == l_mode:
                st.session_state.user = l_u
                nav("Dashboard")
            else: st.error("Invalid credentials or account type.")
        else: st.error("User not found.")
    if st.button("← Back"): nav("Home")

# --- 8. PAGE: DASHBOARD ---
elif st.session_state.page == "Dashboard":
    u = st.session_state.user
    u_data = st.session_state.db[u]
    
    st.sidebar.title(f"🛡️ {u_data['type']}")
    st.sidebar.write(f"Logged in: **{u}**")
    if st.sidebar.button("LOGOUT"):
        st.session_state.user = None
        nav("Home")

    st.title("💳 Card & Fraud Dashboard")
    st.write(f"Verified Contact: {u_data['phone']}")

    t1, t2, t3 = st.tabs(["Manage Cards", "Set Fraud Limits", "AI Transaction Scan"])

    with t1:
        st.subheader("Register Cards")
        with st.form("card_add"):
            c_num = st.text_input("16 Digit Card Number", max_chars=16)
            c_type = st.selectbox("Type", ["Debit", "Credit"])
            if st.form_submit_button("Add and Protect"):
                if len(c_num) == 16 and c_num.isdigit():
                    card_id = f"{c_type} **** {c_num[-4:]}"
                    if card_id not in st.session_state.cards[u]:
                        st.session_state.cards[u].append(card_id)
                        st.session_state.card_limits[card_id] = 1000.0 # Default
                        st.session_state.card_status[card_id] = "Active"
                        st.success(f"Card {card_id} is now monitored.")
                    else: st.warning("Card already exists.")
                else: st.error("Please enter a valid 16-digit card number.")

        st.divider()
        if st.session_state.cards[u]:
            for card in st.session_state.cards[u]:
                c_col1, c_col2, c_col3 = st.columns([2,1,1])
                status = st.session_state.card_status[card]
                c_col1.write(f"**{card}**")
                c_col2.write(f"Status: `{status}`")
                if status == "Active":
                    if c_col3.button("BLOCK", key=f"block_{card}"):
                        st.session_state.card_status[card] = "BLOCKED"
                        st.rerun()
                else:
                    if c_col3.button("UNBLOCK", key=f"un_{card}"):
                        st.session_state.card_status[card] = "Active"
                        st.rerun()

    with t2:
        st.subheader("Manage Alert Thresholds")
        if st.session_state.cards[u]:
            sel_card = st.selectbox("Select Card", st.session_state.cards[u])
            curr_limit = st.session_state.card_limits[sel_card]
            new_limit = st.number_input("Transaction Limit ($)", min_value=1.0, value=float(curr_limit))
            if st.button("Update Alert Limit"):
                st.session_state.card_limits[sel_card] = new_limit
                st.success(f"Limit updated to ${new_limit}")
        else: st.info("Add a card first.")

    with t3:
        st.subheader("🔍 AI Fraud Scanner")
        if st.session_state.cards[u]:
            scan_card = st.selectbox("Scan for Card:", st.session_state.cards[u])
            v14 = st.number_input("V14 Anomaly Factor", value=0.0)
            amt = st.number_input("Amount ($)", min_value=0.01)
            
            if st.button("Validate Transaction"):
                if st.session_state.card_status[scan_card] == "BLOCKED":
                    st.error("ACCESS DENIED: This card is currently BLOCKED.")
                else:
                    # AI Processing
                    feats = np.zeros(29)
                    feats[13], feats[28] = v14, amt
                    is_fraud = model.predict([feats])[0] == 1
                    limit = st.session_state.card_limits[scan_card]
                    
                    if is_fraud or amt > limit:
                        st.error("🚨 FRAUD ALERT / LIMIT EXCEEDED!")
                        if amt > limit: st.warning(f"This transaction of ${amt} exceeds your set limit of ${limit}.")
                        
                        st.write("**Did you authorize this?**")
                        y_col, n_col = st.columns(2)
                        if y_col.button("Yes, it was me"):
                            st.success("Transaction authorized.")
                        if n_col.button("No, BLOCK CARD", type="primary"):
                            st.session_state.card_status[scan_card] = "BLOCKED"
                            st.error(f"Card {scan_card} has been blocked.")
                            st.rerun()
                    else:
                        st.success("✅ Transaction Verified.")
        else: st.warning("Register a card to start scanning.")
