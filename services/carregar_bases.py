import streamlit as st
import pandas as pd
import os
import sys
import glob
from pathlib import Path

# ===============================
# CONFIGURAÇÃO CENTRALIZADA
# ===============================
# Importa config.py da raiz do projeto (funciona em qualquer máquina / usuário)

_ROOT_PROJETO = Path(__file__).resolve().parent.parent.parent  # services → app_gcc_gov_v3 → Projetos_GOV
if str(_ROOT_PROJETO) not in sys.path:
    sys.path.insert(0, str(_ROOT_PROJETO))

from config import BASE_DIR  # detecção automática do OneDrive

# --------------------------------------

# Caminhos das bases

PATH_DIARIO            = BASE_DIR / "Diario_Bordo" / "BD_Diario_Bordo" / "f_Diario_Bordo.xlsx"
PATH_APONT             = BASE_DIR / "Diario_Bordo" / "BD_DIM"          / "d_apontamentos.xlsx"
PATH_CONTROLE          = BASE_DIR / "Diario_Bordo" / "BD_DIM"          / "d_Controle_Projetos.xlsx"
PATH_BACKLOG           = BASE_DIR / "Base_Dados_SGP" / "Bases_Processadas_Python" / "BD_Backlog_SGP.xlsx"
PATH_PRODUCAO_ANALITICO= BASE_DIR / "Base_Dados_SGP" / "Bases_Processadas_Python" / "BD_Produção_Analitica.xlsx"
PATH_PROJETOS          = BASE_DIR / "Diario_Bordo" / "BD_DIM"          / "d_Projetos.xlsx"
PATH_TECNOLOGIA        = BASE_DIR / "Diario_Bordo" / "BD_DIM"          / "d_tecnologia.xlsx"
PATH_RESPONSAVEIS      = BASE_DIR / "Diario_Bordo" / "BD_DIM"          / "d_responsaveis.xlsx"
PATH_PRODUCAO_HISTORICO= BASE_DIR / "Base_Dados_SGP" / "Bases_Processadas_Python" / "BD_Produção_Historico.xlsx"

# --------------------------------------

@st.cache_data
def carregar_diario(ttl=30):
    try:
        df = pd.read_excel(PATH_DIARIO)
        df.columns = (
            df.columns
            .str.strip()
            .str.upper()
            .str.replace(" ", "_")
        )

        if "IDP_PROJETO" not in df.columns:

            if "IDP" in df.columns:
                df["IDP_PROJETO"] = df["IDP"]

            else:
                st.warning("Coluna IDP_PROJETO não encontrada no Diário")

        return df
            
    except Exception as e:
        st.error(f"Erro ao carregar Diário: {e}")
        return pd.DataFrame()

# --------------------------------------

@st.cache_data
def carregar_apontamentos(ttl=30):
    try:
        df = pd.read_excel(PATH_APONT)
        df.columns = df.columns.str.strip().str.upper()

        if "IDP_PROJETO" not in df.columns and "IDP" in df.columns:
            df["IDP_PROJETO"] = df["IDP"]

        return df
    
    except Exception as e:
        st.error(f"Erro ao carregar Apontamentos: {e}")
        return pd.DataFrame()  


# --------------------------------------

@st.cache_data
def carregar_controle(ttl=30):

    try:
        df = pd.read_excel(PATH_CONTROLE)

        df.columns = (
            df.columns
            .str.strip()
            .str.upper()
        )

        # padronização de colunas principais
        if "IDP_PROJETO" not in df.columns and "IDP" in df.columns:
            df["IDP_PROJETO"] = df["IDP"]

        return df
    
    except Exception as e:
        st.error(f"Erro ao carregar Controle: {e}")
        return pd.DataFrame()

# --------------------------------------

@st.cache_data
def carregar_backlog(ttl=30):

    try:
        df = pd.read_excel(PATH_BACKLOG)
        df.columns = df.columns.str.strip().str.upper()

        if "IDP_PROJETO" not in df.columns and "IDP" in df.columns:
            df["IDP_PROJETO"] = df["IDP"]

        return df

    except Exception as e:
        st.error(f"Erro ao carregar Backlog: {e}")
        return pd.DataFrame()

# --------------------------------------

@st.cache_data
def carregar_projetos(ttl=30):

    try:
        df = pd.read_excel(PATH_PROJETOS)

        df.columns = df.columns.str.strip().str.upper()

        if "IDP_PROJETO" not in df.columns and "IDP" in df.columns:
            df["IDP_PROJETO"] = df["IDP"]

        return df

    except Exception as e:
        st.error(f"Erro ao carregar d_Projetos: {e}")
        return pd.DataFrame()

# --------------------------------------
# SALVAR BASE CONTROLE
# --------------------------------------

def salvar_controle(df):

    try:

        df.to_excel(PATH_CONTROLE, index=False)

        return True

    except Exception as e:

        print(f"Erro ao salvar controle: {e}")

        return False
    
# --------------------------------------
    
