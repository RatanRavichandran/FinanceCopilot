from __future__ import annotations

import io
from typing import Iterable

import streamlit as st

from ..services.llm import ChatMessage, LLMUnavailable, chat
from ..utils.contracts import anonymise_text, extract_text_from_pdf

SUPPORTED_TYPES = {"application/pdf", "text/plain"}


def _render_pdf_preview(file_bytes: bytes, max_pages: int = 2) -> None:
    try:
        import pdfplumber
    except ImportError:  # pragma: no cover - optional dependency
        st.info("Install pdfplumber to preview PDF pages.")
        return

    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        max_pages = min(max_pages, len(pdf.pages))
        for page_num in range(max_pages):
            page = pdf.pages[page_num]
            image = page.to_image(resolution=150).original
            st.image(image, caption=f"Page {page_num + 1}", use_column_width=True)


def _summarise_contract(anonymised_text: str) -> str:
    system_message = ChatMessage(
        role="system",
        content=(
            "You summarise legal agreements for business stakeholders. Keep outcomes concise with bullet"
            " sections covering parties, obligations, payments, tenure, termination, confidentiality, liability,"
            " governing law, and notable clauses."
        ),
    )
    user_message = ChatMessage(role="user", content=anonymised_text)
    return chat([system_message, user_message], max_tokens=500, temperature=0.3)


def render() -> None:  # pragma: no cover - Streamlit entry point
    st.title("Contract Intelligence Assistant")
    st.write(
        "Upload agreements, anonymise sensitive entities, and generate explainers that your business teams can act on."
    )

    uploaded = st.file_uploader("Upload a contract (PDF or TXT)", type=["pdf", "txt"])
    if not uploaded:
        st.info("Drag a file into the drop zone to begin.")
        return

    if uploaded.type not in SUPPORTED_TYPES:
        st.error("Unsupported file type. Please upload a PDF or plain text file.")
        return

    file_bytes = uploaded.getvalue()

    if uploaded.type == "application/pdf":
        raw_text = extract_text_from_pdf(io.BytesIO(file_bytes))
    else:
        raw_text = file_bytes.decode("utf-8")

    anonymised = anonymise_text(raw_text)

    col1, col2 = st.columns((1, 1))
    with col1:
        st.subheader("Source preview")
        if uploaded.type == "application/pdf":
            _render_pdf_preview(file_bytes)
        else:
            st.text_area("Source text", raw_text[:3000], height=300)

    with col2:
        st.subheader("Anonymised summary")
        try:
            summary = _summarise_contract(anonymised)
        except LLMUnavailable:
            summary = "Set OPENAI_API_KEY to enable contract summarisation."
        except Exception as exc:  # noqa: BLE001
            summary = f"Something went wrong while generating the summary: {exc}"
        st.markdown(summary)

    st.divider()

    st.subheader("Ask follow-up questions")
    st.caption("Questions run against the anonymised content so personally identifying information stays hidden.")

    if "contract_chat" not in st.session_state:
        st.session_state.contract_chat = []

    for message in st.session_state.contract_chat:
        role = "You" if message["role"] == "user" else "Assistant"
        st.markdown(f"**{role}:** {message['content']}")

    question = st.chat_input("What would you like to know?")
    if question:
        st.session_state.contract_chat.append({"role": "user", "content": question})
        try:
            messages: list[ChatMessage] = [
                ChatMessage(
                    role="system",
                    content="You are a legal assistant explaining the uploaded agreement in plain language.",
                ),
                ChatMessage(role="system", content=anonymised),
            ] + [ChatMessage(**msg) for msg in st.session_state.contract_chat]
            answer = chat(messages, max_tokens=400, temperature=0.4)
        except LLMUnavailable:
            answer = "Set OPENAI_API_KEY to enable question answering."
        except Exception as exc:  # noqa: BLE001
            answer = f"Unable to answer right now: {exc}"

        st.session_state.contract_chat.append({"role": "assistant", "content": answer})
        st.experimental_rerun()


__all__ = ["render"]
