import pandas as pd
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from services.carregar_bases import carregar_producao, carregar_projetos, carregar_backlog
from services.backlog_analytics import normalizar_cliente, matriz_backlog_por_projeto

print("=" * 80)
print("DEBUG: PRODUÇÃO POR CLIENTE")
print("=" * 80)

# Carregar dados
df_producao = carregar_producao()
df_projetos = carregar_projetos()
df_backlog = carregar_backlog()

print(f"\n1. Produção carregada: {len(df_producao)} linhas")
if not df_producao.empty:
    print(f"   Colunas: {list(df_producao.columns)}")
    print(f"   Prefixos únicos: {df_producao['CARIMBO_PREFIXO'].nunique()}")
    print(f"   Total QTD_CIRCUITOS: {df_producao['QTD_CIRCUITOS'].sum()}")
    print(f"\n   Amostra produção:")
    print(df_producao[['CARIMBO_PREFIXO', 'QTD_CIRCUITOS']].head(10))

print(f"\n2. d_Projetos carregada: {len(df_projetos)} linhas")
if not df_projetos.empty:
    print(f"   Colunas: {list(df_projetos.columns)}")
    if 'CARIMBO_PREFIXO' in df_projetos.columns:
        print(f"   Prefixos únicos: {df_projetos['CARIMBO_PREFIXO'].nunique()}")
        print(f"   Clientes únicos: {df_projetos['CLIENTE'].nunique()}")
        print(f"   Clientes com valor: {df_projetos['CLIENTE'].notna().sum()}")
        print(f"\n   Amostra d_Projetos:")
        print(df_projetos[['CARIMBO_PREFIXO', 'CLIENTE']].head(10))

# Agregar produção por prefixo
print("\n3. Agregando produção por prefixo...")
df_prod = df_producao.copy()
df_prod["CARIMBO_PREFIXO"] = df_prod["CARIMBO_PREFIXO"].astype(str).str.strip()
df_prod = df_prod.groupby("CARIMBO_PREFIXO", as_index=False).agg(QTD_CIRCUITOS=("QTD_CIRCUITOS", "sum"))
print(f"   Prefixos únicos após agregação: {len(df_prod)}")
print(f"   Total circuitos: {df_prod['QTD_CIRCUITOS'].sum()}")

# Preparar dimensão de clientes
print("\n4. Preparando mapeamento prefixo → cliente...")
df_dim = df_projetos[["CARIMBO_PREFIXO", "CLIENTE"]].copy()
df_dim["CARIMBO_PREFIXO"] = df_dim["CARIMBO_PREFIXO"].astype(str).str.strip()
df_dim["CLIENTE_ORIGINAL"] = df_dim["CLIENTE"]
df_dim["CLIENTE"] = df_dim["CLIENTE"].fillna("").astype(str).apply(normalizar_cliente)
print(f"   Total linhas em d_Projetos: {len(df_dim)}")
print(f"   Clientes não vazios: {(df_dim['CLIENTE'] != '').sum()}")

df_dim_filtrado = df_dim[df_dim["CLIENTE"].astype(str).str.strip() != ""].drop_duplicates("CARIMBO_PREFIXO")
print(f"   Após filtrar vazios e duplicar: {len(df_dim_filtrado)}")

if not df_dim_filtrado.empty:
    print(f"\n   Amostra mapeamento:")
    print(df_dim_filtrado[['CARIMBO_PREFIXO', 'CLIENTE_ORIGINAL', 'CLIENTE']].head(10))

# Fazer merge
print("\n5. Fazendo merge produção + d_Projetos...")
df_prod_cliente = df_prod.merge(df_dim_filtrado[['CARIMBO_PREFIXO', 'CLIENTE']], on="CARIMBO_PREFIXO", how="left")
print(f"   Linhas após merge: {len(df_prod_cliente)}")
print(f"   Linhas com cliente: {df_prod_cliente['CLIENTE'].notna().sum()}")
print(f"   Linhas SEM cliente: {df_prod_cliente['CLIENTE'].isna().sum()}")

print(f"\n   Prefixos SEM match em d_Projetos:")
sem_match = df_prod_cliente[df_prod_cliente['CLIENTE'].isna() | (df_prod_cliente['CLIENTE'] == '')]
print(sem_match[['CARIMBO_PREFIXO', 'QTD_CIRCUITOS']].head(20))

# Filtrar apenas com cliente válido
df_prod_cliente = df_prod_cliente[df_prod_cliente["CLIENTE"].astype(str).str.strip() != ""].copy()
print(f"\n   Após filtrar vazios: {len(df_prod_cliente)} linhas")

# Agregar por cliente
print("\n6. Agregando por cliente...")
df_prod_final = (
    df_prod_cliente
    .groupby("CLIENTE", as_index=False)
    .agg(PRODUCAO_CIRCUITOS=("QTD_CIRCUITOS", "sum"))
)
print(f"   Clientes únicos: {len(df_prod_final)}")
print(f"   Total circuitos: {df_prod_final['PRODUCAO_CIRCUITOS'].sum()}")

print(f"\n   Top 15 clientes com produção:")
print(df_prod_final.sort_values('PRODUCAO_CIRCUITOS', ascending=False).head(15))

# Verificar matriz backlog
print("\n7. Verificando clientes na matriz backlog...")
from services.carregar_bases import carregar_controle
df_controle = carregar_controle()
df_matriz = matriz_backlog_por_projeto(df_backlog, df_controle, df_projetos)
df_matriz["CLIENTE"] = df_matriz["CLIENTE"].fillna("").astype(str).apply(normalizar_cliente)

print(f"   Clientes na matriz: {len(df_matriz)}")
print(f"   Clientes únicos: {df_matriz['CLIENTE'].nunique()}")

# Comparar clientes
clientes_matriz = set(df_matriz['CLIENTE'].unique())
clientes_producao = set(df_prod_final['CLIENTE'].unique())

print(f"\n8. Comparação de clientes:")
print(f"   Clientes apenas em backlog: {len(clientes_matriz - clientes_producao)}")
print(f"   Clientes apenas em produção: {len(clientes_producao - clientes_matriz)}")
print(f"   Clientes em ambos: {len(clientes_matriz & clientes_producao)}")

if len(clientes_producao - clientes_matriz) > 0:
    print(f"\n   Clientes APENAS em produção (serão adicionados):")
    for cli in sorted(list(clientes_producao - clientes_matriz))[:10]:
        qtd = df_prod_final[df_prod_final['CLIENTE'] == cli]['PRODUCAO_CIRCUITOS'].values[0]
        print(f"   - {cli}: {qtd} circuitos")

# Simular merge final
print("\n9. Simulando merge final (outer)...")
df_teste = df_matriz.merge(df_prod_final, on="CLIENTE", how="outer")
print(f"   Linhas após merge: {len(df_teste)}")
print(f"   Linhas com PRODUCAO_CIRCUITOS > 0: {(df_teste['PRODUCAO_CIRCUITOS'] > 0).sum()}")
print(f"   Total PRODUCAO_CIRCUITOS: {df_teste['PRODUCAO_CIRCUITOS'].sum()}")

print("\n" + "=" * 80)
print("FIM DEBUG")
print("=" * 80)
