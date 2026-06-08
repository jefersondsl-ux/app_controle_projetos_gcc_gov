import pandas as pd
import re
import sys
from pathlib import Path

# ===============================
# CONFIGURAÇÃO CENTRALIZADA
# ===============================
# Importa config.py da raiz do projeto (funciona em qualquer máquina / usuário)

ROOT_PROJETO = Path(__file__).resolve().parent.parent.parent  # sobe: scripts → app_gcc_gov_v3 → Projetos_GOV
if str(ROOT_PROJETO) not in sys.path:
    sys.path.insert(0, str(ROOT_PROJETO))

from config import BASE_DIR  # detecção automática do OneDrive

PATH_CONTROLE = BASE_DIR / "Diario_Bordo"    / "BD_DIM"                     / "d_Controle_Projetos.xlsx"
PATH_BACKLOG  = BASE_DIR / "Base_Dados_SGP"  / "Bases_Processadas_Python"   / "BD_Backlog_SGP.xlsx"
PATH_PRODUCAO = BASE_DIR / "Diario_Bordo"    / "BD_Produção"                / "BD_Produção.xlsx"
PATH_DIARIO   = BASE_DIR / "Diario_Bordo"    / "BD_Diario_Bordo"            / "f_Diario_Bordo.xlsx"

OUTPUT = BASE_DIR / "Diario_Bordo" / "BD_DIM" / "d_Projetos.xlsx"

ROOT = Path(__file__).resolve().parent
MAPPINGS_DIR = ROOT / "mappings"
QA_REPORT_DIR = ROOT / "reports"
IDP_OVERRIDES_PATH      = MAPPINGS_DIR / "idp_overrides.csv"
CLIENTE_OVERRIDES_PATH  = MAPPINGS_DIR / "cliente_overrides.csv"
CARIMBO_MAP_PATH        = MAPPINGS_DIR / "carimbo_to_idp.csv"   # gerado por mapear_prefixos_sem_idp.py


# ===============================
# FUNÇÕES AUXILIARES
# ===============================

def load_idp_overrides(path):
    if not Path(path).exists():
        return {}

    df = pd.read_csv(path, dtype=str).fillna("")
    if "idp_source" not in df.columns or "idp_target" not in df.columns:
        raise ValueError(f"Arquivo de overrides inválido: {path}")

    return {
        row["idp_source"].strip(): row["idp_target"].strip()
        for _, row in df.iterrows()
        if row["idp_source"].strip() and row["idp_target"].strip()
    }


def apply_idp_overrides(df, overrides, cols=("IDP_PROJETO",)):
    if not overrides:
        return df

    for col in cols:
        if col in df.columns:
            df[col] = df[col].apply(
                lambda v: overrides.get(str(v).strip(), v) if pd.notna(v) else v
            )
    return df


def load_cliente_overrides(path):
    """Carrega mapeamento de CARIMBO_PREFIXO → CLIENTE."""
    if not Path(path).exists():
        return {}

    df = pd.read_csv(path, dtype=str).fillna("")
    if "carimbo_prefixo" not in df.columns or "cliente" not in df.columns:
        raise ValueError(f"Arquivo de overrides de cliente inválido: {path}")

    return {
        row["carimbo_prefixo"].strip(): row["cliente"].strip()
        for _, row in df.iterrows()
        if row["carimbo_prefixo"].strip() and row["cliente"].strip()
    }


def apply_cliente_overrides(df, overrides):
    """Aplica overrides de cliente baseado em CARIMBO_PREFIXO."""
    if not overrides or "CARIMBO_PREFIXO" not in df.columns:
        return df

    df["CLIENTE"] = df.apply(
        lambda row: overrides.get(str(row["CARIMBO_PREFIXO"]).strip(), row.get("CLIENTE"))
        if pd.notna(row.get("CARIMBO_PREFIXO"))
        else row.get("CLIENTE"),
        axis=1
    )
    return df


