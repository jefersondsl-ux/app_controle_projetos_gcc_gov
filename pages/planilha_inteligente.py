# Responsável por:

# carregar bases
# chamar service analítico
# exibir tabela


import streamlit as st
import pandas as pd
import io
import streamlit.components.v1 as components

from components.cards import render_card

from services.carregar_bases import (
    carregar_backlog,
    carregar_producao,
    carregar_controle,
    carregar_diario,
    carregar_projetos,
    carregar_receita_historica
)

from services.construir_tabela_analitica import construir_tabela_analitica

from st_aggrid import AgGrid, GridOptionsBuilder

def page_planilha_inteligente():

    # =============================
    # CARREGAR BASES
    # =============================

    df_backlog           = carregar_backlog()
    df_producao          = carregar_producao()
    df_controle          = carregar_controle()
    df_diario            = carregar_diario()
    df_d_projetos        = carregar_projetos()
    df_receita_historica = carregar_receita_historica()

    # =============================
    # CONSTRUIR TABELA ANALÍTICA
    # =============================

    df = construir_tabela_analitica(
        df_d_projetos,
        df_controle,
        df_backlog,
        df_producao,
        df_diario,
        df_receita_historica=df_receita_historica
    )

    # =============================
    # RENOMEAR COLUNAS (APRESENTAÇÃO)
    # =============================

    # Os nomes originais do Backlog devem ser mantidos:
    # BACKLOG_TOTAL, BACKLOG_GROSS, BACKLOG_SERVICOS, BACKLOG_PJE,
    # BACKLOG_CLIENTE, BACKLOG_COMERCIAL, RECEITA_BACKLOG

    # Ajustar apenas nomes de exibição para produção no relatório.
    df = df.rename(columns={
        "Circuitos_Producao": "Produção Mês Atual",
        "Circuitos_Producao_Total": "Produção Total"
    })

    def _format_date(dt):
        if pd.isna(dt):
            return "Sem data"
        return pd.to_datetime(dt).strftime("%d/%m/%Y")

    def _format_datetime(dt):
        if pd.isna(dt):
            return "Sem data"
        return pd.to_datetime(dt).strftime("%d/%m/%Y %H:%M:%S")

    ultima_atualizacao_bases = pd.NaT
    if "DATA_REPORT" in df_backlog.columns:
        ultima_atualizacao_bases = pd.to_datetime(df_backlog["DATA_REPORT"], errors="coerce").max()

    ultima_data_backlog = pd.NaT
    if "DATA_ENTRADA_BACKLOG" in df_backlog.columns:
        ultima_data_backlog = pd.to_datetime(df_backlog["DATA_ENTRADA_BACKLOG"], errors="coerce").max()

    ultima_data_producao = pd.NaT
    data_colunas_producao = [
        "DATA_PRODUZIDO",
        "DATA_ULTIMA_ATIVACAO"
    ]

    date_col = next(
        (col for col in data_colunas_producao if col in df_producao.columns),
        None
    )

    if date_col is not None:
        data_producao = pd.to_datetime(df_producao[date_col], errors="coerce")
        hoje = pd.Timestamp.now().normalize()
        mes_atual = hoje.to_period("M")
        filtro_mes_atual = data_producao.dt.to_period("M") == mes_atual
        filtro_dia_anterior = data_producao.dt.normalize() < hoje
        filtro_producao_valida = filtro_mes_atual & filtro_dia_anterior
        if filtro_producao_valida.any():
            ultima_data_producao = data_producao[filtro_producao_valida].max()

    header_col, card1_col, card2_col, card3_col = st.columns([2.5, 1, 1, 1])

    with header_col:
        st.markdown("## Planilha Inteligente")

    with card1_col:
        render_card(
            "Última atualização das bases",
            _format_datetime(ultima_atualizacao_bases),
            "Data e hora do último processamento das bases SGP",
            "#0F4C81"
        )

    with card2_col:
        render_card(
            "Última Data de Entrada em Backlog",
            _format_date(ultima_data_backlog),
            "Data da base de Backlog SGP",
            "#7A5C00"
        )

    with card3_col:
        render_card(
            "Última Data de Produção",
            _format_date(ultima_data_producao),
            "Data da base de Produção SGP (analítica)",
            "#1B5E20"
        )

    st.divider()

    # =============================
    # FUNÇÃO EXPORTAR TABELA ANALÍTICA
    # =============================

    def gerar_excel(df):

        output = io.BytesIO()

        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Planilha_Inteligente')

        return output.getvalue()

    # =============================
    # LISTAS DE CLASSIFICAÇÃO (GLOBAL)
    # =============================

    cols_controle = [
        "IDP_PROJETO",
        "PROJETO",
        "PROJETO_CARIMBO",
        "OVERVIEW",
        "IDP",
        "DV",
        "GCC",
        "GP",
        "STATUS CADASTRO",
        "STATUS MACRO",
        "TECNOLOGIA",
        "DATA ASSINATURA CONTRATO",
        "DATA FINAL IMPLANTAÇÃO",
        "VALOR CONTRATO",
        "RECEITA MENSAL CONTRATUAL",
        "QTD PONTOS (CIRCUITOS)",
        "QTD CCTOS SOLICITADOS",
        "CCTOS CANCELADOS",
        "OBJETOS",
        "ORDEM"
    ]

    cols_producao = [
        "Produção Mês Atual",
        "Produção Total",
        "Receita_Producao"
    ]

    cols_backlog = [
        "BACKLOG_TOTAL",
        "BACKLOG_GROSS",
        "BACKLOG_SERVICOS",
        "BACKLOG_PJE",
        "BACKLOG_CLIENTE",
        "BACKLOG_COMERCIAL",
        "RECEITA_BACKLOG"
    ]

    cols_total = [
        "Total_Circuitos",
        "Receita_Total",
        "Perc_Conclusao"
    ]

    # =============================
    # LEGENDA
    # =============================

    components.html(
        """
        <div style="font-family:Segoe UI; color:white;">

            <div style="font-size:16px; font-weight:600; margin-bottom:10px;">
                Legenda
            </div>

            <div style="display:flex; flex-wrap:wrap; gap:12px;">

                <div style="display:flex; align-items:center; gap:6px;">
                    <div style="width:12px; height:12px; background:#0B3C5D; border-radius:50%;"></div>
                    <span>Controle de Projetos</span>
                </div>

                <div style="display:flex; align-items:center; gap:6px;">
                    <div style="width:12px; height:12px; background:#7A5C00; border-radius:50%;"></div>
                    <span>Backlog</span>
                </div>

                <div style="display:flex; align-items:center; gap:6px;">
                    <div style="width:12px; height:12px; background:#1B5E20; border-radius:50%;"></div>
                    <span>Produção</span>
                </div>

                <div style="display:flex; align-items:center; gap:6px;">
                    <div style="width:12px; height:12px; background:#064E3B; border-radius:50%;"></div>
                    <span>Total (Backlog + Produção)</span>
                </div>

                <div style="display:flex; align-items:center; gap:6px;">
                    <div style="width:12px; height:12px; background:#312E81; border-radius:50%;"></div>
                    <span>Última Observação</span>
                </div>

            </div>

        </div>
        """,
        height=90
    )

    # =============================
    # CONFIGURAR GRID (AGGRID)
    # =============================

    gb = GridOptionsBuilder.from_dataframe(df)

    # congelar primeira coluna
    gb.configure_column("PROJETO", pinned="left")

    # padrão
    gb.configure_default_column(
        resizable=True,
        filter=True,
        sortable=True,
        minWidth=120
    )

    # ajustes específicos
    gb.configure_column("PROJETO", minWidth=250)
    gb.configure_column("OBJETOS", minWidth=300)

    grid_options = gb.build()

    # =============================
    # GERAR CSS DINÂMICO (HEADER)
    # =============================

    custom_css = {
        ".ag-header-cell-label": {
            "justify-content": "center",
            "font-weight": "bold"
        }
    }

    def add_css(col, color):
        custom_css[f".ag-header-cell[col-id='{col}']"] = {
            "background-color": color,
            "color": "white"
        }

    for col in df.columns:

        if col in cols_controle:
            add_css(col, "#0B3C5D")

        elif col in cols_producao:
            add_css(col, "#1B5E20")

        elif col in cols_backlog:
            add_css(col, "#7A5C00")

        elif col in cols_total:
            add_css(col, "#064E3B")

        elif col.startswith("OBS_"):
            add_css(col, "#312E81")
    

    # =============================
    # BOTÃO DOWNLOAD EXCEL
    # =============================

    excel_bytes = gerar_excel(df)

    st.download_button(
        label="📥 Baixar Planilha Inteligente (Excel)",
        data=excel_bytes,
        file_name="planilha_inteligente.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    # =============================
    # RENDERIZAR GRID (AGGRID)
    # =============================

    AgGrid(
        df,
        gridOptions=grid_options,
        fit_columns_on_grid_load=True,
        height=450,
        custom_css=custom_css )
    