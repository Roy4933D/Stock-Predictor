import streamlit as st

def home_page():
    st.title("User Dashboard")
    st.write("Welcome to your personalized dashboard!")
    st.markdown("""
    - [About](https://example.com/about)
    - [Resources](https://example.com/resources)
    """)
