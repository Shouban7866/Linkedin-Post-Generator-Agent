import streamlit as st
import requests
import time

BACKEND_URL = "http://127.0.0.1:8000"

st.set_page_config(page_title="LinkedIn Post AI Agent", page_icon="🚀")

st.title("🚀 LinkedIn Agent (Human-in-the-Loop)")
st.caption("Apna topic likhein, AI draft review karein aur LinkedIn par post karein.")

if "session_thread_id" not in st.session_state:
    st.session_state.session_thread_id = f"thread_{int(time.time())}"
if "current_agent_state" not in st.session_state:
    st.session_state.current_agent_state = None

# Sidebar Controls
with st.sidebar:
    st.subheader("⚙️ Agent Settings")
    thread_id_input = st.text_input("Thread ID (Session)", value=st.session_state.session_thread_id)
    if thread_id_input != st.session_state.session_thread_id:
        st.session_state.session_thread_id = thread_id_input
        st.session_state.current_agent_state = None
        st.rerun()

    if st.button("🔄 Reset Session & New ID", use_container_width=True):
        st.session_state.session_thread_id = f"thread_{int(time.time())}"
        st.session_state.current_agent_state = None
        if "topic_input" in st.session_state:
            st.session_state.topic_input = ""
        st.success("Session reset successfully!")
        st.rerun()

# Topic text area with state binding
topic = st.text_area(
    "💡 What do you want to write about?",
    placeholder="e.g., Why building in public with FastAPI and LangGraph is a cheat code...",
    height=100,
    key="topic_input"
)

if not st.session_state.current_agent_state:
    if st.button("Draft First Version ✨", type="primary", use_container_width=True):
        if not topic.strip():
            st.error("Pehle koi topic toh likho!")
        else:
            with st.spinner("Communicating with Backend..."):
                try:
                    payload = {"topic": topic, "thread_id": st.session_state.session_thread_id}
                    res = requests.post(f"{BACKEND_URL}/start", json=payload)
                    if res.status_code == 200:
                        st.session_state.current_agent_state = res.json()
                        st.rerun()
                    else:
                        st.error(f"Backend Error: {res.text}")
                except Exception as e:
                    st.error(f"Connection Error: {str(e)}")

state = st.session_state.current_agent_state

if state:
    if state.get("is_paused"):
        st.write("---")
        st.subheader(f"📝 Reviewing Draft (Attempt {state['attempt']}/3)")

        st.info("💡 **AI Generated Draft:**")
        st.code(state["draft"], language="text")

        col1, col2 = st.columns(2)
        with col1:
            st.write("### Actions")
            if st.button("✅ Approve & Publish", type="primary", use_container_width=True):
                with st.spinner("Posting to LinkedIn..."):
                    try:
                        payload = {"user_action": "approved", "thread_id": st.session_state.session_thread_id}
                        res = requests.post(f"{BACKEND_URL}/submit_feedback", json=payload)
                        if res.status_code == 200:
                            st.session_state.current_agent_state = res.json()
                            st.rerun()
                    except Exception as e:
                        st.error(f"Request failed: {str(e)}")

        with col2:
            st.write("### Revision")
            feedback_text = st.text_input("💬 What should be changed?", placeholder="e.g., Make it shorter...",
                                          key="feedback_field")
            if st.button("🔄 Request Rewrite", use_container_width=True):
                if not feedback_text.strip():
                    st.warning("Feedback dena zaroori hai.")
                else:
                    with st.spinner("Regenerating..."):
                        try:
                            payload = {"user_action": feedback_text, "thread_id": st.session_state.session_thread_id}
                            res = requests.post(f"{BACKEND_URL}/submit_feedback", json=payload)
                            if res.status_code == 200:
                                st.session_state.current_agent_state = res.json()
                                st.rerun()
                        except Exception as e:
                            st.error(f"Request failed: {str(e)}")
    else:
        st.write("---")
        if state.get("is_approved"):
            st.success(f"🎉 Approved! Status: {state.get('api_status', '')}")
            st.subheader("📢 Published Post:")
            st.code(state["draft"], language="text")
        else:
            st.error("⚠️ Loop terminated. Max draft attempts reached.")
            st.subheader("Last Generated Draft:")
            st.code(state["draft"], language="text")

        if st.button("📝 Write Another Post", type="secondary", use_container_width=True):
            st.session_state.session_thread_id = f"thread_{int(time.time())}"
            st.session_state.current_agent_state = None
            st.session_state.topic_input = ""  # Input clear karega
            st.rerun()
