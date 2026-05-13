import pandas as pd
from services.carregar_bases import PATH_PRODUCAO_ANALITICO, PATH_PROJETOS
print('PATH_PRODUCAO_ANALITICO', PATH_PRODUCAO_ANALITICO)
print('PATH_PROJETOS', PATH_PROJETOS)

df_prod = pd.read_excel(PATH_PRODUCAO_ANALITICO)
print('prod cols', df_prod.columns.tolist()[:50])
print('prod shape', df_prod.shape)
print(df_prod.head(5).to_dict('records'))

df_proj = pd.read_excel(PATH_PROJETOS)
print('proj cols', df_proj.columns.tolist()[:50])
print('proj shape', df_proj.shape)
print(df_proj.head(5).to_dict('records'))
