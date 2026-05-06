import re
import streamlit as st
import pandas as pd
import html
import streamlit.components.v1 as components

from services.carregar_bases import (
    carregar_controle,
    carregar_backlog,
    carregar_producao,
    carregar_diario
    
)

from services.carregar_bases import carregar_apontamentos

def page_visao_operacional():

    st.markdown("## Painel Operacional")

    st.markdown("""
    <style>
    ::-webkit-scrollbar {
        width: 6px;
    }
    ::-webkit-scrollbar-thumb {
        background: #475569;
        border-radius: 10px;
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
    df_d_apont = carregar_apontamentos()
    #st.write(df_d_apont.columns)

    df_d_apont.columns = df_d_apont.columns.str.strip().str.upper()

    df_d_apont["STATUS_MACRO"] = (
        df_d_apont["STATUS_MACRO"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # ==============================
    # IDENTIFICAR PROJETOS COM PENDÊNCIA
    # ==============================

    df_pend = df_diario.copy()

    df_pend.columns = df_pend.columns.str.strip().str.upper()

    if "PENDENCIA_APONTAMENTO" in df_pend.columns:

        df_pend["PENDENCIA_APONTAMENTO"] = (
            df_pend["PENDENCIA_APONTAMENTO"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        projetos_com_pendencia = set(
            df_pend.loc[
                df_pend["PENDENCIA_APONTAMENTO"] == "SIM",
                "PROJETO"
            ]
            .astype(str)
            .str.strip()
            .unique()
        )

    else:
        projetos_com_pendencia = set()

    # ==============================
    # SELEÇÃO DE PROJETO
    # ==============================

    lista_projetos_base = sorted(df_controle["PROJETO"].dropna().astype(str).unique())

    lista_projetos = []

    for proj in lista_projetos_base:

        if proj in projetos_com_pendencia:
            lista_projetos.append(f"{proj} ⚠️")
        else:
            lista_projetos.append(proj)

    projeto_display = st.selectbox(
        "Selecione o Projeto",
        lista_projetos
    )

    # remover o alerta do nome para buscar nas bases
    projeto = projeto_display.replace(" ⚠️", "")

    df_proj = df_controle[df_controle["PROJETO"] == projeto]

    st.divider()

    # ==============================
    # VERIFICAR PENDÊNCIAS DO PROJETO
    # ==============================

    df_pend_proj = df_diario.copy()

    df_pend_proj = df_pend_proj[
        df_pend_proj["PROJETO"].astype(str).str.strip() == str(projeto).strip()
    ].copy()

    if "PENDENCIA_APONTAMENTO" in df_pend_proj.columns:
        df_pend_proj["PENDENCIA_APONTAMENTO"] = (
            df_pend_proj["PENDENCIA_APONTAMENTO"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

    pendencias_abertas = len(
        df_pend_proj[
            df_pend_proj["PENDENCIA_APONTAMENTO"] == "SIM"
        ]
    )

    # ==============================
    # MOSTRAR ALERTA NO TOPO DA PÁGINA
    # ==============================

    mostrar_alerta_topo = False

    #st.markdown(f"### 🏛 {projeto}")
    if pendencias_abertas > 0 and mostrar_alerta_topo:

        st.markdown(
            f"""
            ## 🏛 {projeto}

            <div style="margin-top:6px; color:#EF4444; font-size:16px; font-weight:600;">
            ⚠️ Esse projeto possui {pendencias_abertas} pendência(s)
            </div>

            <div style="margin-top:4px; color:#FACC15; font-size:13px;">
            Obs: Para verificar o detalhamento da(s) Pendência(s) vá até a sessão 
            <b>"Gestão de Pendências"</b> no final da página.
            </div>
            """,
            unsafe_allow_html=True
        )

    else:

        st.markdown(f"## 🏛 {projeto}")

    st.markdown("---")

    # ==============================
    # DESCRIÇÃO DO PROJETO
    # ==============================

    st.markdown("### 📋 Descrição do Projeto")

    descricao = df_proj["OBJETOS"].iloc[0] if "OBJETOS" in df_proj.columns else ""
    descricao = str(descricao) if descricao is not None else ""
    descricao = re.sub(r"<[^>]+>", "", descricao)
    descricao = html.escape(descricao)

    st.markdown(
        f"""
        <div style="
            background:#1E293B;
            padding:18px;
            border-radius:10px;
            color:#CBD5E1;
            font-size:13px;
            line-height:1.6;
            white-space: normal;
            word-break: break-word;
        ">
        {descricao}
        </div>
        """,
        unsafe_allow_html=True
    )

    st.markdown("---")

    # ==============================
    # STATUS DO PROJETO
    # ==============================

    def get_col(df, nome_alvo: str):
        alvo = nome_alvo.strip().lower()
        for c in df.columns:
            if str(c).strip().lower() == alvo:
                return c
        return None


    st.markdown("### 🏷️ Status do Projeto")

    linha = df_proj.iloc[0]

    # mesmo padrão do código antigo
    col_carimbo = get_col(df_controle, "PROJETO_CARIMBO")
    carimbo_val = linha[col_carimbo] if col_carimbo else "-"

    if pd.isna(carimbo_val) or str(carimbo_val).strip() == "":
        carimbo_val = "-"
    else:
        carimbo_val = str(carimbo_val).strip()

    # =========================

    # status do projeto via backlog, igual ao código antigo
    status_val = "-"

# =========================
# PRIORIDADE 1: IDP_PROJETO
# =========================

    idp = str(linha.get("IDP_PROJETO", "")).strip()

    if "IDP_PROJETO" in df_backlog.columns:

        df_status_proj = df_backlog[
            df_backlog["IDP_PROJETO"].astype(str).str.strip() == idp
        ].copy()

    # =========================
    # FALLBACK: CARIMBO_PREFIXO
    # =========================

    if df_status_proj.empty and "CARIMBO_PREFIXO" in df_backlog.columns:

        carimbo_prefixo = str(carimbo_val).split(" - ")[0].strip()

        df_status_proj = df_backlog[
            df_backlog["CARIMBO_PREFIXO"].astype(str).str.strip() == carimbo_prefixo
        ].copy()

    # =========================
    # EXTRAIR STATUS
    # =========================

    if not df_status_proj.empty:

        df_status_proj["STATUS_PROJETO"] = (
            df_status_proj["STATUS_PROJETO"]
            .astype(str)
            .str.strip()
            .str.upper()
        )

        # status do projeto via backlog, igual ao código antigo
        status_val = "-"

        if "CARIMBO_PREFIXO" in df_backlog.columns and "STATUS_PROJETO" in df_backlog.columns:
            carimbo_prefixo = str(carimbo_val).split(" - ")[0].strip()

            df_status_proj = df_backlog[
                df_backlog["CARIMBO_PREFIXO"].astype(str).str.strip() == carimbo_prefixo
            ].copy()

            if not df_status_proj.empty:
                status_unicos = (
                    df_status_proj["STATUS_PROJETO"]
                    .dropna()
                    .astype(str)
                    .str.strip()
                    .unique()
                )

                if len(status_unicos) > 0:
                    status_val = status_unicos[0]

    # ==============================
    # STATUS MACRO (CONTROLE)
    # ==============================

    status_macro = "-"

    if "STATUS MACRO" in df_controle.columns:
        status_macro = str(linha.get("STATUS MACRO", "")).strip()

    # ==============================
    # STATUS DE COMPARAÇÃO
    # ==============================

    if status_val == "-" or status_val == "":
        status_comparacao = "SEM_SGP"
    elif status_macro == "-" or status_macro == "":
        status_comparacao = "SEM_MACRO"
    else:
        status_comparacao = "INFORMATIVO"

    #---------------------------------------------------

    col_status1, col_status2 = st.columns(2)

    with col_status1:
        st.markdown(
            f"""
            <div style="
                background:#1E293B;
                padding:16px;
                border-radius:10px;
                text-align:center;
            ">
                <div style="font-size:11px;color:#94A3B8;">
                    Carimbo Projeto
                </div>
                <div style="font-size:18px;color:white;font-weight:600;margin-top:6px;">
                    {carimbo_val}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_status2:

    # definir cor do card (baseado na consistência)
        
        if status_comparacao == "SEM_SGP":
            cor_borda = "#64748B"
            status_texto = "⚠ Sem status SGP"

        elif status_comparacao == "SEM_MACRO":
            cor_borda = "#FACC15"
            status_texto = "⚠ Sem status Macro"

        else:
            cor_borda = "#38BDF8"
            status_texto = "ℹ Comparação apenas informativa"


        st.markdown(f"""
        <div style="
            background:#1E293B;
            padding:14px;
            border-radius:10px;
            border-left:4px solid {cor_borda};
            margin-bottom:10px;
        ">

        <div style="font-size:11px;color:#94A3B8;">
        Status do Projeto
        </div>

        <div style="font-size:13px;color:#CBD5E1;margin-top:6px;">
        <b>SGP:</b> {status_val if status_val != "-" else "Não encontrado"}
        </div>

        <div style="font-size:13px;color:#CBD5E1;margin-top:4px;">
        <b>CONTROLE:</b> {status_macro if status_macro != "-" else "Não definido"}
        </div>

        <div style="font-size:12px;color:{cor_borda};margin-top:8px;font-weight:600;">
        {status_texto}
        </div>

        </div>
        """, unsafe_allow_html=True)    

    st.markdown("---")

    # =======================================================
    # 📊 INDICADORES OPERACIONAIS
    # =======================================================

    st.markdown("### 📡 Indicadores Operacionais")

    # garantir limpeza de dados
    df_backlog["CARIMBO_PREFIXO"] = df_backlog["CARIMBO_PREFIXO"].astype(str).str.strip()
    df_producao["CARIMBO_PREFIXO"] = df_producao["CARIMBO_PREFIXO"].astype(str).str.strip()

    carimbo_prefixo = str(carimbo_val).split(" - ")[0].strip()

    qtd_backlog = df_backlog[
        df_backlog["CARIMBO_PREFIXO"] == carimbo_prefixo
    ]["COD_CIR"].nunique()

    df_proj = df_producao[
        df_producao["CARIMBO_PREFIXO"] == carimbo_prefixo
    ]

    if not df_proj.empty:
        qtd_produzido = int(df_proj["QTD_CIRCUITOS"].iloc[0])
    else:
        qtd_produzido = 0

    if (qtd_backlog + qtd_produzido) > 0:
        perc_conversao = round(
            (qtd_produzido / (qtd_backlog + qtd_produzido)) * 100
        )
    else:
        perc_conversao = 0

    col_op1, col_op2, col_op3 = st.columns(3)

    def card_exec(titulo, valor):

        st.markdown(
            f"""
            <div style="
                background:#1E293B;
                padding:16px;
                border-radius:10px;
                text-align:center;
            ">
                <div style="font-size:11px;color:#94A3B8;">
                    {titulo}
                </div>
                <div style="font-size:18px;color:white;font-weight:600;margin-top:6px;">
                    {valor}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    with col_op1:
        card_exec("Qtd Backlog", qtd_backlog)

    with col_op2:
        card_exec("Qtd Produzidos", qtd_produzido)

    with col_op3:
        card_exec("% Conversão", f"{perc_conversao}%")

    st.markdown("---")

    # =======================================================
    # 📄 DADOS CONTRATUAIS
    # =======================================================

    st.markdown("### 📄 Dados Contratuais")

    def formatar_inteiro(valor):
        try:
            return f"{int(float(valor)):,}".replace(",", ".")
        except:
            return "-"

    def formatar_moeda_br(valor):
        try:
            valor = float(valor)
            inteiro = int(valor)
            centavos = int(round((valor - inteiro) * 100))
            inteiro_formatado = f"{inteiro:,}".replace(",", ".")
            return f"R$ {inteiro_formatado},{centavos:02d}"
        except:
            return "R$ 0,00"
        
    # Primeira linha de cards

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        card_exec("IDP Projeto", linha.get("IDP_PROJETO", "-"))

    with col2:
        card_exec("Cliente", linha.get("CLIENTE", "-"))

    with col3:
        card_exec("Tecnologia", linha.get("TECNOLOGIA", "-"))

    with col4:
        card_exec(
            "Qtd Pontos (Circuitos)",
            formatar_inteiro(linha.get("QTD PONTOS (CIRCUITOS)", 0))
        )

    # Segunda linha de cards

    st.markdown("<br>", unsafe_allow_html=True)

    col5, col6, col7, col8 = st.columns(4)

    with col5:
        card_exec(
            "Qtd Cctos Solicitados",
            formatar_inteiro(linha.get("QTD CCTOS SOLICITADOS", 0))
        )

    with col6:
        card_exec(
            "Valor Contrato",
            formatar_moeda_br(linha.get("VALOR CONTRATO", 0))
        )

    with col7:
        card_exec(
            "Receita Mensal",
            formatar_moeda_br(linha.get("RECEITA MENSAL CONTRATUAL", 0))
        )

    with col8:
        card_exec(
            "Vigência (meses)",
            formatar_inteiro(linha.get("VIGÊNCIA CONTRATO (MESES)", 0))
        )

    st.markdown("---")

    # =======================================================
    # 📄 INDICADORES E PRAZOS
    # =======================================================

    st.markdown("### 📅 Indicadores de Prazo")

    data_assinatura = pd.to_datetime(linha.get("DATA ASSINATURA CONTRATO"), errors="coerce")
    data_final_implantacao = pd.to_datetime(linha.get("DATA FINAL IMPLANTAÇÃO"), errors="coerce")
    previsao_rede = pd.to_datetime(linha.get("PREVISÃO CONCLUSÃO DA REDE"), errors="coerce")

    hoje = pd.Timestamp.today().normalize()

    def formatar_data(dt):
        return dt.strftime("%d/%m/%Y") if pd.notna(dt) else "-"
    
    # Status prazo
    
    if pd.notna(data_final_implantacao):

        if hoje <= data_final_implantacao:
            status_prazo = "Em Dia"
            cor_prazo = "#10B981"

        elif (hoje - data_final_implantacao).days <= 15:
            status_prazo = "Atenção"
            cor_prazo = "#FACC15"

        else:
            status_prazo = "Atrasado"
            cor_prazo = "#EF4444"

    else:

        status_prazo = "Sem Data"
        cor_prazo = "#64748B"

    # Cards de datas

    col_d1, col_d2, col_d3, col_d4 = st.columns(4)

    with col_d1:
        card_exec("Data Assinatura", formatar_data(data_assinatura))

    with col_d2:
        card_exec("Data Final Implantação", formatar_data(data_final_implantacao))

    with col_d3:
        card_exec("Previsão Conclusão Rede", formatar_data(previsao_rede))

    with col_d4:
        st.markdown(
            f"""
            <div style="
                background:#1E293B;
                padding:16px;
                border-radius:10px;
                text-align:center;
            ">
                <div style="font-size:11px;color:#94A3B8;">
                    Prazo Implantação
                </div>
                <div style="font-size:18px;color:{cor_prazo};font-weight:600;margin-top:6px;">
                    {status_prazo}
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    # =======================================================
    # 📄 RESPONSÁVEIS PELO PROJETO
    # =======================================================

    st.markdown("---")
    st.markdown("### 👥 Responsáveis pelo Projeto")

    col_r1, col_r2, col_r3, col_r4, col_r5, col_r6 = st.columns(6)

    with col_r1:
        card_exec("Gerente Projeto (GP)", linha.get("GP", "-"))

    with col_r2:
        card_exec("Gerente Comercial (GC)", linha.get("GC", "-"))

    with col_r3:
        card_exec("Consultor Solução (CSOL)", linha.get("CSOL", "-"))

    with col_r4:
        card_exec("Coordenador de Entrega Cliente", linha.get("CEC", "-"))

    with col_r5:
        card_exec("Gerente Coordenação Cliente (GCC)", linha.get("GCC", "-"))

    with col_r6:
        card_exec("Gerente Técnico (GT)", linha.get("COORDENADOR", "-"))

    st.markdown("---")

    # =======================================================
    # CARDS POR ETAPA
    # =======================================================

    #1. Preparar base dos cards

    df_cards = df_diario.copy()

    df_cards = df_cards[
        df_cards["PROJETO"].astype(str).str.strip() == str(projeto)
    ].copy()

    df_cards.columns = df_cards.columns.str.strip().str.upper()

    df_cards.columns = df_cards.columns.str.strip().str.upper()

    df_d_apont.columns = df_d_apont.columns.str.strip().str.upper()

    if "APONTAMENTO_SK" not in df_cards.columns:
        st.error("Coluna APONTAMENTO_SK não existe no df_diario")
        st.stop()

    if "APONTAMENTO_SK" not in df_d_apont.columns:
        st.error("Coluna APONTAMENTO_SK não existe na d_apontamentos")
        st.stop()

    if "STATUS_MACRO" not in df_d_apont.columns:
        st.error("Coluna STATUS_MACRO não existe na d_apontamentos")
        st.stop()

    # merge com dimensão
    df_cards["APONTAMENTO_SK"] = pd.to_numeric(df_cards["APONTAMENTO_SK"], errors="coerce")
    df_d_apont["APONTAMENTO_SK"] = pd.to_numeric(df_d_apont["APONTAMENTO_SK"], errors="coerce")

    df_cards = df_cards.merge(
        df_d_apont[["APONTAMENTO_SK", "STATUS_MACRO"]],
        on="APONTAMENTO_SK",
        how="left",
        suffixes=("", "_DIM")
    )

    # 🔥 GARANTIR QUE STATUS_MACRO EXISTA
    if "STATUS_MACRO" not in df_cards.columns and "STATUS_MACRO_DIM" in df_cards.columns:
        df_cards["STATUS_MACRO"] = df_cards["STATUS_MACRO_DIM"]

    elif "STATUS_MACRO" in df_cards.columns and "STATUS_MACRO_DIM" in df_cards.columns:
        df_cards["STATUS_MACRO"] = df_cards["STATUS_MACRO"].fillna(df_cards["STATUS_MACRO_DIM"])

    # fallback final (EVITA QUEBRAR)
    if "STATUS_MACRO" not in df_cards.columns:
        df_cards["STATUS_MACRO"] = "NÃO CLASSIFICADO"

    # padronizar
    df_cards["STATUS_MACRO"] = (
        df_cards["STATUS_MACRO"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # datas
    df_cards["DATA_OBS"] = pd.to_datetime(df_cards["DATA_OBS"], errors="coerce")

    # pendência
    df_cards["PENDENCIA_APONTAMENTO"] = (
        df_cards["PENDENCIA_APONTAMENTO"]
        .astype(str)
        .str.strip()
        .str.upper()
    )

    # 2. Criar lista de etapas

    etapas = sorted(df_cards["STATUS_MACRO"].dropna().unique())

    # 3. Render dos cards

    st.markdown("### 🚧 Etapas do Projeto")

    cols = st.columns(5)

    for i, etapa in enumerate(etapas[:10]):  # limita a 10 cards

        if i == 5:
            cols = st.columns(5)

        col = cols[i % 5]

        df_etapa = df_cards[df_cards["STATUS_MACRO"] == etapa]

        df_pend = df_etapa[
            df_etapa["PENDENCIA_APONTAMENTO"] == "SIM"
        ].sort_values("DATA_OBS", ascending=False)

        qtd_pend = len(df_pend)

        with col:

            if not df_pend.empty:

                row = df_pend.iloc[0]

                data_txt = row["DATA_OBS"].strftime("%d/%m/%Y") if pd.notna(row["DATA_OBS"]) else "-"

                #-------------------------------------------------------------------
                data_evento = row.get("DATA_REALIZADO")

                if pd.notna(data_evento):
                    data_evento = pd.to_datetime(data_evento, errors="coerce")
                    data_evento_txt = data_evento.strftime("%d/%m/%Y")
                else:
                    data_evento_txt = "-"
                #-------------------------------------------------------------------

                apont = str(row.get("APONTAMENTOS", "")).strip()
                status = str(row.get("STATUS", "")).strip()
                obs = str(row.get("OBSERVACAO", "")).strip()

                st.markdown(f"""
                <div style="
                    background:#1E293B;
                    padding:14px;
                    border-radius:10px;
                    border-left:4px solid #EF4444;
                    margin-bottom:10px;
                    height:180px;
                    overflow-y:auto;
                    padding-right:6px;
                ">

                <div style="font-size:11px;color:#94A3B8;">
                {data_txt}  •  {etapa}
                </div>

                <div style="
                    font-size:11px;
                    color:#EF4444;
                    margin-top:4px;
                    font-weight:600;
                ">
                🔴 {qtd_pend} pendência(s) nesta etapa
                </div>

                <div style="font-weight:bold;color:#FACC15;margin-top:6px;">
                ⚠ {apont}
                </div>                

                <div style="font-size:12px;color:#F87171;margin-top:4px;">
                Status: {status}
                </div>

                <div style="font-size:12px;color:#CBD5E1;margin-top:6px;">
                {obs if obs else "Sem observação"}
                </div>

                <div style="font-size:11px;color:#94A3B8;margin-top:6px;">
                📅 Evento: {data_evento_txt}
                </div>

                </div>
                """, unsafe_allow_html=True)

            else:

                st.markdown(f"""
                <div style="
                    background:#1E293B;
                    padding:14px;
                    border-radius:10px;
                    border-left:4px solid #10B981;
                    margin-bottom:10px;
                    height:180px;
                    overflow-y:auto;
                ">

                <div style="font-size:11px;color:#94A3B8;">
                {etapa}
                </div>

                <div style="font-weight:bold;color:#10B981;margin-top:10px;">
                ✔ Sem pendências
                </div>

                </div>
                """, unsafe_allow_html=True)

    st.markdown("---")

    # =======================================================
    # HISTÓRICO GERAL DO PROJETO (TIMELINE)
    # =======================================================

    st.markdown("### 📜 Histórico Geral do Projeto")

    # ==============================
    # PREPARAR BASE HISTÓRICA
    # ==============================

    df_hist = df_diario.copy()

    df_hist = df_hist[
        df_hist["PROJETO"].astype(str).str.strip() == str(projeto)
    ].copy()

    df_hist["DATA_OBS"] = pd.to_datetime(df_hist["DATA_OBS"], errors="coerce")
    
    # ==============================
    # ENRIQUECER COM DIMENSÃO d_apontamentos
    # (usar APONTAMENTO_SK, não texto)
    # ==============================

    # garantir tipos compatíveis
    if "APONTAMENTO_SK" in df_hist.columns:
        df_hist["APONTAMENTO_SK"] = pd.to_numeric(df_hist["APONTAMENTO_SK"], errors="coerce")

    df_d_apont["APONTAMENTO_SK"] = pd.to_numeric(df_d_apont["APONTAMENTO_SK"], errors="coerce")

    # remover coluna auxiliar antiga, se existir
    if "STATUS_MACRO_DIM" in df_hist.columns:
        df_hist = df_hist.drop(columns=["STATUS_MACRO_DIM"])

    # merge robusto pela chave
    df_hist = df_hist.merge(
        df_d_apont[["APONTAMENTO_SK", "STATUS_MACRO"]],
        on="APONTAMENTO_SK",
        how="left",
        suffixes=("", "_DIM")
    )

    # se a fato já possui STATUS_MACRO, preserva e completa os nulos com a dimensão
    if "STATUS_MACRO" in df_hist.columns and "STATUS_MACRO_DIM" in df_hist.columns:
        df_hist["STATUS_MACRO"] = (
            df_hist["STATUS_MACRO"]
            .fillna(df_hist["STATUS_MACRO_DIM"])
            .astype(str)
            .str.strip()
            .str.upper()
        )
        df_hist = df_hist.drop(columns=["STATUS_MACRO_DIM"])

    # se por algum motivo só veio da dimensão
    elif "STATUS_MACRO_DIM" in df_hist.columns:
        df_hist["STATUS_MACRO"] = (
            df_hist["STATUS_MACRO_DIM"]
            .astype(str)
            .str.strip()
            .str.upper()
        )
        df_hist = df_hist.drop(columns=["STATUS_MACRO_DIM"])

    # fallback defensivo
    if "STATUS_MACRO" not in df_hist.columns:
        df_hist["STATUS_MACRO"] = "NÃO CLASSIFICADO"

    # ==============================
    # FILTRO POR MACRO
    # ==============================

    lista_macro = sorted(
        df_d_apont["STATUS_MACRO"]
        .dropna()
        .astype(str)
        .str.strip()
        .str.upper()
        .unique()
    )

    macro_sel = st.selectbox(
        "Filtrar por Macro",
        ["TODOS"] + lista_macro,
        key="filtro_macro"
    )

    if macro_sel != "TODOS":
        df_hist = df_hist[
            df_hist["STATUS_MACRO"].astype(str).str.strip().str.upper() == macro_sel
        ]

    # ====================================
    # CONTADOR DE EVENTOS
    # ====================================

    st.caption(f"📊 {len(df_hist)} registros encontrados para esta macro")

    # ==============================
    # ORDENAR MAIS RECENTES
    # ==============================

    df_hist["DATA_REGISTRO"] = pd.to_datetime(df_hist["DATA_REGISTRO"], errors="coerce")

    df_hist["DATA_TIMELINE"] = df_hist["DATA_REGISTRO"]

    df_hist.loc[
        df_hist["DATA_TIMELINE"].isna(),
        "DATA_TIMELINE"
    ] = df_hist["DATA_OBS"]

    df_hist = df_hist.sort_values(
        "DATA_TIMELINE",
        ascending=False,
        na_position="last"
    )

    # limitar registros
    df_hist = df_hist.head(30)

    # ==============================
    # ÚLTIMO APONTAMENTO EM DESTAQUE
    # ==============================

    if not df_hist.empty:

        ultimo = df_hist.iloc[0]

        data_ult = pd.to_datetime(ultimo["DATA_OBS"], errors="coerce")
        data_txt = data_ult.strftime("%d/%m/%Y") if pd.notna(data_ult) else "-"

        apont_txt = str(ultimo.get("APONTAMENTOS", "")).strip()
        status_txt = str(ultimo.get("STATUS", "")).strip()

        st.markdown(
            f"""
            <div style="
                background:#0F172A;
                padding:18px;
                border-radius:10px;
                border-left:5px solid #FB923C;
                margin-bottom:20px;
            ">

            <div style="font-size:12px;color:#94A3B8;">
            🟠 Última atualização do projeto
            </div>

            <div style="font-size:16px;font-weight:600;color:white;margin-top:6px;">
            {apont_txt} — {status_txt}
            </div>

            <div style="font-size:12px;color:#94A3B8;margin-top:4px;">
            {data_txt}
            </div>

            </div>
            """,
            unsafe_allow_html=True
        )

    mapa_cores_status = {
        "Concluído": "#60A5FA",
        "Em andamento": "#FACC15",
        "Parcial": "#FB923C",
        "Não iniciado": "#64748B"
    }

    if df_hist.empty:
        st.info("Nenhum histórico encontrado para este projeto.")
    else:
        html_itens = ""

        for _, row in df_hist.iterrows():
            cor_status = mapa_cores_status.get(
                str(row.get("STATUS", "")).strip(),
                "#94A3B8"
            )

            data = row.get("DATA_OBS")
            data_txt = data.strftime("%d/%m/%Y") if pd.notna(data) else "Sem atualização"

            apont_txt = str(row.get("APONTAMENTOS", "")).strip()
            status_txt = str(row.get("STATUS", "")).strip()
            obs_txt = row.get("OBSERVACAO", "")
            area_txt = str(row.get("RESPONSAVEL_AREA", "")).strip()
            resp_txt = str(row.get("RESPONSAVEL_NOME", "")).strip()

            if pd.isna(obs_txt) or str(obs_txt).strip() == "":
                obs_txt = "Sem observação"
            else:
                obs_txt = str(obs_txt).strip()

            html_itens += f"""
            <div style="
                border-left: 3px solid {cor_status};
                padding: 12px 15px;
                margin-bottom: 12px;
                background-color: #1E293B;
                border-radius: 8px;
            ">
                <div style="font-size:13px; color:#94A3B8;">
                    {data_txt}
                </div>

                <div style="font-weight:bold; color:{cor_status}; margin-top:4px;">
                    {apont_txt} — {status_txt}
                </div>

                <div style="margin-top:6px; color:#F8FAFC;">
                    {obs_txt}
                </div>

                <div style="margin-top:6px; font-size:12px; color:#94A3B8;">
                    Área: {area_txt}
                </div>

                <div style="margin-top:4px; font-size:12px; color:#94A3B8;">
                    Responsável: {resp_txt}
                </div>
            </div>
            """

        components.html(
            f"""
            <div style="font-family:Segoe UI, sans-serif;">
                {html_itens}
            </div>
            """,
            height=520,
            scrolling=True
        )

    st.markdown("---")
    st.markdown("### ⚠ Gestão de Pendências")

    # ==============================
    # BASE DE PENDÊNCIAS
    # ==============================

    df_pend = df_diario.copy()

    # padronização defensiva
    df_pend.columns = df_pend.columns.str.strip().str.upper()

    # manter apenas o projeto selecionado
    df_pend = df_pend[
        df_pend["PROJETO"].astype(str).str.strip() == str(projeto).strip()
    ].copy()

    # garantir texto padronizado
    if "PENDENCIA_APONTAMENTO" in df_pend.columns:
        df_pend["PENDENCIA_APONTAMENTO"] = (
            df_pend["PENDENCIA_APONTAMENTO"]
            .astype(str)
            .str.strip()
            .str.upper()
        )
    else:
        df_pend["PENDENCIA_APONTAMENTO"] = "NÃO"

    # manter apenas pendências = SIM
    df_pend = df_pend[
        df_pend["PENDENCIA_APONTAMENTO"] == "SIM"
    ].copy()

    # ==============================
    # CARD DE PENDÊNCIAS
    # ==============================

    total_pendencias = len(df_pend)

    col_p1, col_p2, col_p3 = st.columns([1, 1, 1])

    with col_p1:
        card_exec("⚠ Pendências Abertas", total_pendencias)

    st.markdown("---")

    # ==============================
    # DRILLDOWN POR MACRO
    # ==============================

    st.markdown("### Pendências por Etapa (Macro)")

    if not df_pend.empty:
        df_pend_macro = (
        df_pend
        .groupby("STATUS_MACRO", as_index=False)
        .size()
        .rename(columns={"size": "QTD_PENDENCIAS"})
        .sort_values("QTD_PENDENCIAS", ascending=False)
    )

        col1, col2 = st.columns([2,3])

        with col1:

            st.dataframe(
                df_pend_macro,
                use_container_width=True,
                hide_index=True
            )
        
    else:
        macro_pend_sel = None

    # ==============================
    # FILTRO DE ETAPA
    # ==============================

    if not df_pend.empty:

        lista_macros_pend = (
            df_pend["STATUS_MACRO"]
            .dropna()
            .astype(str)
            .sort_values()
            .unique()
            .tolist()
        )

        col1, col2 = st.columns([2,3])

        with col1:

            macro_pend_sel = st.selectbox(
                "Selecionar Etapa para detalhar",
                lista_macros_pend,
                key="macro_pend_sel"
            )

    else:
        macro_pend_sel = None

    # ==============================
    # DRILLDOWN POR APONTAMENTO
    # ==============================

    st.markdown("### Pendências por Apontamento")

    if not df_pend.empty and macro_pend_sel is not None:

        df_pend_macro_det = df_pend[
            df_pend["STATUS_MACRO"].astype(str) == str(macro_pend_sel)
        ].copy()

        df_pend_apont = (
            df_pend_macro_det
            .groupby("APONTAMENTO_ATIVO", as_index=False)
            .size()
            .rename(columns={"size": "QTD_PENDENCIAS"})
            .sort_values("QTD_PENDENCIAS", ascending=False)
        )

        

        col1, col2 = st.columns([2,3])

        with col1:

            st.dataframe(
                df_pend_apont,
                use_container_width=True,
                hide_index=True
            )


