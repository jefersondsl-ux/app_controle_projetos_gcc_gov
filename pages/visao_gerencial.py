import streamlit as st
import plotly.express as px
import pandas as pd
from components.cards import render_card
import os

from services.carregar_bases import (
    carregar_controle,
    carregar_backlog,
    carregar_producao,
    carregar_diario,
    carregar_projetos
    
)

from services.construir_tabela_analitica import construir_tabela_analitica

from services.calculos_kpi import calcular_kpis

from datetime import datetime



# =============================
# FUNÇÕES DE FORMATAÇÃO
# =============================

def format_int(valor):
    return f"{int(valor):,}".replace(",", ".")


def format_moeda(valor):

    if valor >= 1_000_000_000:
        return f"R$ {valor/1_000_000_000:.1f} Bi"

    elif valor >= 1_000_000:
        return f"R$ {valor/1_000_000:.1f} Mi"

    elif valor >= 1_000:
        return f"R$ {valor/1_000:.1f} K"

    else:
        return f"R$ {valor:,.0f}".replace(",", ".")


def page_visao_gerencial():
    #st.write("[🏗️ EM CONSTRUÇÃO]")

    # =============================
    # CARREGAR BASES
    # =============================

    df_controle = carregar_controle()
    df_backlog = carregar_backlog()
    df_producao = carregar_producao()
    df_diario = carregar_diario()
    df_d_projetos = carregar_projetos()
    
    #st.write(df_controle.columns)
    #st.write(df_producao.columns)
    #st.write(df_backlog.columns)
    #st.write(df_diario.columns)

    df_analitico = construir_tabela_analitica(
        df_d_projetos,
        df_controle,
        df_backlog,
        df_producao,
        df_diario
    )

    projetos_parados_analitico = len(
        df_analitico[
            df_analitico["DIAS_SEM_ATUALIZACAO"] > 10
        ]
    )

    # =============================
    # PADRONIZAÇÃO
    # =============================

    def padronizar_idp(df):
        df["IDP_PROJETO"] = (
            df["IDP_PROJETO"]
            .astype(str)
            .str.strip()
        )
        return df

    df_controle = padronizar_idp(df_controle)
    df_backlog = padronizar_idp(df_backlog)
    df_producao = padronizar_idp(df_producao)
    df_diario = padronizar_idp(df_diario)
    df_d_projetos = padronizar_idp(df_d_projetos)

    # ====================================
    # DEFINIR UNIVERSO DE PROJETOS (CARTEIRA)
    # ====================================

    lista_idp_controle = (
        df_controle["IDP_PROJETO"]
        .astype(str)
        .str.strip()
        .unique()
    )

    # Filtrar bases fato pelo controle

    df_backlog = df_backlog[
        df_backlog["IDP_PROJETO"].astype(str).str.strip().isin(lista_idp_controle)
    ]

    df_producao = df_producao[
        df_producao["IDP_PROJETO"].astype(str).str.strip().isin(lista_idp_controle)
    ]

    df_diario = df_diario[
        df_diario["IDP_PROJETO"].astype(str).str.strip().isin(lista_idp_controle)
    ]

    # ====================================
    # FILTRO DE PROJETO
    # ====================================

    st.sidebar.markdown("---")

    st.sidebar.markdown("### Status do Projeto")

    status_opcoes = ["Todos"] + sorted(
        df_controle["STATUS GERAL"]
        .dropna()
        .astype(str)
        .str.strip()
        .unique()
    )

    status_selecionado = st.sidebar.selectbox(
        "Status",
        status_opcoes
    )

    st.sidebar.markdown("### Filtro de Projeto")

    lista_projetos = sorted(df_d_projetos["PROJETO"].dropna().unique())

    projeto_selecionado = st.sidebar.selectbox(
        "Selecione o projeto",
        ["Todos"] + lista_projetos
    )

    # descobrir o IDP do projeto selecionado
    if projeto_selecionado != "Todos":

        idp_projeto = df_d_projetos.loc[
            df_d_projetos["PROJETO"] == projeto_selecionado,
            "IDP_PROJETO"
        ].iloc[0]

    # Aplicar o filtro nas bases

    if projeto_selecionado != "Todos":

        df_d_projetos = df_d_projetos[
            df_d_projetos["IDP_PROJETO"] == idp_projeto
        ]

        df_controle = df_controle[
            df_controle["IDP_PROJETO"] == idp_projeto
        ]

        df_backlog = df_backlog[
            df_backlog["IDP_PROJETO"] == idp_projeto
        ]

        df_producao = df_producao[
            df_producao["IDP_PROJETO"] == idp_projeto
        ]

        df_diario = df_diario[
            df_diario["IDP_PROJETO"] == idp_projeto
        ]

    # =============================
    # MATRIZ EXECUTIVA POR PROJETO
    # =============================

    # Padronizar chave
    df_backlog["IDP_PROJETO"] = df_backlog["IDP_PROJETO"].astype(str).str.strip()
    df_producao["IDP_PROJETO"] = df_producao["IDP_PROJETO"].astype(str).str.strip()
    df_d_projetos["IDP_PROJETO"] = df_d_projetos["IDP_PROJETO"].astype(str).str.strip()

    # Backlog por projeto
    backlog_proj = (
        df_backlog
        .groupby("IDP_PROJETO", as_index=False)
        .agg(
            Circuitos_Backlog=("COD_CIR", "count"),
            Receita_Backlog=("DELTA_RECEITA", "sum")
        )
    )

    # Produção já vem agregada (BASE ANALÍTICA)

    producao_proj = (
        df_producao
        .groupby("IDP_PROJETO", as_index=False)
        .agg(
            Circuitos_Producao=("QTD_CIRCUITOS", "sum"),
            Receita_Producao=("RECEITA_TOTAL", "sum")
        )
    )

    # garantir chave
    producao_proj["IDP_PROJETO"] = producao_proj["IDP_PROJETO"].astype(str).str.strip()

    # Matriz da carteira (Base = Controle)
    
    df_carteira = df_controle[
        [
            "PROJETO",
            "IDP_PROJETO",
            "STATUS GERAL",
            "DATA ASSINATURA CONTRATO",
            "DATA FINAL IMPLANTAÇÃO",
            "QTD CCTOS SOLICITADOS"            
        ]
    ].copy()

    df_carteira["DATA ASSINATURA CONTRATO"] = pd.to_datetime(
        df_carteira["DATA ASSINATURA CONTRATO"],
        errors="coerce"
    )

    df_carteira["DATA FINAL IMPLANTAÇÃO"] = pd.to_datetime(
        df_carteira["DATA FINAL IMPLANTAÇÃO"],
        errors="coerce"
    )

    df_carteira["IDP_PROJETO"] = df_carteira["IDP_PROJETO"].astype(str).str.strip()

    df_carteira = (
        df_carteira
        .drop_duplicates(subset="IDP_PROJETO")
    )

    df_matriz = (
        df_carteira
        .merge(backlog_proj, on="IDP_PROJETO", how="left")
        .merge(producao_proj, on="IDP_PROJETO", how="left")
    )

    # Renomear Status Geral
    df_matriz = df_matriz.rename(
        columns={"STATUS GERAL": "Status_Projeto"}
    )

    # Tratar nulos
    cols_num = [
        "Circuitos_Backlog",
        "Receita_Backlog",
        "Circuitos_Producao",
        "Receita_Producao"
    ]

    for col in cols_num:
        if col not in df_matriz.columns:
            df_matriz[col] = 0

    df_matriz[cols_num] = df_matriz[cols_num].fillna(0)
   
    # Totais
    df_matriz["Total_Circuitos"] = (
        df_matriz["Circuitos_Backlog"] +
        df_matriz["Circuitos_Producao"]
    )

    df_matriz["Receita_Total"] = (
        df_matriz["Receita_Backlog"] +
        df_matriz["Receita_Producao"]
    )

    # % conclusão
    df_matriz["Perc_Conclusao"] = (
    df_matriz["Circuitos_Producao"] / df_matriz["Total_Circuitos"].replace(0, 1)
    )

    df_matriz["Perc_Conclusao"] = df_matriz["Perc_Conclusao"].fillna(0) * 100
    df_matriz["Perc_Conclusao"] = df_matriz["Perc_Conclusao"].round(1)

    # ====================================
    # MÉTRICAS ANALÍTICAS
    # ====================================

    df_matriz["Perc_Backlog"] = (
        df_matriz["Circuitos_Backlog"] / df_matriz["Total_Circuitos"]
    )

    df_matriz["Perc_Backlog"] = df_matriz["Perc_Backlog"].fillna(0) * 100

    df_matriz["Ticket_Medio"] = (
        df_matriz["Receita_Total"] / df_matriz["Total_Circuitos"]
    )

    df_matriz["Ticket_Medio"] = df_matriz["Ticket_Medio"].fillna(0)

    # ==============================

    if status_selecionado != "Todos":
        df_matriz = df_matriz[
            df_matriz["Status_Projeto"] == status_selecionado
        ]

    # projetos filtrados pelo status
    projetos_filtrados = df_matriz["IDP_PROJETO"].unique()

    if status_selecionado != "Todos":

        df_controle = df_controle[
            df_controle["IDP_PROJETO"].isin(projetos_filtrados)
        ]

        df_backlog = df_backlog[
            df_backlog["IDP_PROJETO"].isin(projetos_filtrados)
        ]

        df_producao = df_producao[
            df_producao["IDP_PROJETO"].isin(projetos_filtrados)
        ]

        df_diario = df_diario[
            df_diario["IDP_PROJETO"].isin(projetos_filtrados)
        ]

    # Visão formatada para exibição
    df_matriz_view = df_matriz[
    [
        "PROJETO",
        "Status_Projeto",
        "DATA ASSINATURA CONTRATO",
        "DATA FINAL IMPLANTAÇÃO",
        "Circuitos_Backlog",
        "Circuitos_Producao",
        "Total_Circuitos",
        "Perc_Conclusao",
        "Receita_Backlog",
        "Receita_Producao",
        "Receita_Total",
        "Ticket_Medio"
        
    ]
    ].copy()

    df_matriz_view["Perc_Conclusao"] = df_matriz_view["Perc_Conclusao"].round(1).astype(str) + "%"
    
    df_matriz_view["DATA ASSINATURA CONTRATO"] = df_matriz_view["DATA ASSINATURA CONTRATO"].dt.strftime("%d/%m/%Y")
    df_matriz_view["DATA FINAL IMPLANTAÇÃO"] = df_matriz_view["DATA FINAL IMPLANTAÇÃO"].dt.strftime("%d/%m/%Y")

    df_matriz_view["Circuitos_Backlog"] = df_matriz_view["Circuitos_Backlog"].astype(int)
    df_matriz_view["Circuitos_Producao"] = df_matriz_view["Circuitos_Producao"].astype(int)
    df_matriz_view["Total_Circuitos"] = df_matriz_view["Total_Circuitos"].astype(int)

    df_matriz_view["Receita_Backlog"] = df_matriz_view["Receita_Backlog"].apply(format_moeda)
    df_matriz_view["Receita_Producao"] = df_matriz_view["Receita_Producao"].apply(format_moeda)
    df_matriz_view["Receita_Total"] = df_matriz_view["Receita_Total"].apply(format_moeda)
    
    df_matriz_view["Ticket_Medio"] = df_matriz_view["Ticket_Medio"].apply(format_moeda)

    # =============================
    # CÁLCULOS
    # =============================

    kpis = calcular_kpis(
        df_controle,
        df_backlog,
        df_producao,
        df_diario
        
    )

    kpis["projetos_parados"] = projetos_parados_analitico
    
    # =============================
    # RECEITAS OPERACIONAIS
    # =============================

    receita_producao = df_producao["RECEITA_TOTAL"].sum()
    receita_backlog = df_backlog["DELTA_RECEITA"].sum()

    receita_total_operacao = receita_producao + receita_backlog

    # ====================================
    # MATRIZ DE INDICADORES
    # ====================================

    df_indicadores = pd.DataFrame({

        "Indicador": [
            "Projetos",
            "Circuitos Backlog",
            "Circuitos Produção",
            "Total Circuitos"
        ],

        "Quantidade": [
            kpis["total_projetos"],
            kpis["circuitos_backlog"],
            kpis["circuitos_producao"],
            kpis["circuitos_total"]
        ],

        "Receita": [
            None,
            receita_backlog,
            receita_producao,
            receita_total_operacao
        ]

    })

    df_indicadores["Quantidade"] = df_indicadores["Quantidade"].apply(format_int)

    df_indicadores["Receita"] = df_indicadores["Receita"].apply(
        lambda x: format_moeda(x) if pd.notnull(x) else ""
    )

    # =============================
    # INTERFACE
    # =============================

    #st.markdown("## Painel Consolidado")

    if projeto_selecionado != "Todos":
        st.info(f"Visualizando projeto: {projeto_selecionado}")

    #st.divider()

    # =============================
    # KPI EXECUTIVO DO PORTFÓLIO
    # =============================

    qtde_cc = pd.to_numeric(
        df_controle["QTD CCTOS SOLICITADOS"],
        errors="coerce"
    ).fillna(0).sum() if "QTD CCTOS SOLICITADOS" in df_controle.columns else 0

    valor_total = pd.to_numeric(
        df_controle["VALOR CONTRATO"],
        errors="coerce"
    ).fillna(0).sum() if "VALOR CONTRATO" in df_controle.columns else 0

    receita_mensal = pd.to_numeric(
        df_controle["RECEITA MENSAL CONTRATUAL"],
        errors="coerce"
    ).fillna(0).sum() if "RECEITA MENSAL CONTRATUAL" in df_controle.columns else 0

    
    #st.markdown("### Resumo Executivo do Portfólio")

    c1, c2, c3 = st.columns(3)

    with c1:
        render_card("Circuitos Contratados", format_int(qtde_cc), "", "#38BDF8")

    with c2:
        render_card("Valor Total Projetos", format_moeda(valor_total), "", "#FACC15")

    with c3:
        render_card("Receita Mensal", format_moeda(receita_mensal), "", "#22C55E")

    st.divider()

    # ====================================
    # STATUS DA CARTEIRA (BASE = CONTROLE)
    # ====================================

    df_status = (
        df_controle[
            ["IDP_PROJETO", "STATUS MACRO", "VALOR CONTRATO"]
        ]
        .copy()
    )

    df_status["STATUS MACRO"] = (
        df_status["STATUS MACRO"]
        .astype(str)
        .str.strip()
    )

    df_status["VALOR CONTRATO"] = pd.to_numeric(
        df_status["VALOR CONTRATO"],
        errors="coerce"
    ).fillna(0)

    status_counts = (
        df_status
        .groupby("STATUS MACRO", as_index=False)
        .agg(
            Quantidade=("IDP_PROJETO", "nunique"),
            Valor_Total=("VALOR CONTRATO", "sum")
        )
    )

    status_counts = status_counts.rename(
        columns={"STATUS MACRO": "Status"}
    )

    # =============================
    # STATUS DA CARTEIRA
    # =============================
    st.markdown("### Status das Etapas")
    
    col_g1, col_g2 = st.columns([1, 1])

    with col_g1:
        fig_status = px.bar(
            status_counts,
            x="Status",
            y="Quantidade",
            text="Quantidade",
            color="Status",
            title="Distribuição da Qtde Projetos por Etapa"
        )

        fig_status.update_traces(textposition="outside")

        fig_status.update_layout(
            xaxis_title="Etapa (Macro)",
            yaxis_title="Qtde Projetos",
            margin=dict(t=50, b=10, l=10, r=10),
            showlegend=False
        )
        fig_status.update_layout(margin=dict(t=50, b=10, l=10, r=10))
        st.plotly_chart(fig_status, use_container_width=True)

    with col_g2:
        df_status_view = status_counts.copy()

        total = df_status_view["Quantidade"].sum()

        df_status_view["Valor Total Projetos"] = (
            df_status_view["Valor_Total"]
            .apply(format_moeda)
        )

        df_status_view["%"] = (
            df_status_view["Quantidade"] / total * 100
        ).round(1).astype(str) + "%"

        df_status_view = df_status_view[
            ["Status", "Quantidade", "Valor Total Projetos", "%"]
        ]

        st.dataframe(
            df_status_view,
            use_container_width=True,
            hide_index=True
        )

    st.divider()

    # =============================
    # PIPELINE DE IMPLANTAÇÃO
    # =============================

    """st.markdown("### Pipeline de Implantação")

    df_pipeline = pd.DataFrame({
        "Fase": ["Backlog", "Produção"],
        "Circuitos": [
            kpis["circuitos_backlog"],
            kpis["circuitos_producao"]
        ],
        "Receita": [
            receita_backlog,
            receita_producao
        ]
    })

    fig_pipeline = px.bar(
        df_pipeline,
        x="Fase",
        y="Circuitos",
        text="Circuitos",
        color="Fase",
        title="Backlog x Produção"
    )

    fig_pipeline.update_traces(textposition="outside")
    fig_pipeline.update_layout(margin=dict(t=50, b=10, l=10, r=10))

    st.plotly_chart(fig_pipeline, use_container_width=True)"""

    st.divider()

    # =============================
    # TOP PROJETOS
    # =============================

    st.markdown("### Top Projetos por Receita")

    df_top = (
        df_matriz.sort_values("Receita_Total", ascending=False)
        .head(10)
        .copy()
    )

    fig_top = px.bar(
        df_top,
        x="PROJETO",
        y="Receita_Total",
        text="Receita_Total",
        title="Top 10 Projetos por Receita Total"
    )

    fig_top.update_traces(
        texttemplate="%{text:,.0f}",
        textposition="outside"
    )

    fig_top.update_layout(
        margin=dict(t=50, b=10, l=10, r=10),
        xaxis_title="Projeto",
        yaxis_title="Receita Total"
    )

    st.plotly_chart(fig_top, use_container_width=True)

    st.divider()

    # =============================
    # TABELA EXECUTIVA
    # =============================

    st.markdown("### Tabela Executiva Consolidada")

    st.dataframe(
        df_matriz_view.sort_values("Total_Circuitos", ascending=False),
        use_container_width=True,
        hide_index=True
    )