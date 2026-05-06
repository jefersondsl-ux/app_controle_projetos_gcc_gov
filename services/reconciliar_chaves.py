# ========================================================
# Módulo de Reconciliação de Chaves usando d_Projetos
# ========================================================

import pandas as pd


def enriquecer_com_d_projetos(df_fato, df_dim, chave_em_fato="CARIMBO_PREFIXO", chave_em_dim="CARIMBO_PREFIXO"):
    """
    Enriquece um dataframe de fato (backlog/produção) com IDP_PROJETO usando d_Projetos como lookup.
    
    :param df_fato: dataframe de fato a enriquecer (backlog ou produção)
    :param df_dim: dimensão d_Projetos
    :param chave_em_fato: coluna em df_fato usada para lookup (ex: "CARIMBO_PREFIXO")
    :param chave_em_dim: coluna em df_dim usada para lookup (ex: "CARIMBO_PREFIXO")
    :return: df_fato enriquecido com IDP_PROJETO preenchido
    
    Exemplo:
        df_backlog_enriq = enriquecer_com_d_projetos(df_backlog, df_d_projetos, "CARIMBO_PREFIXO", "CARIMBO_PREFIXO")
    """
    if df_dim.empty:
        return df_fato

    df_fato = df_fato.copy()
    
    # normalizar chaves
    if chave_em_fato in df_fato.columns:
        df_fato[chave_em_fato] = df_fato[chave_em_fato].astype(str).str.strip()
    
    # criar lookup dictionary
    lookup_dict = (
        df_dim
        .dropna(subset=[chave_em_dim, "IDP_PROJETO"])
        .drop_duplicates(chave_em_dim)
    )
    lookup_dict = dict(zip(lookup_dict[chave_em_dim], lookup_dict["IDP_PROJETO"]))
    
    # garantir coluna IDP_PROJETO
    if "IDP_PROJETO" not in df_fato.columns:
        df_fato["IDP_PROJETO"] = None
    
    # preencher IDP_PROJETO vazio com valor da dimensão
    mask_vazio = (
        (df_fato["IDP_PROJETO"].isna()) | 
        (df_fato["IDP_PROJETO"].astype(str).str.strip() == "")
    )
    
    if chave_em_fato in df_fato.columns and mask_vazio.any():
        df_fato.loc[mask_vazio, "IDP_PROJETO"] = (
            df_fato.loc[mask_vazio, chave_em_fato].map(lookup_dict)
        )
    
    return df_fato


def gerar_relatorio_desconexoes(df_controle, df_backlog, df_producao):
    """
    Gera relatório de desconexões entre bases (backlog/produção sem Controle).
    
    :param df_controle: dataframe de controle
    :param df_backlog: dataframe de backlog processado
    :param df_producao: dataframe de produção processado
    :return: dict com relatórios
    """
    
    backlog_ids = set(df_backlog["IDP_PROJETO"].dropna().unique())
    producao_ids = set(df_producao["IDP_PROJETO"].dropna().unique())
    controle_ids = set(df_controle["IDP_PROJETO"].dropna().unique())
    
    backlog_sem_controle = df_backlog[
        (df_backlog["IDP_PROJETO"].isin(backlog_ids - controle_ids)) &
        (df_backlog["IDP_PROJETO"].notna())
    ].copy()
    
    producao_sem_controle = df_producao[
        (df_producao["IDP_PROJETO"].isin(producao_ids - controle_ids)) &
        (df_producao["IDP_PROJETO"].notna())
    ].copy()
    
    return {
        "backlog_sem_controle": backlog_sem_controle,
        "producao_sem_controle": producao_sem_controle,
        "total_backlog_desconectado": len(backlog_sem_controle),
        "total_producao_desconectado": len(producao_sem_controle),
    }
