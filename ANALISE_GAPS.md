# 🔍 ANÁLISE DE GAPS - Documentação vs Código Real

## Status: Análise realizada 10/04/2026 pelo GitHub Copilot

---

## ✅ O que está CONDIZENTE

| Aspecto | Documentação | Código | Status |
|---------|------|--------|--------|
| Stack (Python/Pandas/Streamlit) | ✅ Descrito | ✅ Implementado | OK |
| Objetivo (Backlog + Produção + Diário) | ✅ Claro | ✅ Parcialmente feito | ⚠️ Diário falta |
| Duas visões (Gerencial/Operacional) | ✅ Mencionado | ✅ Existe | OK |
| Diretrizes de modelagem | ✅ Bem definido | ⚠️ Parcialmente seguido | ⚠️ |
| Arquitetura de dados (5.1-5.5) | ✅ Documentado | ⚠️ Parcialmente usado | ⚠️ |

---

## ❌ GAPS CRÍTICOS

### 1. **Estrutura do Projeto (Seção 7) - INCOMPLETA**

**Documentação vs Realidade:**

```
DOCUMENTADO:              REALIDADE:
components/              components/
  header_cards.py    ≠     header.py ✅
  sidebar.py         =     sidebar.py ✅
  
(falta cards.py!)        cards.py ✅ (EXISTE!)

services/                services/
  carregar_bases.py  =    carregar_bases.py ✅
  calculos_kpi.py    =    calculos_kpi.py ✅
```

**Arquivos EXISTENTES mas não documentados:**
- ✅ `components/cards.py` — componente crítico!
- ✅ `services/backlog_analytics.py` — lógica de agregação
- ✅ `services/construir_tabela_analitica.py` — tabela cruzada
- ✅ `layout/header.py` — renderiza KPIs

**Ações necessárias:**
- [ ] Atualizar seção 7 para listar TODOS os arquivos reais
- [ ] Documentar funções principais em cada arquivo
- [ ] Descrever responsabilidade de cada módulo

---

### 2. **d_apontamentos - DOCUMENTADO MAS NÃO USADO**

**Seção 5.2 descreve:**
```
Tabela de apontamentos padrão
Campos: Apontamento_SK, Apontamentos_Padrao, Status_Macro, Macro_Ordem
```

**Realidade no código:**
- ❌ Nenhuma página usa `d_apontamentos`
- ❌ `carregar_bases.py` tem `carregar_apontamentos()` mas não é chamado
- ❌ `atualizar_diario.py` não integra com apontamentos padrão

**Risco:** Dados não sincronizados, apontamentos duplicados, falta de padronização

**Ações necessárias:**
- [ ] Integrar `d_apontamentos` em `atualizar_diario.py`
- [ ] Criar dropdown de apontamentos padrão
- [ ] Validar consistência com SKs

---

### 3. **Caminhos HARDCODED - NÃO DOCUMENTADO EM DIRETRIZES**

**Seção 6 (Diretrizes) NÃO menciona:**
- Onde centralizar paths
- Como lidar com OneDrive
- Portabilidade entre máquinas

**Realidade:**
```python
# carregar_bases.py - HOJE
PATH_DIARIO = r"C:\Users\z181040\OneDrive - Claro SA\BASES\..."
PATH_BACKLOG = r"C:\Users\z181040\OneDrive - Claro SA\BASES\..."
# ❌ Hardcoded!
```

**Problemas:**
- 🚫 Não funciona em outra máquina
- 🚫 Difícil de mudar paths  
- 🚫 Sem segurança para credenciais

**Ações necessárias:**
- [ ] Criar `config.py` centralizado
- [ ] Usar `st.secrets` para credenciais
- [ ] Atualizar diretrizes seção 6

---

### 4. **Cache Strategy - NÃO DOCUMENTADO**

**Código usa:**
```python
@st.cache_data
def carregar_diario(ttl=30):
```

**Documentação:** ❌ Não menciona

**Problemas:**
- Usuário não sabe que dados são cacheados
- TTL de 30s pode ser insuficiente
- Cache pode mascarar bugs de dados
- Sem invalidação manual

**Ações necessárias:**
- [ ] Documentar cache strategy
- [ ] Definir TTL ideal por tabela
- [ ] Implementar botão de refresh manual

---

### 5. **Validações INSUFICIENTES**

