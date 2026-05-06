import pandas as pd
from pathlib import Path
import datetime

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data"
REPORT_PATH = ROOT / "relatorio_diario.xlsx"

SUPPORTED_EXTENSIONS = [".csv", ".xlsx", ".xls"]
PROJECT_COLUMNS = ["IDP_PROJETO", "PROJETO_CARIMBO", "CARIMBO_PROJETO", "PROJETO", "CARIMBO_PREFIXO"]


def carregar_arquivo(path: Path) -> pd.DataFrame:
    ext = path.suffix.lower()
    if ext == ".csv":
        return pd.read_csv(path, dtype=str)
    if ext in [".xlsx", ".xls"]:
        return pd.read_excel(path, dtype=str)
    raise ValueError(f"Extensão não suportada: {ext}")


def resumir_dataframe(df: pd.DataFrame, nome_arquivo: str) -> dict:
    resumo = {
        "arquivo": nome_arquivo,
        "linhas": len(df),
        "colunas": len(df.columns),
        "colunas_list": ", ".join(df.columns.astype(str).tolist()),
        "colunas_nulas": int(df.isna().sum().sum()),
        "valores_unicos": int(sum(df.nunique(dropna=True))),
    }
    return resumo


def coluna_projeto(df: pd.DataFrame) -> str | None:
    for col in PROJECT_COLUMNS:
        if col in df.columns:
            return col
    return None


def resumo_por_projeto(df: pd.DataFrame, arquivo: str) -> pd.DataFrame:
    projeto_col = coluna_projeto(df)
    if projeto_col is None:
        return pd.DataFrame()

    df_projeto = df.copy()
    df_projeto[projeto_col] = df_projeto[projeto_col].astype(str).str.strip()
    linhas = df_projeto.groupby(projeto_col).size().rename("linhas")
    nulos = (
        df_projeto.assign(_nulos=df_projeto.isna().sum(axis=1))
        .groupby(projeto_col)["_nulos"]
        .sum()
        .rename("nulos")
    )

    resumo = pd.concat([linhas, nulos], axis=1).reset_index()
    resumo = resumo.rename(columns={projeto_col: "projeto"})
    resumo["arquivo"] = arquivo
    resumo["chave_projeto"] = projeto_col
    resumo["colunas"] = len(df.columns)
    return resumo[["arquivo", "chave_projeto", "projeto", "linhas", "colunas", "nulos"]]


def main():
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    arquivos = [p for p in DATA_DIR.iterdir() if p.suffix.lower() in SUPPORTED_EXTENSIONS]

    if not arquivos:
        print("Nenhum arquivo de entrada encontrado em:", DATA_DIR)
        return

    relatorios = []
    projetos = []

    for arquivo in arquivos:
        print(f"Processando: {arquivo.name}")
        try:
            df = carregar_arquivo(arquivo)
            relatorios.append(resumir_dataframe(df, arquivo.name))

            resumo_proj = resumo_por_projeto(df, arquivo.name)
            if not resumo_proj.empty:
                projetos.append(resumo_proj)
        except Exception as e:
            print(f"Erro ao carregar {arquivo.name}: {e}")

    resumo_df = pd.DataFrame(relatorios)
    resumo_df["data_execucao"] = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with pd.ExcelWriter(REPORT_PATH, engine="openpyxl") as writer:
        resumo_df.to_excel(writer, sheet_name="resumo_arquivos", index=False)

        if projetos:
            resumo_projetos_df = pd.concat(projetos, ignore_index=True)
            resumo_projetos_df.to_excel(writer, sheet_name="resumo_por_projeto", index=False)

    print("Relatório diário gerado em:", REPORT_PATH)


if __name__ == "__main__":
    main()
