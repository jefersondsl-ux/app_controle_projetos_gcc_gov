# Pipeline de Integração SGP / d_Projetos

## Objetivo

Construir um fluxo confiável e automatizado que garanta a atualização diária do `d_Projetos` e a conexão 100% entre as bases:
- Controle de Projetos
- Backlog
- Produção
- Diário de Bordo

## Visão geral do fluxo

1. baixar arquivos brutos do sistema SGP (Embratel):
   - `Backlog_SGP.xlsx`
   - `Produção_SGP.xlsx`
   - `Controle_Projetos.xlsx`
   - `f_Diario_Bordo.xlsx`

2. rodar ETL de Backlog
   - script: `ETL_Backlog_SGP/etl_backlog_sgp.py`
   - saída: `BD_Backlog_SGP.xlsx`
   - objetivo: limpar colunas, normalizar `CARIMBO_PROJETO`, extrair `CARIMBO_PREFIXO`, validar chave

3. rodar ETL de Produção
   - script: `ETL_Producao_SGP/etl_producao_sgp.py`
   - saída: `BD_Produção_Analitica.xlsx`
   - objetivo: consolidar produção por `CARIMBO_PREFIXO`, extrair `IDP_PROJETO` e manter métricas analíticas

4. rodar construção da dimensão
   - script: `app_gcc_gov_v2/scripts/build_d_projetos.py`
   - saída: `d_Projetos.xlsx`, `BD_Projetos.xlsx`
   - objetivo: gerar a dimensão mestra de projeto a partir das bases processadas e do controle

5. rodar auditoria de integridade
   - script: `auditoria_integridade_projetos.py`
   - objetivo: detectar gaps entre Backlog, Controle e Diário usando chaves compostas

6. carregar o app
   - `app_gcc_gov_v2` carrega:
     - `d_Projetos.xlsx`
     - `BD_Backlog_SGP.xlsx`
     - `BD_Produção_Analitica.xlsx`
     - `d_Controle_Projetos.xlsx`
     - Diário e apontamentos
   - objetivo: usar `d_Projetos` como lookup mestre e evitar dependência apenas de `IDP_PROJETO`

## Modelo de chave recomendado

### Chaves primárias
- `IDP_PROJETO` — chave principal de projeto
- `CARIMBO_PREFIXO` — fallback de projeto quando `IDP_PROJETO` estiver ausente ou inconsistente
- `CLIENTE_CANON` — contexto para distinguir prefixos iguais
- `PROJ_SK` — chave definitiva da dimensão gerada automaticamente

### Regras de reconciliação
- se `IDP_PROJETO` existe e é consistente, usar diretamente
- se `IDP_PROJETO` está ausente, usar `CARIMBO_PREFIXO + CLIENTE_CANON`
- se `IDP_PROJETO` está em formato diferente, aplicar normalização e overrides
- registrar todos os casos sem correspondência para revisão manual

## Proposta de automação

Criar um script mestre: `app_gcc_gov_v2/scripts/run_pipeline.py`

### Responsabilidades do script
- executar os ETLs em sequência
- gerar artefatos processados
- executar validações de qualidade
- reportar falhas e gaps

### Componentes adicionais
- arquivo de mapeamento de exceções, ex:
  - `mappings/idp_overrides.csv`
  - `mappings/cd_projeto_normalizacao.csv`
- logs de qualidade:
  - `reports/qa_backlog.xlsx`
  - `reports/qa_producao.xlsx`
  - `reports/qa_d_projetos.xlsx`

## Pontos de melhoria imediatos

1. transformar `d_Projetos` em dimensão gerada automaticamente
2. centralizar caminhos e constantes em um único módulo de configuração
3. evitar hardcode de casos específicos no app de consumo (`carregar_bases.py`)
4. criar controle de qualidade de chaves:
   - cobertura de `CARIMBO_PREFIXO`
   - cobertura de `IDP_PROJETO`
   - divergência de `IDP_PROJETO` por mesmo prefixo
   - casos sem correspondência no `d_Projetos`

## Regras de operação diária

1. baixar e salvar os arquivos brutos no OneDrive
2. rodar `python app_gcc_gov_v2/scripts/run_pipeline.py`
3. revisar se há falhas ou gaps reportados
4. abrir o app e validar os dados consolidados

## Diagrama do fluxo

- `SGP raw files` → ETL Backlog → `BD_Backlog_SGP.xlsx`
- `SGP raw files` → ETL Produção → `BD_Produção_Analitica.xlsx`
- `Controle` + `Backlog processado` + `Produção processada` + `Diário` → `build_d_projetos.py` → `d_Projetos.xlsx`
- `d_Projetos.xlsx` + bases processadas → app

## Notas importantes

- `d_Projetos` deve ser gerado por script, não ajustado manualmente todo mês.
- o app deve usar `d_Projetos` como fonte de verdade para projetos.
- a reconciliação deve ser feita o mais cedo possível no processo: idealmente no ETL, antes de alimentar o app.
