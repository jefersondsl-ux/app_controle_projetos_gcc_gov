import openpyxl, os
from openpyxl.utils import get_column_letter
import pandas as pd
path = r'C:/Users/Z181040/OneDrive - Claro Sa/BASES/Projetos_GOV/app_gcc_gov_v3/meta_copy.xlsx'
meta = pd.read_excel(path)
meta.columns = meta.columns.str.strip().str.upper()
meta['CLIENTE'] = meta['CLIENTE'].astype(str).str.strip()
meta['CLASSIFICACAO'] = meta['CLASSIFICACAO'].astype(str).str.upper().str.strip()
meta['PRODUTO_AJUSTADO'] = meta['PRODUTO_AJUSTADO'].astype(str).str.strip().str.upper()
meta['PRODUTO_AJUSTADO'] = meta['PRODUTO_AJUSTADO'].replace({'WI-FI': 'WIFI'})
mask = (meta['CLASSIFICACAO'] == 'GROSS') & (meta['PRODUTO_AJUSTADO'].isin(['INTERNET','DADOS']))
meta_filtered = meta[mask].copy()
print('meta rows', len(meta))
print('meta strategy rows', len(meta_filtered))
print('unique meta clients', meta_filtered['CLIENTE'].nunique())
print('meta client top counts')
print(meta_filtered.groupby('CLIENTE', as_index=False).agg(COUNT=('COD_CIR','count')).sort_values('COUNT', ascending=False).head(20).to_string(index=False))

backlog_path = r'C:/Users/Z181040/OneDrive - Claro Sa/BASES/Projetos_GOV/Base_Dados_SGP/Bases_Processadas_Python/BD_Backlog_SGP.xlsx'
backlog = pd.read_excel(backlog_path)
backlog.columns = backlog.columns.str.strip().str.upper()
backlog['CLIENTE'] = backlog['CLIENTE'].astype(str).str.strip()
meta_clients = set(meta_filtered['CLIENTE'])
backlog_clients = set(backlog['CLIENTE'])
missing = sorted([c for c in meta_clients if c not in backlog_clients])
print('missing clients in backlog', len(missing))
print(missing[:20])
if missing:
    missing_sum = meta_filtered[meta_filtered['CLIENTE'].isin(missing)]['COD_CIR'].count()
    print('missing sum in meta_filtered', missing_sum)

# check for clients in backlog but not in meta filtered
extra = sorted([c for c in backlog_clients if c not in meta_clients])
print('backlog clients not in meta', len(extra))
print(extra[:20])
