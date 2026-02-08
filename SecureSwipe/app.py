# --- 7. PAGE: DASHBOARD ---
elif st.session_state.page == "Dashboard":
    u = st.session_state.user
    u_data = st.session_state.db[u]
    u_type = u_data['type']
    
    # Sidebar navigation
    st.sidebar.title(f"🛡️ {u_type} Portal")
    st.sidebar.write(f"Logged in: **{u}**")
    if st.sidebar.button("LOGOUT"):
        st.session_state.user = None
        nav("Home")

    st.title("💳 Card & Fraud Management")
    
    # Initialize limit and status in session state if not present
    if 'card_limits' not in st.session_state: st.session_state.card_limits = {}
    if 'card_status' not in st.session_state: st.session_state.card_status = {}

    tab1, tab2, tab3 = st.tabs(["Manage Cards", "Set Fraud Limits", "Transaction Scan"])

    # --- TAB 1: MANAGE CARDS ---
    with tab1:
        st.subheader("Add New Card for Monitoring")
        with st.form("add_card_form"):
            c_name = st.text_input("Cardholder Name")
            c_num = st.text_input("Card Number (16 digits)", max_chars=16)
            c_type = st.selectbox("Type", ["Debit", "Credit"])
            if st.form_submit_button("Protect Card"):
                if len(c_num) == 16 and c_num.isdigit():
                    card_id = f"{c_type} **** {c_num[-4:]}"
                    if card_id not in st.session_state.cards[u]:
                        st.session_state.cards[u].append(card_id)
                        st.session_state.card_limits[card_id] = 5000.0  # Default limit
                        st.session_state.card_status[card_id] = "Active"
                        st.success(f"Card {card_id} is now under AI protection.")
                    else:
                        st.warning("This card is already registered.")
                else:
                    st.error("Invalid Card Number. Enter 16 digits.")

        st.divider()
        st.subheader("Your Protected Cards")
        if st.session_state.cards[u]:
            for card in st.session_state.cards[u]:
                col_c1, col_c2, col_c3 = st.columns([2, 1, 1])
                status = st.session_state.card_status.get(card, "Active")
                col_c1.write(f"**{card}**")
                col_c2.write(f"Status: `{status}`")
                if status == "Active":
                    if col_c3.button("Block Card", key=f"block_{card}"):
                        st.session_state.card_status[card] = "BLOCKED"
                        st.rerun()
                else:
                    if col_c3.button("Unblock", key=f"unblock_{card}"):
                        st.session_state.card_status[card] = "Active"
                        st.rerun()
        else:
            st.info("No cards added yet.")

    # --- TAB 2: SET FRAUD LIMITS ---
    with tab2:
        st.subheader("Update Transaction Thresholds")
        st.write("If a transaction exceeds this limit, the AI will trigger a priority fraud alert.")
        if st.session_state.cards[u]:
            selected_card = st.selectbox("Select Card to Update", st.session_state.cards[u])
            current_limit = st.session_state.card_limits.get(selected_card, 5000.0)
            
            new_limit = st.number_input("New Alert Limit ($)", min_value=1.0, value=float(current_limit))
            if st.button("Update Limit"):
                st.session_state.card_limits[selected_card] = new_limit
                st.success(f"Alert limit for {selected_card} updated to ${new_limit}")
        else:
            st.warning("Add a card first to set limits.")

    # --- TAB 3: AI SCANNER ---
    with tab3:
        st.subheader("🔍 Real-Time Transaction Validation")
        if not st.session_state.cards[u]:
            st.error("Please add a card in 'Manage Cards' to perform a scan.")
        else:
            scan_card = st.selectbox("Scan Transaction for:", st.session_state.cards[u])
            v14 = st.number_input("Anomaly Factor (V14)", value=0.0, help="AI feature representing hidden patterns.")
            amt = st.number_input("Transaction Amount ($)", min_value=0.0)
            
            if st.button("VALIDATE NOW"):
                if st.session_state.card_status[scan_card] == "BLOCKED":
                    st.error("Transaction Denied: This card is currently BLOCKED.")
                else:
                    # AI Prediction Logic
                    feats = np.zeros(29)
                    feats[13], feats[28] = v14, amt
                    is_fraud = model.predict([feats])[0] == 1
                    
                    limit = st.session_state.card_limits.get(scan_card, 5000.0)
                    
                    if is_fraud or amt > limit:
                        st.error("🚨 HIGH-RISK TRANSACTION DETECTED!")
                        if amt > limit:
                            st.warning(f"Reason: Transaction of ${amt} exceeds your set limit of ${limit}.")
                        
                        st.write("---")
                        st.write("**Was this you?**")
                        c_col1, c_col2 = st.columns(2)
                        if c_col1.button("Yes, It was me"):
                            st.success("Transaction verified by user.")
                        if c_col2.button("No, BLOCK MY CARD", type="primary"):
                            st.session_state.card_status[scan_card] = "BLOCKED"
                            st.warning(f"Card {scan_card} has been permanently blocked for security.")
                            st.rerun()
                    else:
                        st.success("✅ Transaction Verified: Secure Swipe approved.")