def extrair_prefixo(idp):
    """
    Extrai o CARIMBO_PREFIXO de um IDP_PROJETO no formato canônico 'NNN/AA'.
    Este formato é o mesmo que o ETL de Backlog (etl_backlog_sgp.py) produz,
    garantindo que o JOIN entre d_Projetos e a base de Backlog funcione corretamente.

    Exemplos:
      '2024-597-01'  →  '597/24'   (IDP_PROJETO padrão SGP)
      '597/24'       →  '597/24'   (CARIMBO_PREFIXO já no formato correto)
      '597/24 - X'   →  '597/24'   (com texto adicional)
      '597'          →  None       (número solto sem ano — não é possível reconstruir)
    """
    if pd.isna(idp):
        return None

    texto = str(idp).strip()

    # Padrão IDP_PROJETO: '2024-597-01' → '597/24'
    match = re.search(r"(\d{4})-(\d+)-\d+", texto)
    if match:
        ano_2dig = match.group(1)[-2:]   # '2024' → '24'
        numero   = match.group(2)        # '597'
        return f"{numero}/{ano_2dig}"    # '597/24'

    # Padrão CARIMBO_PREFIXO já no formato correto: '597/24' ou '597/24 - Nome'
    match = re.search(r"\b(\d{1,4}/\d{2})\b", texto)
    if match:
        return match.group(1)

    return None


def limpar_texto(valor):
    if pd.isna(valor):
        return None

    texto = str(valor).strip()
    return texto if texto != "" else None


# ===============================
# CARREGAR BASES
# ===============================

df_controle = pd.read_excel(PATH_CONTROLE)
df_backlog = pd.read_excel(PATH_BACKLOG)
df_producao = pd.read_excel(PATH_PRODUCAO)
df_diario = pd.read_excel(PATH_DIARIO)

idp_overrides = load_idp_overrides(IDP_OVERRIDES_PATH)
if idp_overrides:
    df_controle = apply_idp_overrides(df_controle, idp_overrides)
    df_backlog = apply_idp_overrides(df_backlog, idp_overrides)
    df_producao = apply_idp_overrides(df_producao, idp_overrides)

# ===============================
# PADRONIZAR NOMES DE COLUNAS
# ===============================

for df in [df_controle, df_backlog, df_producao, df_diario]:
    df.columns = (
        df.columns
        .str.strip()
        .str.upper()
    )

print("Controle:", df_controle.columns)
print("Backlog:", df_backlog.columns)
print("Produção:", df_producao.columns)
print("Diário:", df_diario.columns)

# ===============================
# VALIDAR COLUNA CHAVE
# ===============================

COL_IDP = "IDP_PROJETO"

for nome_base, df in {
    "Controle": df_controle,
    "Backlog": df_backlog,
    "Produção": df_producao,
    "Diário": df_diario
}.items():
    if COL_IDP not in df.columns:
        raise KeyError(f"A coluna '{COL_IDP}' não foi encontrada na base {nome_base}.")

# ===============================
# SELECIONAR CAMPOS DISPONÍVEIS
# ===============================

# Controle
cols_controle = [c for c in ["IDP_PROJETO", "PROJETO", "CLIENTE", "CARIMBO_PREFIXO"] if c in df_controle.columns]
tmp_controle = df_controle[cols_controle].copy()

# Backlog
cols_backlog = [c for c in ["IDP_PROJETO", "CARIMBO_PREFIXO"] if c in df_backlog.columns]
tmp_backlog = df_backlog[cols_backlog].copy()

# Produção
cols_producao = [c for c in ["IDP_PROJETO", "CARIMBO_PREFIXO"] if c in df_producao.columns]
tmp_producao = df_producao[cols_producao].copy()

# Diário
cols_diario = [c for c in ["IDP_PROJETO", "PROJETO"] if c in df_diario.columns]
tmp_diario = df_diario[cols_diario].copy()

# ===============================
# GARANTIR ESTRUTURA PADRÃO
# ===============================

for df_tmp in [tmp_controle, tmp_backlog, tmp_producao, tmp_diario]:
    if "PROJETO" not in df_tmp.columns:
        df_tmp["PROJETO"] = None
    if "CLIENTE" not in df_tmp.columns:
        df_tmp["CLIENTE"] = None
    if "CARIMBO_PREFIXO" not in df_tmp.columns:
        df_tmp["CARIMBO_PREFIXO"] = None

    df_tmp["IDP_PROJETO"] = df_tmp["IDP_PROJETO"].apply(limpar_texto)
    df_tmp["PROJETO"] = df_tmp["PROJETO"].apply(limpar_texto)
    df_tmp["CLIENTE"] = df_tmp["CLIENTE"].apply(limpar_texto)
    df_tmp["CARIMBO_PREFIXO"] = df_tmp["CARIMBO_PREFIXO"].apply(limpar_texto)

# ===============================
# CONSOLIDAR BASES
# ===============================

projetos = pd.concat(
    [tmp_controle, tmp_backlog, tmp_producao, tmp_diario],
    ignore_index=True
)

