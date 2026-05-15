import io
import pandas as pd
import streamlit as st
from st_aggrid import AgGrid, GridOptionsBuilder, JsCode
import plotly.graph_objects as go

from services.carregar_bases import carregar_backlog
from services.pendencias_analytics import (
    preparar_base_pendencias,
    aplicar_filtros_pendencias,
    montar_matriz_cliente_tarefa,
    resumo_por_responsavel,
    colunas_detalhe_disponiveis,
)
from components.cards import render_card


def _gerar_excel(df_matriz, df_detalhe, df_resumo):
    output = io.BytesIO()

    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        df_matriz.to_excel(writer, index=False, sheet_name="Matriz_Resumida")
        df_detalhe.to_excel(writer, index=False, sheet_name="Detalhe_Circuitos")
        df_resumo.to_excel(writer, index=False, sheet_name="Resumo_Responsavel")

    return output.getvalue()


def _largura_coluna_por_titulo(titulo):
    tamanho = len(str(titulo))
    return min(max(110, tamanho * 9 + 24), 260)


def _estilo_celula_com_valor():
    return JsCode(
        """
        function(params) {
            if (params.value === null || params.value === undefined || params.value === '' || params.value === 0) {
                return {};
            }

            return {
                backgroundColor: '#F8FAFC',
                color: '#0F172A',
                fontWeight: '600'
            };
        }
        """
    )


def _estilo_linha_total():
    return JsCode(
        """
        function(params) {
            if (params.node && params.node.rowPinned === 'top') {
                return {
                    backgroundColor: '#020617',
                    color: 'white',
                    fontWeight: '700',
                    borderTop: '2px solid #38BDF8'
                };
            }
            return null;
        }
        """
    )


def _css_linha_total():
    return {
        ".ag-floating-top .ag-cell": {
            "background-color": "#020617 !important",
            "color": "white !important",
            "font-weight": "700 !important",
            "border-top": "2px solid #38BDF8 !important"
        },
        ".ag-floating-top .ag-row": {
            "background-color": "#020617 !important"
        },
        ".ag-floating-top": {
            "background-color": "#020617 !important"
        }
    }


