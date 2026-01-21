# Birth Hub 360 Automático

Este repositório contém a implementação completa do sistema de empregabilidade autônomo "Birth Hub 360", consolidando os 4 projetos descritos no material de referência.

## Estrutura do Repositório

O código está organizado para atender aos diferentes estágios de evolução do sistema:

### 1. PROJETO 1: EXTENSÃO CHROME (MVP - LinkedIn)
**Localização:** `chrome_extension/`
- Manifest V3 simples.
- Automação via injeção de script (`content.js`) para "Candidatura Simplificada".

### 2. PROJETO 2: EXTENSÃO MULTI-PLATAFORMA
**Localização:** `chrome_extension/`
- Evolução da extensão para suportar Infojobs e Vagas.com.
- Uso de `background.js` para orquestração de abas.
- Bots específicos: `linkedin_bot.js`, `infojobs_bot.js`, `vagas_bot.js`.

### 3. PROJETO 3: ROBÔ SELENIUM (InfoJobs & Vagas.com)
**Localização:** `src/modules/selenium_bot/`
- Automação Python pura (sem navegador visível/headless).
- Simulação de comportamento humano (`human_bot.py`).
- Scripts específicos: `infojobs.py`, `vagas.py`.
- Runner 24h: `runner.py`.
- **Deployment:** Veja `deploy/bot_vagas.service` e `docs/AWS_SETUP.md`.

### 4. PROJETO 4: ARQUITETURA FINAL (Playwright + SQLite)
**Localização:** `src/core/` e `src/drivers/`
- Arquitetura robusta para escala (50+ candidaturas/dia).
- Banco de dados SQLite (`src/core/db.py`) para evitar candidaturas duplicadas.
- Orquestrador Playwright (`src/core/runner.py`) mais rápido e estável que Selenium.
- Configuração via JSON (`profile_br.json`).
- Exportação de dados (`src/core/export.py`).
- **Deployment:** Veja `deploy/autoapply.service` e `docs/SYSTEMD_SETUP.md`.

## Como Usar

### Instalação
```bash
pip install -r requirements.txt
playwright install chromium
```

### Configuração
1. Copie o arquivo de exemplo de ambiente:
   ```bash
   cp .env .env.example
   ```
   *(Preencha suas senhas no .env)*

2. Edite `profile_br.json` com seus dados pessoais.

### Execução (Arquitetura Final)
```bash
python -m src.core.runner
```

### Documentação Completa
Todo o código fonte concatenado para referência rápida está disponível em:
- [docs/CODIGO_CONSOLIDADO.md](docs/CODIGO_CONSOLIDADO.md)
