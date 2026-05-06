import sys
from pathlib import Path
import pandas as pd

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.carregar_bases import carregar_diario

OUTPUT_PROMPTS = ROOT / "ia_prompts.csv"
OUTPUT_SUMMARY = ROOT / "ia_summary.txt"

MODEL_NAME = "sshleifer/distilbart-cnn-12-6"


def carregar_apontamentos():
    df_diario = carregar_diario()
    if df_diario.empty:
        raise RuntimeError("Base Diário de Bordo não carregou")

    cols_necessarias = ["IDP_PROJETO", "PROJETO", "PROJETO_CARIMBO", "STATUS_MACRO", "APONTAMENTO", "OBJETOS"]
    for col in cols_necessarias:
        if col not in df_diario.columns:
            df_diario[col] = None

    return df_diario


def montar_prompt(linha: pd.Series) -> str:
    projeto = str(linha.get("PROJETO_CARIMBO") or linha.get("PROJETO") or "Projeto").strip()
    idp = str(linha.get("IDP_PROJETO") or "Não informado").strip()
    status_macro = str(linha.get("STATUS_MACRO") or "Não informado").strip()
    objetos = str(linha.get("OBJETOS") or "").strip()
    apontamento = str(linha.get("APONTAMENTO") or "").strip()

    prompt = (
        f"Projeto: {projeto}\n"
        f"IDP: {idp}\n"
        f"Status Macro: {status_macro}\n"
        f"Objetos: {objetos if objetos else 'Não informado'}\n"
        f"Apontamentos: {apontamento if apontamento else 'Sem apontamentos'}\n\n"
        "Com base nestas informações, responda em formato de resumo executivo:\n"
        "1) Resumo do andamento em uma frase.\n"
        "2) Principais riscos ou pendências em uma frase.\n"
        "3) Uma mensagem curta sobre o status.\n"
        "Use linguagem objetiva e concisa."
    )
    return prompt


def montar_prompts_por_projeto(df: pd.DataFrame) -> pd.DataFrame:
    df = df.copy()
    df["PROJETO_BASE"] = df["PROJETO_CARIMBO"].fillna(df["PROJETO"]).fillna("Projeto").astype(str).str.strip()
    df["APONTAMENTO"] = df["APONTAMENTO"].astype(str).fillna("")
    df = df.sort_values(["PROJETO_BASE", "IDP_PROJETO"])
    df_grouped = (
        df.groupby(["PROJETO_BASE", "IDP_PROJETO", "STATUS_MACRO", "OBJETOS"], dropna=False)["APONTAMENTO"]
        .apply(lambda x: " \n ".join(x.tolist()))
        .reset_index()
    )
    df_grouped["prompt"] = df_grouped.apply(montar_prompt, axis=1)
    return df_grouped[["PROJETO_BASE", "IDP_PROJETO", "prompt"]]


def carregar_summarizer():
    try:
        from transformers import pipeline
    except ModuleNotFoundError:
        print("Dependência ausente: instale 'transformers' para gerar resumos locais.")
        print("Exemplo: pip install transformers")
        return None

    try:
        summarizer = pipeline("summarization", model=MODEL_NAME)
        return summarizer
    except Exception as exc:
        print("Não foi possível inicializar o summarizer local:", exc)
        return None


def gerar_resposta(summarizer, prompt: str) -> str:
    if summarizer is None:
        return "[Resumo não gerado - summarizer indisponível]"

    try:
        resultado = summarizer(prompt, max_length=120, min_length=40, do_sample=False)
        return resultado[0]["summary_text"].strip()
    except Exception as exc:
        return f"[Erro na inferência local: {exc}]"


def main():
    df_diario = carregar_apontamentos()
    df_prompts = montar_prompts_por_projeto(df_diario)

    df_prompts.to_csv(OUTPUT_PROMPTS, index=False, encoding="utf-8-sig")
    print(f"Prompts gerados em: {OUTPUT_PROMPTS}")

    summarizer = carregar_summarizer()
    if summarizer is None:
        print("A geração de resumos será ignorada. Instale 'transformers' para usar o summarizador local.")

    with open(OUTPUT_SUMMARY, "w", encoding="utf-8") as f:
        for _, row in df_prompts.iterrows():
            resumo = gerar_resposta(summarizer, row["prompt"])
            f.write(f"=== Projeto: {row['PROJETO_BASE']} | IDP: {row['IDP_PROJETO']} ===\n")
            f.write(resumo + "\n\n")

    print(f"Resumo gerado em: {OUTPUT_SUMMARY}")


if __name__ == "__main__":
    main()
