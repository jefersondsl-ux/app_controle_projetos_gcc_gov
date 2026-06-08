# Sistema de Overrides - d_Projetos

Este diretório contém arquivos de mapeamento para corrigir informações no `d_Projetos.xlsx` que não podem ser capturadas automaticamente das bases de origem.

## Arquivos de Override

### 1. `idp_overrides.csv`
Corrige IDP_PROJETO duplicados ou inconsistentes.

**Formato:**
```csv
idp_source,idp_target
2024-597-01,2024-597-02
```

### 2. `cliente_overrides.csv`
Adiciona CLIENTE para prefixos que aparecem em Produção mas não têm cliente em d_Controle_Projetos.

**Formato:**
```csv
carimbo_prefixo,cliente
103/24,BANCO DO BRASIL
41/23,CAIXA ECONOMICA FEDERAL
```

## Como Usar

### Identificar prefixos sem cliente

Rode o app e verifique o terminal. Você verá mensagens como:

```
⚠️ DEBUG: 7 prefixos SEM cliente em d_Projetos:
   • 103/24: 2 circuitos
   • 41/23: 11 circuitos
```

### Adicionar overrides

1. Abra `cliente_overrides.csv`
2. Adicione uma linha para cada prefixo:
   ```csv
   103/24,BANCO DO BRASIL
   41/23,CAIXA ECONOMICA FEDERAL
   ```
3. Salve o arquivo

### Regenerar d_Projetos

Execute o script de build:

```powershell
cd "c:\Users\f282465\OneDrive - Claro SA\BASES\Projetos_GOV\app_gcc_gov_v3\scripts"
python build_d_projetos.py
```

### Limpar cache e recarregar

1. No Streamlit, pressione `C` e escolha "Clear cache"
2. Ou reinicie o app: `Ctrl+C` e `streamlit run app.py`
3. Recarregue a página (`R` ou `F5`)

## Validação

Após rodar o script, verifique o relatório de QA:

```
scripts/reports/qa_d_projetos.xlsx
```

Ele contém uma aba `cliente_overrides` mostrando todos os mapeamentos aplicados.

## Observações

- Os overrides são aplicados **depois** da consolidação automática
- Se um prefixo já tem cliente nas bases de origem, o override **sobrescreve**
- Mantenha os arquivos de override versionados no Git
- Use nomes de cliente **exatamente** como aparecem nas outras bases para garantir o merge correto
