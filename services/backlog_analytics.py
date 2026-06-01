import os
import re
import unicodedata
import numpy as np
import pandas as pd
from .carregar_bases import carregar_meta_mensal


def normalizar_produto_ajustado(valor):
    if valor is None:
        return ""

    produto = str(valor).strip().upper()

    if produto == "":
        return ""

    if "SDWAN" in produto:
        return "INTERNET"
    if "BANDA LARGA" in produto or "MÓVEL" in produto or "MÓVEL" in produto:
        return "INTERNET"
    if "INFOSAT" in produto or "SAT" in produto:
        return "DADOS"
    if "INTERNET" in produto:
        return "INTERNET"
    if "DADOS" in produto or "DATA" in produto:
        return "DADOS"
    if "VOZ" in produto or "VOICE" in produto:
        return "VOZ"
    if "WIFI" in produto or "WI-FI" in produto:
        return "WIFI"

    return produto


def categorizar_produto(valor):
    if valor is None:
        return "OUTROS"

    produto = str(valor).strip().upper()

    if produto in ["INTERNET", "DADOS", "VOZ", "WIFI"]:
        return produto

    return "OUTROS"


def normalizar_cliente(valor):
    if valor is None or pd.isna(valor):
        return ""

    texto = str(valor).strip()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    texto = texto.replace("\xa0", " ")
    texto = re.sub(r"[^\w\s]", " ", texto)
    texto = re.sub(r"\s+", " ", texto).strip().upper()

    return texto


def extrair_prefixo_carimbo(texto):
    if pd.isna(texto):
        return ""
    texto = str(texto).strip()
    match = re.search(r"\b\d{1,4}/\d{2}\b", texto)
    return match.group(0) if match else ""


def calcular_forecast_inicio_mes(df_meta):
    """
    Calcula forecast de início do mês por cliente (estratégia de redes)
    Filtra apenas GROSS + INTERNET/DADOS
    """
    if df_meta is None or df_meta.empty:
        return pd.DataFrame()
    
    df = df_meta.copy()
    
    # Padronização
    if "CLASSIFICACAO" in df.columns:
        df["CLASSIFICACAO"] = df["CLASSIFICACAO"].astype(str).str.upper().str.strip()
    if "PRODUTO_AJUSTADO" in df.columns:
        df["PRODUTO_AJUSTADO"] = df["PRODUTO_AJUSTADO"].astype(str).str.upper().str.strip()
    if "CLIENTE" in df.columns:
        df["CLIENTE"] = df["CLIENTE"].apply(normalizar_cliente)

    def _parse_num(valor):
        if pd.isna(valor):
            return 0.0
        texto = str(valor).strip()
        if texto == "":
            return 0.0
        texto = texto.replace("\xa0", "").replace(" ", "")
        if "." in texto and "," in texto:
            # 1.234,56 -> 1234.56
            texto = texto.replace(".", "").replace(",", ".")
        elif "," in texto:
            # 1234,56 -> 1234.56
            texto = texto.replace(",", ".")
        # else: ``1234.56`` remains as is
        try:
            return float(texto)
        except Exception:
            return 0.0

    if "DELTA_RECEITA" in df.columns:
        df["DELTA_RECEITA"] = df["DELTA_RECEITA"].apply(_parse_num)
    if "REGRA_COMERCIAL_PY" in df.columns:
        df["REGRA_COMERCIAL_PY"] = df["REGRA_COMERCIAL_PY"].apply(_parse_num)
    
    # Filtrar estratégia de redes
    df_estrategia = df[
        (df["CLASSIFICACAO"] == "GROSS") &
        (df["PRODUTO_AJUSTADO"].isin(["INTERNET", "DADOS"]))
    ]
    
    # Agregar por cliente
    if df_estrategia.empty:
        return pd.DataFrame()
    
    forecast = (
        df_estrategia
        .groupby("CLIENTE", as_index=False)
        .agg(
            FORECAST_INICIO_MES=("COD_CIR", "count"),
            FORECAST_REGRA_COMERCIAL=("REGRA_COMERCIAL_PY", "sum"),
            FORECAST_DELTA_RECEITA=("DELTA_RECEITA", "sum"),
        )
    )
    
    return forecast


