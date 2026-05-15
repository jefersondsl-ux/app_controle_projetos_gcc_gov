import os
import re
import pandas as pd


DEFAULT_TAREFA_LABELS = {
    "IT0301": "Autorizar entrada",
    "IT0302": "Esclarecimento proj. especiais",
    "IT0304": "Esclarecimento de vendas",
    "IT0305": "Agendar com vendas",
    "IT0306": "Suporte vendas",
    "IT0307": "Esclarecimento proj. especiais recurso",
    "IT0501": "Autorizar entrada condominio/datacenter",
    "IT0502": "Providenciar equipamento",
    "IT0503": "Finalizar infra/rede",
    "IT0504": "Atualizar dados de contato",
    "IT0506": "Informar data de agendamento",
    "IT0507": "Validar entrega do acesso/servico",
    "IT0508": "Conveniencia cliente",
    "IT0509": "Negociar data de agendamento",
    "IT0510": "Informar dados para configuracao",
    "IT0511": "Ajustar CNPJ",
    "IT0512": "Atualizar dados de contato PA",
    "IT0514": "Confirmar data agendada BLC",
    "IT0515": "Autorizar entrada condominio/datacenter PA",
    "IT0516": "Informar data de agendamento PA",
    "IT0517": "Informar cronograma",
    "IT0518": "Informar data de agendamento blacklist",
    "IT0519": "Validar entrega blacklist",
    "IT0520": "Aguardando confirmacao de agenda",
}


def _carregar_labels_externos():
    path = os.path.abspath(
        os.path.join(
            os.path.dirname(__file__),
            "..",
            "scripts",
            "mappings",
            "tarefa_labels.csv",
        )
    )

    if not os.path.exists(path):
        return {}

    try:
        df_labels = pd.read_csv(path)
    except Exception:
        return {}

    colunas_necessarias = {"cod_tarefa", "label_amigavel"}
    if not colunas_necessarias.issubset(set(df_labels.columns)):
        return {}

    df_labels["cod_tarefa"] = (
        df_labels["cod_tarefa"].astype(str).str.upper().str.strip()
    )
    df_labels["label_amigavel"] = (
        df_labels["label_amigavel"].astype(str).str.strip()
    )

    df_labels = df_labels[
        (df_labels["cod_tarefa"] != "") &
        (df_labels["label_amigavel"] != "")
    ].drop_duplicates("cod_tarefa", keep="last")

    return dict(zip(df_labels["cod_tarefa"], df_labels["label_amigavel"]))


def _faixa_aging(valor):
    if pd.isna(valor):
        return "Sem aging"

    valor = float(valor)
    if valor <= 5:
        return "0-5"
    if valor <= 15:
        return "6-15"
    if valor <= 30:
        return "16-30"
    return "31+"


def _fallback_label(tarefa_atual, cod_tarefa):
    tarefa_atual = "" if pd.isna(tarefa_atual) else str(tarefa_atual).strip()
    if " - " in tarefa_atual:
        tarefa_atual = tarefa_atual.split(" - ", 1)[1].strip()

    tarefa_atual = re.sub(r"\[[^\]]+\]", "", tarefa_atual).strip()
    tarefa_atual = re.sub(r"\s+", " ", tarefa_atual)

    if tarefa_atual:
        return tarefa_atual

    return cod_tarefa if cod_tarefa else "Tarefa nao identificada"


def preparar_base_pendencias(df_backlog):
    df = df_backlog.copy()

    df.columns = df.columns.str.strip().str.upper()

    if "COD_CIR" not in df.columns:
        raise Exception("COD_CIR nao encontrado na base de backlog")

    if "COD_TAREFA_ATUAL" not in df.columns:
        if "TAREFA_ATUAL" in df.columns:
            df["COD_TAREFA_ATUAL"] = (
                df["TAREFA_ATUAL"]
                .astype(str)
                .str.split(" - ")
                .str[0]
                .str.strip()
                .str.upper()
            )
        else:
            df["COD_TAREFA_ATUAL"] = ""

    if "TAREFA_ATUAL" not in df.columns:
        df["TAREFA_ATUAL"] = ""

    if "TAREFA_RESPONSAVEL" not in df.columns:
        df["TAREFA_RESPONSAVEL"] = "Outras Tarefas"

    if "CLIENTE" not in df.columns:
        df["CLIENTE"] = "Cliente nao informado"

    if "CARIMBO_PROJETO" not in df.columns:
        if "PROJETO" in df.columns:
            df["CARIMBO_PROJETO"] = df["PROJETO"]
        elif "PROJETO_NOME_DEPENDENCIA_CLIENTE" in df.columns:
            df["CARIMBO_PROJETO"] = df["PROJETO_NOME_DEPENDENCIA_CLIENTE"]
        else:
            df["CARIMBO_PROJETO"] = "Projeto nao informado"

    if "CLASSIFICACAO" not in df.columns:
        df["CLASSIFICACAO"] = ""

    if "ESTRATEGIA_REDES" not in df.columns:
        df["ESTRATEGIA_REDES"] = ""

    if "GER_TEC_AJUST" not in df.columns:
        df["GER_TEC_AJUST"] = ""

    if "AGING_TAREFA" not in df.columns:
        df["AGING_TAREFA"] = pd.NA

    df["CLIENTE"] = df["CLIENTE"].fillna("Cliente nao informado").astype(str).str.strip()
    df["CARIMBO_PROJETO"] = (
        df["CARIMBO_PROJETO"]
        .fillna("")
        .astype(str)
        .str.strip()
    )
    if "PROJETO" in df.columns:
        fallback_projeto = df["PROJETO"].fillna("").astype(str).str.strip()
    elif "PROJETO_NOME_DEPENDENCIA_CLIENTE" in df.columns:
        fallback_projeto = df["PROJETO_NOME_DEPENDENCIA_CLIENTE"].fillna("").astype(str).str.strip()
    else:
        fallback_projeto = "Projeto nao informado"

    df["CARIMBO_PROJETO"] = df["CARIMBO_PROJETO"].where(
        df["CARIMBO_PROJETO"].ne(""),
        fallback_projeto,
    )
    df["CLASSIFICACAO"] = df["CLASSIFICACAO"].fillna("").astype(str).str.upper().str.strip()
    df["ESTRATEGIA_REDES"] = df["ESTRATEGIA_REDES"].fillna("").astype(str).str.upper().str.strip()
    df["GER_TEC_AJUST"] = df["GER_TEC_AJUST"].fillna("").astype(str).str.strip()
    df["TAREFA_RESPONSAVEL"] = df["TAREFA_RESPONSAVEL"].fillna("Outras Tarefas").astype(str).str.strip()
    df["COD_TAREFA_ATUAL"] = df["COD_TAREFA_ATUAL"].fillna("").astype(str).str.upper().str.strip()

    df["AGING_TAREFA"] = pd.to_numeric(df["AGING_TAREFA"], errors="coerce")
    df["AGING_FAIXA"] = df["AGING_TAREFA"].apply(_faixa_aging)

    labels = DEFAULT_TAREFA_LABELS.copy()
    labels.update(_carregar_labels_externos())

    df["TAREFA_LABEL"] = df.apply(
        lambda row: labels.get(
            row["COD_TAREFA_ATUAL"],
            _fallback_label(row["TAREFA_ATUAL"], row["COD_TAREFA_ATUAL"]),
        ),
        axis=1,
    )

    return df