def page_backlog_pendencias_tarefas():
    def _format_date(dt):
        if pd.isna(dt):
            return "Sem data"
        return pd.to_datetime(dt).strftime("%d/%m/%Y")

    def _format_datetime(dt):
        if pd.isna(dt):
            return "Sem data"
        return pd.to_datetime(dt).strftime("%d/%m/%Y %H:%M:%S")

    st.markdown("### Pendencias do Backlog por Tarefa")
    
    df_backlog = carregar_backlog()

    if df_backlog.empty:
        st.warning("Base de backlog nao carregada.")
        st.stop()

    ultima_atualizacao_bases = pd.NaT
    if "DATA_REPORT" in df_backlog.columns:
        ultima_atualizacao_bases = pd.to_datetime(df_backlog["DATA_REPORT"], errors="coerce").max()

    ultima_data_backlog = pd.NaT
    if "DATA_ENTRADA_BACKLOG" in df_backlog.columns:
        ultima_data_backlog = pd.to_datetime(df_backlog["DATA_ENTRADA_BACKLOG"], errors="coerce").max()

    st.markdown(
        f"""
        <div style="display:flex; justify-content:flex-end; align-items:flex-start; gap:24px; text-align:right; margin-bottom:16px;">
            <div style="min-width:170px;">
                <div style="font-size:12px; font-weight:700; line-height:1.0; color:#CBD5E1;">Última Atualização</div>
                <div style="font-size:14px; line-height:1.0; margin-top:2px; color:#F8FAFC;">{_format_datetime(ultima_atualizacao_bases)}</div>
            </div>
            <div style="min-width:170px;">
                <div style="font-size:12px; font-weight:700; line-height:1.0; color:#CBD5E1;">Última Entrada</div>
                <div style="font-size:14px; line-height:1.0; margin-top:2px; color:#F8FAFC;">{_format_date(ultima_data_backlog)}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    
    st.divider()

    df_base = preparar_base_pendencias(df_backlog)

    # Card com total de pendências e gráfico por tipo
    st.write("")  # Espaço vertical
    
    # Calcular totais
    backlog_total = df_base["COD_CIR"].nunique()
    
    # Tipos de tarefa que são pendências (interrupções)
    tipos_pendencia = ["Cliente", "Vendas", "Outras Interrupções", "Projetos Especiais"]
    df_pendencias = df_base[df_base["TAREFA_RESPONSAVEL"].isin(tipos_pendencia)]
    total_pendencias = df_pendencias["COD_CIR"].nunique()
    
    # Calcular percentual
    pct_pendencias = (total_pendencias / backlog_total * 100) if backlog_total > 0 else 0
    
    col_backlog, col_pendencias, col_gap, col_grafico = st.columns([0.62, 0.62, 0.28, 3.48])
    
    with col_backlog:
        render_card(
            titulo="Backlog Total",
            valor=f"{backlog_total}",
            cor="#64748B",
            title_size="10px",
            value_size="20px",
            subtitle_size="9px",
            card_height=140,
        )
    
    with col_pendencias:
        render_card(
            titulo="Pendências Total",
            valor=f"{total_pendencias}",
            subtitulo=f"{pct_pendencias:.1f}% do backlog",
            cor="#F97316",
            title_size="10px",
            value_size="20px",
            subtitle_size="9px",
            card_height=140,
        )
    
    with col_grafico:
        pendencias_por_tipo = df_pendencias.groupby("TAREFA_RESPONSAVEL")["COD_CIR"].nunique().sort_values(ascending=False)
        
        fig = go.Figure(data=[
            go.Bar(
                x=pendencias_por_tipo.index,
                y=pendencias_por_tipo.values,
                marker=dict(color=pendencias_por_tipo.values, colorscale="Viridis", showscale=False),
                text=pendencias_por_tipo.values,
                textposition="auto",
            )
        ])
        
        fig.update_layout(
            title="Pendências por Tipo de Interrupção",
            xaxis_title="Tipo",
            yaxis_title="Quantidade de Circuitos",
            height=320,
            showlegend=False,
            hovermode="x unified",
            margin=dict(l=10, r=10, t=50, b=10),
        )
        
        st.plotly_chart(fig, use_container_width=True)

    st.write("")  # Espaço vertical
    st.divider()

    eixo_y = st.radio(
        "Eixo Y da matriz",
        ["CLIENTE", "CARIMBO_PROJETO"],
        horizontal=True,
    )

    responsaveis_disponiveis = sorted(
        [x for x in df_base["TAREFA_RESPONSAVEL"].dropna().astype(str).unique() if x.strip()]
    )

    st.divider()
    st.markdown("#### Filtros")

    col1, col2, col3 = st.columns(3)

    with col1:
        filtro_responsaveis = st.multiselect(
            "TAREFA_RESPONSAVEL",
            responsaveis_disponiveis,
            default=responsaveis_disponiveis,
        )

        clientes_disponiveis = sorted(
            [x for x in df_base["CLIENTE"].dropna().astype(str).unique() if x.strip()]
        )
        filtro_clientes = st.multiselect("CLIENTE", clientes_disponiveis)

    with col2:
        classificacoes_disponiveis = sorted(
            [x for x in df_base["CLASSIFICACAO"].dropna().astype(str).unique() if x.strip()]
        )
        filtro_classificacao = st.multiselect("CLASSIFICACAO", classificacoes_disponiveis)

        estrategias_disponiveis = sorted(
            [x for x in df_base["ESTRATEGIA_REDES"].dropna().astype(str).unique() if x.strip()]
        )
        filtro_estrategia = st.multiselect("ESTRATEGIA_REDES", estrategias_disponiveis)

    with col3:
        gerentes_disponiveis = sorted(
            [x for x in df_base["GER_TEC_AJUST"].dropna().astype(str).unique() if x.strip()]
        )
        filtro_gerentes = st.multiselect("Gerente Técnico", gerentes_disponiveis)

        aging_disponivel = ["0-5", "6-15", "16-30", "31+", "Sem aging"]
        filtro_aging = st.multiselect("AGING_TAREFA (faixas)", aging_disponivel)

    df_filtrado = aplicar_filtros_pendencias(
        df_base,
        responsaveis=filtro_responsaveis,
        classificacoes=filtro_classificacao,
        estrategias=filtro_estrategia,
        gerentes_tecnicos=filtro_gerentes,
        aging_faixas=filtro_aging,
        clientes=filtro_clientes,
    )

    if df_filtrado.empty:
        st.warning("Nao ha dados para os filtros selecionados.")
        st.stop()

    matriz = montar_matriz_cliente_tarefa(
        df_filtrado,
        eixo_y=eixo_y,
    )

    if matriz.empty:
        st.warning("Nao ha matriz para os filtros selecionados.")
        st.stop()

    totais_matriz = {coluna: 0 for coluna in matriz.columns}
    totais_matriz[eixo_y] = "TOTAL GERAL"
    for coluna in matriz.columns:
        if coluna not in [eixo_y]:
            totais_matriz[coluna] = pd.to_numeric(matriz[coluna], errors="coerce").fillna(0).sum()

    linha_total = pd.DataFrame([totais_matriz])

    st.info(
        f"Registros filtrados: {len(df_filtrado)} | "
        f"Circuitos unicos: {df_filtrado['COD_CIR'].nunique()} | "
        f"{eixo_y.lower()} no eixo Y: {matriz[eixo_y].nunique()}"
    )

    st.markdown("#### Tabela dinamica")

    gb = GridOptionsBuilder.from_dataframe(matriz)
    gb.configure_default_column(resizable=True, sortable=True, filter=True, minWidth=120)
    gb.configure_column(eixo_y, pinned="left", minWidth=260)
    gb.configure_column("TOTAL", type=["numericColumn"], pinned="left", minWidth=110)

    for coluna in matriz.columns:
        if coluna in [eixo_y, "TOTAL"]:
            continue
        gb.configure_column(
            coluna,
            minWidth=_largura_coluna_por_titulo(coluna),
            cellStyle=_estilo_celula_com_valor(),
        )

    gb.configure_column(
        "TOTAL",
        type=["numericColumn"],
        pinned="left",
        minWidth=110,
        cellStyle=_estilo_celula_com_valor(),
    )

    gb.configure_grid_options(
        pinnedTopRowData=[linha_total.iloc[0].to_dict()]
    )

    grid_options = gb.build()

    AgGrid(
        matriz,
        gridOptions=grid_options,
        fit_columns_on_grid_load=False,
        allow_unsafe_jscode=True,
        custom_css=_css_linha_total(),
        height=420,
    )

    st.markdown("#### Drilldown")

    col_d1, col_d2 = st.columns(2)

    with col_d1:
        eixo_valor = st.selectbox(
            f"Selecionar {eixo_y}",
            options=matriz[eixo_y].astype(str).tolist(),
        )

    with col_d2:
        tarefas_disponiveis = ["Todas"] + [c for c in matriz.columns if c not in [eixo_y, "TOTAL"]]
        tarefa_valor = st.selectbox("Selecionar tarefa", options=tarefas_disponiveis)

    df_detalhe = df_filtrado[df_filtrado[eixo_y].astype(str) == str(eixo_valor)].copy()

    if tarefa_valor != "Todas":
        df_detalhe = df_detalhe[df_detalhe["TAREFA_LABEL"].astype(str) == str(tarefa_valor)]

    colunas_detalhe = colunas_detalhe_disponiveis(df_detalhe)
    if colunas_detalhe:
        df_detalhe = df_detalhe[colunas_detalhe].copy()

    df_detalhe = df_detalhe.sort_values(by=["AGING_TAREFA"], ascending=False, na_position="last")

    st.dataframe(df_detalhe, use_container_width=True, height=320)

    df_resumo_resp = resumo_por_responsavel(df_filtrado)

    st.markdown("#### Resumo por responsavel")
    st.dataframe(df_resumo_resp, use_container_width=True)

    excel_bytes = _gerar_excel(matriz, df_detalhe, df_resumo_resp)

    st.download_button(
        label="Baixar analise de pendencias (Excel)",
        data=excel_bytes,
        file_name="pendencias_backlog_cliente_tarefa.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )
