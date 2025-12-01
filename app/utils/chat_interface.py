import streamlit as st
import google.generativeai as genai
import os

def setup_chat_interface(vector_store):
    """
    Sets up the chat interface and handles the Q&A logic.
    """
    st.divider()
    st.subheader("💬 Chat with ENSA Bot")
    
    # Configure Gemini
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        st.error("Google API Key not found. Please add it in the sidebar.")
        return
    
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-2.0-flash-lite')
    except Exception as e:
        st.error(f"Failed to configure Gemini: {e}")
        return
    
    # Chat History
    if "messages" not in st.session_state:
        st.session_state.messages = []

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # User Input
    if prompt := st.chat_input("Ask about ENSA Al Hoceima..."):
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Generate Response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                # Retrieve relevant documents
                docs = vector_store.similarity_search(prompt, k=3)
                context = "\n\n".join([doc.page_content for doc in docs])
                
                # System Prompt for Multilingual Support
                full_prompt = f"""You are an expert assistant for ENSA Al Hoceima (École Nationale des Sciences Appliquées d'Al Hoceima).
Your goal is to provide helpful, accurate answers about the school, its programs, departments, student life, and related topics.

INSTRUCTIONS:
1. ALWAYS base your answers on the provided context below.
2. Detect the language of the user's question (French, English, or Arabic/Darija) and reply in the SAME language.
3. If the context contains relevant information, provide a clear and complete answer.
4. If the context does NOT contain enough information to answer, say "I don't have enough information about that" in the user's language.
5. Be friendly and helpful.

CONTEXT FROM KNOWLEDGE BASE:
---
{context}
---

USER QUESTION: {prompt}

YOUR ANSWER:"""
                
                try:
                    response = model.generate_content(full_prompt)
                    result = response.text
                except Exception as e:
                    result = f"Sorry, I encountered an error: {str(e)}"
                
                st.markdown(result)
                st.session_state.messages.append({"role": "assistant", "content": result})
                
                # Show sources (Optional, good for debugging/learning)
                with st.expander("View Source Documents"):
                    for doc in docs:
                        st.write(doc.page_content)