**Seção 6 (Diretrizes) menciona:**
- "validar duplicidades antes de merges"
- "tratar datas de forma robusta"
- "validar existência de colunas antes de utilizar"

**Realidade no código:**
- ⚠️ Algumas validações existem
- ❌ Nicht consistente entre páginas
- ❌ Sem tratamento global de erros
- ❌ Mensagens de erro genéricas

**Exemplo de gap:**
```python
# backlog_analytics.py - BOM
if "CLIENTE" not in df.columns:
    raise Exception("CLIENTE não encontrado")

# backlog_visao_geral.py - MISSING
# Não valida se colunas de receita existem
df_grid["DELTA_RECEITA_GERAL"] = ...  # Pode quebrar!
```

**Ações necessárias:**
- [ ] Criar validador centralizado
- [ ] Aplicar em todas as páginas
- [ ] Definir tratamento de erros padrão

---

### 6. **Requisitos de Produção - FALTAM COMPLETAMENTE**

**Documentação:** ❌ Não menciona

**Perguntas sem resposta:**
- Como monitora erros em produção?
- Qual o SLA de performance?
- Como fazer backup de dados?
- Como auditar mudanças?
- Qual o plano de continuidade?

**Ações necessárias:**
- [ ] Criar seção "Requisitos de Produção"
- [ ] Definir SLAs
- [ ] Implementar logging estruturado
- [ ] Criar plano de backup

---

### 7. **Dependências NÃO LISTADAS**

**requirements.txt:** ❌ Não existe

**Stack real inferido:**
```
streamlit==1.x
pandas==1.x
numpy==1.x
openpyxl==3.x
st-aggrid==0.x
```

**Risco:** Conflitos de versão, não reproduzível

**Ações necessárias:**
- [ ] Criar `requirements.txt`
- [ ] Documentar versões mínimas
- [ ] Testar em ambiente limpo

---

### 8. **Integração Entre Páginas - VAGA**

**Documentação:** Não descreve o fluxo

**Problemas no código:**
```python
# app.py - carrega TUDO
df_controle = carregar_controle()
df_backlog = carregar_backlog()
df_producao = carregar_producao()
df_diario = carregar_diario()
df_projeto = carregar_projetos()
# ✅ Bom: carrega uma vez

# pages/backlog_visao_geral.py - recarrega TUDO
df_backlog = carregar_backlog()
df_projetos = carregar_projetos()  # ← USELESS!
df_controle = carregar_controle()
# ❌ Ruim: recarrega, mesmo com cache
```

**Ações necessárias:**
- [ ] Refatorar para passar dados entre páginas
- [ ] Reduzir recarregos
- [ ] Sincronizar filtros

---

## 📊 Resumo de Prioridades

| Prioridade | Tarefa | Impacto | Esforço |
|-----------|--------|--------|--------|
| 🔴 CRÍTICO | Criar `config.py` | Alto | Baixo |
| 🔴 CRÍTICO | Criar `requirements.txt` | Alto | Muito Baixo |
| 🔴 CRÍTICO | Documentar estrutura real (seção 7) | Alto | Baixo |
| 🟠 ALTO | Integrar `d_apontamentos` | Médio | Médio |
| 🟠 ALTO | Implementar validações centralizadas | Alto | Alto |
| 🟡 MÉDIO | Documentar cache strategy | Médio | Muito Baixo |
| 🟡 MÉDIO | Requisitos de produção | Médio | Médio |
| 🔵 BAIXO | Refatorar fluxo entre páginas | Médio | Alto |

---

## ✅ Recomendações Finais

1. **Imediato (hoje):**
   - [ ] Criar `config.py`
   - [ ] Criar `requirements.txt`
   - [ ] Atualizar seção 7 da documentação

2. **Curto prazo (esta semana):**
   - [ ] Criar validador centralizado
   - [ ] Integrar `d_apontamentos`
   - [ ] Documentar cache strategy

3. **Médio prazo (este mês):**
   - [ ] Requisitos de produção
   - [ ] Refatorar fluxo entre páginas
   - [ ] Testes de integração

---

## 📝 Conclusão

**A documentação é boa CONCEITUALMENTE**, mas:
- ❌ Desatualizada em relação ao código real
- ❌ Faltam aspectos técnicos críticos (config, cache, validação)
- ❌ Alguns documentos não estão sendo usados (`d_apontamentos`)

**Recomendação:** Atualizar a documentação antes de novas features, para manter consistência.