# ===============================
# ENRIQUECER IDPs NULOS VIA CARIMBO_PREFIXO
# (usa carimbo_to_idp.csv gerado por mapear_prefixos_sem_idp.py)
# ===============================

SEP = "=" * 65

if CARIMBO_MAP_PATH.exists():
    print(f"\n{SEP}")
    print("ENRIQUECENDO IDPs NULOS VIA carimbo_to_idp.csv")
    print(SEP)

    df_cmap = pd.read_csv(CARIMBO_MAP_PATH, dtype=str).fillna("")
    df_cmap.columns = df_cmap.columns.str.strip().str.upper()

    df_cmap["CARIMBO_PREFIXO"] = df_cmap["CARIMBO_PREFIXO"].str.strip()
    df_cmap["IDP_PROJETO"]     = df_cmap["IDP_PROJETO"].str.strip()
    df_cmap = (
        df_cmap
        .query("CARIMBO_PREFIXO != '' and IDP_PROJETO != ''")
        .drop_duplicates("CARIMBO_PREFIXO")
    )

    cmap_idp     = df_cmap.set_index("CARIMBO_PREFIXO")["IDP_PROJETO"].to_dict()
    cmap_projeto = df_cmap.set_index("CARIMBO_PREFIXO")["PROJETO"].to_dict() if "PROJETO" in df_cmap.columns else {}
    cmap_cliente = df_cmap.set_index("CARIMBO_PREFIXO")["CLIENTE"].to_dict() if "CLIENTE" in df_cmap.columns else {}

    n_antes = projetos["IDP_PROJETO"].isna().sum()

    # Máscara: linhas sem IDP mas com CARIMBO_PREFIXO
    mask = projetos["IDP_PROJETO"].isna() & projetos["CARIMBO_PREFIXO"].notna()

    # Preenche IDP_PROJETO
    projetos.loc[mask, "IDP_PROJETO"] = (
        projetos.loc[mask, "CARIMBO_PREFIXO"].map(cmap_idp)
    )

    # Preenche PROJETO e CLIENTE (apenas onde ainda estão nulos)
    mask_sem_proj = mask & projetos["PROJETO"].isna()
    mask_sem_cli  = mask & projetos["CLIENTE"].isna()

    if cmap_projeto:
        projetos.loc[mask_sem_proj, "PROJETO"] = (
            projetos.loc[mask_sem_proj, "CARIMBO_PREFIXO"].map(cmap_projeto)
        )
    if cmap_cliente:
        projetos.loc[mask_sem_cli, "CLIENTE"] = (
            projetos.loc[mask_sem_cli, "CARIMBO_PREFIXO"].map(cmap_cliente)
        )

    n_depois     = projetos["IDP_PROJETO"].isna().sum()
    n_recuperado = n_antes - n_depois
    print(f"  Registros com IDP_PROJETO nulo (antes): {n_antes}")
    print(f"  Recuperados via mapping:                {n_recuperado}")
    print(f"  Ainda sem IDP após enriquecimento:      {n_depois}")
    print(f"  Mappings carregados:                    {len(cmap_idp)}")
    print(SEP)

else:
    print(f"\n[AVISO] {CARIMBO_MAP_PATH.name} não encontrado — enriquecimento ignorado.")
    print("  Rode antes:  python scripts\\mapear_prefixos_sem_idp.py\n")

projetos = projetos.dropna(subset=["IDP_PROJETO"]).copy()

# Se CARIMBO_PREFIXO vier vazio, tenta extrair do IDP
projetos["CARIMBO_PREFIXO"] = projetos.apply(
    lambda row: row["CARIMBO_PREFIXO"]
    if pd.notna(row["CARIMBO_PREFIXO"])
    else extrair_prefixo(row["IDP_PROJETO"]),
    axis=1
)

# ===============================
# CONSOLIDAR 1 LINHA POR IDP
# ===============================

def first_valid(series):
    valid = series.dropna()
    return valid.iloc[0] if not valid.empty else None


df_projetos = (
    projetos
    .groupby("IDP_PROJETO", as_index=False)
    .agg({
        "CARIMBO_PREFIXO": first_valid,
        "PROJETO": first_valid,
        "CLIENTE": first_valid
    })
)

# ===============================
# APLICAR OVERRIDES DE CLIENTE
# ===============================

cliente_overrides = load_cliente_overrides(CLIENTE_OVERRIDES_PATH)
if cliente_overrides:
    print(f"\nAplicando {len(cliente_overrides)} override(s) de cliente...")
    df_projetos = apply_cliente_overrides(df_projetos, cliente_overrides)

