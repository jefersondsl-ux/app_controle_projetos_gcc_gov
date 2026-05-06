import pandas as pd
from datetime import datetime

def calcular_kpis(df_controle, df_backlog, df_producao, df_diario):

    # ==============================
    # PROJETOS
    # ==============================

    total_projetos = df_controle["PROJETO"].nunique()

    # ==============================
    # STATUS DOS PROJETOS
    # ==============================

    df_diario = df_diario.dropna(subset=["PROJETO", "STATUS"])

    df_diario["STATUS"] = df_diario["STATUS"].str.strip()

    df_status = (
        df_diario
        .groupby("PROJETO")["STATUS"]
        .apply(set)
        .reset_index()
    )

    def calcular_status(status_set):

        if status_set == {"Não iniciado"}:
            return "Novo"

        elif status_set == {"Concluído"}:
            return "Concluído"

        else:
            return "Parcial"


    df_status["Status_Projeto"] = df_status["STATUS"].apply(calcular_status)

    # ==============================
    # CONTAGENS
    # ==============================

    total_projetos = df_status["PROJETO"].nunique()

    projetos_novos = (df_status["Status_Projeto"] == "Novo").sum()
    projetos_parcial = (df_status["Status_Projeto"] == "Parcial").sum()
    projetos_concluido = (df_status["Status_Projeto"] == "Concluído").sum()

    # ==============================
    # PROJETOS PARADOS (BASE ANALÍTICA)
    # ==============================

    projetos_parados = 0  # placeholder (será sobrescrito)

    # ==============================
    # CIRCUITOS
    # ==============================

    circuitos_backlog = len(df_backlog)
    circuitos_producao = df_producao["QTD_CIRCUITOS"].sum()
    circuitos_total = circuitos_backlog + circuitos_producao

    # ==============================
    # DATA ÚLTIMA ATUALIZAÇÃO
    # ==============================

    ultima_data = pd.to_datetime(df_diario["DATA_OBS"], errors="coerce").max()

    ultima_atualizacao = (
        ultima_data.strftime("%d/%m/%Y")
        if pd.notnull(ultima_data)
        else "-"
    )

    # ==============================
    # RESULTADO
    # ==============================

    kpis = {

        "total_projetos": total_projetos,

        "projetos_novos": projetos_novos,
        "projetos_parcial": projetos_parcial,
        "projetos_concluido": projetos_concluido,
        "projetos_parados": projetos_parados,

        "circuitos_backlog": circuitos_backlog,
        "circuitos_producao": circuitos_producao,
        "circuitos_total": circuitos_total,

        "ultima_atualizacao": ultima_atualizacao
    }

    return kpis