def preparar_base_backlog(df_backlog):
    """
    Apenas padronização leve
    NÃO recalcula regra de negócio (isso é responsabilidade do ETL)
    """

    df = df_backlog.copy()

    df.columns = df.columns.str.strip().str.upper()

    if "PRODUTO_AJUSTADO" in df.columns:
        df["PRODUTO_AJUSTADO"] = (
            df["PRODUTO_AJUSTADO"]
            .fillna("")
            .astype(str)
            .str.strip()
            .str.upper()
            .apply(normalizar_produto_ajustado)
        )
        df["PRODUTO_CATEGORIA"] = df["PRODUTO_AJUSTADO"].apply(categorizar_produto)

    if "CLIENTE" in df.columns:
        df["CLIENTE"] = df["CLIENTE"].apply(normalizar_cliente)

    return df


def resumo_backlog(df):
    """
    Gera visão geral do backlog
    """

    df = preparar_base_backlog(df)

    resumo = {}

    # =========================
    # TOTAL
    # =========================

    resumo["total"] = len(df)

    # =========================
    # CLASSIFICAÇÃO
    # =========================

    if "CLASSIFICACAO" in df.columns:

        total = len(df)

        gross = (df["CLASSIFICACAO"] == "GROSS").sum()
        servico = (df["CLASSIFICACAO"] == "SERVICO").sum()

        outros = total - (gross + servico)

        resumo["gross"] = gross
        resumo["servico"] = servico
        resumo["outros"] = outros

    else:
        resumo["gross"] = 0
        resumo["servico"] = 0
        resumo["outros"] = 0

    # =========================
    # PRODUTO
    # =========================

    if "PRODUTO_CATEGORIA" in df.columns:

        resumo["internet"] = (df["PRODUTO_CATEGORIA"] == "INTERNET").sum()
        resumo["dados"] = (df["PRODUTO_CATEGORIA"] == "DADOS").sum()
        resumo["voz"] = (df["PRODUTO_CATEGORIA"] == "VOZ").sum()
        resumo["wifi"] = (df["PRODUTO_CATEGORIA"] == "WIFI").sum()
        resumo["outros_produtos"] = (df["PRODUTO_CATEGORIA"] == "OUTROS").sum()

    elif "PRODUTO_AJUSTADO" in df.columns:
        resumo["internet"] = (df["PRODUTO_AJUSTADO"] == "INTERNET").sum()
        resumo["dados"] = (df["PRODUTO_AJUSTADO"] == "DADOS").sum()
        resumo["voz"] = (df["PRODUTO_AJUSTADO"] == "VOZ").sum()
        resumo["wifi"] = (df["PRODUTO_AJUSTADO"] == "WIFI").sum()
        resumo["outros_produtos"] = len(df) - (resumo["internet"] + resumo["dados"] + resumo["voz"] + resumo["wifi"])

    else:
        resumo["internet"] = 0
        resumo["dados"] = 0
        resumo["voz"] = 0
        resumo["wifi"] = 0
        resumo["outros_produtos"] = len(df)

    return resumo


def filtrar_estrategia(df):
    df = preparar_base_backlog(df)

    if "CLASSIFICACAO" in df.columns:
        df["CLASSIFICACAO"] = (
            df["CLASSIFICACAO"]
            .astype(str)
            .str.upper()
            .str.strip()
        )
    else:
        df["CLASSIFICACAO"] = ""

    if "PRODUTO_AJUSTADO" in df.columns:
        df["PRODUTO_AJUSTADO"] = (
            df["PRODUTO_AJUSTADO"]
            .astype(str)
            .str.upper()
            .str.strip()
        )
    else:
        df["PRODUTO_AJUSTADO"] = ""

    return df[
        (df["CLASSIFICACAO"] == "GROSS") &
        (df["PRODUTO_AJUSTADO"].isin(["INTERNET", "DADOS"]))
    ]


