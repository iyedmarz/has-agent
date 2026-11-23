"""Streamlit chat UI. Run with:  streamlit run src/has_agent/ui.py"""

from __future__ import annotations

import streamlit as st

from has_agent.agent import HASAgent

st.set_page_config(page_title="Assistant HAS (local)", page_icon="🩺", layout="wide")

VERDICT_LABEL = {
    "supported": ("✅ Réponse soutenue par les sources", "success"),
    "partially_supported": ("⚠️ Partiellement soutenue : vérifier les sources", "warning"),
    "unsupported": ("❌ Non soutenue par les sources", "error"),
    "unknown": ("Vérification indisponible", "info"),
}


@st.cache_resource(show_spinner="Chargement de l'index local…")
def get_agent() -> HASAgent:
    return HASAgent()


agent = get_agent()

with st.sidebar:
    st.title("🩺 Assistant HAS")
    st.caption("100 % local : modèle, index et journaux restent sur cette machine.")
    top_k = st.slider("Extraits récupérés (top-k)", 3, 12, agent.settings.top_k)
    verify = st.toggle("Vérifier l'ancrage de la réponse", value=True)
    st.divider()
    st.metric("Passages indexés", agent.retriever.size)
    st.caption(f"LLM : `{agent.settings.llm_model}`")
    st.caption(f"Embeddings : `{agent.settings.embed_model}`")
    if st.button("Nouvelle conversation"):
        st.session_state.messages = []
        st.rerun()

if "messages" not in st.session_state:
    st.session_state.messages = []


def render_sources(hits, cited):
    shown = cited or list(range(1, len(hits) + 1))
    with st.expander(f"Sources ({len(shown)})"):
        for n in shown:
            hit = hits[n - 1]
            st.markdown(f"**[{n}] {hit.title}** — `{hit.source}`, page {hit.page}")
            st.caption(hit.text[:600] + ("…" if len(hit.text) > 600 else ""))


def render_verdict(verdict, claims):
    if not verdict:
        return
    label, kind = VERDICT_LABEL.get(verdict, VERDICT_LABEL["unknown"])
    getattr(st, kind)(label)
    for claim in claims:
        st.caption(f"Affirmation non soutenue : {claim}")


for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and "hits" in message:
            render_verdict(message.get("verdict"), message.get("claims", []))
            render_sources(message["hits"], message["cited"])

question = st.chat_input("Posez une question sur les documents HAS…")
if question:
    history = [
        {"role": m["role"], "content": m["content"]} for m in st.session_state.messages
    ]
    st.session_state.messages.append({"role": "user", "content": question})
    with st.chat_message("user"):
        st.markdown(question)

    with st.chat_message("assistant"):
        placeholder = st.empty()
        buffer = []

        def on_token(token: str) -> None:
            buffer.append(token)
            placeholder.markdown("".join(buffer) + "▌")

        answer = agent.ask(question, history=history, top_k=top_k,
                           verify=verify, on_token=on_token)
        placeholder.markdown(answer.text)
        render_verdict(answer.verdict, answer.unsupported_claims)
        if answer.hits:
            render_sources(answer.hits, answer.cited)
        st.caption(
            f"{answer.seconds:.1f}s · Aide à la recherche documentaire, "
            "ne remplace pas l'avis d'un professionnel de santé."
        )

    st.session_state.messages.append(
        {
            "role": "assistant",
            "content": answer.text,
            "hits": answer.hits,
            "cited": answer.cited,
            "verdict": answer.verdict,
            "claims": answer.unsupported_claims,
        }
    )