# ===============================
# CHAVE SURROGATE
# ===============================

df_projetos = df_projetos.sort_values(["IDP_PROJETO"]).reset_index(drop=True)
df_projetos["PROJ_SK"] = df_projetos.index + 1

# ===============================
# ORDENAR COLUNAS
# ===============================

df_projetos = df_projetos[
    [
        "PROJ_SK",
        "IDP_PROJETO",
        "CARIMBO_PREFIXO",
        "PROJETO",
        "CLIENTE"
    ]
]

# ===============================
# SALVAR
# ===============================

OUTPUT_PATH = OUTPUT  # já é Path (via config.py)
OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
QA_REPORT_DIR.mkdir(parents=True, exist_ok=True)

with pd.ExcelWriter(OUTPUT_PATH, engine="openpyxl") as writer:
    df_projetos.to_excel(writer, index=False)

# ===============================
# VALIDAÇÕES E REPORTES DE QA
# ===============================

# conflitos de IDP por prefixo
conflicts = (
    projetos[projetos["CARIMBO_PREFIXO"].notna()]
    .groupby("CARIMBO_PREFIXO")["IDP_PROJETO"]
    .nunique()
    .reset_index(name="unique_idp_count")
    .query("unique_idp_count > 1")
)

# registros sem prefixo (chave sem extrair)
missing_prefix = projetos[projetos["CARIMBO_PREFIXO"].isna()][["IDP_PROJETO", "PROJETO", "CLIENTE"]].drop_duplicates()

# backlog/produção não em controle
backlog_ids = set(tmp_backlog["IDP_PROJETO"].dropna().unique())
producao_ids = set(tmp_producao["IDP_PROJETO"].dropna().unique())
controle_ids = set(tmp_controle["IDP_PROJETO"].dropna().unique())

backlog_sem_controle = projetos[
    (projetos["IDP_PROJETO"].isin(backlog_ids - controle_ids)) & 
    (projetos["IDP_PROJETO"].notna())
][["IDP_PROJETO", "PROJETO", "CLIENTE", "CARIMBO_PREFIXO"]].drop_duplicates()

producao_sem_controle = projetos[
    (projetos["IDP_PROJETO"].isin(producao_ids - controle_ids)) & 
    (projetos["IDP_PROJETO"].notna())
][["IDP_PROJETO", "PROJETO", "CLIENTE", "CARIMBO_PREFIXO"]].drop_duplicates()

# registros sem nenhuma chave
sem_chave = projetos[
    (projetos["IDP_PROJETO"].isna() | (projetos["IDP_PROJETO"] == "")) &
    (projetos["CARIMBO_PREFIXO"].isna() | (projetos["CARIMBO_PREFIXO"] == ""))
][["PROJETO", "CLIENTE"]].drop_duplicates()

with pd.ExcelWriter(QA_REPORT_DIR / "qa_d_projetos.xlsx", engine="openpyxl") as writer:
    df_projetos.to_excel(writer, sheet_name="d_Projetos", index=False)
    conflicts.to_excel(writer, sheet_name="prefixo_conflicts", index=False)
    missing_prefix.to_excel(writer, sheet_name="missing_prefix", index=False)
    backlog_sem_controle.to_excel(writer, sheet_name="backlog_sem_controle", index=False)
    producao_sem_controle.to_excel(writer, sheet_name="producao_sem_controle", index=False)
    sem_chave.to_excel(writer, sheet_name="sem_chave", index=False)
    pd.DataFrame(
        list(idp_overrides.items()),
        columns=["idp_source", "idp_target"]
    ).to_excel(writer, sheet_name="idp_overrides", index=False)
    pd.DataFrame(
        list(cliente_overrides.items()),
        columns=["carimbo_prefixo", "cliente"]
    ).to_excel(writer, sheet_name="cliente_overrides", index=False)

print(f"\nValidações:")
print(f"- Conflitos de IDP por prefixo: {len(conflicts)}")
print(f"- Registros sem prefixo válido: {len(missing_prefix)}")
print(f"- Backlog sem Controle: {len(backlog_sem_controle)}")
print(f"- Produção sem Controle: {len(producao_sem_controle)}")
print(f"- Registros sem nenhuma chave: {len(sem_chave)}")

print("Dimensão d_Projetos criada com sucesso!")
print(f"Total de projetos: {len(df_projetos)}")
print(f"QA report salvo em: {QA_REPORT_DIR / 'qa_d_projetos.xlsx'}")
print(df_projetos.head())