def aplicar_filtros_pendencias(
    df,
    responsaveis,
    classificacoes,
    estrategias,
    gerentes_tecnicos,
    aging_faixas,
    clientes,
):
    df_filtrado = df.copy()

    if responsaveis:
        df_filtrado = df_filtrado[df_filtrado["TAREFA_RESPONSAVEL"].isin(responsaveis)]

    if classificacoes:
        df_filtrado = df_filtrado[df_filtrado["CLASSIFICACAO"].isin(classificacoes)]

    if estrategias:
        df_filtrado = df_filtrado[df_filtrado["ESTRATEGIA_REDES"].isin(estrategias)]

    if gerentes_tecnicos:
        df_filtrado = df_filtrado[df_filtrado["GER_TEC_AJUST"].isin(gerentes_tecnicos)]

    if aging_faixas:
        df_filtrado = df_filtrado[df_filtrado["AGING_FAIXA"].isin(aging_faixas)]

    if clientes:
        df_filtrado = df_filtrado[df_filtrado["CLIENTE"].isin(clientes)]

    return df_filtrado


def montar_matriz_cliente_tarefa(df, eixo_y="CLIENTE", escopo_tarefas="Todas", responsavel_foco="Todos"):
    df_matrix = df.copy()

    if escopo_tarefas == "Somente responsavel" and responsavel_foco != "Todos":
        df_matrix = df_matrix[df_matrix["TAREFA_RESPONSAVEL"] == responsavel_foco]

    if eixo_y not in df_matrix.columns:
        raise Exception(f"Eixo Y invalido: {eixo_y}")

    if df_matrix.empty:
        return pd.DataFrame(columns=[eixo_y, "TOTAL"])

    tabela = pd.pivot_table(
        df_matrix,
        index=eixo_y,
        columns="TAREFA_LABEL",
        values="COD_CIR",
        aggfunc=pd.Series.nunique,
        fill_value=0,
    )

    if tabela.empty:
        return pd.DataFrame(columns=[eixo_y, "TOTAL"])

    totais_colunas = tabela.sum(axis=0).sort_values(ascending=False)
    tabela = tabela[totais_colunas.index.tolist()]

    tabela["TOTAL"] = tabela.sum(axis=1)
    tabela = tabela.sort_values("TOTAL", ascending=False)

    colunas_finais = ["TOTAL"] + [c for c in tabela.columns if c != "TOTAL"]
    tabela = tabela[colunas_finais]

    return tabela.reset_index()


def resumo_por_responsavel(df):
    if df.empty:
        return pd.DataFrame(columns=["TAREFA_RESPONSAVEL", "QTD_CIRCUITOS", "QTD_TAREFAS"])

    resumo = (
        df.groupby("TAREFA_RESPONSAVEL", as_index=False)
        .agg(
            QTD_CIRCUITOS=("COD_CIR", pd.Series.nunique),
            QTD_TAREFAS=("TAREFA_LABEL", pd.Series.nunique),
        )
        .sort_values("QTD_CIRCUITOS", ascending=False)
    )

    return resumo


def colunas_detalhe_disponiveis(df):
    preferidas = [
        "COD_CIR",
        "CLIENTE",
        "CARIMBO_PROJETO",
        "PROJETO",
        "IDP_PROJETO",
        "CLASSIFICACAO",
        "TAREFA_RESPONSAVEL",
        "COD_TAREFA_ATUAL",
        "TAREFA_LABEL",
        "TAREFA_ATUAL",
        "AGING_TAREFA",
        "AGING_FAIXA",
        "GER_TEC_AJUST",
        "ESTRATEGIA_REDES",
        "DATA_ENTRADA_BACKLOG",
        "DATA_PREVISAO_ATIVACAO_CLIENTE",
        "FAIXA_BACKLOG",
    ]

    return [col for col in preferidas if col in df.columns]
