# Jornal Diário

Esta pasta foi criada para armazenar arquivos de análise e gerar um jornal diário de informações.

## Estrutura

- `data/` - local para colocar arquivos de entrada (`.xlsx`, `.csv`, `.txt`, etc.).
- `jornal_diario.py` - script para ler os arquivos na pasta `data`, gerar um resumo e salvar um relatório diário.

## Como usar

1. Copie os arquivos que deseja analisar para `app_gcc_gov_v2/jornal_diario/data/`.
2. Execute o script:
   ```bash
   python app_gcc_gov_v2/jornal_diario/jornal_diario.py
   ```
3. O relatório será gerado em `app_gcc_gov_v2/jornal_diario/relatorio_diario.xlsx`.
4. Se os arquivos tiverem colunas de projeto (`IDP_PROJETO`, `PROJETO_CARIMBO`, `PROJETO_CARIMBO`, `PROJETO`, `CARIMBO_PREFIXO`), o relatório incluirá uma aba de resumo por projeto.

## Teste de IA local

Um script de teste local foi adicionado em `app_gcc_gov_v2/jornal_diario/test_ia_local.py`.

- Ele cria prompts a partir dos apontamentos do Diário de Bordo.
- Salva os prompts em `ia_prompts.csv`.
- Tenta gerar uma resposta usando `transformers` e o modelo `sshleifer/distilbart-cnn-12-6`.
- Salva o output em `ia_summary.txt`.

Para usar este teste, instale as dependências e execute:
```bash
python app_gcc_gov_v2/jornal_diario/test_ia_local.py
```

## Objetivos

- criar um ponto central de análise para arquivos do projeto
- gerar um resumo diário das entradas
- facilitar a visualização de métricas e pendências