def resumo_estrategia(df):
    df_total = preparar_base_backlog(df)
    df_estrategia = filtrar_estrategia(df_total)

    total = len(df_estrategia)
    internet = (df_estrategia["PRODUTO_AJUSTADO"] == "INTERNET").sum()
    dados = (df_estrategia["PRODUTO_AJUSTADO"] == "DADOS").sum()
    perc = (total / len(df_total) * 100) if len(df_total) else 0

    return {
        "total": total,
        "internet": internet,
        "dados": dados,
        "perc": perc,
    }


# ==============================
# AGGRID - MATRIZ BACKLOG
# ==============================

def matriz_backlog_por_projeto(df_backlog, df_controle, df_d_projetos=None):
    """
    Matriz backlog com nome do projeto (fallback para carimbo)
    """

    df = preparar_base_backlog(df_backlog)

    # =========================
    # USAR CLIENTE DE d_Projetos QUANDO DISPONÍVEL
    # =========================

    if df_d_projetos is not None and "CARIMBO_PREFIXO" in df.columns and "CARIMBO_PREFIXO" in df_d_projetos.columns and "CLIENTE" in df_d_projetos.columns:
        df_dim = df_d_projetos[["CARIMBO_PREFIXO", "CLIENTE"]].copy()
        df_dim["CARIMBO_PREFIXO"] = df_dim["CARIMBO_PREFIXO"].astype(str).str.strip()
        df_dim["CLIENTE_DIM"] = df_dim["CLIENTE"].apply(normalizar_cliente)
        # Somente usar cliente de d_Projetos quando existir valor válido.
        # Não devemos sobrescrever o cliente do backlog com uma string vazia.
        df_dim = df_dim.loc[df_dim["CLIENTE_DIM"].astype(str).str.strip() != "", ["CARIMBO_PREFIXO", "CLIENTE_DIM"]]
        df_dim = df_dim.drop_duplicates("CARIMBO_PREFIXO")
        df = df.merge(df_dim, on="CARIMBO_PREFIXO", how="left")
        df["CLIENTE"] = df["CLIENTE_DIM"].fillna(df["CLIENTE"])
        df = df.drop(columns=["CLIENTE_DIM"])

    # =========================
    # VALIDAÇÃO
    # =========================

    if "CLIENTE" not in df.columns:
        raise Exception("CLIENTE não encontrado")

    df["CLIENTE"] = df["CLIENTE"].astype(str).str.strip()
    df["CLIENTE"] = df["CLIENTE"].replace({"": "CLIENTE NÃO INFORMADO", "NAN": "CLIENTE NÃO INFORMADO"})

    # =========================
    # PADRONIZAÇÃO
    # =========================

    df["CLASSIFICACAO"] = df["CLASSIFICACAO"].astype(str).str.upper().str.strip()
    df["PRODUTO_AJUSTADO"] = df["PRODUTO_AJUSTADO"].astype(str).str.upper().str.strip()

    if "TAREFA_RESPONSAVEL" in df.columns:
        df["TAREFA_RESPONSAVEL"] = df["TAREFA_RESPONSAVEL"].astype(str).str.upper().str.strip()
    else:
        df["TAREFA_RESPONSAVEL"] = ""

    # =========================
    # FLAGS GROSS + PRODUTO + ESTRATÉGIA
    # =========================

    df["FLAG_GROSS"] = df["CLASSIFICACAO"] == "GROSS"
    df["FLAG_SERVICO"] = df["CLASSIFICACAO"] == "SERVICO"

    df["FLAG_INTERNET"] = df["PRODUTO_AJUSTADO"] == "INTERNET"
    df["FLAG_DADOS"] = df["PRODUTO_AJUSTADO"] == "DADOS"
    df["FLAG_VOZ"] = df["PRODUTO_AJUSTADO"] == "VOZ"
    df["FLAG_WIFI"] = df["PRODUTO_AJUSTADO"] == "WIFI"

    df["FLAG_ESTRATEGIA"] = (
        df["FLAG_GROSS"] &
        (df["FLAG_INTERNET"] | df["FLAG_DADOS"])
    )

    # =========================
    # FLAGS DE TEMPO

    hoje = pd.Timestamp.today().normalize()
    inicio_mes_atual = hoje.replace(day=1)
    next1 = inicio_mes_atual + pd.DateOffset(months=1)
    next2 = inicio_mes_atual + pd.DateOffset(months=2)

    meses_abrev = {
        1: "JAN",
        2: "FEV",
        3: "MAR",
        4: "ABR",
        5: "MAI",
        6: "JUN",
        7: "JUL",
        8: "AGO",
        9: "SET",
        10: "OUT",
        11: "NOV",
        12: "DEZ",
    }
    next1_label = f"FORECAST_{meses_abrev[next1.month]}_{next1.year}"
    next2_label = f"FORECAST_{meses_abrev[next2.month]}_{next2.year}"

    if "DATA_PREVISAO_ATIVACAO_CLIENTE" in df.columns:
        df["DATA_PREVISAO_ATIVACAO_CLIENTE"] = pd.to_datetime(
            df["DATA_PREVISAO_ATIVACAO_CLIENTE"],
            errors="coerce"
        )

        def classificar_faixa_backlog(data):
            if pd.isna(data):
                return "FORECAST_A_DEFINIR"
            if data < inicio_mes_atual:
                return "FORECAST_AJUSTAR"
            if data.year == hoje.year and data.month == hoje.month:
                return "BACKLOG_ATUAL"
            if data.year == next1.year and data.month == next1.month:
                return f"FORECAST_{meses_abrev[next1.month]}_{next1.year}"
            if data.year == next2.year and data.month == next2.month:
                return f"FORECAST_{meses_abrev[next2.month]}_{next2.year}"
            if data > next2 + pd.offsets.MonthEnd(0):
                return "MESES_RESTANTES"
            return "OUTROS_FORECAST"

        df["FAIXA_BACKLOG"] = df["DATA_PREVISAO_ATIVACAO_CLIENTE"].apply(classificar_faixa_backlog)

    # =========================

    df["FLAG_BACKLOG_ATUAL"] = df["FAIXA_BACKLOG"] == "BACKLOG_ATUAL"
    df["FLAG_NEXT1"] = df["FAIXA_BACKLOG"] == next1_label
    df["FLAG_NEXT2"] = df["FAIXA_BACKLOG"] == next2_label
    df["FLAG_RESTANTE"] = df["FAIXA_BACKLOG"] == "MESES_RESTANTES"
    df["FLAG_AJUSTAR"] = df["FAIXA_BACKLOG"] == "FORECAST_AJUSTAR"
    df["FLAG_DEFINIR"] = df["FAIXA_BACKLOG"] == "FORECAST_A_DEFINIR"

    df["FLAG_PEND_CLIENTE"] = df["TAREFA_RESPONSAVEL"] == "CLIENTE"
    df["FLAG_PEND_VENDAS"] = df["TAREFA_RESPONSAVEL"] == "VENDAS"
    df["FLAG_PEND_PJE"] = df["TAREFA_RESPONSAVEL"] == "PROJETOS ESPECIAIS"

    if "CARIMBO_STATUS" not in df.columns:
        if "CARIMBO_PREFIXO" in df.columns:
            df["CARIMBO_STATUS"] = np.where(
                df["CARIMBO_PREFIXO"].astype(str).str.strip().ne(""),
                "Com carimbo",
                "Sem carimbo"
            )
        elif "CARIMBO_PROJETO" in df.columns:
            df["CARIMBO_PREFIXO"] = df["CARIMBO_PROJETO"].astype(str).apply(extrair_prefixo_carimbo)
            df["CARIMBO_STATUS"] = np.where(
                df["CARIMBO_PREFIXO"].astype(str).str.strip().ne(""),
                "Com carimbo",
                "Sem carimbo"
            )
        else:
            df["CARIMBO_STATUS"] = "Sem carimbo"

    df["FLAG_SEM_CARIMBO"] = df["CARIMBO_STATUS"].astype(str).str.upper().str.strip() == "SEM CARIMBO"

    if "AGING_CIRCUITO" in df.columns:
        df["AGING_CIRCUITO"] = pd.to_numeric(df["AGING_CIRCUITO"], errors="coerce").fillna(0)
    else:
        df["AGING_CIRCUITO"] = 0

    df["SEM_CARIMBO_MAX_AGING"] = df["AGING_CIRCUITO"].where(df["FLAG_SEM_CARIMBO"], 0)

    df["FLAG_PEND_CLIENTE_EST"] = df["FLAG_PEND_CLIENTE"] & df["FLAG_ESTRATEGIA"]
    df["FLAG_PEND_VENDAS_EST"] = df["FLAG_PEND_VENDAS"] & df["FLAG_ESTRATEGIA"]
    df["FLAG_PEND_PJE_EST"] = df["FLAG_PEND_PJE"] & df["FLAG_ESTRATEGIA"]
    df["FLAG_SEM_CARIMBO_EST"] = df["FLAG_SEM_CARIMBO"] & df["FLAG_ESTRATEGIA"]

    # =========================
    # FLAGS DE ESTRATÉGIA + TEMPO
    # =========================

    df["FLAG_BACKLOG_ATUAL_EST"] = df["FLAG_BACKLOG_ATUAL"] & df["FLAG_ESTRATEGIA"]
    df["FLAG_NEXT1_EST"] = df["FLAG_NEXT1"] & df["FLAG_ESTRATEGIA"]
    df["FLAG_NEXT2_EST"] = df["FLAG_NEXT2"] & df["FLAG_ESTRATEGIA"]
    df["FLAG_RESTANTE_EST"] = df["FLAG_RESTANTE"] & df["FLAG_ESTRATEGIA"]
    df["FLAG_AJUSTAR_EST"] = df["FLAG_AJUSTAR"] & df["FLAG_ESTRATEGIA"]
    df["FLAG_DEFINIR_EST"] = df["FLAG_DEFINIR"] & df["FLAG_ESTRATEGIA"]

    # =========================
    # VALIDAR FAIXA_BACKLOG
    # =========================

    if "FAIXA_BACKLOG" not in df.columns:
        raise Exception("FAIXA_BACKLOG não encontrada. Verifique o ETL.")
    
    # =========================
    # FLAGS DE FORECAST
    # Já definidos acima com labels dinâmicos para os próximos meses.
    # =========================

    df["FLAG_BACKLOG_ATUAL"] = df["FAIXA_BACKLOG"] == "BACKLOG_ATUAL"
    df["FLAG_NEXT1"] = df["FAIXA_BACKLOG"] == next1_label
    df["FLAG_NEXT2"] = df["FAIXA_BACKLOG"] == next2_label
    df["FLAG_RESTANTE"] = df["FAIXA_BACKLOG"] == "MESES_RESTANTES"
    df["FLAG_AJUSTAR"] = df["FAIXA_BACKLOG"] == "FORECAST_AJUSTAR"
    df["FLAG_DEFINIR"] = df["FAIXA_BACKLOG"] == "FORECAST_A_DEFINIR"

    # ========================= 
    # DELTA RECEITA ESTRATÉGIA
    # =========================

    df["DELTA_RECEITA"] = pd.to_numeric(df["DELTA_RECEITA"], errors="coerce").fillna(0)
    if "REGRA_COMERCIAL_PY" in df.columns:
        df["REGRA_COMERCIAL_PY"] = pd.to_numeric(df["REGRA_COMERCIAL_PY"], errors="coerce").fillna(0)
    else:
        df["REGRA_COMERCIAL_PY"] = 0

    df["DELTA_RECEITA_ESTRATEGIA"] = df["DELTA_RECEITA"] * df["FLAG_ESTRATEGIA"]
    df["REGRA_COMERCIAL_ESTRATEGIA"] = df["REGRA_COMERCIAL_PY"] * df["FLAG_ESTRATEGIA"]
    df["BACKLOG_REGRA_COMERCIAL"] = df["REGRA_COMERCIAL_PY"] * df["FLAG_BACKLOG_ATUAL_EST"]
    df["BACKLOG_DELTA_RECEITA"] = df["DELTA_RECEITA"] * df["FLAG_BACKLOG_ATUAL_EST"]

    # Receita segmentada por classificação e por produto
    df["RECEITA_GROSS"] = df["DELTA_RECEITA"] * df["FLAG_GROSS"]
    df["RECEITA_SERVICO"] = df["DELTA_RECEITA"] * df["FLAG_SERVICO"]
    df["RECEITA_INTERNET"] = df["DELTA_RECEITA"] * df["FLAG_INTERNET"]
    df["RECEITA_DADOS"] = df["DELTA_RECEITA"] * df["FLAG_DADOS"]
    df["RECEITA_VOZ"] = df["DELTA_RECEITA"] * df["FLAG_VOZ"]
    df["RECEITA_WIFI"] = df["DELTA_RECEITA"] * df["FLAG_WIFI"]

    # =========================
    # AGREGAÇÃO
    # =========================

    df_group = (
        df
        .groupby("CLIENTE", as_index=False)
        .agg(
            TOTAL=("CLIENTE", "count"),

            # classificação
            GROSS=("FLAG_GROSS", "sum"),
            RECEITA_GROSS=("RECEITA_GROSS", "sum"),
            SERVICO=("FLAG_SERVICO", "sum"),
            RECEITA_SERVICO=("RECEITA_SERVICO", "sum"),

            # produto
            INTERNET=("FLAG_INTERNET", "sum"),
            RECEITA_INTERNET=("RECEITA_INTERNET", "sum"),
            DADOS=("FLAG_DADOS", "sum"),
            RECEITA_DADOS=("RECEITA_DADOS", "sum"),
            VOZ=("FLAG_VOZ", "sum"),
            RECEITA_VOZ=("RECEITA_VOZ", "sum"),
            WIFI=("FLAG_WIFI", "sum"),
            RECEITA_WIFI=("RECEITA_WIFI", "sum"),

            # estratégia
            ESTRATEGIA=("FLAG_ESTRATEGIA", "sum"),
            DELTA_RECEITA_GERAL=("DELTA_RECEITA", "sum"),
            DELTA_RECEITA_ESTRATEGIA=("DELTA_RECEITA_ESTRATEGIA", "sum"),
            REGRA_COMERCIAL_ESTRATEGIA=("REGRA_COMERCIAL_ESTRATEGIA", "sum"),

            # 🔥 NOVO BLOCO TEMPORAL
            BACKLOG_ATUAL=("FLAG_BACKLOG_ATUAL_EST", "sum"),
            BACKLOG_REGRA_COMERCIAL=("BACKLOG_REGRA_COMERCIAL", "sum"),
            BACKLOG_DELTA_RECEITA=("BACKLOG_DELTA_RECEITA", "sum"),
            PEND_CLIENTE=("FLAG_PEND_CLIENTE_EST", "sum"),
            PEND_VENDAS=("FLAG_PEND_VENDAS_EST", "sum"),
            PEND_PJE=("FLAG_PEND_PJE_EST", "sum"),
            SEM_CARIMBO=("FLAG_SEM_CARIMBO_EST", "sum"),
            SEM_CARIMBO_AGING=("SEM_CARIMBO_MAX_AGING", "max"),
            MESES_RESTANTES=("FLAG_RESTANTE_EST", "sum"),
            FORECAST_AJUSTAR=("FLAG_AJUSTAR_EST", "sum"),
            FORECAST_A_DEFINIR=("FLAG_DEFINIR_EST", "sum"),
            **{
                next1_label: ("FLAG_NEXT1_EST", "sum"),
                next2_label: ("FLAG_NEXT2_EST", "sum"),
            }
        )
    )

    # =========================
    # INTEGRAR META MENSAL
    # =========================
    
    df_meta = carregar_meta_mensal()
    df_forecast_mes = calcular_forecast_inicio_mes(df_meta)
    
    if not df_forecast_mes.empty:
        unmatched_clients = df_forecast_mes[~df_forecast_mes["CLIENTE"].isin(df_group["CLIENTE"])]
        if not unmatched_clients.empty:
            report_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'clientes_meta_sem_correspondencia.csv'))
            unmatched_clients.to_csv(report_path, index=False)
            print(f"WARNING: {len(unmatched_clients)} cliente(s) meta sem correspondência gravados em {report_path}")

        df_group = df_group.merge(df_forecast_mes, on="CLIENTE", how="left")
        df_group["FORECAST_INICIO_MES"] = df_group["FORECAST_INICIO_MES"].fillna(0).astype(int)
        df_group["FORECAST_REGRA_COMERCIAL"] = df_group["FORECAST_REGRA_COMERCIAL"].fillna(0)
        df_group["FORECAST_DELTA_RECEITA"] = df_group["FORECAST_DELTA_RECEITA"].fillna(0)
    else:
        df_group["FORECAST_INICIO_MES"] = 0
        df_group["FORECAST_REGRA_COMERCIAL"] = 0
        df_group["FORECAST_DELTA_RECEITA"] = 0

    return df_group

