import streamlit as st
import requests
import os

ROUTER_URL = os.getenv("ROUTER_URL", "http://router:8000")

st.title("RAG Chatbot (AIOps Demo)")
query = st.text_input("Ask something:")

if st.button("Send") and query.strip():
    with st.spinner("Thinking..."):
        try:
            r = requests.post(f"{ROUTER_URL}/chat", json={"query": query}, timeout=40)
            if r.status_code == 200:
                res = r.json()
                st.markdown("**Answer:**")
                st.write(res.get("answer"))
                st.markdown("**Retrieved docs:**")
                for d in res.get("retrieved", []):
                    st.write("-", d[:300] + ("..." if len(d)>300 else ""))
            else:
                st.error(f"Error: {r.status_code} {r.text}")
        except Exception as e:
            st.error(f"Connection error: {e}")
