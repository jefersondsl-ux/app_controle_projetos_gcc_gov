# Responsável por: Construir dataset analítico

import pandas as pd
from .reconciliar_chaves import enriquecer_com_d_projetos


def construir_tabela_analitica(
    df_d_projetos,
    df_controle,
    df_backlog,
    df_producao,
    df_diario
):

    # =============================
    # ENRIQUECER BACKLOG E PRODUÇÃO COM d_Projetos
    # =============================
    
    # backlog: usar CARIMBO_PREFIXO para lookup
    if "CARIMBO_PREFIXO" in df_backlog.columns and "CARIMBO_PREFIXO" in df_d_projetos.columns:
        df_backlog = enriquecer_com_d_projetos(
            df_backlog, 
            df_d_projetos, 
            chave_em_fato="CARIMBO_PREFIXO",
            chave_em_dim="CARIMBO_PREFIXO"
        )
    
    # produção: usar CARIMBO_PREFIXO para lookup
    if "CARIMBO_PREFIXO" in df_producao.columns and "CARIMBO_PREFIXO" in df_d_projetos.columns:
        df_producao = enriquecer_com_d_projetos(
            df_producao, 
            df_d_projetos, 
            chave_em_fato="CARIMBO_PREFIXO",
            chave_em_dim="CARIMBO_PREFIXO"
        )

    # =============================
    # PADRONIZAR CHAVES
    # =============================

    df_d_projetos["IDP_PROJETO"] = df_d_projetos["IDP_PROJETO"].astype(str).str.strip()
    df_controle["IDP_PROJETO"] = df_controle["IDP_PROJETO"].astype(str).str.strip()
    df_backlog["IDP_PROJETO"] = df_backlog["IDP_PROJETO"].astype(str).str.strip()
    df_producao["IDP_PROJETO"] = df_producao["IDP_PROJETO"].astype(str).str.strip()
    df_diario["IDP_PROJETO"] = df_diario["IDP_PROJETO"].astype(str).str.strip()

    # =============================
    # CONTROLE POR PROJETO
    # =============================

    controle_proj = (
        df_controle
        .groupby("IDP_PROJETO", as_index=False)
        .agg(
            Valor_Contrato=("VALOR CONTRATO", "sum")
        )
    )

    # =============================
    # BACKLOG POR PROJETO (DETALHADO)
    # =============================

    # garantir colunas (evita quebra)
    for col in ["CLASSIFICACAO", "TAREFA_RESPONSAVEL", "DELTA_RECEITA", "COD_CIR"]:
        if col not in df_backlog.columns:
            df_backlog[col] = None

    # normalização leve
    df_backlog["CLASSIFICACAO"] = df_backlog["CLASSIFICACAO"].astype(str).str.upper().str.strip()
    df_backlog["TAREFA_RESPONSAVEL"] = df_backlog["TAREFA_RESPONSAVEL"].astype(str).str.upper().str.strip()

    # agregação
    backlog_proj = (
        df_backlog
        .groupby("IDP_PROJETO")
        .agg(

            # TOTAL
            BACKLOG_TOTAL=("COD_CIR", "count"),

            # CLASSIFICAÇÃO
            BACKLOG_GROSS=("CLASSIFICACAO", lambda x: (x == "GROSS").sum()),
            BACKLOG_SERVICOS=("CLASSIFICACAO", lambda x: (x == "SERVICO").sum()),

            # RESPONSÁVEL
            BACKLOG_PJE=("TAREFA_RESPONSAVEL", lambda x: (x == "PROJETOS ESPECIAIS").sum()),
            BACKLOG_CLIENTE=("TAREFA_RESPONSAVEL", lambda x: (x == "CLIENTE").sum()),
            BACKLOG_COMERCIAL=("TAREFA_RESPONSAVEL", lambda x: (x == "VENDAS").sum()),

            # RECEITA
            RECEITA_BACKLOG=("DELTA_RECEITA", "sum")

        )
        .reset_index()
    )

    # =============================
    # PRODUÇÃO POR PROJETO
    # =============================

    # Produção já vem agregada (BASE ANALÍTICA)

    producao_proj = df_producao.rename(
        columns={
            "QTD_CIRCUITOS": "Circuitos_Producao",
            "RECEITA_TOTAL": "Receita_Producao"
        }
    ).copy()

    # garantir chave
    producao_proj["IDP_PROJETO"] = producao_proj["IDP_PROJETO"].astype(str).str.strip()

    # =============================
    # DIÁRIO POR PROJETO
    # =============================

    diario_proj = (
        df_diario
        .groupby("IDP_PROJETO", as_index=False)
        .agg(
            Apontamentos=("APONTAMENTO_SK", "count"),
            Etapas_Concluidas=("STATUS", lambda x: (x == "CONCLUÍDO").sum())
        )
    )

    # =============================
    # DIÁRIO - ÚLTIMA OBS POR ETAPA
    # =============================

    # validar colunas necessárias
    cols_diario = ["IDP_PROJETO", "STATUS_MACRO", "DATA_OBS"]

    for col in cols_diario:
        if col not in df_diario.columns:
            df_diario[col] = None

    # converter data
    df_diario["DATA_OBS"] = pd.to_datetime(df_diario["DATA_OBS"], errors="coerce")

    # remover linhas inválidas
    df_diario_valid = df_diario.dropna(subset=["IDP_PROJETO", "STATUS_MACRO", "DATA_OBS"])

    # ordenar (ESSENCIAL)
    df_diario_valid = df_diario_valid.sort_values("DATA_OBS")

    # pegar última observação por projeto + etapa
    df_last_obs = (
        df_diario_valid
        .groupby(["IDP_PROJETO", "STATUS_MACRO"], as_index=False)
        .last()
    )

    # pivotar para colunas
    df_pivot_obs = df_last_obs.pivot(
        index="IDP_PROJETO",
        columns="STATUS_MACRO",
        values="OBSERVACAO"  # ajuste se o nome da coluna for diferente
    )

    # resetar index
    df_pivot_obs = df_pivot_obs.reset_index()

    # prefixar colunas
    df_pivot_obs.columns = [
        "IDP_PROJETO" if col == "IDP_PROJETO" else f"OBS_{col}"
        for col in df_pivot_obs.columns
    ]

    # =============================
    # DIÁRIO - ÚLTIMA DATA POR ETAPA
    # =============================

    df_pivot_data_obs = df_last_obs.pivot(
        index="IDP_PROJETO",
        columns="STATUS_MACRO",
        values="DATA_OBS"
    )

    df_pivot_data_obs = df_pivot_data_obs.reset_index()

    df_pivot_data_obs.columns = [
        "IDP_PROJETO" if col == "IDP_PROJETO" else f"DATA_OBS_{col}"
        for col in df_pivot_data_obs.columns
    ]

    # =============================
    # UNIR NA DIMENSÃO (BASE DA PLANILHA = CONTROLE)
    # =============================

    colunas_controle = [

        "PROJETO",
        "IDP_PROJETO",
        "CLIENTE",        
        "PROJETO_CARIMBO",
        "OVERVIEW",
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

    # mantém apenas colunas que realmente existem
    colunas_existentes = [
        c for c in colunas_controle if c in df_controle.columns
    ]

    df_base = df_controle[colunas_existentes].copy()

    # =============================
    # AJUSTAR COLUNA ORDEM
    # =============================

    if "ORDEM" in df_base.columns:
        df_base["ORDEM"] = (
            pd.to_numeric(df_base["ORDEM"], errors="coerce")
            .fillna(0)
            .astype(int)
        )

    df_base["IDP_PROJETO"] = (
        df_base["IDP_PROJETO"]
        .astype(str)
        .str.strip()
    )

    df_base = df_base.drop_duplicates(subset="IDP_PROJETO")

    # =============================
    # UNIR DADOS ANALÍTICOS
    # =============================

    df = (
        df_base
        .merge(controle_proj, on="IDP_PROJETO", how="left")
        .merge(backlog_proj, on="IDP_PROJETO", how="left")
        .merge(producao_proj, on="IDP_PROJETO", how="left")
        .merge(diario_proj, on="IDP_PROJETO", how="left")
        .merge(df_pivot_obs, on="IDP_PROJETO", how="left")
        .merge(df_pivot_data_obs, on="IDP_PROJETO", how="left")
    )

    # =============================
    # TRATAR NULOS
    # =============================

    cols = [
        "Valor_Contrato",

        # NOVO BACKLOG
        "BACKLOG_TOTAL",
        "BACKLOG_GROSS",
        "BACKLOG_SERVICOS",
        "BACKLOG_PJE",
        "BACKLOG_CLIENTE",
        "BACKLOG_COMERCIAL",
        "RECEITA_BACKLOG",

        # PRODUÇÃO
        "Circuitos_Producao",
        "Receita_Producao"        
    ]

    # mantém apenas colunas existentes (ROBUSTEZ)
    cols_existentes = [c for c in cols if c in df.columns]

    df[cols_existentes] = df[cols_existentes].fillna(0)

    # =============================
    # TOTAIS
    # =============================

    df["Total_Circuitos"] = (
        df.get("BACKLOG_TOTAL", 0) +
        df.get("Circuitos_Producao", 0)
    )

    df["Receita_Total"] = (
        df.get("RECEITA_BACKLOG", 0) +
        df.get("Receita_Producao", 0)
    )

    # =============================
    # % CONCLUSÃO DO PROJETO
    # =============================

    df["Perc_Conclusao"] = ( 
        df["Circuitos_Producao"]
        .div(df["Total_Circuitos"])
        .replace([float("inf"), -float("inf")], 0)
        .fillna(0)
        .clip(0, 1)  # evita valores acima de 100%
    )

    # =============================
    # ORDENAR COLUNAS
    # =============================

    colunas_base = [
        "PROJETO",
        "IDP_PROJETO",
        "CLIENTE",        
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
        "CCTOS CANCELADOS"
        
    ]

    colunas_analiticas = [

        # BACKLOG NOVO
        "BACKLOG_TOTAL",
        "BACKLOG_GROSS",
        "BACKLOG_SERVICOS",
        "BACKLOG_PJE",
        "BACKLOG_CLIENTE",
        "BACKLOG_COMERCIAL",
        "RECEITA_BACKLOG",

        # (opcional compatibilidade)
        "Circuitos_Backlog",
        "Receita_Backlog",

        # PRODUÇÃO
        "Circuitos_Producao",
        "Receita_Producao",

        # TOTAIS
        "Total_Circuitos",
        "Receita_Total",

        # DATA
        "DIAS_SEM_ATUALIZACAO",

        # DIÁRIO        
        "Perc_Conclusao"
    ]

    # =============================
    # ORGANIZAR OBS + DATA LADO A LADO
    # =============================

    cols_obs = [c for c in df.columns if c.startswith("OBS_")]
    cols_data_obs = [c for c in df.columns if c.startswith("DATA_OBS_")]

    # extrair nomes das etapas
    etapas = sorted([
        col.replace("OBS_", "")
        for col in cols_obs
    ])

    # montar ordem final intercalada
    cols_etapas_ordenadas = []

    for etapa in etapas:

        col_obs = f"OBS_{etapa}"
        col_data = f"DATA_OBS_{etapa}"

        if col_obs in df.columns:
            cols_etapas_ordenadas.append(col_obs)

        if col_data in df.columns:
            cols_etapas_ordenadas.append(col_data)

    # montar colunas finais
    colunas = colunas_base + colunas_analiticas + cols_etapas_ordenadas

    

    # ADICIONAR OBJETOS NO FINAL
    if "OBJETOS" in df.columns:
        colunas.append("OBJETOS")

    # ADICIONAR ORDEM NO FINAL
    if "ORDEM" in df.columns:
        colunas.append("ORDEM")

    # mantém apenas colunas existentes
    colunas = [c for c in colunas if c in df.columns]

    df = df[colunas]

    # =============================
    # DIAS SEM ATUALIZAÇÃO
    # =============================

    from datetime import datetime

    # pegar todas as colunas de data das etapas
    cols_data_obs = [c for c in df.columns if c.startswith("DATA_OBS_")]

    if cols_data_obs:

        # converter para datetime (garantia)
        for col in cols_data_obs:
            df[col] = pd.to_datetime(df[col], errors="coerce")

        # pegar a última data entre todas as etapas
        df["ULTIMA_ATUALIZACAO"] = df[cols_data_obs].max(axis=1)

        # calcular diferença em dias
        hoje = pd.Timestamp.today().normalize()

        df["DIAS_SEM_ATUALIZACAO"] = (
            (hoje - df["ULTIMA_ATUALIZACAO"])
            .dt.days
            .fillna(0)
            .astype(int)
        )

    # =============================
    # FORMATAR DATAS
    # =============================

    colunas_data = [
        "DATA ASSINATURA CONTRATO",
        "DATA FINAL IMPLANTAÇÃO"
    ]

    # incluir datas das etapas
    cols_data_obs = [c for c in df.columns if c.startswith("DATA_OBS_")]

    colunas_data = colunas_data + cols_data_obs

    for col in colunas_data:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce").dt.strftime("%d/%m/%Y")

    # =============================
    # AJUSTAR NÚMEROS INTEIROS
    # =============================

    colunas_inteiras = [

        # BACKLOG NOVO
        "BACKLOG_TOTAL",
        "BACKLOG_GROSS",
        "BACKLOG_SERVICOS",
        "BACKLOG_PJE",
        "BACKLOG_CLIENTE",
        "BACKLOG_COMERCIAL",

        # PRODUÇÃO / EXISTENTE
        "Circuitos_Producao",
        "Total_Circuitos",
        "Apontamentos",
        "Etapas_Concluidas",
        "QTD PONTOS (CIRCUITOS)",
        "QTD CCTOS SOLICITADOS",
        "CCTOS CANCELADOS"
    ]

    for col in colunas_inteiras:
        if col in df.columns:
            df[col] = (
                pd.to_numeric(df[col], errors="coerce")
                .fillna(0)
                .astype(int)
            )

    # =============================
    # FORMATAR VALORES MONETÁRIOS
    # =============================

    colunas_moeda = [
        "VALOR CONTRATO",
        "RECEITA MENSAL CONTRATUAL",
        "RECEITA_BACKLOG",
        "Receita_Producao",
        "Receita_Total"
    ]

    def formatar_moeda(valor):

        try:
            valor = float(valor)
            return f"R$ {valor:,.0f}".replace(",", ".")
        except:
            return "R$ 0"

    for col in colunas_moeda:
        if col in df.columns:
            df[col] = df[col].apply(formatar_moeda)

    # =============================
    # FORMATAR PERCENTUAL
    # =============================

    def formatar_percentual(valor):
        try:
            return f"{round(valor * 100)}%"
        except:
            return "0%"

    if "Perc_Conclusao" in df.columns:
        df["Perc_Conclusao"] = df["Perc_Conclusao"].apply(formatar_percentual)

    # =============================
    # ORDENAR POR ORDEM
    # =============================

    if "ORDEM" in df.columns:
        df = df.sort_values("ORDEM", ascending=False)

    # =============================
    # RETURN FINAL
    # =============================

    return df