import sys
from pathlib import Path
import pandas as pd
import datetime

ROOT = Path(__file__).resolve().parent
PROJECT_ROOT = ROOT.parent
sys.path.insert(0, str(PROJECT_ROOT))

from services.carregar_bases import (
    carregar_controle,
    carregar_backlog,
    carregar_producao,
    carregar_diario,
    carregar_projetos
)
from services.construir_tabela_analitica import construir_tabela_analitica

OUTPUT_PATH = ROOT / "resumo_projetos.txt"


def normalizar_texto(valor):
    if pd.isna(valor):
        return "Não informado"
    texto = str(valor).strip()
    return texto if texto else "Não informado"


def formatar_moeda(valor):
    try:
        if pd.isna(valor):
            return "Não informado"
        v = float(str(valor).replace("R$", "").replace(".", "").replace(",", "."))
        return f"R$ {v:,.2f}".replace(",", "#").replace(".", ",").replace("#", ".")
    except Exception:
        return "Não informado"


def comentario_status(df_linha):
    status = normalizar_texto(df_linha.get("STATUS MACRO") or df_linha.get("STATUS_MACRO"))
    status_text = f"Status: {status}" if status != "Não informado" else "Status: Não informado"

    produzidos = int(df_linha.get("Circuitos_Producao") or 0)
    backlog = int(df_linha.get("QTD TOTAL") or df_linha.get("BACKLOG_TOTAL") or 0)
    total = int(df_linha.get("Total_Circuitos") or 0)

    passos = []
    if backlog > 0 and produzidos == 0:
        passos.append("Rollout não iniciado")
    elif backlog > 0 and produzidos > 0:
        passos.append("Rollout em andamento")
    elif backlog == 0 and produzidos > 0:
        passos.append("Rollout concluído")

    obj = str(df_linha.get("OBJETOS") or "").strip().lower()
    if "upgrade" in obj and "Upgrade" not in passos:
        passos.append("Upgrade pendente")
    if "cpe" in obj and "CPE" not in passos:
        passos.append("Troca de CPE pendente")

    observacoes = []
    if resumo := df_linha.get("backlog_observacao"):
        observacoes.append(str(resumo).strip())

    if passos:
        observacoes.extend(passos)

    if not observacoes:
        return status_text

    return f"{status_text} • {' • '.join(observacoes)}"


def montar_resumo(df_proj, arquivo="planilha_analitica"):
    linhas = []
    for _, row in df_proj.iterrows():
        nome = normalizar_texto(row.get("PROJETO_CARIMBO") or row.get("PROJETO") or "Projeto")
        dv = normalizar_texto(row.get("DV"))
        titulo = f"🏛️ {nome} - {dv}" if dv != "Não informado" else f"🏛️ {nome}"

        objeto = normalizar_texto(row.get("OBJETOS"))
        resumo_objeto = objeto if objeto != "Não informado" else "Objeto não informado"

        idp = normalizar_texto(row.get("IDP_PROJETO") or row.get("IDP"))
        valor_total = formatar_moeda(row.get("VALOR CONTRATO"))
        valor_mensal = formatar_moeda(row.get("RECEITA MENSAL CONTRATUAL"))
        gcc = normalizar_texto(row.get("GCC"))
        gp = normalizar_texto(row.get("GP") or row.get("PJE"))
        assinatura = normalizar_texto(row.get("DATA ASSINATURA CONTRATO") or row.get("DATA_ASSINATURA"))

        dados_principais = (
            f"📘 RESUMO DO PROJETO • {resumo_objeto}. • IDP: {idp} | Valor Total: {valor_total} | Mensal: {valor_mensal} • GCC: {gcc} | GP: {gp} | Assinatura: {assinatura}"
        )

        placa = (
            f"📊 PLACAR • Produzidos: {int(row.get('Circuitos_Producao') or 0)} | Backlog: {int(row.get('QTD TOTAL') or row.get('BACKLOG_TOTAL') or 0)} | Internalizados/Cadastrados: {int(row.get('Total_Circuitos') or 0)}"
        )

        pendencias = comentario_status(row)

        linha = f"{titulo}\n{dados_principais}\n⚠️ PRINCIPAIS PENDÊNCIAS • {pendencias}\n{placa}"
        linhas.append(linha)

    return linhas


def main():
    df_controle = carregar_controle()
    df_backlog = carregar_backlog()
    df_producao = carregar_producao()
    df_diario = carregar_diario()
    df_projetos = carregar_projetos()

    df_analitico = construir_tabela_analitica(
        df_projetos,
        df_controle,
        df_backlog,
        df_producao,
        df_diario
    )

    # renomeia para o padrão da planilha inteligente
    df_analitico = df_analitico.rename(columns={
        "BACKLOG_TOTAL": "QTD TOTAL"
    })

    # garantir colunas necessárias
    cols = [
        "PROJETO_CARIMBO",
        "DV",
        "OBJETOS",
        "IDP_PROJETO",
        "VALOR CONTRATO",
        "RECEITA MENSAL CONTRATUAL",
        "GCC",
        "GP",
        "STATUS MACRO",
        "DATA ASSINATURA CONTRATO",
        "Circuitos_Producao",
        "QTD TOTAL",
        "Total_Circuitos"
    ]
    for col in cols:
        if col not in df_analitico.columns:
            df_analitico[col] = None

    textos = montar_resumo(df_analitico, arquivo="planilha_analitica")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n\n".join(textos))

    print(f"Resumos gerados em: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