# ==============================
# SÉRIE TEMPORAL: CIRCUITOS POR MÊS
# ==============================

def circuitos_por_mes_cliente(df_backlog, cliente_selecionado="Todos"):
    """
    Agrega quantidade de circuitos por mês de previsão de ativação
    para um cliente específico ou todos os clientes.
    
    Parâmetros:
    - df_backlog: DataFrame com dados de backlog
    - cliente_selecionado: Cliente específico ou "Todos"
    
    Retorna:
    - DataFrame com colunas: Mês (YYYY-MM), Quantidade
    """
    
    if df_backlog.empty:
        return pd.DataFrame(columns=["Mês", "Quantidade"])
    
    df = df_backlog.copy()
    
    # Normalizar cliente para comparação
    if "CLIENTE" in df.columns:
        df["CLIENTE"] = df["CLIENTE"].apply(normalizar_cliente)
    
    # Filtrar por cliente se não for "Todos"
    if cliente_selecionado != "Todos":
        cliente_norm = normalizar_cliente(cliente_selecionado)
        df = df[df["CLIENTE"] == cliente_norm]
    
    # Verificar se tem a coluna de data
    if "DATA_PREVISAO_ATIVACAO_CLIENTE" not in df.columns:
        return pd.DataFrame(columns=["Mês", "Quantidade"])
    
    # Converter para datetime
    df["DATA_PREVISAO_ATIVACAO_CLIENTE"] = pd.to_datetime(
        df["DATA_PREVISAO_ATIVACAO_CLIENTE"],
        errors="coerce"
    )
    
    # Remover nulos
    df = df[df["DATA_PREVISAO_ATIVACAO_CLIENTE"].notna()]
    
    if df.empty:
        return pd.DataFrame(columns=["Mês", "Quantidade"])
    
    # Extrair ano-mês
    df["Mês"] = df["DATA_PREVISAO_ATIVACAO_CLIENTE"].dt.to_period("M")
    
    # Contar circuitos por mês
    resultado = (
        df
        .groupby("Mês", as_index=False)
        .agg(Quantidade=("COD_CIR", "count"))
        .sort_values("Mês")
    )
    
    # Converter período de volta para string (YYYY-MM)
    resultado["Mês"] = resultado["Mês"].astype(str)
    
    return resultado
