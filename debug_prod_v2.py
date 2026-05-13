import pandas as pd
import os
import sys

# Add app directory to path
app_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, app_dir)

# Import após adicionar ao path
from services import carregar_bases as cb
from services import backlog_analytics as ba

print("=" * 80)
print("DEBUG: PRODUÇÃO POR CLIENTE - v2")
print("=" * 80)

# Carregar dados
try:
    df_producao = cb.carregar_producao()
    df_projetos = cb.carregar_projetos()
    df_backlog = cb.carregar_backlog()
    df_controle = cb.carregar_controle()
except Exception as e:
    print(f"ERRO ao carregar dados: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print(f"\n1. Produção: {len(df_producao)} linhas")
if not df_producao.empty:
    print(f"   Colunas: {list(df_producao.columns)[:5]}")
    print(f"   Total QTD_CIRCUITOS: {df_producao['QTD_CIRCUITOS'].sum() if 'QTD_CIRCUITOS' in df_producao.columns else 'N/A'}")

print(f"\n2. d_Projetos: {len(df_projetos)} linhas")
if not df_projetos.empty and 'CLIENTE' in df_projetos.columns:
    clientes_nao_vazios = df_projetos[df_projetos['CLIENTE'].notna() & (df_projetos['CLIENTE'] != '')]
    print(f"   Clientes preenchidos: {len(clientes_nao_vazios)}")

print(f"\n3. Backlog: {len(df_backlog)} linhas")

# Testar função de agregação
print("\n4. Testando agregação de produção...")

def agregar_producao_por_cliente(df_producao, df_projetos):
    if df_producao.empty or df_projetos is None:
        return pd.DataFrame(columns=["CLIENTE", "PRODUCAO_CIRCUITOS"])

    df_prod = df_producao.copy()
    df_prod["CARIMBO_PREFIXO"] = df_prod["CARIMBO_PREFIXO"].astype(str).str.strip()
    df_prod = df_prod.groupby("CARIMBO_PREFIXO", as_index=False).agg(QTD_CIRCUITOS=("QTD_CIRCUITOS", "sum"))
    
    print(f"   Produção agregada por prefixo: {len(df_prod)} prefixos")

    if "CARIMBO_PREFIXO" not in df_projetos.columns or "CLIENTE" not in df_projetos.columns:
        print("   ERRO: Colunas faltantes em d_Projetos")
        return pd.DataFrame(columns=["CLIENTE", "PRODUCAO_CIRCUITOS"])

    df_dim = df_projetos[["CARIMBO_PREFIXO", "CLIENTE"]].copy()
    df_dim["CARIMBO_PREFIXO"] = df_dim["CARIMBO_PREFIXO"].astype(str).str.strip()
    df_dim["CLIENTE"] = df_dim["CLIENTE"].fillna("").astype(str).apply(ba.normalizar_cliente)
    df_dim = df_dim[df_dim["CLIENTE"].astype(str).str.strip() != ""].drop_duplicates("CARIMBO_PREFIXO")

    print(f"   d_Projetos com cliente válido: {len(df_dim)} prefixos")

    if df_dim.empty:
        print("   ERRO: Nenhum cliente válido em d_Projetos")
        return pd.DataFrame(columns=["CLIENTE", "PRODUCAO_CIRCUITOS"])

    df_prod = df_prod.merge(df_dim, on="CARIMBO_PREFIXO", how="left")
    matches = df_prod['CLIENTE'].notna().sum()
    print(f"   Merge resultado: {matches} matches de {len(df_prod)}")
    
    df_prod["CLIENTE"] = df_prod["CLIENTE"].fillna("").astype(str).apply(ba.normalizar_cliente)
    df_prod = df_prod[df_prod["CLIENTE"].astype(str).str.strip() != ""].copy()

    if df_prod.empty:
        print("   AVISO: Nenhum prefixo de produção casou com cliente em d_Projetos")
        return pd.DataFrame(columns=["CLIENTE", "PRODUCAO_CIRCUITOS"])

    result = (
        df_prod
        .groupby("CLIENTE", as_index=False)
        .agg(PRODUCAO_CIRCUITOS=("QTD_CIRCUITOS", "sum"))
    )
    
    print(f"   Resultado final: {len(result)} clientes com produção")
    print(f"   Total circuitos: {result['PRODUCAO_CIRCUITOS'].sum()}")
    
    return result

df_prod_cliente = agregar_producao_por_cliente(df_producao, df_projetos)

if not df_prod_cliente.empty:
    print(f"\n5. TOP 10 clientes com produção:")
    top10 = df_prod_cliente.sort_values('PRODUCAO_CIRCUITOS', ascending=False).head(10)
    for idx, row in top10.iterrows():
        print(f"   {row['CLIENTE']}: {int(row['PRODUCAO_CIRCUITOS'])} circuitos")
else:
    print("\n5. ERRO: Nenhuma produção por cliente gerada!")

print("\n" + "=" * 80)
