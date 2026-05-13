import streamlit as st
import pandas as pd
import os
import glob

# --------------------------------------

# Caminhos das bases

PATH_DIARIO = r"C:\Users\z181040\OneDrive - Claro SA\BASES\Projetos_GOV\Diario_Bordo\BD_Diario_Bordo\f_Diario_Bordo.xlsx"
PATH_APONT = r"C:\Users\z181040\OneDrive - Claro SA\BASES\Projetos_GOV\Diario_Bordo\BD_DIM\d_apontamentos.xlsx"
PATH_CONTROLE = r"C:\Users\z181040\OneDrive - Claro SA\BASES\Projetos_GOV\Diario_Bordo\BD_DIM\d_Controle_Projetos.xlsx"
PATH_BACKLOG = r"C:\Users\z181040\OneDrive - Claro SA\BASES\Projetos_GOV\Base_Dados_SGP\Bases_Processadas_Python\BD_Backlog_SGP.xlsx"
PATH_PRODUCAO_ANALITICO = r"C:\Users\z181040\OneDrive - Claro SA\BASES\Projetos_GOV\Base_Dados_SGP\Bases_Processadas_Python\BD_Produção_Analitica.xlsx"
PATH_PROJETOS = r"C:\Users\z181040\OneDrive - Claro SA\BASES\Projetos_GOV\Base_Dados_SGP\Bases_Processadas_Python\BASE_PROJETOS\d_Projetos.xlsx"
PATH_TECNOLOGIA = r"C:\Users\z181040\OneDrive - Claro SA\BASES\Projetos_GOV\Diario_Bordo\BD_DIM\d_tecnologia.xlsx"
PATH_RESPONSAVEIS = r"C:\Users\z181040\OneDrive - Claro SA\BASES\Projetos_GOV\Diario_Bordo\BD_DIM\d_responsaveis.xlsx"

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
        colunas_esperadas = ["CARIMBO_PREFIXO", "QTD_CIRCUITOS"]

        faltantes = [c for c in colunas_esperadas if c not in df.columns]

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
        onedrive_path = os.environ.get("OneDriveCommercial") or os.environ.get("OneDrive")
        if not onedrive_path:
            st.warning("OneDrive não configurado")
            return pd.DataFrame()
        
        output_dir = os.path.join(
            onedrive_path,
            'BASES/Projetos_GOV/Base_Dados_SGP/Bases_Processadas_Python/Backlog_Meta_Mensal'
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