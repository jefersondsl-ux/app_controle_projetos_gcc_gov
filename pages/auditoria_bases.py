import streamlit as st
import pandas as pd
import re
import html

from components.cards import render_card

from services.carregar_bases import (
    carregar_controle,
    carregar_backlog,
    carregar_producao,
    carregar_diario,
    carregar_projetos
)
from services.reconciliar_chaves import enriquecer_com_d_projetos

def page_auditoria():

    st.markdown("## Auditoria de Bases")

    st.markdown(
        """
        Esta auditoria compara a dimensão de projetos (`d_Projetos`) com as bases de Controle, Diário, Backlog e Produção.
        Para a Produção, também tentamos preencher IDP faltante a partir do `CARIMBO_PREFIXO` usando a dimensão de projetos.
        
        - `Produção` pode faltar muitos `IDP_PROJETO` se a base analítica não tiver a coluna preenchida corretamente.
        - `Erro` na matriz indica falta de presença em qualquer das bases principais.
        """,
        unsafe_allow_html=True
    )

    # ==============================
    # CARREGAR BASES
    # ==============================

    df_controle = carregar_controle()
    df_backlog = carregar_backlog()
    df_producao = carregar_producao()
    df_diario = carregar_diario()
    df_d_projetos = carregar_projetos()

    # ==============================
    # VALIDAR ESTRUTURA DA PRODUÇÃO (BASE ANALÍTICA)
    # ==============================

    colunas_esperadas = [
        "IDP_PROJETO",
        "QTD_CIRCUITOS",
        "RECEITA_TOTAL",
        "DATA_ULTIMA_ATIVACAO"
    ]

    colunas_faltantes = [c for c in colunas_esperadas if c not in df_producao.columns]

    if colunas_faltantes:
        st.error(f"⚠ Base de produção analítica inválida. Colunas faltantes: {colunas_faltantes}")
        st.stop()

    # ==============================
    # PADRONIZAR CHAVES
    # ==============================

    for df in [df_controle, df_backlog, df_diario, df_d_projetos]:
        df["IDP_PROJETO"] = df["IDP_PROJETO"].astype(str).str.strip()

    if "IDP_PROJETO" not in df_producao.columns and "IDP" in df_producao.columns:
        df_producao["IDP_PROJETO"] = df_producao["IDP"]

    if "IDP_PROJETO" not in df_producao.columns:
        df_producao["IDP_PROJETO"] = ""

    df_producao["IDP_PROJETO"] = df_producao["IDP_PROJETO"].astype(str).str.strip()
    df_producao["IDP_PROJETO_ORIGINAL"] = df_producao["IDP_PROJETO"].copy()

    # preencher IDP_PROJETO em produção usando CARIMBO_PREFIXO e d_Projetos
    if "CARIMBO_PREFIXO" in df_producao.columns and not df_d_projetos.empty:
        df_producao = enriquecer_com_d_projetos(
            df_producao,
            df_d_projetos,
            chave_em_fato="CARIMBO_PREFIXO",
            chave_em_dim="CARIMBO_PREFIXO"
        )

    # ==============================
    # LISTAS DE PROJETOS
    # ==============================

    dim_proj = set(df_d_projetos["IDP_PROJETO"].unique())
    controle_proj = set(df_controle["IDP_PROJETO"].unique())
    diario_proj = set(df_diario["IDP_PROJETO"].unique())
    backlog_proj = set(df_backlog["IDP_PROJETO"].unique())
    producao_proj = set(df_producao["IDP_PROJETO"].unique())

    st.divider()

    # ==============================
    # CARDS DE AUDITORIA
    # ==============================
    tooltip_text = html.escape(
        "Se Controle tiver menos projetos que Diário, procure na matriz abaixo as linhas com ❌ na coluna Controle; "
        "elas são os projetos que estão faltando no Controle."
    )
    st.markdown(
        f"### Indicadores de cobertura <span title=\"{tooltip_text}\" "
        "style='color:#6b7280; cursor:help; font-size:0.9em;'>ℹ️</span>",
        unsafe_allow_html=True
    )

    total_dim = df_d_projetos["PROJETO"].nunique()
    total_controle = df_controle["PROJETO"].nunique()
    total_diario = df_diario["PROJETO"].nunique()

    inconsistentes = dim_proj - controle_proj

    c1, c2, c3, c4 = st.columns(4)

    with c1:
        render_card(
            "Projetos Dimensão",
            total_dim,
            "Universo de projetos únicos na dimensão d_Projetos.",
            "#60A5FA"
        )

    with c2:
        render_card(
            "Projetos Controle",
            total_controle,
            "Projetos únicos presentes na base Controle.",
            "#38BDF8"
        )

    with c3:
        render_card(
            "Projetos Diário",
            total_diario,
            "Projetos únicos presentes na base Diário.",
            "#FACC15"
        )

    with c4:
        render_card(
            "Projetos Inconsistentes",
            len(inconsistentes),
            "Projetos na dimensão que não aparecem na base Controle.",
            "#EF4444"
        )

    if len(inconsistentes) > 0:
        st.warning(f"⚠ {len(inconsistentes)} projetos apresentam inconsistência entre a dimensão e a base de Controle.")

    st.divider()

    # ==============================
    # MATRIZ DE VALIDAÇÃO
    # ==============================

    df_auditoria = df_d_projetos[["PROJETO", "IDP_PROJETO", "CLIENTE"]].copy()

    df_auditoria["Controle"] = df_auditoria["IDP_PROJETO"].apply(
        lambda x: "✔" if x in controle_proj else "❌"
    )

    df_auditoria["Diário"] = df_auditoria["IDP_PROJETO"].apply(
        lambda x: "✔" if x in diario_proj else "❌"
    )

    df_auditoria["Backlog"] = df_auditoria["IDP_PROJETO"].apply(
        lambda x: "✔" if x in backlog_proj else "❌"
    )

    df_auditoria["Produção"] = df_auditoria["IDP_PROJETO"].apply(
        lambda x: "✔" if x in producao_proj else "❌"
    )

    df_auditoria["Erro"] = (
        (df_auditoria["Controle"] == "❌") |
        (df_auditoria["Diário"] == "❌") |
        (df_auditoria["Backlog"] == "❌") |
        (df_auditoria["Produção"] == "❌")
    )

    df_auditoria = df_auditoria.sort_values(
        ["Erro", "PROJETO"],
        ascending=[False, True]
    )

    tooltip_text = html.escape(
        "Aqui você vai encontrar todos os Projetos/IDP's extraídos de todas as bases "
        "(Controle de Projetos, Backlog e Produção) e consolidados em uma dimensão "
        "d_Projetos que é, na prática, uma visão única de projetos baseada em prefixo "
        "de carimbo, IDP e cliente, com chaves calculadas para compatibilidade entre bases."
    )

    st.markdown(
        f"### Validação entre bases <span title=\"{tooltip_text}\" "
        "style='color:#6b7280; cursor:help; font-size:0.9em;'>ℹ️</span>",
        unsafe_allow_html=True
    )

    st.dataframe(
        df_auditoria.sort_values("IDP_PROJETO"),
        use_container_width=True,
        hide_index=True
    )

    st.markdown("### Diagnóstico de Produção e d_Projetos")

    df_prod_diag = df_producao.copy()
    if "IDP_PROJETO" not in df_prod_diag.columns:
        df_prod_diag["IDP_PROJETO"] = ""
    if "CARIMBO_PREFIXO" not in df_prod_diag.columns:
        df_prod_diag["CARIMBO_PREFIXO"] = ""
    if "CLIENTE" not in df_prod_diag.columns:
        df_prod_diag["CLIENTE"] = ""

    df_prod_diag["CARIMBO_PREFIXO"] = df_prod_diag["CARIMBO_PREFIXO"].astype(str).str.strip()
    df_prod_diag["CLIENTE"] = df_prod_diag["CLIENTE"].astype(str).str.strip()
    df_prod_diag["IDP_PROJETO"] = df_prod_diag["IDP_PROJETO"].astype(str).str.strip()

    production_without_idp = df_prod_diag[df_prod_diag["IDP_PROJETO"] == ""]
    clients_without_idp = (
        production_without_idp["CLIENTE"]
        .replace({"nan": "", "None": ""})
        .replace("", pd.NA)
        .dropna()
        .nunique()
    )

    production_prefixes = set(df_prod_diag["CARIMBO_PREFIXO"].dropna().unique())
    dproj_prefixes = set(
        df_d_projetos["CARIMBO_PREFIXO"].astype(str).str.strip().replace("nan", pd.NA).dropna().unique()
    )
    prefixes_missing_in_dproj = sorted(production_prefixes - dproj_prefixes)

    client_counts = (
        df_prod_diag[df_prod_diag["CLIENTE"] != ""]
        .groupby("CARIMBO_PREFIXO")["CLIENTE"]
        .nunique()
    )
    ambiguous_prefixes = client_counts[client_counts > 1].index.tolist()

    duplicate_prefixes_dproj = df_d_projetos[
        df_d_projetos["CARIMBO_PREFIXO"].duplicated(keep=False)
    ].copy()

    st.info(
        f"Produção sem IDP: {len(production_without_idp)} linha(s); "
        f"{clients_without_idp} cliente(s) distintos. "
        f"Prefixes de produção não mapeados em d_Projetos: {len(prefixes_missing_in_dproj)}. "
        f"Prefixes ambíguos (mesmo carimbo com mais de 1 cliente): {len(ambiguous_prefixes)}. "
        f"Duplicates em d_Projetos: {len(duplicate_prefixes_dproj)}."
    )

    with st.expander("Ver produção sem IDP"):
        if not production_without_idp.empty:
            st.dataframe(
                production_without_idp[
                    ["CARIMBO_PREFIXO", "CLIENTE", "IDP_PROJETO"]
                ].drop_duplicates(),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.write("Nenhuma linha de produção sem IDP encontrada no conjunto carregado.")

    with st.expander("Ver prefixes de produção não mapeados em d_Projetos"):
        if prefixes_missing_in_dproj:
            st.write("Prefixes de produção que não existem em d_Projetos:")
            st.write(prefixes_missing_in_dproj)
        else:
            st.write("Todos os prefixes de produção estão presentes em d_Projetos.")

    with st.expander("Ver prefixes ambíguos em produção"):
        if ambiguous_prefixes:
            ambiguous_rows = df_prod_diag[df_prod_diag["CARIMBO_PREFIXO"].isin(ambiguous_prefixes)]
            st.dataframe(
                ambiguous_rows[
                    ["CARIMBO_PREFIXO", "CLIENTE", "IDP_PROJETO"]
                ].drop_duplicates(),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.write("Nenhum prefixo ambíguo encontrado na produção.")

    with st.expander("Ver duplicidades de CARIMBO_PREFIXO em d_Projetos"):
        if not duplicate_prefixes_dproj.empty:
            st.dataframe(
                duplicate_prefixes_dproj[
                    ["CARIMBO_PREFIXO", "IDP_PROJETO", "PROJETO", "CLIENTE"]
                ].sort_values(["CARIMBO_PREFIXO", "IDP_PROJETO"]),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.write("Nenhuma duplicidade de CARIMBO_PREFIXO encontrada em d_Projetos.")

    st.markdown("#### Como encontrar projetos faltantes no Controle")
    st.markdown(
        "A tabela acima valida cada projeto da dimensão contra todas as bases. "
        "Linhas com ❌ na coluna `Controle` são projetos que existem na dimensão mas não aparecem no Controle. "
        "Se você tem mais projetos no Diário do que no Controle, esses casos costumam ser os que estão faltando no Controle."
    )

    df_falta_controle = df_auditoria[df_auditoria["Controle"] == "❌"].copy()
    df_falta_controle = df_falta_controle.sort_values(["Diário", "PROJETO"], ascending=[False, True])
    df_falta_controle_diario = df_falta_controle[df_falta_controle["Diário"] == "✔"]

    st.info(
        f"Mostrando {len(df_falta_controle)} projeto(s) ausentes no Controle, "
        f"dos quais {len(df_falta_controle_diario)} também aparecem no Diário."
    )

    with st.expander(f"Ver {len(df_falta_controle)} projeto(s) ausentes no Controle"):
        st.dataframe(
            df_falta_controle,
            use_container_width=True,
            hide_index=True
        )

    if len(df_falta_controle_diario) > 0:
        st.success(
            f"Desses, {len(df_falta_controle_diario)} estão presentes no Diário e ausentes no Controle. "
            "Use a tabela acima para identificar os projetos específicos."
        )

    st.markdown("### Auditoria por projeto")

    lista_idps = [
        str(x).strip()
        for x in df_d_projetos["IDP_PROJETO"].dropna().unique()
    ]
    lista_idps = sorted([x for x in lista_idps if x != ""])

    idp_sel = st.selectbox(
        "Selecione um IDP para inspeção detalhada",
        ["Todos"] + lista_idps,
        key="auditoria_idp_selecao"
    )

    if idp_sel != "Todos":

        controle_count = len(df_controle[df_controle["IDP_PROJETO"] == idp_sel])
        diario_count = len(df_diario[df_diario["IDP_PROJETO"] == idp_sel])
        backlog_count = len(df_backlog[df_backlog["IDP_PROJETO"] == idp_sel])
        producao_count = len(df_producao[df_producao["IDP_PROJETO"] == idp_sel])

        carimbos_projeto = []
        if "CARIMBO_PREFIXO" in df_d_projetos.columns:
            carimbos_projeto = (
                df_d_projetos[df_d_projetos["IDP_PROJETO"] == idp_sel]
                ["CARIMBO_PREFIXO"]
                .dropna()
                .astype(str)
                .str.strip()
                .unique()
                .tolist()
            )

        producao_carimbo_count = 0
        producao_carimbo_sem_idp = 0
        if carimbos_projeto and "CARIMBO_PREFIXO" in df_producao.columns:
            df_producao_carimbo = df_producao[df_producao["CARIMBO_PREFIXO"].astype(str).str.strip().isin(carimbos_projeto)]
            producao_carimbo_count = len(df_producao_carimbo)
            if "IDP_PROJETO" in df_producao_carimbo.columns:
                producao_carimbo_sem_idp = len(
                    df_producao_carimbo[df_producao_carimbo["IDP_PROJETO"].astype(str).str.strip() == ""]
                )
            else:
                producao_carimbo_sem_idp = len(df_producao_carimbo)
        else:
            df_producao_carimbo = pd.DataFrame()

        st.markdown(
            f"""
            **Resumo do projeto selecionado:**
            - Controle: {controle_count} registro(s)
            - Diário: {diario_count} registro(s)
            - Backlog: {backlog_count} registro(s)
            - Produção: {producao_count} registro(s)
            - Carimbos do projeto: {len(carimbos_projeto)}
            - Produção por carimbo: {producao_carimbo_count}
            - Produção por carimbo sem IDP: {producao_carimbo_sem_idp}
            """
        )

        with st.expander("Ver linhas de Produção relacionadas ao projeto"):
            if not df_producao_carimbo.empty:
                st.dataframe(
                    df_producao_carimbo.sort_values("DATA_ULTIMA_ATIVACAO", ascending=False),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.write("Nenhuma linha de Produção encontrada por carimbo para este projeto.")
    else:
        st.info("Selecione um projeto para ver o resumo detalhado de auditoria.")

    st.divider()

    # ==============================
    # AUDITORIA DA BASE DE PRODUÇÃO
    # ==============================

    st.markdown("### Auditoria da Produção")

    # garantir tipo data
    if "DATA_ULTIMA_ATIVACAO" in df_producao.columns:
        df_producao["DATA_ULTIMA_ATIVACAO"] = pd.to_datetime(
            df_producao["DATA_ULTIMA_ATIVACAO"],
            errors="coerce"
        )

    # criar cópia para filtro
    df_prod_auditoria = df_producao.copy()

    if "IDP_PROJETO" not in df_prod_auditoria.columns:
        df_prod_auditoria["IDP_PROJETO"] = ""

    df_prod_auditoria["IDP_PROJETO"] = df_prod_auditoria["IDP_PROJETO"].astype(str).str.strip()
    df_prod_auditoria["IDP_PROJETO_ORIGINAL"] = df_prod_auditoria["IDP_PROJETO"].copy()

    # Detectar projetos sem carimbo válido
    def validar_carimbo(valor):

        if pd.isna(valor):
            return False

        valor = str(valor).strip()

        # remove espaços duplicados
        valor = " ".join(valor.split())

        padrao = r"\b\d{1,4}/\d{2}\b"

        return bool(re.search(padrao, valor))

    df_prod_auditoria["CARIMBO_VALIDO"] = df_prod_auditoria["CARIMBO_PREFIXO"].apply(validar_carimbo)

    st.write("Carimbos válidos detectados:", df_prod_auditoria["CARIMBO_VALIDO"].sum())

    # remover linhas sem data, se existir a coluna
    if "DATA_PRODUZIDO" in df_prod_auditoria.columns:
        df_prod_auditoria = df_prod_auditoria.dropna(subset=["DATA_ULTIMA_ATIVACAO"])

    

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        data_ini = st.date_input(
            "Data inicial da produção",
            value=df_prod_auditoria["DATA_ULTIMA_ATIVACAO"].min().date() if not df_prod_auditoria.empty else None,
            key="auditoria_prod_data_ini"
        )

    with col2:
        data_fim = st.date_input(
            "Data final da produção",
            value=df_prod_auditoria["DATA_ULTIMA_ATIVACAO"].max().date() if not df_prod_auditoria.empty else None,
            key="auditoria_prod_data_fim"
        )

    with col3:

        lista_acao = ["Todos"]

        if "ACAO" in df_prod_auditoria.columns:
            lista_acao += sorted(
                df_prod_auditoria["ACAO"]
                .dropna()
                .astype(str)
                .str.strip()
                .unique()
                .tolist()
            )

        acao_sel = st.selectbox(
            "Ação",
            lista_acao,
            key="auditoria_prod_acao"
        )

    with col4:

        filtro_carimbo = st.selectbox(
            "Filtro Carimbo",
            ["Todos", "Somente com carimbo", "Sem carimbo"],
            key="auditoria_filtro_carimbo"
        )

    
    # aplicar filtro Carimbo
    if filtro_carimbo == "Somente com carimbo":
        df_prod_auditoria = df_prod_auditoria[df_prod_auditoria["CARIMBO_VALIDO"]]

    elif filtro_carimbo == "Sem carimbo":
        df_prod_auditoria = df_prod_auditoria[~df_prod_auditoria["CARIMBO_VALIDO"]]

    # aplicar filtro de período
    if "DATA_ULTIMA_ATIVACAO" in df_prod_auditoria.columns and data_ini and data_fim:

        df_prod_auditoria = df_prod_auditoria[
            (df_prod_auditoria["DATA_ULTIMA_ATIVACAO"] >= pd.to_datetime(data_ini)) &
            (df_prod_auditoria["DATA_ULTIMA_ATIVACAO"] <= pd.to_datetime(data_fim))
        ]

    # aplicar filtro de ação
    if acao_sel != "Todos" and "ACAO" in df_prod_auditoria.columns:
        df_prod_auditoria = df_prod_auditoria[
            df_prod_auditoria["ACAO"].astype(str).str.strip() == acao_sel
        ]

    # calcular clientes sem carimbo
    clientes_sem_carimbo = (
        df_prod_auditoria[~df_prod_auditoria["CARIMBO_VALIDO"]]["CLIENTE"]
        .dropna()
        .nunique()
    )

    # resumo rápido
    c1, c2, c3, c4, c5 = st.columns(5)

    with c1:
        render_card(
            "Linhas Produção Filtradas",
            len(df_prod_auditoria),
            "",
            "#22C55E"
        )

    with c2:
        qtd_circuitos = (
            df_prod_auditoria["COD_CIR"].nunique()
            if "COD_CIR" in df_prod_auditoria.columns else 0
        )

        render_card(
            "Circuitos Únicos",
            qtd_circuitos,
            "",
            "#60A5FA"
        )

    with c3:

        render_card(
            "Com Carimbo",
            df_prod_auditoria["CARIMBO_VALIDO"].sum(),
            "",
            "#22C55E"
        )

    with c4:

        render_card(
            "Sem Carimbo",
            (~df_prod_auditoria["CARIMBO_VALIDO"]).sum(),
            "",
            "#EF4444"
        )

    with c5:

        render_card(
            "Clientes sem Carimbo",
            clientes_sem_carimbo,
            "",
            "#F97316"
        )

    # ==============================
    # AUDITORIA DE IDP EM PRODUÇÃO
    # ==============================

    production_missing_idp = 0
    production_filled_by_carimbo = 0
    prod_idp_unique = 0

    if "IDP_PROJETO" in df_prod_auditoria.columns:
        production_missing_idp = (
            df_prod_auditoria["IDP_PROJETO"].astype(str).str.strip() == ""
        ).sum()

        if "IDP_PROJETO_ORIGINAL" in df_prod_auditoria.columns:
            production_filled_by_carimbo = (
                (df_prod_auditoria["IDP_PROJETO_ORIGINAL"].astype(str).str.strip() == "") &
                (df_prod_auditoria["IDP_PROJETO"].astype(str).str.strip() != "")
            ).sum()

        prod_idp_unique = (
            df_prod_auditoria["IDP_PROJETO"]
            .replace("", pd.NA)
            .dropna()
            .nunique()
        )

    col6, col7, col8 = st.columns(3)

    with col6:
        render_card(
            "Linhas sem IDP",
            production_missing_idp,
            "",
            "#EF4444"
        )

    with col7:
        render_card(
            "IDPs únicos Produção",
            prod_idp_unique,
            "",
            "#60A5FA"
        )

    with col8:
        render_card(
            "IDPs preenchidos por Carimbo",
            production_filled_by_carimbo,
            "",
            "#22C55E"
        )

    st.markdown("### Tabela Analítica da Produção")

    # ordenar corretamente pela nova lógica

    if "DATA_ULTIMA_ATIVACAO" in df_prod_auditoria.columns:

        df_prod_auditoria = df_prod_auditoria.sort_values(
            "DATA_ULTIMA_ATIVACAO",
            ascending=False
        )

    st.dataframe(
        df_prod_auditoria,
        use_container_width=True,
        hide_index=True
    )

    st.divider()

    