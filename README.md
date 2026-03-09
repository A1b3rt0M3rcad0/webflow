# WebFlow

Interface gráfica para criar e executar workflows de automação no navegador usando **Playwright**. Você monta **steps** (ações isoladas), combina em **workflows** e roda tudo com um clique; a saída aparece em uma janela tipo terminal.

---

## Requisitos

- **Python 3.13+**
- **uv** — [instalação](https://docs.astral.sh/uv/)

---

## Instalação e execução

```bash
# Instalar dependências
uv sync

# Abrir a interface
uv run python main.py
```

A UI usa **tkinter** (já vem com o Python). Playwright baixa os browsers na primeira execução (Chromium, Firefox, WebKit).

---

## Configuração

Arquivo **`.env`** na raiz do projeto (opcional):

| Variável | Uso |
|----------|-----|
| `CAPTCHA_API_KEY` | Chave da API do [2Captcha](https://2captcha.com/) para a action **Resolver reCAPTCHA v2**. Sem isso, a action não consegue resolver captcha. |

---

## Conceitos

### Steps

Um **step** é um arquivo JSON em `steps/` com uma lista de **actions**. Cada action tem `name` e `params`. Os steps são reutilizáveis: você cria uma vez e usa em vários workflows.

**Exemplo** (`steps/meu_step.json`):

```json
{
  "actions": [
    { "name": "goto", "params": { "url": "https://example.com" } },
    { "name": "click", "params": { "selector": "button#submit" } },
    { "name": "fill", "params": { "selector": "input[name='email']", "text": "test@test.com" } }
  ]
}
```

### Workflows

Um **workflow** é um JSON em `workflows/` que descreve um ou mais **browsers**, cada um com **pages** e uma sequência de **actions**. Pode ser montado na UI a partir de vários steps (que são concatenados em uma única página) ou editado manualmente (modo avançado).

**Estrutura** (resumida):

- `browsers`: lista de browsers (chromium, firefox, webkit).
- Cada browser tem `pages` com `url` e `actions`.
- Cada action: `name` + `params`, iguais aos dos steps.

---

## Actions disponíveis

| Action | Descrição | Params principais |
|--------|-----------|-------------------|
| **goto** | Abre uma URL | `url` |
| **click** | Clica em um elemento | `selector`, `force` (opcional) |
| **fill** | Preenche input/textarea | `selector`, `text`, `delay`, `force` |
| **screenshot** | Captura tela | `path` (arquivo) |
| **title** | Obtém o título da página | — |
| **wait_for_selector** | Espera elemento aparecer | `selector`, `timeout` |
| **get_element_data** | Lê texto/html/atributo de um elemento | `selector`, `data_type` (text/html/attribute/value), `attribute_name` (se for attribute) |
| **solve_recaptcha_v2_and_inject** | Resolve reCAPTCHA v2 (2Captcha) e injeta o token na página | `sitekey` (opcional), `sitekey_selector` (ex: `[data-sitekey]`), `max_retries`. A URL da página é usada automaticamente. |

Seletores são **CSS** (ex.: `button#submit`, `input[name="email"]`, `.classe`).

---

## Interface (UI)

### Painel esquerdo

- **Steps**: lista de arquivos em `steps/`. Duplo clique abre no editor de Step.
- **Workflows**: lista de arquivos em `workflows/`. Duplo clique abre no editor de Workflow.
- **Deletar workflow**: remove o workflow selecionado (com confirmação).
- **Atualizar listas**: recarrega as listas de steps e workflows.

### Aba Step

- **Nome do step** + botões: **Novo**, **Salvar step**, **Testar**, **Carregar**.
- **Actions**: lista de actions. Para cada uma: tipo (dropdown), parâmetros (formulário), botões Remover / Subir / Descer.
- **+ Adicionar action**: adiciona nova action ao step.
- **Testar**: roda o step atual em uma janela de console (terminal), sem salvar.
- **Carregar**: abre o step selecionado na lista da esquerda.

### Aba Workflow

- **Nome** + **Novo**, **Salvar**, **Visualizar código**.
- **Montagem por steps**: escolha os steps na lista, ordem, browser (chromium/firefox/webkit); salva um JSON em `workflows/`.
- **Visualizar código**: abre uma janela com o JSON do workflow (só leitura).
- Workflows são salvos em `workflows/<nome>.json`.

### Barra central (ambas as abas)

- **Salvar**: salva o step ou workflow da aba atual.
- **Executar workflow selecionado**: roda o workflow selecionado na lista à esquerda. Abre uma **janela de console** (fundo escuro, estilo terminal) com todos os prints das actions em tempo real ([GOTO], [CLICK], [FILL], erros, etc.).

---

## Estrutura do projeto

```
webflow/
├── main.py          # Entrada da interface gráfica
├── pyproject.toml      # Dependências (uv)
├── .env                # Opcional: CAPTCHA_API_KEY
├── steps/              # JSON dos steps
├── workflows/           # JSON dos workflows
└── src/
    ├── core/           # Núcleo
    │   ├── entity/     # Workflow, Browser, Page, Action (Pydantic)
    │   ├── workers/    # PageWorker (implementação das actions com Playwright)
    │   ├── mappers.py  # Liga action name → função do worker
    │   ├── webflow.py  # Orquestra browsers e actions
    │   └── solvers/    # 2Captcha (reCAPTCHA v2)
    ├── ui/             # Interface
    │   ├── app.py      # Janela principal, listas, console de execução
    │   ├── step_editor.py
    │   ├── workflow_editor.py
    │   ├── action_form.py   # Formulários por tipo de action
    │   └── runner.py       # Executa workflow em thread, redireciona stdout para a queue
    └── utils/
        ├── workflow_runner.py  # load_workflow_from_json, run_workflow_sync
        ├── make_workflows_by_step.py  # Monta workflow a partir de vários steps
        ├── steps_finder.py
        └── workflows_finder.py
```

---

## Dependências principais

- **playwright** (pytest-playwright): automação do navegador.
- **pydantic**: modelos dos workflows e actions.
- **2captcha-python**: resolução de reCAPTCHA v2.
- **python-dotenv**: carrega `.env`.

---

## Resumo rápido

1. **Steps**: crie em `steps/` pela UI (actions + params); use **Testar** para rodar só aquele step.
2. **Workflows**: monte em `workflows/` a partir de steps ou edite o JSON; selecione na lista e use **Executar workflow selecionado**.
3. A saída de qualquer execução aparece na **janela de console** que abre automaticamente.
4. Para reCAPTCHA v2, configure `CAPTCHA_API_KEY` no `.env`.
