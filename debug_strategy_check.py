import os
import sys
sys.path.insert(0, os.getcwd())
import pandas as pd
from services.carregar_bases import carregar_backlog
from services.backlog_analytics import resumo_estrategia, matriz_backlog_por_projeto

# Load backlog from app data path
print('Working dir:', os.getcwd())
df_backlog = carregar_backlog()
print('Backlog rows:', len(df_backlog))

resumo = resumo_estrategia(df_backlog)
print('resumo_estrategia total:', resumo['total'])
print('resumo_estrategia internet:', resumo['internet'], 'dados:', resumo['dados'], 'perc:', resumo['perc'])

df_matriz = matriz_backlog_por_projeto(df_backlog, None)
print('matriz rows:', len(df_matriz))
print('matriz total strategy across clients:', df_matriz['ESTRATEGIA'].sum() if 'ESTRATEGIA' in df_matriz.columns else 'n/a')
print('matriz positive strategy clients:', (df_matriz['ESTRATEGIA'] > 0).sum() if 'ESTRATEGIA' in df_matriz.columns else 'n/a')
print('columns:', df_matriz.columns.tolist())
print(df_matriz[['CLIENTE','ESTRATEGIA']].sort_values('ESTRATEGIA', ascending=False).head(20).to_string(index=False))
