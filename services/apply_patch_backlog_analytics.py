from pathlib import Path

path = Path(__file__).parent / 'backlog_analytics.py'
text = path.read_text(encoding='utf-8')
normalized = text.replace('\r\n', '\n')

old1 = '''    # =========================
    # FLAGS DE TEMPO

    df["FLAG_BACKLOG_ATUAL"] = df["FAIXA_BACKLOG"] == "BACKLOG_ATUAL"
    df["FLAG_MAI"] = df["FAIXA_BACKLOG"] == "FORECAST_MAI_2026"
    df["FLAG_JUN"] = df["FAIXA_BACKLOG"] == "FORECAST_JUN_2026"
    df["FLAG_RESTANTE"] = df["FAIXA_BACKLOG"] == "MESES_RESTANTES"
    df["FLAG_AJUSTAR"] = df["FAIXA_BACKLOG"] == "FORECAST_AJUSTAR"
    df["FLAG_DEFINIR"] = df["FAIXA_BACKLOG"] == "FORECAST_A_DEFINIR"
'''
new1 = '''    # =========================
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

    df["FLAG_BACKLOG_ATUAL"] = df["FAIXA_BACKLOG"] == "BACKLOG_ATUAL"
    df["FLAG_NEXT1"] = df["FAIXA_BACKLOG"] == next1_label
    df["FLAG_NEXT2"] = df["FAIXA_BACKLOG"] == next2_label
    df["FLAG_RESTANTE"] = df["FAIXA_BACKLOG"] == "MESES_RESTANTES"
    df["FLAG_AJUSTAR"] = df["FAIXA_BACKLOG"] == "FORECAST_AJUSTAR"
    df["FLAG_DEFINIR"] = df["FAIXA_BACKLOG"] == "FORECAST_A_DEFINIR"
'''

old2 = '''    df["FLAG_BACKLOG_ATUAL_EST"] = df["FLAG_BACKLOG_ATUAL"] & df["FLAG_ESTRATEGIA"]
    df["FLAG_MAI_EST"] = df["FLAG_MAI"] & df["FLAG_ESTRATEGIA"]
    df["FLAG_JUN_EST"] = df["FLAG_JUN"] & df["FLAG_ESTRATEGIA"]
    df["FLAG_RESTANTE_EST"] = df["FLAG_RESTANTE"] & df["FLAG_ESTRATEGIA"]
    df["FLAG_AJUSTAR_EST"] = df["FLAG_AJUSTAR"] & df["FLAG_ESTRATEGIA"]
    df["FLAG_DEFINIR_EST"] = df["FLAG_DEFINIR"] & df["FLAG_ESTRATEGIA"]
'''
new2 = '''    df["FLAG_BACKLOG_ATUAL_EST"] = df["FLAG_BACKLOG_ATUAL"] & df["FLAG_ESTRATEGIA"]
    df["FLAG_NEXT1_EST"] = df["FLAG_NEXT1"] & df["FLAG_ESTRATEGIA"]
    df["FLAG_NEXT2_EST"] = df["FLAG_NEXT2"] & df["FLAG_ESTRATEGIA"]
    df["FLAG_RESTANTE_EST"] = df["FLAG_RESTANTE"] & df["FLAG_ESTRATEGIA"]
    df["FLAG_AJUSTAR_EST"] = df["FLAG_AJUSTAR"] & df["FLAG_ESTRATEGIA"]
    df["FLAG_DEFINIR_EST"] = df["FLAG_DEFINIR"] & df["FLAG_ESTRATEGIA"]
'''

old3 = '''    # =========================
    # FLAGS DE FORECAST

    df["FLAG_BACKLOG_ATUAL"] = df["FAIXA_BACKLOG"] == "BACKLOG_ATUAL"
    df["FLAG_MAI"] = df["FAIXA_BACKLOG"] == "FORECAST_MAI_2026"
    df["FLAG_JUN"] = df["FAIXA_BACKLOG"] == "FORECAST_JUN_2026"
    df["FLAG_RESTANTE"] = df["FAIXA_BACKLOG"] == "MESES_RESTANTES"
    df["FLAG_AJUSTAR"] = df["FAIXA_BACKLOG"] == "FORECAST_AJUSTAR"
    df["FLAG_DEFINIR"] = df["FAIXA_BACKLOG"] == "FORECAST_A_DEFINIR"

    # ========================= 
    # DELTA RECEITA ESTRATÉGIA
'''
new3 = '''    # =========================
    # FLAGS DE FORECAST

    # Already defined above with dynamic labels for next months.

    # ========================= 
    # DELTA RECEITA ESTRATÉGIA
'''

old4 = '''            FORECAST_MAI_2026=("FLAG_MAI_EST", "sum"),
            FORECAST_JUN_2026=("FLAG_JUN_EST", "sum"),
'''
new4 = '''            next1_label=("FLAG_NEXT1_EST", "sum"),
            next2_label=("FLAG_NEXT2_EST", "sum"),
'''

for i, (old, new) in enumerate([(old1, new1), (old2, new2), (old3, new3), (old4, new4)], start=1):
    if old not in normalized:
        raise ValueError(f'old block {i} not found')
    normalized = normalized.replace(old, new, 1)

path.write_text(normalized.replace('\n', '\r\n'), encoding='utf-8')
print('patch applied')