@st.cache_data
def carregar_producao(ttl=30):

    try:

        df = pd.read_excel(PATH_PRODUCAO_ANALITICO)

        df.columns = df.columns.str.strip().str.upper()

        # =========================
        # VALIDAÇÃO DE ESTRUTURA
        # =========================
        colunas_obrigatorias = ["CARIMBO_PREFIXO", "QTD_CIRCUITOS"]

        faltantes = [c for c in colunas_obrigatorias if c not in df.columns]

        if faltantes:
            st.error(f"Base analítica inválida. Colunas faltantes: {faltantes}")
            return pd.DataFrame()

        if "QTD_ESTRATEGIA_SIM" not in df.columns:
            st.warning(
                "A base analítica não contém QTD_ESTRATEGIA_SIM. "
                "Será usado QTD_CIRCUITOS como fallback para a produção."
            )
        else:
            df["QTD_ESTRATEGIA_SIM"] = pd.to_numeric(
                df["QTD_ESTRATEGIA_SIM"], errors="coerce"
            ).fillna(0).astype(int)

        if "QTD_CIRCUITOS_TOTAL" in df.columns:
            df["QTD_CIRCUITOS_TOTAL"] = pd.to_numeric(
                df["QTD_CIRCUITOS_TOTAL"], errors="coerce"
            ).fillna(0).astype(int)

        df["QTD_CIRCUITOS"] = pd.to_numeric(
            df["QTD_CIRCUITOS"], errors="coerce"
        ).fillna(0).astype(int)

        return df

    except Exception as e:

        st.error(f"Erro ao carregar produção: {e}")
        return pd.DataFrame()

# --------------------------------------

@st.cache_data
def carregar_responsaveis(ttl=30):

    try:
        df = pd.read_excel(PATH_RESPONSAVEIS)

        df.columns = (
            df.columns
            .str.strip()
            .str.upper()
        )

        # validação mínima
        colunas_esperadas = ["NOME", "FUNCAO", "ATIVO"]

        faltantes = [c for c in colunas_esperadas if c not in df.columns]

        if faltantes:
            st.error(f"d_responsaveis inválido. Faltando: {faltantes}")
            return pd.DataFrame()

        return df

    except Exception as e:
        st.error(f"Erro ao carregar responsáveis: {e}")
        return pd.DataFrame()

# --------------------------------------

@st.cache_data
def carregar_tecnologia(ttl=30):

    try:
        df = pd.read_excel(PATH_TECNOLOGIA)

        df.columns = df.columns.str.strip().str.upper()

        if "TECNOLOGIA" not in df.columns:
            st.error("d_tecnologia inválido")
            return pd.DataFrame()

        return df

    except Exception as e:
        st.error(f"Erro ao carregar tecnologia: {e}")
        return pd.DataFrame()
    
# --------------------------------------

@st.cache_data
def carregar_meta_mensal(ttl=30):
    """Carrega a meta mensal mais recente de backlog"""
    try:
        output_dir = str(
            BASE_DIR / "Base_Dados_SGP" / "Bases_Processadas_Python" / "Backlog_Meta_Mensal"
        )
        
        if not os.path.exists(output_dir):
            st.warning(f"Pasta de metas não encontrada: {output_dir}")
            return pd.DataFrame()
        
        # Procura o arquivo mais recente
        padrao = os.path.join(output_dir, 'Meta_Mensal_Backlog_*.xlsx')
        arquivos = sorted(glob.glob(padrao), reverse=True)
        
        if not arquivos:
            st.warning("Nenhuma meta mensal salva encontrada")
            return pd.DataFrame()
        
        df = pd.read_excel(arquivos[0], engine='openpyxl')
        df.columns = df.columns.str.strip().str.upper()
        
        return df
        
    except Exception as e:
        st.error(f"Erro ao carregar meta mensal: {e}")
        return pd.DataFrame()

# --------------------------------------

@st.cache_data
def carregar_receita_historica(ttl=30):
    """
    Carrega BD_Produção_Historico.xlsx e agrega DELTA_RECEITA por IDP_PROJETO.

    Retorna um DataFrame com colunas [IDP_PROJETO, Receita_Historico] representando
    a receita de produção acumulada histórica — usado para substituir RECEITA_TOTAL
    da BD_Produção_Analitica.xlsx, que reflete apenas o período corrente.

    Aplica enriquecimento via CARIMBO_PREFIXO → d_Projetos para recuperar registros
    com IDP_PROJETO nulo (mesma lógica da tabela analítica principal).
    """
    try:
        df = pd.read_excel(PATH_PRODUCAO_HISTORICO)
        df.columns = df.columns.str.strip().str.upper()

        colunas_necessarias = ["IDP_PROJETO", "DELTA_RECEITA"]
        faltantes = [c for c in colunas_necessarias if c not in df.columns]
        if faltantes:
            st.warning(f"BD_Produção_Historico sem colunas: {faltantes}")
            return pd.DataFrame()

        df["DELTA_RECEITA"] = pd.to_numeric(df["DELTA_RECEITA"], errors="coerce").fillna(0)

        # ── Enriquecimento via CARIMBO_PREFIXO ──────────────────────────────
        # Registros com IDP_PROJETO nulo recebem o IDP a partir de d_Projetos,
        # usando CARIMBO_PREFIXO como chave — evita perder receita dessas linhas.
        if "CARIMBO_PREFIXO" in df.columns:
            try:
                d_proj = pd.read_excel(PATH_PROJETOS)
                d_proj.columns = d_proj.columns.str.strip().str.upper()

                from services.reconciliar_chaves import enriquecer_com_d_projetos
                df = enriquecer_com_d_projetos(
                    df, d_proj,
                    chave_em_fato="CARIMBO_PREFIXO",
                    chave_em_dim="CARIMBO_PREFIXO"
                )
            except Exception:
                pass  # se falhar, continua sem enriquecimento

        # ── Normalizar IDP e excluir registros sem chave ────────────────────
        df["IDP_PROJETO"] = df["IDP_PROJETO"].astype(str).str.strip()
        df = df[~df["IDP_PROJETO"].isin(["nan", "None", ""])]

        receita_hist = (
            df.groupby("IDP_PROJETO", as_index=False)
            .agg(Receita_Historico=("DELTA_RECEITA", "sum"))
        )

        return receita_hist

    except Exception as e:
        st.error(f"Erro ao carregar receita histórica: {e}")
        return pd.DataFrame()

# --------------------------------------