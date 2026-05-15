import streamlit as st

def render_sidebar():
    st.sidebar.markdown("# Páginas")

    menu = st.sidebar.radio(
        "Navegação",
        [
            "Painel Consolidado",
            "Painel Operacional",
            "Planilha Inteligente",
            "Auditoria das Bases",
            "Painel Backlog",
            "Pendencias Backlog"
        ]
    )

    return menu