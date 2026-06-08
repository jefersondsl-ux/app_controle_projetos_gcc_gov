import streamlit as st
import pandas as pd

st.set_page_config(
    page_title="Controle de Projetos GCC GOV",
    layout="wide"
)

from components.sidebar import render_sidebar
from layout.header import render_header

from pages.visao_gerencial import page_visao_gerencial
from pages.visao_operacional import page_visao_operacional
from pages.planilha_inteligente import page_planilha_inteligente
from pages.auditoria_bases import page_auditoria
from pages.backlog_visao_geral import page_backlog_visao_geral
from pages.backlog_pendencias_tarefas import page_backlog_pendencias_tarefas

# NOVO
from services.carregar_bases import (
    
    carregar_controle,
    carregar_backlog,
    carregar_producao,
    carregar_diario,
    carregar_projetos
)

from services.calculos_kpi import calcular_kpis

# ==============================
# HEADER OCUPAR 100% DA LARGURA DO CONTAINER
# ==============================

st.markdown("""
<style>

/* REMOVE LIMITAÇÃO DE LARGURA DO STREAMLIT */
[data-testid="stAppViewContainer"] {
    max-width: 100%;
}

/* REMOVE PADDING LATERAL */
.block-container {
    padding-left: 1rem;
    padding-right: 1rem;
}

/* OPCIONAL: REMOVE ESPAÇO SUPERIOR */
.block-container {
    padding-top: 0.5rem;
}

</style>
""", unsafe_allow_html=True)

# ============================
# PADRÃO GLOBAL DE BOTÕES
# ============================

st.markdown("""
<style>

div.stButton > button {
    transition: all 0.2s ease;
    background-color: #1E293B;
    color: white;
    border-radius: 8px;
    border: 1px solid #334155;
    height: 42px;
    font-weight: 500;
}

/* hover */

div.stButton > button:hover {
    background-color: #3B82F6;
    border: 1px solid #3B82F6;
    color: white;
}

/* quando clica */

div.stButton > button:active {
    background-color: #2563EB;
    border: 1px solid #2563EB;
}

/* mantém azul quando selecionado */

div.stButton > button:focus {
    background-color: #2563EB;
    border: 1px solid #2563EB;
    box-shadow: none;
}

</style>
""", unsafe_allow_html=True)

# ==============================
# REMOVE MENU AUTOMÁTICO (Nativo do streamlit)
# ==============================

st.markdown("""
<style>

[data-testid="stSidebarNav"] {
    display: none;
}

</style>
""", unsafe_allow_html=True)

# ==============================
# CARREGAR BASES
# ==============================

df_controle = carregar_controle()
df_backlog = carregar_backlog()
df_producao = carregar_producao()
df_diario = carregar_diario()
df_projeto = carregar_projetos()

# ==============================
# KPIs BASEADOS 100% NA CONTROLE
# ==============================

df_ctrl = df_controle.copy()

# padronizar
df_ctrl["IDP_PROJETO"] = df_ctrl["IDP_PROJETO"].astype(str).str.strip()
df_ctrl["STATUS GERAL"] = df_ctrl["STATUS GERAL"].astype(str).str.strip()

# remover duplicidade
df_ctrl_proj = df_ctrl.drop_duplicates(subset="IDP_PROJETO")

total_projetos = df_ctrl_proj["IDP_PROJETO"].nunique()

projetos_novos = df_ctrl_proj[
    df_ctrl_proj["STATUS GERAL"] == "Novo"
]["IDP_PROJETO"].nunique()

projetos_parcial = df_ctrl_proj[
    df_ctrl_proj["STATUS GERAL"] == "Em andamento"
]["IDP_PROJETO"].nunique()

projetos_concluido = df_ctrl_proj[
    df_ctrl_proj["STATUS GERAL"] == "Concluído"
]["IDP_PROJETO"].nunique()

# última atualização
ultima_atualizacao = df_ctrl["DATA_BASE"].max() if "DATA_BASE" in df_ctrl.columns else ""

# ==============================
# PROJETOS PARADOS (BASE DIÁRIO)
# ==============================

from services.construir_tabela_analitica import construir_tabela_analitica

df_analitico = construir_tabela_analitica(
    df_projeto,
    df_controle,
    df_backlog,
    df_producao,
    df_diario
)

projetos_parados = df_analitico[
    df_analitico["DIAS_SEM_ATUALIZACAO"] > 30
]["IDP_PROJETO"].nunique()

kpis = {
    "total_projetos": total_projetos,
    "projetos_novos": projetos_novos,
    "projetos_parcial": projetos_parcial,
    "projetos_concluido": projetos_concluido,
    "projetos_parados": projetos_parados,
    "ultima_atualizacao": (
        pd.to_datetime(df_diario["DATA_REGISTRO"], errors="coerce")
        .max()
        .strftime("%d/%m/%Y")
        if pd.notnull(pd.to_datetime(df_diario["DATA_REGISTRO"], errors="coerce").max())
        else "-"
    )
}

# ==============================
# SIDEBAR
# ==============================

menu = render_sidebar()

# ==============================
# NAVEGAÇÃO
# ==============================

PAGINAS = {
    "Painel Consolidado": (page_visao_gerencial, True),
    "Painel Operacional": (page_visao_operacional, True),
    "Planilha Inteligente": (page_planilha_inteligente, True),
    "Auditoria das Bases": (page_auditoria, True),
    "Painel Backlog": (page_backlog_visao_geral, True),
    "Pendencias Backlog": (page_backlog_pendencias_tarefas, True)
}

if menu in PAGINAS:

    pagina, mostrar_cards = PAGINAS[menu]

    render_header(kpis, mostrar_cards=mostrar_cards)

    pagina()

#===========================================================
## FIM DO CÓDIGO
#===========================================================
# cd C:\Users\f282465\Projetos_Python\PRODUÇÃO\PROJETOS_GOV\app_gcc_gov_v2
# cd C:\Atlas_Local\Diario_Bordo_APP\app_gcc_gov_v2
# Ativar ambiente virtual: .venv\Scripts\activate 
# Rodar o app: streamlit run app.py