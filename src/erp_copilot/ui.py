"""Streamlit chat UI for ERP Copilot. Talks to the FastAPI backend over HTTP.

Run: uv run streamlit run src/erp_copilot/ui.py
"""

import os

import httpx
import streamlit as st

DEFAULT_API_URL = os.environ.get("ERP_API_URL", "http://localhost:8000")
EXAMPLES = [
    "What is the total value of open sales orders?",
    "Which work orders are overdue?",
    "Show purchase orders that are still waiting to be received",
    "Who are our top customers by revenue?",
]

st.set_page_config(page_title="ERP Copilot", page_icon="📦")


def backend_is_up(api_url: str) -> bool:
    try:
        return httpx.get(f"{api_url}/health", timeout=3).status_code == 200
    except httpx.HTTPError:
        return False


def ask_backend(api_url: str, message: str) -> dict:
    """Return {"reply": str, "blocked": bool, "error": bool}."""
    try:
        response = httpx.post(f"{api_url}/chat", json={"message": message}, timeout=60)
    except httpx.HTTPError as exc:
        return {"reply": f"Could not reach the backend: {exc}", "blocked": False, "error": True}
    if response.status_code != 200:
        detail = response.json().get("detail", response.text) if response.content else response.text
        return {"reply": f"Backend error ({response.status_code}): {detail}", "blocked": False, "error": True}
    data = response.json()
    return {"reply": data["reply"], "blocked": data["blocked"], "error": False}


def render_message(message: dict) -> None:
    with st.chat_message(message["role"]):
        if message.get("error"):
            st.error(message["content"])
        elif message.get("blocked"):
            st.warning(message["content"])
        else:
            st.markdown(message["content"])


with st.sidebar:
    st.header("ERP Copilot")
    api_url = st.text_input("Backend URL", DEFAULT_API_URL).rstrip("/")
    if backend_is_up(api_url):
        st.success("Backend connected")
    else:
        st.error("Backend not reachable. Start it with `uv run erp-copilot`.")

    st.subheader("Try asking")
    clicked_example = None
    for example in EXAMPLES:
        if st.button(example, use_container_width=True):
            clicked_example = example

    if st.button("Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.title("📦 ERP Copilot")
st.caption("Ask about sales orders, purchase orders or work orders.")

if "messages" not in st.session_state:
    st.session_state.messages = []

for message in st.session_state.messages:
    render_message(message)

prompt = st.chat_input("Ask about your orders...") or clicked_example
if prompt:
    st.session_state.messages.append({"role": "user", "content": prompt})
    render_message(st.session_state.messages[-1])

    with st.spinner("Thinking..."):
        result = ask_backend(api_url, prompt)

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": result["reply"],
            "blocked": result["blocked"],
            "error": result["error"],
        }
    )
    render_message(st.session_state.messages[-1])
