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
        model = genai.GenerativeModel('models/gemini-flash-lite-latest')
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
                
                # System Prompt for Multilingual Support + General Conversation
                full_prompt = f"""You are a friendly AI assistant for ENSA Al Hoceima (École Nationale des Sciences Appliquées d'Al Hoceima).

INSTRUCTIONS:
1. Detect the language of the user's message (French, English, or Arabic/Darija) and reply in the SAME language.

2. For GREETINGS and GENERAL CONVERSATION (like "hi", "hello", "how are you", "thank you", "bonjour", "salut", "merci", etc.):
   - Respond naturally and friendly
   - You can introduce yourself as the ENSA Al Hoceima AI Assistant
   - No need to use the context for these

3. For QUESTIONS ABOUT ENSA (programs, departments, student life, location, history, etc.):
   - Use ONLY the provided context to answer
   - If the context contains relevant information, provide a clear and complete answer
   - If the context does NOT contain enough information, say "I don't have enough information about that in my knowledge base" in the user's language

4. Be helpful, friendly, and concise.

CONTEXT FROM KNOWLEDGE BASE:
---
{context}
---

USER MESSAGE: {prompt}

YOUR RESPONSE:"""
                
                try:
                    response = model.generate_content(full_prompt)
                    result = response.text
                except Exception as e:
                    result = f"Sorry, I encountered an error: {str(e)}"
                
                st.markdown(result)
                st.session_state.messages.append({"role": "assistant", "content": result})
                
                # Show sources (Optional, good for debugging/learning)
                with st.expander("📚 View Source Documents"):
                    if docs:
                        for i, doc in enumerate(docs, 1):
                            st.markdown(f"**Source {i}:**")
                            st.write(doc.page_content[:500] + "..." if len(doc.page_content) > 500 else doc.page_content)
                            st.divider()
                    else:
                        st.write("No relevant documents found.")
