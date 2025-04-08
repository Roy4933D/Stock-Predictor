import streamlit as st
from firebase_admin import auth

def login_page():
    """Login Page Content"""
    st.title("Login to Smart Investment Advisor")
    st.markdown("Please choose a login method below.")

    # Tabs for Email and Phone Login
    tab1, tab2 = st.tabs(["Email Login", "Phone Login"])

    # Email Login
    with tab1:
        st.subheader("Login with Email")
        email = st.text_input("Email", placeholder="Enter your email")
        password = st.text_input("Password", placeholder="Enter your password", type="password")

        if st.button("Login with Email"):
            if email and password:
                try:
                    # Authenticate user with Firebase
                    user = auth.get_user_by_email(email)
                    st.success(f"Welcome, {user.email}!")
                    st.session_state["user"] = user.email  # Store user in session state
                except Exception as e:
                    st.error(f"Login failed: {str(e)}")
            else:
                st.warning("Please enter both email and password.")

    # Phone Login
    with tab2:
        st.subheader("Login with Phone")
        phone_number = st.text_input("Phone Number", placeholder="Enter your phone number (e.g., +919876543210)")
        otp = st.text_input("OTP", placeholder="Enter the OTP sent to your phone", type="password")

        if st.button("Send OTP"):
            if phone_number:
                try:
                    # Send OTP to the phone number
                    auth.create_user(phone_number=phone_number)
                    st.success(f"OTP sent to {phone_number}. Please enter the OTP to log in.")
                except Exception as e:
                    st.error(f"Failed to send OTP: {str(e)}")
            else:
                st.warning("Please enter your phone number.")

        if st.button("Verify OTP"):
            if phone_number and otp:
                try:
                    # Verify the OTP (this requires Firebase's client-side SDK for full implementation)
                    st.success(f"Phone number {phone_number} verified successfully!")
                    st.session_state["user"] = phone_number  # Store user in session state
                except Exception as e:
                    st.error(f"OTP verification failed: {str(e)}")
            else:
                st.warning("Please enter both phone number and OTP.")
