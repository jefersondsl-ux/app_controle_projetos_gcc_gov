import re
import streamlit as st
import pandas as pd
import io
from st_aggrid import JsCode
import streamlit.components.v1 as components

from services.carregar_bases import carregar_backlog
from services.backlog_analytics import resumo_backlog, resumo_estrategia, matriz_backlog_por_projeto
from components.cards import render_card
from services.carregar_bases import carregar_projetos
from st_aggrid import AgGrid, GridOptionsBuilder
from services.carregar_bases import carregar_controle

# ==============================
# FORMATAÇÃO MOEDA
# ==============================

def formatar_moeda(valor):
    if pd.isna(valor):
        return "R$ 0"
    valor = float(valor)
    if valor >= 1_000_000_000:
        return f"R$ {valor/1_000_000_000:.1f} Bi"
    elif valor >= 1_000_000:
        return f"R$ {valor/1_000_000:.1f} Mi"
    elif valor >= 1_000:
        return f"R$ {valor/1_000:.1f} K"
    else:
        return f"R$ {valor:,.0f}".replace(",", ".")
    
# ==============================

def page_backlog_visao_geral():

    st.divider()

    # ==============================
    # CARREGAR BASE
    # ==============================

    df_backlog = carregar_backlog()

    if df_backlog.empty:
        st.warning("Base de backlog não carregada.")
        st.stop()

    df_projetos = carregar_projetos()

    df_controle = carregar_controle()

    df_matriz = matriz_backlog_por_projeto(df_backlog, df_controle)

    # ==============================
    # RESUMOS
    # ==============================

    resumo = resumo_backlog(df_backlog)
    resumo_estrat = resumo_estrategia(df_backlog)

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

    # título e cards na mesma linha com alinhamento à direita
    title_col, spacer, data_col1, data_col2 = st.columns([3, 0.5, 1, 1])

    with title_col:
        st.markdown("### Painel Backlog")

    with data_col1:
        st.markdown("**Última Atualização**")
        st.markdown(f"<span style='font-size:18px'>{_format_datetime(ultima_atualizacao_bases)}</span>", unsafe_allow_html=True)
        #st.markdown("<span style='color:#94A3B8; font-size:12px'>Último DATA_REPORT carregado</span>", unsafe_allow_html=True)

    with data_col2:
        st.markdown("**Última Entrada**")
        st.markdown(f"<span style='font-size:18px'>{_format_date(ultima_data_backlog)}</span>", unsafe_allow_html=True)
        #st.markdown("<span style='color:#94A3B8; font-size:12px'>Última DATA_ENTRADA_BACKLOG</span>", unsafe_allow_html=True)

    st.divider()

    tab_geral, tab_estrategia = st.tabs([
        "Visão Geral",
        "Estratégia de Redes"
    ])

    with tab_geral:
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            render_card("Total Backlog", resumo["total"], "", "#F97316")

        with col2:
            render_card("Gross", resumo["gross"], "", "#F97316")

        with col3:
            render_card("Serviço", resumo["servico"], "", "#F97316")

        with col4:
            render_card("Outros", resumo["outros"], "", "#F97316")

        col1, col2, col3, col4, col5 = st.columns(5)

        with col1:
            render_card("Internet", resumo["internet"], "", "#F97316")

        with col2:
            render_card("Dados", resumo["dados"], "", "#F97316")

        with col3:
            render_card("Voz", resumo["voz"], "", "#F97316")

        with col4:
            render_card("WiFi", resumo["wifi"], "", "#F97316")

        with col5:
            render_card("Outros Produtos", resumo.get("outros_produtos", 0), "", "#F97316")

        st.divider()
        st.markdown("### 📈 Matriz Analítica por Cliente - Visão Geral")

        # ==============================
        # ORDENAR E ORGANIZAR COLUNAS
        # ==============================

        df_grid = df_matriz.sort_values("TOTAL", ascending=False)

        # ordem estratégica das colunas
        colunas_ordem = [
            "CLIENTE",
            "TOTAL",

            "GROSS",
            "SERVICO",
            "OUTROS",
            "INTERNET",
            "DADOS",
            "VOZ",
            "WIFI",
            "DELTA_RECEITA_GERAL",

            "FORECAST_INICIO_MES",
            "FORECAST_REGRA_COMERCIAL",
            "FORECAST_DELTA_RECEITA",
            "BACKLOG_ATUAL",
            "BACKLOG_REGRA_COMERCIAL",
            "BACKLOG_DELTA_RECEITA",
            "ESTRATEGIA",
            "PEND_CLIENTE",
            "PEND_VENDAS",
            "PEND_PJE",
            "SEM_CARIMBO",
            "SEM_CARIMBO_AGING",
            "DELTA_RECEITA_ESTRATEGIA",
            "REGRA_COMERCIAL_ESTRATEGIA",
            "FORECAST_MAI_2026",
            "FORECAST_JUN_2026",
            "MESES_RESTANTES",
            "FORECAST_AJUSTAR",
            "FORECAST_A_DEFINIR",
        ]

        # manter apenas colunas existentes (evita erro)
        colunas_existentes = [c for c in colunas_ordem if c in df_grid.columns]

        if "OUTROS" not in df_grid.columns:
            df_grid["OUTROS"] = df_grid["TOTAL"] - (df_grid["GROSS"] + df_grid["SERVICO"])

        df_grid = df_grid[colunas_existentes]

        # ==============================
        # RENOMEAR COLUNAS (DISPLAY)
        # ==============================

        def formatar_nome_forecast(col_name: str) -> str | None:
            match = re.match(r"^FORECAST_([A-Z]{3})_(\d{4})$", col_name)
            if not match:
                return None
            mes_token, ano = match.groups()
            meses = {
                "JAN": "Janeiro",
                "FEV": "Fevereiro",
                "MAR": "Março",
                "ABR": "Abril",
                "MAI": "Maio",
                "JUN": "Junho",
                "JUL": "Julho",
                "AGO": "Agosto",
                "SET": "Setembro",
                "OUT": "Outubro",
                "NOV": "Novembro",
                "DEZ": "Dezembro",
            }
            return f"{meses.get(mes_token, mes_token.capitalize())}/{ano}"

        mapa_renomeio = {
            "TOTAL": "TOTAL",
            "GROSS": "GROSS",
            "SERVICO": "SERVIÇO",
            "OUTROS": "OUTROS",
            "INTERNET": "INTERNET",
            "DADOS": "DADOS",
            "VOZ": "VOZ",
            "WIFI": "WIFI",
            "DELTA_RECEITA_GERAL": "Receita\nGeral",
            "ESTRATEGIA": "Estratégia\nde Redes",
            "DELTA_RECEITA_ESTRATEGIA": "Receita\nEstratégia",
            "REGRA_COMERCIAL_ESTRATEGIA": "Regra\nComercial\nEstratégia",
            "FORECAST_INICIO_MES": "Forecast\nInício Mês\n(Qtd)",
            "FORECAST_REGRA_COMERCIAL": "Regra\nComercial",
            "FORECAST_DELTA_RECEITA": "Receita\nForecast",
            "BACKLOG_ATUAL": "Backlog\nAtual\n(Qtd)",
            "BACKLOG_REGRA_COMERCIAL": "Regra\nComercial\nBacklog",
            "BACKLOG_DELTA_RECEITA": "Receita\nBacklog",
            "PEND_CLIENTE": "Cliente",
            "PEND_VENDAS": "Vendas",
            "PEND_PJE": "PJE",
            "MESES_RESTANTES": "Outros Meses",
            "FORECAST_AJUSTAR": "A ajustar",
            "FORECAST_A_DEFINIR": "A definir",
            "SEM_CARIMBO": "S/ Carimbo",
            "SEM_CARIMBO_AGING": "Dias S/ Carimbo",
        }

        for coluna in df_grid.columns:
            nome = formatar_nome_forecast(coluna)
            if nome:
                mapa_renomeio[coluna] = nome

        df_grid = df_grid.rename(columns=mapa_renomeio)

        # =============================    # FUNÇÃO EXPORTAR MATRIZ ANALÍTICA
        # =============================

        def gerar_excel(df):

            output = io.BytesIO()

            with pd.ExcelWriter(output, engine='openpyxl') as writer:
                df.to_excel(writer, index=False, sheet_name='Matriz_Analitica_Clientes')

            return output.getvalue()

        # =============================    # LINHA DE TOTAL
        # ==============================

        colunas_numericas = [
            "TOTAL",
            "GROSS",
            "SERVIÇO",
            "OUTROS",
            "INTERNET",
            "DADOS",
            "VOZ",
            "WIFI",
            "Receita\nGeral",
            "Estratégia\nde Redes",
            "Receita\nEstratégia",
            "Regra\nComercial\nEstratégia",
            "Forecast\nInício Mês\n(Qtd)",
            "Regra\nComercial",
            "Receita\nForecast",
            "Backlog\nAtual\n(Qtd)",
            "Regra\nComercial\nBacklog",
            "Receita\nBacklog",
            "Cliente",
            "Vendas",
            "PJE",
            "S/ Carimbo",
            "Outros Meses",
            "A ajustar",
            "A definir"
        ]

        # remover duplicatas para evitar erro de reindexação
        colunas_numericas = list(dict.fromkeys(colunas_numericas))

        # incluir colunas de forecast mensais dinâmicos, como Maio/2026 ou Junho/2026
        forecast_mensal = [
            c for c in df_grid.columns
            if isinstance(c, str) and re.match(r"^[A-Za-zÀ-ÿ]+/\d{4}$", c)
        ]
        colunas_numericas += forecast_mensal

        # garantir apenas colunas existentes
        colunas_numericas = [c for c in colunas_numericas if c in df_grid.columns]

        # calcular totais
        totais = df_grid[colunas_numericas].sum()

        # criar linha final
        linha_total = pd.DataFrame([totais])

        # adicionar identificador
        linha_total["CLIENTE"] = "TOTAL GERAL"

        # reordenar colunas usando reindex para preencher colunas faltantes com zero
        linha_total = linha_total.reindex(columns=df_grid.columns, fill_value=0)

        # concatenar com base
        df_grid = pd.concat([df_grid, linha_total], ignore_index=True)

        # ==============================
        # FIXAR TOTAL NO TOPO
        # ==============================

        df_total = df_grid[df_grid["CLIENTE"] == "TOTAL GERAL"]
        df_dados = df_grid[df_grid["CLIENTE"] != "TOTAL GERAL"]

        df_grid = pd.concat([df_total, df_dados], ignore_index=True)

        # ==============================
        # FORMATAR RECEITA (APÓS CALCULAR E FIXAR TOTAIS)
        # ==============================
        if "Receita\nGeral" in df_grid.columns:
            df_grid["Receita\nGeral"] = df_grid["Receita\nGeral"].apply(formatar_moeda)

        if "Receita\nEstratégia" in df_grid.columns:
            df_grid["Receita\nEstratégia"] = df_grid["Receita\nEstratégia"].fillna(0).apply(formatar_moeda)
        if "Forecast\nInício Mês\n(Qtd)" in df_grid.columns:
            df_grid["Forecast\nInício Mês\n(Qtd)"] = df_grid["Forecast\nInício Mês\n(Qtd)"].fillna(0).astype(int)
        if "Regra\nComercial" in df_grid.columns:
            df_grid["Regra\nComercial"] = df_grid["Regra\nComercial"].fillna(0)
        if "Regra\nComercial\nEstratégia" in df_grid.columns:
            df_grid["Regra\nComercial\nEstratégia"] = df_grid["Regra\nComercial\nEstratégia"].fillna(0)
        if "Receita\nForecast" in df_grid.columns:
            df_grid["Receita\nForecast"] = df_grid["Receita\nForecast"].fillna(0).apply(formatar_moeda)
        if "Backlog\nAtual\n(Qtd)" in df_grid.columns:
            df_grid["Backlog\nAtual\n(Qtd)"] = df_grid["Backlog\nAtual\n(Qtd)"].fillna(0).astype(int)
        if "Regra\nComercial\nBacklog" in df_grid.columns:
            df_grid["Regra\nComercial\nBacklog"] = df_grid["Regra\nComercial\nBacklog"].fillna(0)
        if "Receita\nBacklog" in df_grid.columns:
            df_grid["Receita\nBacklog"] = df_grid["Receita\nBacklog"].fillna(0).apply(formatar_moeda)

        # ============================================================================

        cell_style_total = JsCode("""
        function(params) {
            if (params.data && params.data.CLIENTE === 'TOTAL GERAL') {
                return {
                    'backgroundColor': '#020617',
                    'color': 'white',
                    'fontWeight': 'bold',
                    'borderTop': '2px solid #38BDF8'
                }
            }
            return null;
        }
        """)

        gb_geral = GridOptionsBuilder.from_dataframe(df_grid)
        gb_estrategia = GridOptionsBuilder.from_dataframe(df_grid)

        # ==============================
        # CABEÇALHOS POR GRUPO
        # ==============================

        colunas_backlog = [
            "TOTAL", "GROSS", "SERVIÇO",
            "INTERNET", "DADOS", "VOZ", "WIFI", "Receita\nGeral"
        ]

        colunas_backlog_atual = [
            "Backlog\nAtual\n(Qtd)",
            "Regra\nComercial\nBacklog",
            "Receita\nBacklog"
        ]

        colunas_estrategia = [
            "Estratégia\nde Redes",
            "Receita\nEstratégia",
            "Regra\nComercial\nEstratégia",
            "Forecast\nInício Mês\n(Qtd)",
            "Regra\nComercial",
            "Receita\nForecast",
            "Backlog\nAtual\n(Qtd)",
            "Regra\nComercial\nBacklog",
            "Receita\nBacklog",
            "Cliente",
            "Vendas",
            "PJE",
            "A ajustar",
            "Maio/2026",
            "Junho/2026",
            "Outros Meses",
            "A definir",
            "S/ Carimbo",
            "Dias S/ Carimbo"
        ]

        colunas_pendencias = ["Cliente", "Vendas", "PJE"]

        largura_coluna_backlog = 130
        largura_coluna_estrategia = 130

        for gb in (gb_geral, gb_estrategia):
            gb.configure_default_column(
                filter=True,
                sortable=True,
                resizable=True
            )

            gb.configure_column("CLIENTE", pinned="left")

        # DEFINIR CLASSES NO GRID

        for col in colunas_backlog:
            for gb in (gb_geral, gb_estrategia):
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    cellStyle=cell_style_total,
                    headerClass="header-backlog",
                    width=largura_coluna_backlog,
                    minWidth=largura_coluna_backlog,
                    maxWidth=largura_coluna_backlog,
                    suppressSizeToFit=True,
                    wrapHeaderText=True,
                    autoHeaderHeight=True
                )

        for col in colunas_backlog_atual:
            for gb in (gb_geral, gb_estrategia):
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    cellStyle=cell_style_total,
                    headerClass="header-backlog",
                    width=largura_coluna_backlog,
                    minWidth=largura_coluna_backlog,
                    maxWidth=largura_coluna_backlog,
                    suppressSizeToFit=True,
                    wrapHeaderText=True,
                    autoHeaderHeight=True
                )

        for col in colunas_estrategia:
            for gb in (gb_geral, gb_estrategia):
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    cellStyle=cell_style_total,
                    headerClass="header-estrategia",
                    width=largura_coluna_estrategia,
                    minWidth=largura_coluna_estrategia,
                    maxWidth=largura_coluna_estrategia,
                    suppressSizeToFit=True,
                    wrapHeaderText=True,
                    autoHeaderHeight=True
                )

        for col in colunas_pendencias:
            for gb in (gb_geral, gb_estrategia):
                gb.configure_column(
                    col,
                    type=["numericColumn"],
                    cellStyle=cell_style_total,
                    headerClass="header-pendencias",
                    width=largura_coluna_estrategia,
                    minWidth=largura_coluna_estrategia,
                    maxWidth=largura_coluna_estrategia,
                    suppressSizeToFit=True,
                    wrapHeaderText=True,
                    autoHeaderHeight=True
                )

        check_formatter = JsCode("""
        function(params) {
            if (params.value === null || params.value === undefined || params.value === "") {
                return "";
            }
            var num = Number(params.value);
            if (isNaN(num)) {
                return params.value;
            }
            return (num === 0 ? "✅ " : "⚠️ ") + params.value.toString();
        }
        """)

        for col in ["A ajustar", "A definir"]:
            for gb in (gb_geral, gb_estrategia):
                if col in df_grid.columns:
                    gb.configure_column(
                        col,
                        valueFormatter=check_formatter
                    )

        for coluna_pendencia in ["S/ Carimbo", "Dias S/ Carimbo"]:
            if coluna_pendencia in df_grid.columns:
                for gb in (gb_geral, gb_estrategia):
                    gb.configure_column(
                        coluna_pendencia,
                        type=["numericColumn"],
                        cellStyle=cell_style_total,
                        headerClass="header-pendencias",
                        width=largura_coluna_estrategia,
                        minWidth=largura_coluna_estrategia,
                        maxWidth=largura_coluna_estrategia,
                        suppressSizeToFit=True,
                        wrapHeaderText=True,
                        autoHeaderHeight=True
                    )

        # ocultar colunas de estratégia e backlog atual no geral
        for col in colunas_estrategia + colunas_backlog_atual:
            if col in df_grid.columns:
                gb_geral.configure_column(col, hide=True)

        # ocultar colunas de backlog geral no estratégico
        for col in colunas_backlog:
            if col in df_grid.columns:
                gb_estrategia.configure_column(col, hide=True)

        # -------------------------------------------------

        custom_css = {
            ".header-backlog": {
                "background-color": "#92400e !important",
                "color": "white !important",
                "font-weight": "700 !important",
                "text-align": "center !important",
                "display": "flex !important",
                "justify-content": "center !important",
                "align-items": "center !important"
            },
            ".header-backlog .ag-header-cell-label": {
                "justify-content": "center !important"
            },
            ".header-backlog .ag-header-cell-text": {
                "text-align": "center !important",
                "justify-content": "center !important",
                "width": "100% !important"
            },
            ".header-estrategia": {
                "background-color": "#facc15 !important",
                "color": "#1f2937 !important",
                "font-weight": "700 !important",
                "text-align": "center !important",
                "display": "flex !important",
                "justify-content": "center !important",
                "align-items": "center !important"
            },
            ".header-estrategia .ag-header-cell-label": {
                "justify-content": "center !important"
            },
            ".header-estrategia .ag-header-cell-text": {
                "text-align": "center !important",
                "justify-content": "center !important",
                "width": "100% !important"
            },
            ".header-pendencias": {
                "background-color": "#fecaca !important",
                "color": "#991b1b !important",
                "font-weight": "700 !important",
                "text-align": "center !important",
                "display": "flex !important",
                "justify-content": "center !important",
                "align-items": "center !important"
            },
            ".header-pendencias .ag-header-cell-label": {
                "justify-content": "center !important"
            },
            ".header-pendencias .ag-header-cell-text": {
                "text-align": "center !important",
                "justify-content": "center !important",
                "width": "100% !important"
            },
            ".ag-header-group-cell-label": {
                "justify-content": "center !important",
                "text-align": "center !important",
                "width": "100% !important"
            },
            ".ag-header-group-cell-text": {
                "text-align": "center !important",
                "justify-content": "center !important",
                "width": "100% !important"
            },
            ".ag-header-cell-label": {
                "justify-content": "center !important",
                "text-align": "center !important"
            },
            ".ag-header-cell-text": {
                "text-align": "center !important",
                "justify-content": "center !important"
            }
        }

        # -------------------------------------------------

        for gb in (gb_geral, gb_estrategia):
            gb.configure_column(
                "CLIENTE",
                pinned="left",
                cellStyle=cell_style_total,
                width=220,
                wrapHeaderText=True,
                autoHeaderHeight=True
            )

        grid_options_geral = gb_geral.build()
        grid_options_estrategia = gb_estrategia.build()

        # Agrupamento de cabeçalho para as três colunas de Forecast Início Mês
        if "columnDefs" in grid_options_estrategia:
            original_defs = grid_options_estrategia["columnDefs"]
            strategy_children = []
            forecast_inicio_children = []
            forecast_children = []
            backlog_children = []
            pendencias_children = []
            sem_carimbo_children = []
            ungrouped_defs = []
            sem_carimbo_child = None
            for col_def in original_defs:
                field = col_def.get("field")
                if field in ["Estratégia\nde Redes", "Regra\nComercial\nEstratégia", "Receita\nEstratégia"]:
                    child = col_def.copy()
                    if field == "Estratégia\nde Redes":
                        child["headerName"] = "Qtd"
                    elif field == "Regra\nComercial\nEstratégia":
                        child["headerName"] = "Regra"
                    elif field == "Receita\nEstratégia":
                        child["headerName"] = "Receita"
                    strategy_children.append(child)
                elif field in ["Forecast\nInício Mês\n(Qtd)", "Regra\nComercial", "Receita\nForecast"]:
                    child = col_def.copy()
                    if field == "Forecast\nInício Mês\n(Qtd)":
                        child["headerName"] = "Qtd"
                    elif field == "Regra\nComercial":
                        child["headerName"] = "Regra"
                    elif field == "Receita\nForecast":
                        child["headerName"] = "Receita"
                    forecast_inicio_children.append(child)
                elif field in ["Maio/2026", "Junho/2026", "Outros Meses", "A ajustar", "A definir"]:
                    child = col_def.copy()
                    forecast_children.append(child)
                elif field in ["Backlog\nAtual\n(Qtd)", "Regra\nComercial\nBacklog", "Receita\nBacklog"]:
                    child = col_def.copy()
                    if field == "Backlog\nAtual\n(Qtd)":
                        child["headerName"] = "Qtd"
                    elif field == "Regra\nComercial\nBacklog":
                        child["headerName"] = "Regra"
                    elif field == "Receita\nBacklog":
                        child["headerName"] = "Receita"
                    backlog_children.append(child)
                elif field in ["Cliente", "Vendas", "PJE"]:
                    child = col_def.copy()
                    pendencias_children.append(child)
                elif field == "S/ Carimbo":
                    child = col_def.copy()
                    child["headerName"] = "S/ Carimbo"
                    sem_carimbo_children.append(child)
                elif field == "Dias S/ Carimbo":
                    child = col_def.copy()
                    child["headerName"] = "Dias S/ Carimbo"
                    sem_carimbo_children.append(child)
                else:
                    ungrouped_defs.append(col_def)
            new_defs = []
            new_defs.extend(ungrouped_defs)
            if forecast_inicio_children:
                forecast_inicio_group_def = {
                    "headerName": "Forecast Início Mês",
                    "children": forecast_inicio_children
                }
                new_defs.append(forecast_inicio_group_def)
            if backlog_children:
                backlog_group_def = {
                    "headerName": "Backlog Atual",
                    "children": backlog_children
                }
                new_defs.append(backlog_group_def)
            if strategy_children:
                strategy_group_def = {
                    "headerName": "Backlog Total",
                    "children": strategy_children
                }
                new_defs.append(strategy_group_def)
            if pendencias_children:
                pendencias_group_def = {
                    "headerName": "Pendências",
                    "children": pendencias_children
                }
                new_defs.append(pendencias_group_def)
            if forecast_children:
                forecast_group_def = {
                    "headerName": "Forecast",
                    "children": forecast_children
                }
                new_defs.append(forecast_group_def)
            if sem_carimbo_children:
                sem_carimbo_group_def = {
                    "headerName": "Carimbo Projeto",
                    "children": sem_carimbo_children
                }
                new_defs.append(sem_carimbo_group_def)
            grid_options_estrategia["columnDefs"] = new_defs

        # Configurar auto-sizing baseado na documentação do AgGrid
        for grid_options in (grid_options_geral, grid_options_estrategia):
            grid_options['autoSizeStrategy'] = {
                'type': 'fitCellContents',
                'defaultMinWidth': 90,
                'columnLimits': [
                    {
                        'colId': 'CLIENTE',
                        'minWidth': 220
                    }
                ]
            }

        df_grid["IS_TOTAL"] = df_grid["CLIENTE"] == "TOTAL GERAL"

        df_grid_geral = df_grid[
            [
                c for c in [
                    "CLIENTE",
                    "TOTAL",
                    "GROSS",
                    "SERVIÇO",
                    "OUTROS",
                    "INTERNET",
                    "DADOS",
                    "VOZ",
                    "WIFI",
                    "Receita\nGeral",
                    "IS_TOTAL"
                ]
                if c in df_grid.columns
            ]
        ].copy()

        df_grid_estrategia = df_grid[
            (df_grid["Estratégia\nde Redes"] > 0) |
            (df_grid["CLIENTE"] == "TOTAL GERAL")
        ]

        df_grid_estrategia = df_grid_estrategia[
            [
                c for c in list(dict.fromkeys([
                    "CLIENTE",
                    "TOTAL",
                    "Forecast\nInício Mês\n(Qtd)",
                    "Regra\nComercial",
                    "Receita\nForecast",
                    "Backlog\nAtual\n(Qtd)",
                    "Regra\nComercial\nBacklog",
                    "Receita\nBacklog",
                    "Cliente",
                    "Vendas",
                    "PJE",
                    "Estratégia\nde Redes",
                    "Receita\nEstratégia",
                    "Regra\nComercial\nEstratégia",
                    "Maio/2026",
                    "Junho/2026",
                    "Outros Meses",
                    "A ajustar",
                    "A definir",
                    "S/ Carimbo",
                    "IS_TOTAL"
                ]))
                if c in df_grid_estrategia.columns
            ]
        ].copy()

        # =============================
        # BOTÃO DOWNLOAD EXCEL
        # =============================

        excel_bytes = gerar_excel(df_grid_geral.drop(columns=["IS_TOTAL"], errors='ignore'))
        excel_bytes_estrategia = gerar_excel(df_grid_estrategia.drop(columns=["IS_TOTAL"], errors='ignore'))

        st.download_button(
            label="📥 Baixar Matriz Analítica por Cliente (Excel)",
            data=excel_bytes,
            file_name="matriz_analitica_por_cliente.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        AgGrid(
            df_grid_geral,
            gridOptions=grid_options_geral,
            height=500,
            fit_columns_on_grid_load=False,
            theme="balham",
            allow_unsafe_jscode=True,
            custom_css=custom_css
        )

    with tab_estrategia:
        st.markdown("### Backlog - Estratégia de Redes")

        col1, col2, col3 = st.columns(3)

        with col1:
            render_card("Estratégia de Redes", resumo_estrat["total"], f"{resumo_estrat['perc']:.1f}% do Total", "#EAB308")

        with col2:
            render_card("Internet (Estratégia)", resumo_estrat["internet"], "", "#EAB308")

        with col3:
            render_card("Dados (Estratégia)", resumo_estrat["dados"], "", "#EAB308")

        st.divider()
        st.markdown("### 📈 Matriz Analítica por Cliente - Estratégia")

        st.download_button(
            label="📥 Baixar Matriz Analítica Estratégica por Cliente (Excel)",
            data=excel_bytes_estrategia,
            file_name="matriz_analitica_estrategia_por_cliente.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )

        AgGrid(
            df_grid_estrategia,
            gridOptions=grid_options_estrategia,
            height=500,
            fit_columns_on_grid_load=False,
            theme="balham",
            allow_unsafe_jscode=True,
            custom_css=custom_css
        )

    # ==============================
    # SELETOR DE CLIENTE
    # ==============================

    st.markdown("### 🔎 Detalhamento por Cliente")

    cliente_sel = st.selectbox(
        "Selecione o cliente",
        ["Todos"] + sorted(df_matriz["CLIENTE"].dropna().unique())
    )

    # FILTRAR BASE ORIGINAL

    if cliente_sel != "Todos":
        df_detalhe = df_backlog[df_backlog["CLIENTE"] == cliente_sel]
    else:
        df_detalhe = df_backlog.copy()

    # PREPARAR BASE PARA DRILL

    df_detalhe = df_detalhe.copy()

    df_detalhe["CLASSIFICACAO"] = df_detalhe["CLASSIFICACAO"].astype(str).str.upper().str.strip()
    df_detalhe["PRODUTO_AJUSTADO"] = df_detalhe["PRODUTO_AJUSTADO"].astype(str).str.upper().str.strip()

    df_detalhe["FLAG_ESTRATEGIA"] = (
        (df_detalhe["CLASSIFICACAO"] == "GROSS") &
        (df_detalhe["PRODUTO_AJUSTADO"].isin(["INTERNET", "DADOS"]))
    )

    # AGRUPAR POR CARIMBO (DRILL) 

    df_proj = (
        df_detalhe
        .groupby("CARIMBO_PROJETO", as_index=False)
        .agg(
            TOTAL=("CARIMBO_PROJETO", "count"),
            ESTRATEGIA=("FLAG_ESTRATEGIA", "sum")
        )
        .sort_values("TOTAL", ascending=False)
    )

    st.dataframe(
        df_proj,
        use_container_width=True,
        hide_index=True
    )

    # ==============================
    # TABELA BRUTA (DEBUG)
    # ==============================

    st.markdown("### 📄 Base Bruta Backlog (SGP)")

    st.dataframe(
        df_detalhe.head(200),
        use_container_width=True,
        hide_index=True
    )