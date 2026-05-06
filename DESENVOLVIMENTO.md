# 📋 DESENVOLVIMENTO - App GCC GOV v2

## 🎯 Visão Geral do Projeto
Sistema "Diário de Bordo" - aplicação analítica em Python/Streamlit para controle de projetos de implantação de circuitos de internet (Claro/Embratel).

**Objetivos principais**:
- ✅ Monitorar backlog de circuitos
- 🔄 Monitorar produção de circuitos
- 📋 Registrar evolução dos projetos (Diário de Bordo)
- 🎯 Centralizar apontamentos operacionais
- 📊 Crear alertas e auditorias de dados
- 📈 Apoiar análise operacional e gerencial

**Stack**: Python, Pandas, Numpy, Streamlit, Excel, SharePoint
**Integrações futuras**: Power BI, n8n, IA Analítica
**Status**: Em produção 🚀

---

## 🏗️ Arquitetura do Projeto

### Estrutura de Pastas
```
app_gcc_gov_v2/
├── app.py                          # Main - orquestra navegação + carrega bases
├── components/
│   ├── cards.py                    # render_card() - HTML customizado com cores
│   └── sidebar.py                  # render_sidebar() - navegação radio button
├── layout/
│   └── header.py                   # render_header() - exibe KPIs em cards
├── pages/
│   ├── backlog_visao_geral.py      # 📊 Matriz analítica + drill-down
│   ├── auditoria_bases.py          # 🔍 Auditoria das bases
│   ├── planilha_inteligente.py     # 📋 Planilha inteligente
│   ├── visao_gerencial.py          # 👔 Visão gerencial
│   └── visao_operacional.py        # ⚙️ Visão operacional
├── services/
│   ├── carregar_bases.py           # 🔄 Loaders com @st.cache_data
│   ├── backlog_analytics.py        # 📊 Lógica: resumo_backlog() e matriz_backlog_por_projeto()
│   ├── calculos_kpi.py             # 📈 Cálculos de KPIs
│   ├── construir_tabela_analitica.py # 🏗️ Tabela analítica
│   └── ...
└── scripts/
    └── build_d_projetos.py         # 🔧 Scripts de construção
```

---

## 📝 Histórico de Mudanças

### ✅ Fix: DELTA_RECEITA não somava na linha TOTAL GERAL (10/04/2026)
**Problema**: Colunas DELTA_RECEITA_GERAL e DELTA_RECEITA_ESTRATEGIA eram formatadas para "R$ X Mi" ANTES de calcular os totais. Quando o código tentava fazer `.sum()`, recebia strings em vez de números.

**Solução**:
1. Removido bloco de formatação logo após carregar `df_matriz`
2. Movido formatação para DEPOIS de calcular totais e concatenar linha_total
3. Adicionado DELTA_RECEITA_GERAL nas `colunas_backlog` (header marrom/laranja)
4. Adicionado DELTA_RECEITA_ESTRATEGIA nas `colunas_estrategia` (header amarelo)
5. Removido duplicação: lista `colunas_numericas` que não era usada

**Arquivos alterados**: `pages/backlog_visao_geral.py` (8 linhas, ordem corrigida)

---

## 📋 Próximas Melhorias (Backlog)

### 🔧 Limpeza de Código
- [ ] Remover `df_projetos` não usado de `backlog_visao_geral.py`
- [ ] Usar `df_controle` na função `matriz_backlog_por_projeto()` ou remover parâmetro
- [ ] Remover duplicação de flags em `backlog_analytics.py`

### 🚀 Melhorias de Performance
- [ ] Passar dados de `app.py` para páginas (reduz recarregar)
- [ ] Centralizar caminhos em `config.py` ou `st.secrets`
- [ ] Otimizar queries de agregação

### 🎨 Melhorias de UX
- [ ] Adicionar filtros na Matriz Analítica
- [ ] Expandir drill-down por projeto
- [ ] Melhorar responsividade do AgGrid

---

## 📌 Padrões e Convenções

### Carregar Dados
- `@st.cache_data` com TTL de 30s
- Padronização: colunas UPPERCASE + underscores
- Validação de estrutura antes de usar

### Transformações
- Flags booleanas para agregação (ex: `FLAG_ESTRATEGIA`)
- Agregação com `.groupby()` + `.agg()`
- Ordenação por colunas numéricas

### UI/Styling
- Cards customizados com HTML + `st.components.html()`
- AgGrid com `GridOptionsBuilder`
- CSS customizado via `custom_css` dict
- Linha "TOTAL GERAL" sempre no topo

### Headers por Grupo
- 🔸 **Marrom/Laranja** (`#92400e`): Backlog (TOTAL, GROSS, SERVICO, etc.)
- 🟡 **Amarelo** (`#facc15`): Estratégia (ESTRATEGIA, BACKLOG_ATUAL, etc.)

### Formatação Moeda
- ✅ Sempre APÓS agregação (nunca antes!)
- K/Mi/Bi para valores grandes
- "R$ 0" para valores nulos

---

## 🔗 Dependências Críticas

### backlog_visao_geral.py depende de:
- `carregar_backlog()` → base bruta
- `carregar_controle()` → filtra clientes
- `resumo_backlog()` → resumo de contagens
- `matriz_backlog_por_projeto()` → agregação principal
- `render_card()` → exibe KPIs
- `JsCode()` + `GridOptionsBuilder` + `AgGrid` → (from st_aggrid)

### backlog_analytics.py contém:
- `resumo_backlog(df)` → conta totais por classificação/produto
- `matriz_backlog_por_projeto(df_backlog, df_controle)` → agrupa por CLIENTE + cria flags

---

## ⚠️ Avisos Importantes

### Produção
- 🚨 **NÃO alterar** lógica de negócio sem testes
- 🚨 **NÃO remover** validações existentes
- 🚨 **Testar** sempre em ambiente de desenvolvimento primeiro

### Dados
- 📂 Caminhos hardcoded para OneDrive (pouco portável)
- 🔄 Cache pode mascarar problemas de dados
- 📊 Validar estrutura das bases antes de usar

---

## 📞 Contato
Para dúvidas sobre desenvolvimento, consulte este arquivo ou abra issue no repositório.