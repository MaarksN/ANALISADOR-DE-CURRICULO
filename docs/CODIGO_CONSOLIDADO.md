# CÓDIGO FONTE CONSOLIDADO - HUB DE VAGAS (V9 - ULTRA FINAL)

## .env.example
```
RUN_MODE=local
HEADLESS=0
TIMEZONE=America/Sao_Paulo
LINKEDIN_EMAIL=email@exemplo.com
LINKEDIN_PASSWORD=SUA_SENHA_AQUI
GUPY_EMAIL=email@exemplo.com
GUPY_PASSWORD=SUA_SENHA_AQUI
OPENAI_API_KEY=sk-...
TELEGRAM_BOT_TOKEN=123456:ABC-DEF
TELEGRAM_CHAT_ID=987654321

```

## requirements.txt
```
openai
streamlit
ics
requests

```

## profile_br.json
```
{
  "pessoal": {
    "nome_completo": "Nome Sobrenome",
    "email": "email@exemplo.com",
    "telefone": "11999999999",
    "linkedin": "https://www.linkedin.com/in/maarkss",
    "cidade": "Ribeirão Preto",
    "estado": "SP",
    "pais": "Brasil"
  },
  "preferencias": {
    "idioma_ui": "pt-BR",
    "modalidade": ["Remoto", "Hibrido", "Presencial"],
    "localizacoes_alvo": ["Brasil", "Ribeirão Preto SP"],
    "meta_candidaturas_dia": 50,
    "cv_nome_arquivo": "CV_Marcelo_Nascimento.pdf"
  },
  "skills": [
    "Revenue Operations", "Sales Operations", "RevOps", "Sales Enablement", "CRM",
    "Salesforce", "HubSpot", "RD Station", "Pipedrive",
    "Python", "SQL", "REST APIs", "Webhooks", "Dashboards", "Lead Scoring",
    "Power BI", "Excel", "OKRs", "Forecast", "Pipeline", "Go-to-Market",
    "SDR", "BDR", "Inside Sales", "Pré-vendas", "Outbound", "Prospecção",
    "Cold calling", "Cold email", "Cadência", "Sequência", "Qualificação",
    "Sales Navigator", "MQL", "SQL (Sales Qualified Lead)", "Follow-up", "Discovery call",
    "SPIN", "AIDA"
  ],
  "documentos": {
    "cv_pdf_path": "./docs/CV_Marcelo_Nascimento.pdf"
  },
  "seeds": {
    "linkedin_search_pages": [
      "https://br.linkedin.com/jobs/revenue-operations-vagas",
      "https://br.linkedin.com/jobs/sales-operations-vagas",
      "https://br.linkedin.com/jobs/sales-operations-analyst-vagas",
      "https://br.linkedin.com/jobs/sales-development-representative-trabalho-remoto-vagas",
      "https://br.linkedin.com/jobs/inside-sales-trabalho-remoto-vagas",
      "https://br.linkedin.com/jobs/remote-sales-vagas"
    ],
    "gupy_search_pages": [
      "https://portal.gupy.io/job-search/term=Sdr&workplaceTypes%5B%5D=remote",
      "https://portal.gupy.io/job-search/term=sdr&workplaceTypes"
    ]
  }
}

```

## chrome_extension/background.js
```
let jobQueue = [];
let isProcessing = false;

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.action === "QUEUE_JOBS") {
    const newJobs = request.urls;
    console.log(`[Background] Received ${newJobs.length} jobs to queue.`);

    // Add unique jobs
    newJobs.forEach(url => {
        if (!jobQueue.includes(url)) {
            jobQueue.push(url);
        }
    });

    sendResponse({status: "queued", count: jobQueue.length});

    if (!isProcessing) {
        processQueue();
    }
  } else if (request.action === "JOB_COMPLETE") {
      // Content script tells us it finished applying on the current tab
      console.log("[Background] Job Complete signal received.");
      // We can close the tab?
      if (sender.tab) {
          chrome.tabs.remove(sender.tab.id);
      }
      // Continue processing is handled by the loop/recursion,
      // but since we close the tab, we rely on the processQueue loop or re-trigger.
      // Actually, since processQueue is async, it might need to wait.
  }
});

async function processQueue() {
    if (jobQueue.length === 0) {
        isProcessing = false;
        console.log("[Background] Queue empty.");
        return;
    }

    isProcessing = true;
    const url = jobQueue.shift();
    console.log(`[Background] Processing: ${url}`);

    try {
        const tab = await chrome.tabs.create({ url: url, active: true });

        // Wait for page load
        await waitTabLoad(tab.id);

        // Inject the start command
        // Note: The content script (loader -> router) runs automatically on match.
        // But we need to tell it "Auto Start" because it's an automated tab.
        // We can do this by sending a message after load.

        await sleep(3000); // Wait for DOM

        chrome.tabs.sendMessage(tab.id, {action: "start"}, (response) => {
            if (chrome.runtime.lastError) {
                console.log("[Background] Error sending start command: ", chrome.runtime.lastError.message);
            } else {
                console.log("[Background] Start command sent to tab.");
            }
        });

        // Wait for job completion?
        // Realistically, we need a timeout or a message back.
        // For this MVP, we give it X seconds then close.
        await sleep(10000);

        // Close tab
        try {
            await chrome.tabs.remove(tab.id);
        } catch (e) { /* Tab might be closed by user */ }

    } catch (err) {
        console.error("[Background] Error processing job:", err);
    }

    // Process next
    setTimeout(processQueue, 1000);
}

function waitTabLoad(tabId) {
    return new Promise(resolve => {
        chrome.tabs.onUpdated.addListener(function listener(tid, changeInfo) {
            if (tid === tabId && changeInfo.status === 'complete') {
                chrome.tabs.onUpdated.removeListener(listener);
                resolve();
            }
        });
    });
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

```

## chrome_extension/content_router.js
```
import { runLinkedInBot } from './linkedin_bot.js';
import { runInfojobsBot } from './infojobs_bot.js';
import { runVagasBot } from './vagas_bot.js';
import { log } from './utils.js';

log("Extension Loaded. Waiting for start command...");

chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
    if (request.action === "start") {
        log("Command received: START");

        const hostname = window.location.hostname;

        if (hostname.includes('linkedin.com')) {
            runLinkedInBot();
        } else if (hostname.includes('infojobs.com.br')) {
            runInfojobsBot();
        } else if (hostname.includes('vagas.com.br')) {
            runVagasBot();
        } else {
            alert("Site não suportado por este bot.");
        }

        sendResponse({status: "started"});
    }
});

```

## chrome_extension/infojobs_bot.js
```
import { sleep, log } from './utils.js';

export async function runInfojobsBot() {
    log("Iniciando Bot Infojobs...");

    // Look for the main Apply button
    const applyBtn = document.querySelector('.js_apply_vacancy');

    if (applyBtn) {
        if (applyBtn.classList.contains('disabled')) {
            log("Botão de candidatura desabilitado ou vaga já aplicada.");
            return;
        }

        log("Clicando em Candidatar-se...");
        applyBtn.click();
        await sleep(2000);

        // Try the specific selector provided in the snippet
        const confirmBtnSnippet = document.querySelector('#ctl00_phMasterPage_cContent_ucApplyVacancy_lbtnApply');
        // Also fallback to generic selector just in case
        const confirmBtnGeneric = document.querySelector('a[id*="lbtnApply"]');

        const confirmBtn = confirmBtnSnippet || confirmBtnGeneric;

        if (confirmBtn) {
            log("Confirmando candidatura...");
            confirmBtn.click();
            await sleep(2000);
            log("Candidatura enviada no Infojobs!");
        } else {
            // Check for login requirement
            if (document.querySelector('.login-form')) {
                log("Necessário login. O bot não preenche senhas por segurança.");
            } else {
                log("Botão de confirmação não encontrado.");
            }
        }
    } else {
        log("Botão de candidatura não encontrado nesta página.");
    }
}

```

## chrome_extension/linkedin_bot.js
```
import { userProfile } from './user_profile.js';
import { sleep, log } from './utils.js';

export async function runLinkedInBot() {
    log("Iniciando Bot LinkedIn...");

    // Find job cards in the left sidebar
    const jobs = document.querySelectorAll('.job-card-container');
    if (jobs.length === 0) {
        log("Nenhuma vaga encontrada na lista lateral. Certifique-se de estar na página de busca de vagas.");
        return;
    }

    for (let job of jobs) {
        // Scroll to job to ensure it loads
        job.scrollIntoView({ behavior: 'smooth', block: 'center' });
        job.click();
        log("Vaga clicada, aguardando carregamento...");
        await sleep(2000);

        // Check for Easy Apply button
        const applyBtn = document.querySelector('.jobs-apply-button--top-card');

        if (applyBtn) {
            log("Botão Candidatura Simplificada encontrado.");
            applyBtn.click();
            await sleep(1500);

            // Handle Modal
            await handleModal();
        } else {
            log("Botão de Candidatura Simplificada não encontrado ou vaga já aplicada.");
        }

        await sleep(1000);
    }
    log("Fim da lista de vagas visíveis.");
}

async function handleModal() {
    let maxSteps = 20; // Prevent infinite loops
    let step = 0;

    while (document.querySelector('.jobs-easy-apply-modal') && step < maxSteps) {
        step++;

        // Buttons
        const buttons = Array.from(document.querySelectorAll('button'));
        const nextBtn = buttons.find(b => b.innerText.includes('Avançar') || b.innerText.includes('Next'));
        const reviewBtn = buttons.find(b => b.innerText.includes('Revisar') || b.innerText.includes('Review'));
        const submitBtn = buttons.find(b => b.innerText.includes('Enviar candidatura') || b.innerText.includes('Submit application'));

        // Fill Inputs
        await fillInputs();

        if (submitBtn) {
            log("Enviando candidatura...");
            // submitBtn.click(); // UNCOMMENT TO ACTUALLY APPLY
            // await sleep(2000);

            // Close modal after submit (usually "Done" button appears)
            const closeBtn = document.querySelector('button[aria-label="Dismiss"]');
            if(closeBtn) closeBtn.click();
            return;
        }
        else if (reviewBtn) {
            log("Revisando...");
            reviewBtn.click();
            await sleep(1500);
        }
        else if (nextBtn) {
            log("Avançando...");
            nextBtn.click();
            await sleep(1500);

            // Check for errors (did not advance)
            if (document.querySelector('.artdeco-inline-feedback--error')) {
                log("Erro no formulário detectado. Pulando vaga.");
                const closeBtn = document.querySelector('button[aria-label="Dismiss"]');
                if(closeBtn) closeBtn.click();
                await sleep(500);
                const confirmDiscard = buttons.find(b => b.innerText.includes('Descartar') || b.innerText.includes('Discard'));
                if (confirmDiscard) confirmDiscard.click();
                return;
            }
        } else {
            // Unexpected state or just wait
            // Sometimes it takes a moment for buttons to update
            await sleep(1000);
        }
    }
}

async function fillInputs() {
    // 1. Radio Buttons (Yes/No)
    const radioGroups = document.querySelectorAll('.jobs-easy-apply-form-section__grouping');
    for (const group of radioGroups) {
        // Simple heuristic: always click the first radio (usually "Yes" or top option)
        // A real AI would analyze the label text.
        const radios = group.querySelectorAll('input[type="radio"]');
        if (radios.length > 0) {
            // Check if one is already checked
            const checked = Array.from(radios).some(r => r.checked);
            if (!checked) {
                // Determine logic based on label text?
                // For MVP, click the first one (often 'Sim' or 'Yes')
                // But safer to check label.

                // For now, Marcelo wants to automate, so let's default to positive/first.
                radios[0].click();
                await sleep(200);
            }
        }
    }

    // 2. Text Inputs (Phone, City, etc)
    const textInputs = document.querySelectorAll('input[type="text"], input[type="number"]');
    for (const input of textInputs) {
        if (!input.value) {
            const label = input.id ? document.querySelector(`label[for="${input.id}"]`)?.innerText.toLowerCase() : "";

            if (label.includes("phone") || label.includes("telefone") || label.includes("celular")) {
                fireInputEvent(input, userProfile.personal.phone);
            } else if (label.includes("city") || label.includes("cidade")) {
                fireInputEvent(input, userProfile.personal.city);
            }
            // Add more mappings as needed
        }
    }
}

function fireInputEvent(input, value) {
    input.value = value;
    input.dispatchEvent(new Event('input', { bubbles: true }));
    input.dispatchEvent(new Event('change', { bubbles: true }));
}

```

## chrome_extension/loader.js
```
(async () => {
    const src = chrome.runtime.getURL('content_router.js');
    const contentMain = await import(src);
})();

```

## chrome_extension/manifest.json
```
{
  "manifest_version": 3,
  "name": "Marcelo AutoApply - Multi",
  "version": "2.2",
  "permissions": ["activeTab", "scripting", "storage", "tabs"],
  "host_permissions": [
    "*://*.linkedin.com/*",
    "*://*.infojobs.com.br/*",
    "*://*.vagas.com.br/*"
  ],
  "action": { "default_popup": "popup.html" },
  "background": { "service_worker": "background.js" },
  "web_accessible_resources": [
    {
        "resources": ["content_router.js", "linkedin_bot.js", "infojobs_bot.js", "vagas_bot.js", "utils.js", "user_profile.js"],
        "matches": ["<all_urls>"]
    }
  ],
  "content_scripts": [
    {
      "matches": [
        "*://*.linkedin.com/*",
        "*://*.infojobs.com.br/*",
        "*://*.vagas.com.br/*"
      ],
      "js": ["loader.js"]
    }
  ]
}

```

## chrome_extension/popup.html
```
<!DOCTYPE html>
<html>
<head>
  <style>
    body { width: 250px; padding: 15px; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f3f2ef; }
    h3 { color: #0a66c2; text-align: center; margin-top: 0; }
    .status { font-size: 12px; margin-bottom: 10px; color: #666; text-align: center; }
    button {
      width: 100%;
      padding: 12px;
      background: #0a66c2;
      color: white;
      border: none;
      border-radius: 20px;
      cursor: pointer;
      font-weight: bold;
      transition: background 0.2s;
    }
    button:hover { background: #004182; }
    .platform-tag {
        display: inline-block;
        padding: 2px 6px;
        border-radius: 4px;
        background: #ddd;
        font-size: 10px;
        margin-right: 4px;
    }
  </style>
</head>
<body>
  <h3>AutoApply 2.0</h3>
  <div class="status">
    Plataformas:
    <span class="platform-tag">LinkedIn</span>
    <span class="platform-tag">Infojobs</span>
    <span class="platform-tag">Vagas</span>
  </div>
  <button id="startBtn">Iniciar Automação</button>
  <script src="popup.js"></script>
</body>
</html>

```

## chrome_extension/popup.js
```
document.getElementById('startBtn').addEventListener('click', () => {
    chrome.tabs.query({active: true, currentWindow: true}, (tabs) => {
      // Send a message to the active tab's content script
      chrome.tabs.sendMessage(tabs[0].id, {action: "start"}, (response) => {
        if (chrome.runtime.lastError) {
             // If content script isn't loaded yet (e.g. new tab), inject it first?
             // Or just tell user to refresh.
             alert("Erro: Recarregue a página e tente novamente.");
        }
      });
    });
  });

```

## chrome_extension/user_profile.js
```
export const userProfile = {
    personal: {
      firstName: "Marcelo",
      lastName: "Nascimento",
      fullName: "Nome Sobrenome",
      email: "email@exemplo.com",
      phone: "11999999999",
      linkedin: "www.linkedin.com/in/maarkss",
      city: "Ribeirão Preto",
      state: "SP",
      summary: "Engenheiro de RevOps e Sales Operations com foco em automação, Python e IA. Transformo processos manuais em máquinas de receita escaláveis. +7 anos de experiência."
    },
    skills: [
      "Revenue Operations", "Sales Operations", "Salesforce", "HubSpot",
      "Python", "Automação", "SQL", "APIs", "CRM Implementation", "Data Science"
    ],
    education: [
      {
        institution: "UNINTER",
        degree: "Tecnólogo em Ciência de Dados",
        start: "2025",
        end: "2028"
      },
      {
        institution: "Universidade de Ribeirão Preto",
        degree: "Educação Física",
        start: "2013",
        end: "2016"
      }
    ],
    lastRole: {
      title: "Analista de Revenue Operations",
      company: "Auto Arremate",
      description: "Automação de processos comerciais, integração de 14 plataformas e implementação de CRM HubSpot."
    }
  };

```

## chrome_extension/utils.js
```
export function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

export function log(msg) {
    console.log(`[AutoApply] ${msg}`);
}

```

## chrome_extension/vagas_bot.js
```
import { sleep, log } from './utils.js';

export async function runVagasBot() {
    log("Iniciando Bot Vagas.com...");

    // Check if we are on a search list
    if (document.querySelector('.vaga')) {
        log("Lista de vagas detectada.");
        const cards = document.querySelectorAll('.vaga');
        const urls = [];

        cards.forEach(card => {
            const link = card.querySelector('a.link-detalhes-vaga');
            if (link) {
                // Vagas.com often uses relative URLs or full URLs
                urls.push(link.href);
            }
        });

        if (urls.length > 0) {
            log(`Coletados ${urls.length} links. Enviando para fila de processamento...`);
            chrome.runtime.sendMessage({
                action: "QUEUE_JOBS",
                urls: urls
            }, (response) => {
                log(`Background respondeu: ${response?.status} (${response?.count} na fila)`);
            });
        } else {
            log("Nenhum link encontrado.");
        }

    } else {
        // Single Job Page
        // Check for "Candidatar-se" button
        const applyBtn = document.querySelector('button[name="btCandidatura"]');

        if (applyBtn) {
            log("Botão de candidatura encontrado.");
            applyBtn.click();
            await sleep(2000);

            // If already applied or success
            if (document.body.innerText.includes("Candidatura realizada")) {
                log("Candidatura confirmada.");
            }
        } else {
            // Might be already applied
            log("Botão de Candidatura não identificado ou vaga já aplicada.");
        }

        // Signal completion (optional, background closes anyway)
    }
}

```

## deploy/autoapply.service
```
[Unit]
Description=AutoApply (LinkedIn + Gupy)
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/autoapply
ExecStart=/opt/autoapply/.venv/bin/python -m src.core.runner
Restart=always
RestartSec=120
Environment=RUN_MODE=ec2
Environment=HEADLESS=1

[Install]
WantedBy=multi-user.target

```

## deploy/bot_vagas.service
```
[Unit]
Description=AutoApply Bot (Selenium)
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/BotVagas
ExecStart=/home/ubuntu/BotVagas/venv/bin/python3 -m src.modules.selenium_bot.runner
Restart=always
RestartSec=300

[Install]
WantedBy=multi-user.target

```

## docs/AWS_SETUP.md
```
# Configuração do Bot na AWS (EC2 / Ubuntu)

Siga os passos abaixo para configurar o ambiente e rodar o bot em modo headless (sem interface gráfica) em um servidor Ubuntu.

## 1. Atualizar o sistema
```bash
sudo apt update && sudo apt upgrade -y
```

## 2. Instalar o Google Chrome (versão estável)
```bash
wget https://dl.google.com/linux/direct/google-chrome-stable_current_amd64.deb
sudo apt install -y ./google-chrome-stable_current_amd64.deb
```

## 3. Instalar dependências do Python
```bash
sudo apt install -y python3-pip python3-venv unzip
```

## 4. Configurar o Projeto

Clone o repositório ou crie a pasta:

```bash
mkdir HubDeVagas
cd HubDeVagas
# (Aqui você faria o git clone ou upload dos arquivos)
```

## 5. Criar e ativar o ambiente virtual
```bash
python3 -m venv venv
source venv/bin/activate
```

## 6. Instalar bibliotecas
```bash
pip install -r requirements.txt
```
*Certifique-se de que `selenium` e `webdriver-manager` estão no requirements.txt.*

## 7. Configurar Variáveis de Ambiente
Para segurança, não salve senhas no código. Exporte-as antes de rodar:
```bash
export INFOJOBS_PASSWORD="sua_senha_real"
export VAGAS_PASSWORD="sua_senha_real"
```

## 8. Executar o Bot 24h
```bash
python3 src/modules/selenium_bot/runner.py
```
*Para manter rodando mesmo ao fechar o terminal, use `nohup` ou `tmux`.*

```bash
nohup python3 src/modules/selenium_bot/runner.py > bot.log 2>&1 &
```

```

## docs/SYSTEMD_SETUP.md
```
# Configuração do Systemd para AutoApply

Para rodar o AutoApply como um serviço de fundo (daemon) no Ubuntu, siga estes passos:

## 1. Criar o arquivo de serviço
Crie o arquivo `/etc/systemd/system/autoapply.service` com o seguinte conteúdo:

```ini
[Unit]
Description=AutoApply (LinkedIn + Gupy)
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/home/ubuntu/HubDeVagas
# Ajuste o caminho do python conforme seu venv
ExecStart=/home/ubuntu/HubDeVagas/venv/bin/python -m src.core.runner
Restart=always
RestartSec=120
Environment=RUN_MODE=ec2
Environment=HEADLESS=1

[Install]
WantedBy=multi-user.target
```

## 2. Ativar e Iniciar o Serviço

```bash
sudo systemctl daemon-reload
sudo systemctl enable autoapply
sudo systemctl start autoapply
```

## 3. Verificar Logs

```bash
sudo journalctl -u autoapply -f
```

```

## docs/assets/css/style.css
```
:root {
    --primary: #0a66c2;
    --secondary: #004182;
    --dark: #111;
    --light: #f3f2ef;
    --white: #fff;
    --gray: #666;
}

* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
    color: var(--dark);
    background-color: var(--light);
}

.container {
    max-width: 1100px;
    margin: 0 auto;
    padding: 0 20px;
}

/* Header */
header {
    background: var(--white);
    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    position: sticky;
    top: 0;
    z-index: 100;
}

header .container {
    display: flex;
    justify-content: space-between;
    align-items: center;
    height: 70px;
}

.logo {
    font-size: 1.5rem;
    font-weight: bold;
    color: var(--primary);
}

nav ul {
    list-style: none;
    display: flex;
}

nav ul li {
    margin-left: 20px;
}

nav ul li a {
    text-decoration: none;
    color: var(--gray);
    font-weight: 500;
    transition: color 0.3s;
}

nav ul li a:hover, nav ul li a.btn-github {
    color: var(--primary);
}

.btn-github {
    color: var(--dark) !important;
}

/* Hero */
.hero {
    background: linear-gradient(135deg, var(--secondary) 0%, var(--primary) 100%);
    color: var(--white);
    padding: 100px 0;
    text-align: center;
}

.hero h1 {
    font-size: 3rem;
    margin-bottom: 20px;
}

.hero p {
    font-size: 1.2rem;
    max-width: 700px;
    margin: 0 auto 40px;
    opacity: 0.9;
}

.btn {
    display: inline-block;
    padding: 12px 30px;
    border-radius: 30px;
    text-decoration: none;
    font-weight: bold;
    transition: transform 0.2s, box-shadow 0.2s;
}

.btn:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 10px rgba(0,0,0,0.2);
}

.btn-primary {
    background: var(--white);
    color: var(--primary);
    margin-right: 15px;
}

.btn-secondary {
    border: 2px solid var(--white);
    color: var(--white);
}

.btn-light {
    background: var(--white);
    color: var(--primary);
}

/* Features */
.features {
    padding: 80px 0;
    background: var(--white);
}

.features h2 {
    text-align: center;
    margin-bottom: 50px;
    font-size: 2rem;
}

.grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 30px;
}

.card {
    background: var(--light);
    padding: 30px;
    border-radius: 10px;
    text-align: center;
    transition: transform 0.3s;
}

.card:hover {
    transform: translateY(-5px);
}

.icon {
    font-size: 3rem;
    color: var(--primary);
    margin-bottom: 20px;
}

.card h3 {
    margin-bottom: 15px;
}

/* Download */
.download-section {
    padding: 80px 0;
    background: var(--primary);
    color: var(--white);
    text-align: center;
}

.download-box {
    background: rgba(255,255,255,0.1);
    border: 1px solid rgba(255,255,255,0.3);
    border-radius: 10px;
    padding: 20px;
    display: inline-flex;
    align-items: center;
    gap: 20px;
    margin: 30px 0;
}

.download-box i {
    font-size: 2.5rem;
}

.download-box .info {
    text-align: left;
}

.download-box .info strong {
    display: block;
    font-size: 1.2rem;
}

.download-box .info span {
    font-size: 0.9rem;
    opacity: 0.8;
}

.note {
    font-size: 0.9rem;
    opacity: 0.8;
    max-width: 600px;
    margin: 0 auto;
}

/* Docs */
.docs-section {
    padding: 80px 0;
    background: var(--light);
    text-align: center;
}

.doc-links {
    display: flex;
    justify-content: center;
    gap: 20px;
    flex-wrap: wrap;
    margin-top: 40px;
}

.doc-card {
    background: var(--white);
    padding: 20px 40px;
    border-radius: 8px;
    text-decoration: none;
    color: var(--dark);
    display: flex;
    align-items: center;
    gap: 15px;
    box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    transition: all 0.2s;
}

.doc-card:hover {
    color: var(--primary);
    box-shadow: 0 5px 15px rgba(0,0,0,0.1);
}

.doc-card i {
    font-size: 1.5rem;
}

/* Footer */
footer {
    background: var(--dark);
    color: var(--white);
    text-align: center;
    padding: 20px 0;
}

```

## docs/downloads/chrome_extension.zip
```
PK
     J5\              chrome_extension/UT	 \x87\x99piG\x96piux \xe9  \xe9  PK    J5\ )\xfd]\xae  &    chrome_extension/background.jsUT	 \x87\x99pi\x87\x99piux \xe9  \xe9  \x95Vmo\xdb6\xfe\xee_q\x86F.T%ž9H\x8b$\xf3\x80I\x93\xe6\xa5P--\xd16;\x9aTI*\x99\xf8\xbf\xf7\x8e\xd4\xe58\xeb\xe6vB\xdd\xef\x9e{\x9e;I\xee\xe0\x9b\x9e}\xa8y\xcd\xe1>}>I<\xf6\xca\xe8\x82[+\xd4\x8f\xe7LZ~8K\xa3W<7\xb5r\xb5\xba@\xb6\xe09+\xcbsaWܤ\xa9\xe1\xdfkn]\x96\xab\x92\x9b\xf0{\xcdm\xa5\x95\xe5c8z\x8f# 1\x87\xd62g\x85Z\xc1\xd1\xd1$\xee\xa6w\xd3/\xef.On\x92\xb17(\xd0с\xe2\xef\xf4\xccb:\xad[m\xa4=\xec,\xb4\xe4\xb9ԋ\xf4\xeb\xa7V\xfc\xbd0\xbaV\xe5g\xb8\xe6\xf7\xbc\x84_\x9b \xb9\xe4j\xe1\x96\xaaۂ\xd3\xf0\x9d\x8aϿ\x8eC(\xff\xb5\xbf\xc7e	\xb5\xf8\xd0\xfa\xe36\xc2\\x9b)+\x96)&Ж>T\xd4/-\x9e\xb9P\x85\xacKn\xc9n<\x8e\xcc\xe8\xd3YU\xb5\xf5\x91\x9a\xfb\xe9\xb3\xf1m\xe2\x8cb\xd3G똫\xed\x9f{\x99d\x88 6e\xd2Gm\x8a\x8cC\xf8\xe4\xe2\xce\xc6)U\xe1\xd4;\xa7\x8d\xa5\xb1\x8e\xbd\xb6[ا/\xa7\x97W\xe7\xd3\xdbi\xd2\xc7C\xfcN\xb5B>8\xb0\x85\x95ǥ\xb4P[\xe6B	\xbbĞ\xb0\xaa\x92k\xa2\x86sKEm\xf986kōM\x8d\xc5F\xe0\xab
\xe9\xca\xc1\x8a\x85b\x89\x9a\x9d'\x98\x98ɟ\x98)(\xa4\xc6B\xe8\xffv\xd47,\xd04\xc7\xd3a\x8f\xb6\xe3\xb9\xcd_\xe9{\x99\xe6\xa2\xec\xee\xd8\xab
9S\xf5\xfa\x96L\x95\x9e\xad}R\xebj\x93\xad\x8dE$3\xe8\xfdg5"\x86\xbc\xe1\xf0\xc0\x87gtb\xb8\\xb7`\xc5\xf3A4x\xe5\x8cX,0\xc9>\xe8q\xe1j&\xe5:kB<1;fתȨ3+\xb1X\x92\xd20U\xc6\x8e\xc2lFģ\x917\x83y\xadB\xff\x87\x8ci\x90#<\xb78\xe8\x89rC\xbb{\xbat\xb0?\xdb\xf2\x900_Unu\xb0hW\xd5rv\xb4\xe3
gj~\xcd/\xdc^,v)\xe6\xaee\xfd\xf3\xb3\xa49\xc1q\x821644\xbc\x933\xeb\xa8\xc0p	6/a\x84\xe2\x80K\x85\xe1̡\x88)\x8b	}e@\x92\xba\xe7\x9fg\xa7\xfbN\xb8-\x8f)\x8e\xa8p\xe4b\xc7Y\xd9=\x97\xd0\xd7-\x9b\x9d\xe3\x93t\x8b\xa2\xc3Hg\xea/\x9cgN\x83\xe9\xe9\xd5
)ۼ\xd7\xba%U\x95\x9c\xd2\xcd\xdc\xc0\xab7\x80\xb88nƀYT;\xbdbND5")\xfeS,\xf38\xe6	\xb2Y\xdc\xf2\x8bf\xb1.9FW\xb8\xa1L\x98\xf1\x82\xd54q\xdc\xc6TmX\xf2\xc0\x92x]\x97h\x89,Fm\x91<\xa9\xe1Va1\x9bc\x82\xab\xfc)5+9\xaf\xd2\xdfƇ\x98\xbf\xbcx\xea7\x92\xaek6`\x83w\x8fa:\xe2h\xf6\xc8&\x9b\x8c\xe7\xd6\xee\xeb?\xa4\x97\xad\xad*\x99uSc\xb4\xd9\xde\xff.\xef\xd2!0h+&\x93\xc1s\xb7\xe4TU\xbc\x8e\xc2\xdc\xff?\xdc\xc4wR&\xce7\x81I\xb6\x83\xf7\x9b\xeeg\G\x8dRH\xf3\xebہ\xd15g\xdf:㲎Y\xa8B\xa4&Ğ
3Lu\xc0\x9f?\xf0\xb1g\xce\xc5\xc7+\xef\xbd@\xff\xc2\xe4\xb1\xccҒB\x9aő\xefd\xcd\xeb\x83@\x9b\x9d5\x9c\x86\xf1\xdd\xed\xb2\xed)\xd1۱i\x9e\xe8w\x83dG=A\x8a4z\x84\xfd\x97\x80Jo\xe6\xf5\xacY~\xbf\xa0v\xbc܏0\xdd̀Xm;9qa'\xa5\xa2M\x86͘ \x95(\xc4`\xdab\xb1\xcdl\xc4\xfc\xe3\x9awڐƛ"\x83\xd7\xb2\xbav\xabdkp\x9d\x95m\x86a\xb2\xd3{]\xb0\xf8\xee\x83b\xd2\xfb4\x90R\xa0VwUIc\xf0V\xda\xdd%\xdbGr-p3/\xf8\x99\x9a\xebm\xb5\x912\xd1\xc4o/\x9f\xbcx\x99\xe7\xe1\xcc?\xdek\xca\xf7vJvgn\xa1\xcd]zmV[B	\xf8\x82ӟjh\xb3\x85j\xa0\xe8\xca\xfe70\xa3~5\xa7\xa0\xaf\x8f\xf9PK    J5\[\xe2\xee\xe1Z      chrome_extension/manifest.jsonUT	 s\x99piR\x96piux \xe9  \xe9  \x8dQ\xcbj\xc30\xbc\xe7+\x84\x8e!u \xbd\x85R\xc8\xf4\xd6[	B\x92׎Y+\xf4p(!\xff^I\x8ec7\x85P\x8cvf3\xbb\x97!\xb4\xe3F5\xe0\xeb\xc1y\x85\x86n\xc9\xeb*\x86w\x90\xfa\xc1\x9d\x8dd\xee\xac\xd5\xdf\xe4\x85|D-iS\xddT\x9b\xb3\xe0:\xe53\xec\xfeE\xb9\xaa\x87O.\xe8\x8aP/\x9d\xb2A\x99\xb6o!?\x9e\xeeK\xfd\x93\x9e\x87&	O\xccr\xbb^/+\xad\xcc	je*\x89\xddzYf\xde9e<\xa2𙫄{\xa4{\xde\xf2\x97\xa8ad\x96X\\\xad\xa1\xe1\xc9 \xb3h\xa3\xcd\xc6ʣ:\x84NSr-\xe9\x82\xcbS\xeb0\x9az(\xf1\xe0z%\x81\x9dѝ\xc0\xe5\x9a)\xa3:\xfa\xb1\xec\x82q)!\xd9\x98\x8f1mw2x)\xff\xa2\xf7I%\x9a &\xb0\xd41\x80\xcb-\xd3\xca\xc6=0\x81\xe1\x8d\xf6gP\xb1<\x8bcPڏ\xef$\x9cY\x87\x8dҐ\xa1\xfdj\xd0\xf1 \xb7\xf1o\k\x9d\xf6\xeft_2\xae\xf7͍ʆ\xbb\xfe\xb52\xef35r\xc8\xf3\xe9A\xf3w\xf7A\x8f\x83\x8d\xbc\xf66ӿ\xb8.~ PK    kH5\\xc8\xd5k-  q    chrome_extension/popup.htmlUT	 Z\x96piZ\x96piux \xe9  \xe9  \x8dT\xdbn\x9b@}\xcfWL]Uy	6\xc6	\xaa0\xb5\x94^TE\xaa\xd4HM#\xf5q`\xd8v\xd1\xeebǉ\xfa5}\xe8\x87\xe4\xc7:,`H[\xa9}b\x9993s\xce\xd9K\xfc\xe2\xfd\xe7w7߮?@a\xabrs\x8els{(y\xbbH;\xc0#\xec\xb3E\xc1\x85_߯\xa1FƄ\xcc#X^\xb4\xbf\x99\x92\xd6˰\xe5!\x82\xd3/<W\xbe^\x9d\x9e\xc1\xaa\xc23\xf8\xc8%\xdf\xd1\xf7\x96k\x86\x92\xa5\xf1\xd7"[C\x82\xe96ת\x91\xccKU\xa9t/\xb3UpJ}w\x8aR>\x86a\xac\xc1\xf2{\xeba)rAʥ\xe5z\xea\HϪ:\xa8\x9e\x8b\xb61\xd4\xc2\xd14\xe2\x81\xef\xa0\xe5\xdd\xe3e\xad\xaa(\xe8\xb4\x83\xc20\xfc\xfb\x94\xaem\xd2P\x91\xa4\xae\xee\x83\x96\xbe\xffj=\xc4F\x9bܸ>:\xea\x9d\xc8\xe9s\xfd\xf0}!,\x94f\x9c\xa2R\xc9߃\x9eF&C\xd3r\x9a4ڴ]j%:\xc6}\xdc\xe9\xdfs\x916\xa2\xfa\x92V\xd3v+\xa9ف?L\x99J\x8e
\xb5㚄?\xd7\xe1\x9f/_G\xcf\xebm\xa6t\xe5Y\xcc\xe1\xb1\xc0\x84\xa1!K!\xb9\x97\x94*ݮ\x8f\xe9\xa3_d\x84\xa3\xa0?Ԟ?\xcbMy0\xc6\xc6\xcct\xc3\xfdiI\xbf\xf1\xba\xb3\xe2ح%/\xfa\xc3/\xba\xeb\xb77\xc0݊b\xb5\xb9l\xac\xba\xac\xeb\xf2 \xc1\xdc'\xc4\xca%\x98\xd8AZ\xa21of\xdda\x9buw\xe7\x9a\\xc0\xd6$\xce.\x9b倝\x9a4\xdb|r\xcbٕ$\x84\xd9\xfc~%3u\xa7\xf3\x9f\xf0[\xccq\x82\x8d\xc4\xd9-\xfas,\x98\xe3\xae\xed[+\xdb\xe6"\xa8\xa1\x95[\xe1\xd3ϧ*^t\xc8\xee}H\xb5\xa8-\x9d\xd2U7\xf5\xfc\x8e4S{o\xbd\xebL#\x87\xdc\xcb\xf2PK    rH5\}\x95?\xdcW  \xc9     chrome_extension/user_profile.jsUT	 g\x96pig\x96piux \xe9  \xe9  \x85S\xc9nA\xbd\xf3\xa5\xb9b98\x84l	+	\xc2q\x8cN\x88C\xa5\xa7\xec\x94\xd2\xcb\xd0ݓE(q@B\xe2\xc4'̏Q=\xcf\x84\xb6\xbb\xd6\xf7\xaa^\xd1m\xe1|\xe5l\x88P\xf23	^\xc1\x97' \x9f\x82|p\xf5a\xf3X\xb2q\x8a\x86!;E\xafH\xbbl\xd0\xf84\xb6\xae)ņl\xec\xbc\xcbR\xeb\xdf\xe1\x91(2\xc8\xd2.3u[\xf9\xbdz\xbdJơr\xa6+.\x9dM\x95F\xbb\xf2\xd9\xd9\xdf\xd9;\xe8`\xb0\xbd\xa2\x9c\xad\xb8onn\x86\x9bg\xca\xdfb\xbbePJ\x86І+\x8ew:\xe7b_}u0\xf3\xd4"\xc6\xd4i1\xebL\xa5X)\xe9Į\xc8^J\x9e\x83\x9c`N\xd7gE \x82j
p&\xd3\xc3\xc82\\x99\xb0\x81\xa5SN\xe8\x96\xd1\xac\xbeI\xab\xcc\xee\xa20\x91\x94\xc9x\xe7mX:o\xde)
\xc10hK\xe4\x902M\xf5\xf0\xb9d\x8b!5\xf3\xa4\x88#\x85\xbaz\xb8&Cx\xbah]\xed\xa7[i\xcf\xd5w\xab\x87Y\x8d\xfc~M \\xb1\xd6\xe1>6t2\xc1M\xb6\xa4\xe0l \x84\xff \xd1\xda\xa1\xa2\xf4z[^,
\xe5\xef\xa6ҚN\xf2\x8d;\x96u\xe2\xfbw\xb5u6\xa9\xeb\xcdOab
Mi\xf9u\xf9d=F\xe1\xb3PLV\xea\xd7%?\xadS^\xaa:\xaa\xbd\xd1# \x8bx9\x96kw\xf6a:\x99\x9e\x9f\xcc\xdb]\x81\xccb\xe5)m𜔭~j\xb7\xaa\xd7p\xd4\xcc&\xcd\xeasz)\xb2s%c\xfb\xd9\xf6\x8b\x9e\x99l\xbe6\xeeg\x8d\xed~\xf0?8\x96\xaf\xe5\x868Gi\x93$\xf2\x95\xf5`\x9e$\xb2\xf5\xe0\xe0M\xf5#\xb0\xc2G\x91\x8d\x9e?\x82l\xb4\xdb"\xeb\xcf/\xe6\xdci\xea\xceX \xa6g6\x96\xe3f)\xda\xc8\xf7/lnęmR|\xda+\x8c\xbd\x97;\x8d\xd4\xfasQ\xa1\xe7\xa2!\xdd\xdb}\xaa\xdbiYʐ\x97\x99sȜ\xa20\xee\xa2F;Ph@\xd2?\xa6#\xe2VmL\x92M#\xba\x8d\xa4\xe5\xfb\xfe\xe5\x93_PK    &J5\\xf6)Jl\xf4      chrome_extension/vagas_bot.jsUT	 \x98\x99pi\x98\x96piux \xe9  \xe9  }U\xdbn\xdb0}\xcfWƀ\xd8@\xab{\xec\xd0K\x91\x87\xbbw\xdd\xcbP\xac\x8cL\xc7Z\xc9ӥ]V\xf8c\x86}Jl\x94\xd3ܜ\xb4~\xb0-\x93:"i5k\xacp^5\xa0\xedZ\xa8\x9c\x9d\xc1PŠ\xb4?\xfd\xf0\xc5`@\xbf;O\xf4s#\xa1\x8aFe\xb8h\xbe\xe1\xfdȆ\xbc\x80\xbb\xf0\xc5y\xf6\xc6(\xa9Д\xd8\x9d\x8f\x90v&\x84Ȋ\x9d[w;:\x82\xb3\x9a\xe45\xa8
n	\xd00*\x82't\xb2\xad|\xe8\xfc؜\x97V\xc6\x99 ~Er\xf3s\xd2$\x83u\xf9P\xdc0\xfa\xb0X\xbf
\xe1oF(	\x92\xdd\xf3K\xe0X\xe2*\x82tIk| \x89\xae\xf4p
\xfb\x8fx\xad\xf5\xea\x94\xfe\xce\xe8t\xda\xf8\xfdrmX{$TQY7FY\xe7i\xa7/7\xa2\\xa3he\xae%\xb9\xf4\xb3C\x91\x8c\x87=\xea\x9a\xfca?\x8c%;ɫ\xe8\x81?0\xbcbl\xc8@\xf4\xe4\xc1\x91Ơn.\xbe\xbc\xf3`\xd7T\xebn\xb1\x91rM\xf4uw\x88\xa8U\xbd \xdaժ-\xf6\x91\xe2\xeb@4\x99i\xa8\xe1%\xf7CM\xbb:\xb3\x9a\xd3,\xad\x87gw\xfemǏ067M5\xe8*\xa5\xbb\xf26\xceJ\xf2S\xe1,\xec\xaa\x9c\xacY\xce$X\xaaA\xf1ӓ)\xdf'\xff)\xe5\xbbta\xa7\xeb\xc8>_\x8c/\xc6?\xde~\x9dg{9\xe9\xee\xdb4@\xee\xc87\S*vk\xbd\xcas\x84\xf2z\xeal4%,\xdcK\x8a'\x9c\xf3r\xef+\xc1\xcaѷ\x90o~\x94\xbc#\xb4`\xa9\xfd<7\xa9o\x81\xb4\xa7=g\xc8\xd4q\xb6P\x96_p\xcc\xf8VO\xb4\xdb\xdc\xc1bI\x9d+3\xd5o\xed>1\x91\x9b\xa6E?\xb3\xea!;\xe3b\xa9\xbaCOLb\xd6\xf4\x9bF\xcfG\xc1<\xda}\xf9p\xb1\xef\xbb\xe1
\x9ff\x93\xb0D\x8d\xb3Kn\xd8/\xb8%\xf0>\xa5e<\x94\xee\xff٤\xb9F{\x8c\x8fNhBj%\xaf\xf3\xbe\xf5UX\xcc\xd0\xfc\xf9\xf1\xf1qϼ\xb5`\x8a\xdeT\x80\xda\x96\xf3WQ\x99\xd0G\x99t\xbc\xd3\xd9+Z&\xb6\x9ce\xb9\xaf\xf4;\xf0\x9bԱ$\x9fg\x8c\xb0\xa0P\xab?<\xe6\xb2b\xdf8\xe8\xb2\xdf\xf4\xe7\x8c+\xe5f\xfd\xb9\xb8\xad\x83\xbdr\xe2Dޫi`B\xfdt\x9e"|\xf3p\x93\xbe\xa9\x92\x93S\x95\x92\xcc;\xd8؍k\xf8y\xff\x97\xc1t\xfa\x88O\x89\xf3!\x90s55\xa89\x99Y\xc3#$\xfd\x99rۤ'\xea\x98\xac\xdbMj\x9b\x86\x9a\xf9-΋\x85\xbc\xed\xe0?PK    xH5\\xfc\xfd\xe2\xe2z   \x9f     chrome_extension/utils.jsUT	 t\x96pit\x96piux \xe9  \xe9  ]\x8cA
\xc20E\xf79\xc5,\\xb4 ^@*\xf4.܉P(\xdfH2a2\xb1J\xe9\xdd\xdd\xf8\x97\x8f\xffޙE\xe9YӨ\x9e\x95 \xe4&\x96\x96G6\x81VI\x940\xd3U8\xfa\x82FP8\xbc@݅
\xf4\xe6#\xb8\xeaN\x8fdn{v\xabs\xf8K\x9e,<\xed呓8\xfd\xf0p\xef\xabr\x9fs\xf8<\xe8\xb0\xd8k\xb6\xc8PK    /J5\\xa9Z˿t  \xed     chrome_extension/infojobs_bot.jsUT	 \xa9\x99pi\x8e\x96piux \xe9  \xe9  \x85T\xcdn\xdb0\xbe\xfb)\xb8\xec`gX\x9d`נ\x876\x87\xa1@\xf7t\xd8e(Y\xa6%\xb2\xe4Jr\xb6\xa0\xcd\xc3;\xf4A\xfcb\xa3\xed\xc4q\xe2\xa4\xd3\xc1\x90%\x92\xdfG\xf2\xa3D\x96k\xe3\xe0\xacD\xcc?\x82\xd43\xd8@jt~8*\x9c\x906\X\xe2y\xf8\xa7\xb6dv\xad8\xa4\x85\xe2Nh\xa6Pw*\xd5\xdb[\xed\x82!<{@\x8b\xc2\x83;%\xb8`*\xd1@W\xb07\xc3p0\x9c\xd4V\xf5g4\x82{\xad\x97\x90jn\x8e\x901\xa1\xe0&\xcf\xe5\xe2\xc29\xadj+\xae\x95%\xf0\xea\xf8\xd6)\xb8\x86D\xf3"C\xe5§\xcd\xfa%r\xa7M\xe0ۨ6\x8bV\x8c3\xc5\xd7\xfep4\x91B\xb0\x8f\xb2'{zrɬ\xbdօ눏\xfcDXKL\xfca׭͕2,\xffjH4	s\x85a\xf4KNB
Ǩ\xba\x80\x9b1X\x94[JD
\xce֖b\xbf\x92\xa3:\x9cm<\xefgZ\xf9U%\xc5\xa6;$f\xae,v\xcaZ\xadN.\x82/\x83\xee\xcdo&\\xd3\xee\xe0\xd3x<\xee\\xb5\xea\xc9\xb3\xae\xdbas\xe4"\xec\xaeĐ\xbd	&@}\xaa-\x94\xc8st\xads\xd3*\xfa\xa6\xc2dD᡹\xa3g﹓\xe3q\x94Ͽ0\xeb\xd0|g3\x8c\xf8\x94JO\xb6Q\xc1k1\xfcl\xba\xc9ة\xfa\xc0\xef'\xbe7\xd2jH\x99\x941\xe3Kpf\xa8\xd0ty/
\xa2E\x9c9\xb3x\x91\xec\xe7\x9d\xd7e\xb2\xec\x97H>\Z\x83G\xff\	OS\xc4~I^^\xfa\xd0gbU\xe2<؝\xd5ߴ\xb9\xae\xa5\xd1Q\xe0\x89*v\xc4v\x81\xfa\xda\xf8\x8f>h\x8d\xa3Z	R2(ݎ\xf8\xbb.\xe6PZ<\xe1L\x9bΑ7SO!\xa9-\x9f
a\xb0*\xf9\x91i\x95\xfc\xc5a\xaf]\xaf(H֟˖\xedW\xe4hm\xb95B7X!|\x83\x98\x9e$U\x8dln\xaft\x8cj\xce,\xd0+G\xdb\xa5\xa6\xca\xd7\xfe\x80\x9eM\xa7\x85\xea<\xbb\x86\x94\xaf\xd5A\x8dD0\xa4iCoA?\xaaw\xbc롼\xf1Ȝ\xc4\x85\xd61\xc8\xcb-ez\xe0\xbf\xf16\xde?PK    \x83H5\\x8f\xa0g\xc2.  \xb1     chrome_extension/linkedin_bot.jsUT	 \x85\x96pi\x85\x96piux \xe9  \xe9  \xb5X_o\xb9\xf7\xa7\x98
\xc5i\x85\x93ֺ }\x89\xab\xc7i\xd8>#\xce\x82 G\xedRc\x8aܒ\9\xaaO&\xb8\x87{\xea\xa7\xf0\xeb\xb9ZQ\xab\x95zA\xdb}\xb0\xa4\xe5p8~\xf3\x9b\xa1Ţ\xd0\xc6\xc1#\x94\x96\x9b[\xa3\xa7BrX\xc3\xd4\xe8t\xd3Sz\xfb\xa9\xaf\xd3϶{v"6\xac\xe4\xbc\xe8\x83ԳX\xde	i\x83\xe0	\xff\xe2%\x99]\xa9\xa6\xa5ʜ\xd0
L\xa9\xae\x84\xba\xe7\xf9\xa5z\xa9]҃\xc7\xc0\xd5$\x9dK%2\xc1T\xae\x97`#\x96\xa6i\xa7w\xe6\xa5\xfc\x9f\xd3Sx-T\x9f\xf52frB\x81\x9bs\x90|\xea\xc0\x8a\x9cO\x98\xf1\x92\x99V֑\x9c\x85\xe4:+\\xb9\xf4%7\xab;.y\xe6\xb4K\x99tS\x90\xaa\xeepL(n\xbaՉb
	)H%W37\x87\xd1hÍѵ\xe17\\xcd\xcb\x83%\x9b1\xe0\x8a\xb4\x963P\xa4\xb0\xff2\xc7\x93)\x9cs\xe3\xc4T\xa0\xcb!\xe7\xc0qِ`\xf1\xf4u&\xf0\xdfMJ\x9b\xf9/\xa4\xcf\xd6\xde\xd3c\xb8+\x8d
\xbf\xd7'\xfec\xaa$\x92{GAO\xbd\xbf\xb1\x85\xaf\xbb\xcch)\xc1i/\x83\\xd9\xd2p\xedg\xb9\xadeq9\xb5^\xf8R9\xfdN\xf0\x87\xe4&|ΖB\x9b\xe7е\xadݼۇ\x89\xd4\xd9=\xbe\xc80\xa2-XG6\x92\x92L\x8a\xec>\xe9\x9d\xc1n\xa0\xdeQ\x80h\xa3\xd36+1\xe8>\xe1}\xc3g\x8c\xa4\xa3\x84\xd3\xc3\xda\xe9\xe1\x96<\x87\xa44v\xee|γ{\x85\xc4\x8c\x8bB\xae0\x84\xceiU\x8b$0Zz\xe9\xd4A4(؁\x83\x81ӅGG72\xaa\xfeB \xd9荣^\xbb\x8cP~\xfaM\xc39\xba)r\x86\xd9cp\x87E$\x85-\\xf4\x8e\xd7\xde\xf3Jo\xcd\xdd\xd5(.?\xfc\x85ⲳ\xbc\xf3\xc3\xf4w4 k\xfbZ\xe7L\xb6\xe8\x99\xfbe\xbf\xb4.\xa8\x87\xfdB\x94tM\x91\xc0\xd6?\xd0e\xa8\x90\xcfO_ѷ\x80\x82\xa7\xd7\xfb\xf1\xdd\xf1rX{\xb9޲\xc6k\xb1\x80|Sh\x9b\xa2\x81\xa5\xb0O\xffZr\xcaK\xa5\xc1C;\xfenH\x8bh\xc1\xbe\xdc9^c<\x9eQ\xe0n_"R\x90e\xa6B	\x87<\xa3ua\xeb\xa5Qxx@\xf90'M\x8e㋣1\xc8dA\xb7\xdf}4\xfd\xb5\xb6 F-}\xff}\xfcо\x97\xa6\xb6\x81\xf5 ^rcl[\xa5\xc4\xd0\xac\xf2份(A\x91\xe2_\\xa8\x99Je\x8aaȓ	\x8c~\x84I*\x92\xe5[\xc1o\x99,sn\x93\xeex\xc9\xd4\xd3\xef9~\xfd\xf5\x80\xcc\xfel9C\x8d\x9c\xf3mǽ\xc1=\xf6\xf8io\xbcږ\xf3l9Y\x88ot\xefB-Rv\xb6E\xfd\xb1\xa3\xef\xfc	\xbe\x94\xef=oF\x9c\xc0\xd7\xb9\xf9R\xa5\xb3\xd8cەa!\x89\xf7\xe7Ԗ\xb7\x92\x8e\xb71\xf0jme\x83V\xab\xc3k=[\xcaƷ?ߜ\xfft}}q\xf3\xde\xfe\xe3\xf3\xb7?\x8f\xaf\xae\xde\xc3\xf8\xf6\xf6\xea}S\xc1>=\xa5\xa1s\xa9\x91O<\xea\x81M\xb1wT@RڒI\xa4\xee\xce+\xadx\xa7J\x8e3c{;zB\xf22Ru\x9c΃\x92\xcc6\x90l\xc2\xe5\xa8\xf3J؅\xb0\xb6\xf3\xb1۰TL\x93\x8d\xc6^\xad\xbb\x9dz\xe3.L\xcfz릧KJP\xe5\xd6\xd0b\x86Z\xb2R\xef\xfcf\xde_\xef\x9bQ\x95o\xabU\xa1\xb6[Qm\xfc\x9f\xf4\x9em\x8b\xe6\xc6hc\x91E
\x87<\x96\xa3\xef52q\x84@\x99q9\xcf\xf4@(\x89\x83\xda`\xcay>a\xd9\xfd`\xe0Ucq5<\xad\xbd\xbd\xc0u<\x93\xccX\x94\xf2\xe9\xabԽ\xea\xa5\xde\xb7\xa5\xf4C\xedc/\xf4\xfc_@\xdc\xfd\xc3\xc0k\xc6~?\xf4\x91\xa5\x96Y\xe0\xd14\xbc|\xc1\xbd\xe2\xb4\xc3\xa7\xd4J\xed\xa7\xc6\xf9\xdb=\xbdװ\xe6\xb0w\xcdҢgZ\xcb8B|\x85h-0\xfc<\xc7V\x89\xb36 \xd4>\x97\x8aUS\xf8N/\xb8ni\xfeu\xec\xbf0d$J\xa5\xc7\xe8\xa6u\xe2\x9c\ȝ\xfc0\xf4\x87-\xe5\xb7n\x996b"\xaf\xacGC~H\xe1\xcb\x86U\x87\xe4=\xb7\xa77\xba\xdd^	\xfc\xcd\xe8\xb2\xf8\x97\x98\x9dɂp\x8e\x97o\xc0\xa7O3R!\xd4l@kG\xf8%\xba9Dg5/4\xd6q\x98\xf3\xd2\xe0\x98%\xb2\xe7\xc0\xe4[Y?\xcb\xdf\xfb\xdbfwcn\xc4\xe5\xe8P\x87\x92\x8134\xe8\x82L\xe9\xc5zǘol\xe3KxХ́)&W\xff\xe4\xe1:G\xa5\x8e`ל\xe8
\x87\xb7\xbc%\x82B\xfd\xc1\xad
>\xeax\xe1\xdd\xc2\xf3\xf4\xecul\xaeu?\xee^\xea*\xebm\xa146$\x88\x89\xd6\xe6+\xc8\xe8=\xcf\xdbZRXٝ\xba\xc2Q\xbd\xd4"\xc4Cug\xd2Jp\xafA\xf2\xa7\xcdR\x8f\xa1M\xaf\x90\xb1\xcc\x99\x8fHMd0a\xcfC\x88m\xc3\xf5\xda6\xbe\xc6,\\xbf\xbb\xed樓\x9cK4\xb6b]\xccs\x97\xd2\xd5żu{mj\xaa`ٔSJ\x83\xbb\xe1\xe4tO\xf8\x90J?\xf4ᚙ\x8cK\x8d\xf5\xa9\x9c\xaf4V:\xbd\xc0Z\xeb\x83\xd54Ww-\x92\xf3\x94\x95\xd2\xd1j\xa1\xadpb\xc9O\xbd\xc9\xfbg\x85~l\xb9xn\x9eƠ\xd2;\xc81\xf1\xe5m~\x96q_5\xa1Ar;ǈ\xf5\xe1\\xb8U\xb8\xcb\xe2j\xa5\xf0WrG\x8b5(\xed\xe9|\xecC\xfcN\x95\x8b	7[\xd4F\xd5\xeaŨZ\xb7g\xc5P\xf1\xf22\xe9\x92ɒ7a\x94\xb0\x8c\x82\xb2{\xf1\x8bC\xdd\xec/\xfau\xfe\xfc\xb8\x91_w>\xfe\xd2{5\xa7\xaf\xf47\xe7\x88Fd\xb8\xe7\xd0\xe9\x99\xc8\xc6 \x9a\xba\x9ft
\x8aj\xc77\x9c\xe6\x92C[\xa6WFعM\xa7\xb5\xf1#\\xb8\x8f\xd1]\xe1o~?\xfe_WZpc5\xb2N\xeah\x82b;G\xed\x8b\xe9?`\xce\xdb9\xff\xaf\xed\xa1b\xb4\x82\xe68ϱq\x9c\xa7\x91\xf2\x91ܑ\xa2,n<\x8f\xc8)jJQ;j3c/\x84'\xfe\xf3,Zȅ-\x98\xcb\xe6A\x81\xe2\xbedw\xfb\xf0\x88mt2\x91\xdc>gP\xc7z3(\xfc\x87\xfd^\xccg\xfc\x90\x82\xf5ɿPK    nH5\Xn\xceF  '    chrome_extension/popup.jsUT	 _\x96pi_\x96piux \xe9  \xe9  e\x91\xc1J1\x86\xef>\xc5\xcf^vJ깢B\xa1\x87\x82"\xe8\xc1\x83x\x88\xc9\xec6u\x9b\xd4\xc9lK)}\x9f\xc53\xdb]\xa5\xd5\x92!\x99\xf9\xf2eb\x83iW\xe4E\xd5$\xb3\x86\xbap\xba\x9b\xdb"\x8f\xa2Y\xa6\xe2\xf3Rikg\x9btp碐'.r\xd38\xf3\x9e\x8fP\x94\xb8\xbe\xc1\xfei\x98\x87)\xd1oQ}\xb4Ļb\xaf\x8d\xb8M \xdc\xd2\xa6eN\x94g\xe7m\xd8\xf6\x9b\x87\x84\xe8
N0\xc0x\x8c'\xf2+\x8aQ\xd7	\x90\xa1\xc7!\xe4&\xf8$#\x88\x86\xddZ\x86\xd2S\x87\x98\xf7=\xe0x\xc7\xcb\xe5\xabrv\x84\xa3U\xf0d\xc7'f\x9dS\\xe9\xccp\x8aɭ\x97\xd6FG\x991.O\xf2~\xb4\xe7\xd5-\xb8\xe8sA\xb4%\x8b
R\xb5\x82\xa7m\xf7\x8cr\xe7\x97dR\x9e\xa0r\xe5\xff\xa0\x8ceBM\x836w\xed`\xaa\x92\xf3B\x9dg\xeb\x86X\x8a\xac\xf3\x9b\xe0\x91\x8cN\xaf\xdb\xd48\xac\xbf>k\xe75R\xf7\x92\xc1\x87\x8d\xee\xfe\x9aTV^\xfdBCt\xf6\xfa\xb5\x9b\xbfPK    \x8fH5\Kքt  R  "  chrome_extension/content_router.jsUT	 \x9e\x96pi\x9e\x96piux \xe9  \xe9  \x8dRAN\xc30\xbc\xf7\xab\\x92J\xc8܋\x82\x88C\xa5ri+8"7޴.\x89\xb7x\x9d\xa9\xcakx
\xc3nk\x94B@\xf8\xb2\xd6zfv\x92Y]o\xc8:؃m\xccD\x9bTcsKZ(-Ր\x8a\xcb\xea\xd0\xd5\xe6yAN\xac9\xbd\xe8glJZӂ\xcf9\xfa\xd4\xed\xe7<ʥ\xfcF؆V\xba\xa2e\xd58]\xf11\xf0/Yr\xff\xe6а&\x92
\x95\x80'\xa9\x9d6K(\xc9;\xe9E
\xaaki\x94"z^\xb1\xf2b(\xbc\xa7}%\xf3\x80\xccr\x89B*5\xd1\xec\xf5\xd0f\x99\xc5\xd7\xd9] \xa3Qh\x8fu\x8a\xbc!\xc38\x84\xfc\xf6\xf0G\x97\xb1B.8\xc9\xf3\x92\xc3\xe8dxB\x85s\xf0{w\xf4\xd4[T#\x98\xcdo\xa6\xf3`,\xe2\xbe.\x85\xe5`E쌬r\xd8i\xa3h'**d$\xe2\x93\xff\xa8\xc8	vb[hST\x8dB\xce\xd2\xa1\xf0\xff"v]\x85s\x9e|\xd6\xf1\xd2V\x8c\xbf\xa9Ɛ\x83\xaaX\xd8^\xe1\xcez\xfc_\xf8\xb0\xa9\xc6\xea\x91<\xc7\xca
\xad˒\x99v\xe6㝀\x9b\xb0XR\xf8
>5\x84\xb0t\xdd ڟQt\xc3\xcf\xf6>[\xd7\xf0\xe82\xaa\xa4=\xb1\xdbA\xb8}PK    \xdcH5\\x96f\x8d6h   |     chrome_extension/loader.jsUT	 /\x97pi/\x97piux \xe9  \xe9  \xd3H,\xae\xccKV\xd0\xd0T\xb0\xb5S\xa8\xe6R \x82\xe4\xfc\xbc\xe2\x85\xe2\xa2d[\x85䌢\xfc\xdcT\xbd\xa2Ҽ\x92L \x9d\x9eZ䣡TR\x92\x9aW_\x94_Z\x92Z\xa4\x97U\xac\xaei\x8d\xa4*훘\x994#\xb1<1\xb3D!3\xb7 \xbf\xa8Dh,Pi\xad\xa6\x90 PK
     J5\                     \xfdA    chrome_extension/UT \x87\x99piux \xe9  \xe9  PK    J5\ )\xfd]\xae  &           \xb4\x81K   chrome_extension/background.jsUT \x87\x99piux \xe9  \xe9  PK    J5\[\xe2\xee\xe1Z             \xb4\x81Q  chrome_extension/manifest.jsonUT s\x99piux \xe9  \xe9  PK    kH5\\xc8\xd5k-  q           \xb4\x81  chrome_extension/popup.htmlUT Z\x96piux \xe9  \xe9  PK    rH5\}\x95?\xdcW  \xc9            \xb4\x81\x85	  chrome_extension/user_profile.jsUT g\x96piux \xe9  \xe9  PK    &J5\\xf6)Jl\xf4             \xb4\x816  chrome_extension/vagas_bot.jsUT \x98\x99piux \xe9  \xe9  PK    xH5\\xfc\xfd\xe2\xe2z   \x9f            \xb4\x81\x81  chrome_extension/utils.jsUT t\x96piux \xe9  \xe9  PK    /J5\\xa9Z˿t  \xed            \xb4\x81N  chrome_extension/infojobs_bot.jsUT \xa9\x99piux \xe9  \xe9  PK    \x83H5\\x8f\xa0g\xc2.  \xb1            \xb4\x81  chrome_extension/linkedin_bot.jsUT \x85\x96piux \xe9  \xe9  PK    nH5\Xn\xceF  '           \xb4\x81\xa4  chrome_extension/popup.jsUT _\x96piux \xe9  \xe9  PK    \x8fH5\Kքt  R  "         \xb4\x81=  chrome_extension/content_router.jsUT \x9e\x96piux \xe9  \xe9  PK    \xdcH5\\x96f\x8d6h   |            \xb4\x81  chrome_extension/loader.jsUT /\x97piux \xe9  \xe9  PK      \x9b  \xc9    
```

## docs/index.html
```
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Hub de Vagas Automático</title>
    <link rel="stylesheet" href="assets/css/style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <header>
        <div class="container">
            <div class="logo">
                <i class="fas fa-rocket"></i> Hub de Vagas
            </div>
            <nav>
                <ul>
                    <li><a href="#projetos">Módulos</a></li>
                    <li><a href="#download">Download</a></li>
                    <li><a href="#docs">Documentação</a></li>
                    <li><a href="https://github.com/marcelinmark/hub-de-vagas" target="_blank" class="btn-github"><i class="fab fa-github"></i> GitHub</a></li>
                </ul>
            </nav>
        </div>
    </header>

    <section class="hero">
        <div class="container">
            <h1>A Revolução na Empregabilidade</h1>
            <p>Uma plataforma autônoma que gerencia sua carreira, aplica para vagas e prepara você para entrevistas. 24 horas por dia.</p>
            <div class="hero-btns">
                <a href="#download" class="btn btn-primary"><i class="fas fa-download"></i> Baixar Extensão</a>
                <a href="#docs" class="btn btn-secondary">Ver Documentação</a>
            </div>
        </div>
    </section>

    <section id="projetos" class="features">
        <div class="container">
            <h2>Ecossistema Completo</h2>
            <div class="grid">
                <div class="card">
                    <i class="fab fa-chrome icon"></i>
                    <h3>Extensão Multi-Plataforma</h3>
                    <p>Automação de candidaturas para LinkedIn, Infojobs e Vagas.com diretamente do seu navegador.</p>
                </div>
                <div class="card">
                    <i class="fas fa-robot icon"></i>
                    <h3>Bots Selenium 24h</h3>
                    <p>Robôs autônomos que operam em servidores (AWS/Headless) simulando comportamento humano.</p>
                </div>
                <div class="card">
                    <i class="fas fa-brain icon"></i>
                    <h3>Inteligência Playwright</h3>
                    <p>Arquitetura escalável com banco de dados SQLite para gerenciar milhares de aplicações.</p>
                </div>
                <div class="card">
                    <i class="fas fa-chart-line icon"></i>
                    <h3>Dashboard 360</h3>
                    <p>Painel de controle em tempo real com métricas, estratégias e monitoramento de networking.</p>
                </div>
            </div>
        </div>
    </section>

    <section id="download" class="download-section">
        <div class="container">
            <h2>Comece Agora</h2>
            <p>Baixe a extensão para Google Chrome e inicie sua automação de candidaturas.</p>
            <div class="download-box">
                <i class="fas fa-file-archive"></i>
                <div class="info">
                    <strong>Marcelo AutoApply - v2.1</strong>
                    <span>Extensão para Chrome (ZIP)</span>
                </div>
                <a href="downloads/chrome_extension.zip" class="btn btn-light" download>Baixar .ZIP</a>
            </div>
            <p class="note">Para instalar: Extraia o arquivo, acesse <code>chrome://extensions</code>, ative o "Modo do desenvolvedor" e clique em "Carregar sem compactação".</p>
        </div>
    </section>

    <section id="docs" class="docs-section">
        <div class="container">
            <h2>Documentação Técnica</h2>
            <div class="doc-links">
                <a href="AWS_SETUP.md" class="doc-card">
                    <i class="fab fa-aws"></i>
                    <span>Guia de Deploy AWS</span>
                </a>
                <a href="CODIGO_CONSOLIDADO.md" class="doc-card">
                    <i class="fas fa-code"></i>
                    <span>Código Fonte Completo</span>
                </a>
                <a href="SYSTEMD_SETUP.md" class="doc-card">
                    <i class="fas fa-server"></i>
                    <span>Configuração Systemd</span>
                </a>
            </div>
        </div>
    </section>

    <footer>
        <div class="container">
            <p>&copy; 2025 Hub de Vagas Automático. Desenvolvido por Nome Sobrenome.</p>
        </div>
    </footer>
</body>
</html>

```

## scripts/login_seed.py
```
from pathlib import Path
from src.core.auth import interactive_login_and_save_state

interactive_login_and_save_state(platform="linkedin", login_url="https://www.linkedin.com/login/pt", state_path=Path("data/sessions/linkedin_state.json"))
interactive_login_and_save_state(platform="gupy", login_url="https://login.gupy.io/", state_path=Path("data/sessions/gupy_state.json"))

```

## src/__init__.py
```

```

## src/core/__init__.py
```

```

## src/core/auth.py
```
from pathlib import Path
from playwright.sync_api import sync_playwright

AUTH_DIR = Path("data") / "sessions"
AUTH_DIR.mkdir(parents=True, exist_ok=True)

def interactive_login_and_save_state(platform: str, login_url: str, state_path: Path):
    state_path.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context()
        page = context.new_page()
        page.goto(login_url, wait_until="domcontentloaded")
        print(f" [LOGIN] Faça login manualmente em {platform} e depois volte aqui.")
        input("Quando terminar, pressione ENTER para salvar o state...")
        context.storage_state(path=str(state_path))
        context.close()
        browser.close()

```

## src/core/browser.py
```
from pathlib import Path
from playwright.sync_api import sync_playwright

def _route_block_heavy(route):
    rt = route.request.resource_type
    if rt in ("image", "font", "stylesheet", "media"):
        return route.abort()
    return route.continue_()

def open_context(headless: bool, storage_state_path: Path | None):
    p = sync_playwright().start()
    browser = p.chromium.launch(headless=headless)
    if storage_state_path and storage_state_path.exists():
        context = browser.new_context(storage_state=str(storage_state_path))
    else:
        context = browser.new_context()
    context.route("**/*", _route_block_heavy)
    page = context.new_page()
    return p, browser, context, page

```

## src/core/db.py
```
import sqlite3
from pathlib import Path

DB_PATH = Path("data") / "autoapply.db"

def init_db():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS jobs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                platform TEXT NOT NULL,
                job_url TEXT NOT NULL,
                title TEXT,
                company TEXT,
                location TEXT,
                score INTEGER DEFAULT 0,
                status TEXT NOT NULL,
                reason TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                UNIQUE (platform, job_url)
            );
        """)
        con.commit()

def upsert_job(platform, job_url, status, title=None, company=None, location=None, score=0, reason=None):
    with sqlite3.connect(DB_PATH) as con:
        con.execute("""
            INSERT INTO jobs (platform, job_url, title, company, location, score, status, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(platform, job_url) DO UPDATE SET
                title=excluded.title,
                company=excluded.company,
                location=excluded.location,
                score=excluded.score,
                status=excluded.status,
                reason=excluded.reason;
        """, (platform, job_url, title, company, location, score, status, reason))
        con.commit()

def seen(platform, job_url):
    with sqlite3.connect(DB_PATH) as con:
        cur = con.execute("SELECT status FROM jobs WHERE platform=? AND job_url=?", (platform, job_url))
        row = cur.fetchone()
        return row[0] if row else None

```

## src/core/export.py
```
import csv
import sqlite3
from pathlib import Path
from datetime import datetime

def export_daily(db_path: Path, out_path: Path):
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as con:
        rows = con.execute("""
            SELECT platform, job_url, title, company, location, score, status, reason, created_at
            FROM jobs
            ORDER BY created_at DESC
        """).fetchall()
    with out_path.open("w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(["platform", "job_url", "title", "company", "location", "score", "status", "reason", "created_at"])
        w.writerows(rows)

def daily_filename():
    return datetime.now().strftime("out/daily_export_%Y-%m-%d.csv")

```

## src/core/llm.py
```
import os
try:
    from openai import OpenAI
except ImportError:
    OpenAI = None

class LLMClient:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        self.client = None
        if self.api_key and OpenAI:
            try:
                self.client = OpenAI(api_key=self.api_key)
            except:
                pass

    def is_active(self):
        return self.client is not None

    def generate_response(self, prompt, system_role="Você é um assistente de carreira útil."):
        if not self.is_active():
            return None

        try:
            response = self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_role},
                    {"role": "user", "content": prompt}
                ],
                max_tokens=300
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return None

```

## src/core/models.py
```
from typing import List, Optional, Dict
from pydantic import BaseModel, Field
from datetime import datetime, date
from uuid import uuid4, UUID

class Experience(BaseModel):
    title: str
    company: str
    start_date: date
    end_date: Optional[date] = None
    description: str

class Education(BaseModel):
    institution: str
    degree: str
    start_date: date
    end_date: Optional[date] = None
    field_of_study: str

class Skill(BaseModel):
    name: str
    level: str  # e.g., Beginner, Intermediate, Expert

class CandidateProfile(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    name: str
    email: str
    phone: str
    summary: str
    experiences: List[Experience] = []
    education: List[Education] = []
    skills: List[Skill] = []
    linkedin_url: Optional[str] = None
    portfolio_url: Optional[str] = None

class JobOpportunity(BaseModel):
    id: str
    title: str
    company: str
    description: str
    requirements: List[str]
    url: str
    source: str # e.g., "LinkedIn", "Indeed"
    match_score: float = 0.0

class Resume(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    profile_id: UUID
    job_id: str
    content: str  # The actual text of the resume
    created_at: datetime = Field(default_factory=datetime.now)
    version_tag: str

class Application(BaseModel):
    id: UUID = Field(default_factory=uuid4)
    job_id: str
    profile_id: UUID
    resume_id: UUID
    status: str = "Applied" # Applied, Interviewing, Rejected, Offer
    applied_at: datetime = Field(default_factory=datetime.now)
    platform: str
    notes: Optional[str] = None

```

## src/core/persistence.py
```
import json
import os
from typing import Dict, List, Any
from src.core.models import CandidateProfile, Application

DATA_DIR = "data"
PROFILE_FILE = os.path.join(DATA_DIR, "profile.json")
METRICS_FILE = os.path.join(DATA_DIR, "metrics.json")
APPLICATIONS_FILE = os.path.join(DATA_DIR, "applications.json")

class PersistenceManager:
    def __init__(self):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)

    def save_data(self, profile: CandidateProfile, metrics: Dict[str, int], applications: List[Application]):
        """Saves current system state to JSON files."""
        # Save Profile
        if profile:
            with open(PROFILE_FILE, "w", encoding="utf-8") as f:
                f.write(profile.model_dump_json(indent=2))

        # Save Metrics
        with open(METRICS_FILE, "w", encoding="utf-8") as f:
            json.dump(metrics, f, indent=2)

        # Save Applications
        # Application contains UUIDs and Datetimes, need robust serialization
        # Pydantic's model_dump_json works for individual models, but for a list we need to handle it.
        # Simplest way for pydantic v2:
        app_list_json = [app.model_dump(mode='json') for app in applications]
        with open(APPLICATIONS_FILE, "w", encoding="utf-8") as f:
            json.dump(app_list_json, f, indent=2, ensure_ascii=False)

    def load_data(self):
        """
        Loads system state. Returns tuple (profile, metrics, applications).
        Returns (None, None, None) if files don't exist.
        """
        profile = None
        metrics = None
        applications = []

        if os.path.exists(PROFILE_FILE):
            with open(PROFILE_FILE, "r", encoding="utf-8") as f:
                try:
                    profile = CandidateProfile.model_validate_json(f.read())
                except:
                    pass # Corrupt or old format

        if os.path.exists(METRICS_FILE):
            with open(METRICS_FILE, "r", encoding="utf-8") as f:
                metrics = json.load(f)

        if os.path.exists(APPLICATIONS_FILE):
            with open(APPLICATIONS_FILE, "r", encoding="utf-8") as f:
                try:
                    raw_apps = json.load(f)
                    applications = [Application.model_validate(app) for app in raw_apps]
                except:
                    pass

        return profile, metrics, applications

```

## src/core/runner.py
```
import json
import os
import random
import time
import re
from pathlib import Path
from datetime import datetime, date
from rich.console import Console
from src.core.db import init_db, seen, upsert_job, DB_PATH
from src.core.export import export_daily, daily_filename
from src.core.browser import open_context
from src.core.sources import enqueue, extract_gupy_links
from src.drivers.linkedin_easy_apply import process_job as li_process
from src.drivers.gupy_fast_apply import process_job as gupy_process
from src.modules.notifications.telegram_bot import TelegramBot

console = Console()
telegram = TelegramBot()

PROFILE_PATH = Path("profile_br.json")
QUEUE_PATH = Path("data") / "queue.jsonl"
STATE_LI = Path("data") / "sessions" / "linkedin_state.json"
STATE_GUPY = Path("data") / "sessions" / "gupy_state.json"

def load_profile(): return json.loads(PROFILE_PATH.read_text(encoding="utf-8"))

def count_applied_today():
    import sqlite3
    today = date.today().isoformat()
    with sqlite3.connect(DB_PATH) as con:
        row = con.execute("SELECT COUNT(*) FROM jobs WHERE status='applied' AND substr(created_at, 1, 10)=?", (today,)).fetchone()
    return row[0] if row else 0

def read_queue(limit=200):
    if not QUEUE_PATH.exists(): return []
    lines = QUEUE_PATH.read_text(encoding="utf-8").splitlines()
    items = []
    for ln in lines[:limit]:
        try: items.append(json.loads(ln))
        except: pass
    return items

def main():
    init_db()

    if not PROFILE_PATH.exists():
        console.print("[red]Erro: profile_br.json não encontrado![/red]")
        return

    profile = load_profile()
    headless = os.environ.get("HEADLESS", "1") == "1"

    console.print(f"[bold green]Iniciando Hub de Vagas Runner[/bold green] (Headless={headless})")

    # Enqueue seeds
    console.print("[cyan]Carregando seeds...[/cyan]")
    for url in profile.get("seeds", {}).get("linkedin_search_pages", []):
        enqueue("linkedin_search", url)
    for url in profile.get("seeds", {}).get("gupy_search_pages", []):
        enqueue("web_discovery", url)

    meta_daily = int(profile["preferencias"]["meta_candidaturas_dia"])
    applied_today = count_applied_today()
    remaining = max(0, meta_daily - applied_today)

    console.print(f"Meta Diária: {meta_daily} | Já aplicados: {applied_today} | Restante: {remaining}")

    if remaining == 0:
        console.print("[yellow]Meta diária atingida. Gerando export e encerrando.[/yellow]")
        export_daily(DB_PATH, Path(daily_filename()))
        return

    windows = 10
    per_window = min(max(1, remaining // windows), 6)

    try:
        p1, b1, c1, page_li = open_context(headless=headless, storage_state_path=STATE_LI)
        p2, b2, c2, page_gupy = open_context(headless=headless, storage_state_path=STATE_GUPY)
        console.print("[green]Browsers iniciados com sucesso.[/green]")
    except Exception as e:
        console.print(f"[red]Erro crítico ao iniciar browsers: {e}[/red]")
        return

    try:
        for w in range(windows):
            if count_applied_today() >= meta_daily: break

            queue = read_queue(limit=400)
            if not queue:
                console.print("[yellow]Fila vazia. Aguardando...[/yellow]")
                time.sleep(5)
                continue

            random.shuffle(queue)
            applied_in_window = 0

            console.print(f"\n--- Janela {w+1}/{windows} ---")

            for item in queue:
                if applied_in_window >= per_window: break
                platform = item.get("platform")
                url = item.get("url")

                if not url: continue
                if seen(platform if platform in ("linkedin", "gupy") else "source", url):
                    continue

                console.print(f"Processando: {platform} - {url[:50]}...")

                try:
                    if platform == "linkedin_search":
                        page_li.goto(url, wait_until="domcontentloaded")
                        page_li.wait_for_timeout(2000)
                        found = set(re.findall(r"https://www\.linkedin\.com/jobs/view/\d+", page_li.content()))
                        console.print(f"  > Encontradas {len(found)} novas vagas.")
                        for m in found:
                            enqueue("linkedin", m)
                        continue

                    if platform == "web_discovery":
                        page_gupy.goto(url, wait_until="domcontentloaded")
                        page_gupy.wait_for_timeout(2000)
                        links = extract_gupy_links(page_gupy.content())
                        console.print(f"  > Encontrados {len(links)} links Gupy.")
                        for lk in links: enqueue("gupy", lk)
                        continue

                    if platform == "linkedin":
                        li_process(page_li, url, profile)
                        status = seen("linkedin", url)
                        console.print(f"  > Status: {status}")
                        if status == "applied":
                            applied_in_window += 1
                            telegram.send_notification(f"🚀 *Aplicação Sucesso (LinkedIn)*\n{url}")
                        continue

                    if platform == "gupy":
                        gupy_process(page_gupy, url, profile)
                        status = seen("gupy", url)
                        console.print(f"  > Status: {status}")
                        if status == "applied":
                            applied_in_window += 1
                            telegram.send_notification(f"🚀 *Aplicação Sucesso (Gupy)*\n{url}")
                        continue

                except Exception as e:
                    console.print(f"  [red]Erro no loop: {e}[/red]")

            sleep_s = random.randint(30, 60) # Reduced for demo/testing responsiveness
            console.print(f"[blue]Dormindo por {sleep_s}s...[/blue]")
            time.sleep(sleep_s)
    except KeyboardInterrupt:
        console.print("\n[red]Interrupção manual.[/red]")
    finally:
        export_daily(DB_PATH, Path(daily_filename()))
        try:
            c1.close(); b1.close(); p1.stop()
            c2.close(); b2.close(); p2.stop()
        except:
            pass
        console.print("[bold green]Execução finalizada.[/bold green]")

if __name__ == "__main__":
    main()

```

## src/core/scoring.py
```
def score_text(text: str, keywords: list[str]) -> int:
    t = (text or "").lower()
    return sum(1 for k in keywords if k.lower() in t)

def decide(score: int) -> str:
    if score >= 5: return "apply"
    if score >= 3: return "needs_manual"
    return "skip"

```

## src/core/sources.py
```
import json
import re
from pathlib import Path
from urllib.parse import quote

QUEUE_PATH = Path("data") / "queue.jsonl"
QUEUE_PATH.parent.mkdir(parents=True, exist_ok=True)

def enqueue(platform: str, url: str, meta: dict | None = None):
    meta = meta or {}
    with QUEUE_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps({"platform": platform, "url": url, "meta": meta}, ensure_ascii=False) + "\n")

def linkedin_search_urls(queries: list[str], geo: str = "106057199"):
    urls = []
    for q in queries:
        urls.append(f"https://www.linkedin.com/jobs/search/?keywords={quote(q)}&locationId={geo}")
    return urls

GUPY_RE = re.compile(r"https?://[a-z0-9\-]+\.gupy\.io/[^\s\"'>)]+", re.IGNORECASE)

def extract_gupy_links(text: str) -> list[str]:
    return list(dict.fromkeys(GUPY_RE.findall(text or "")))

```

## src/drivers/gupy_fast_apply.py
```
from src.core.db import upsert_job
from src.core.scoring import score_text, decide
PLATFORM = "gupy"

def process_job(page, job_url, profile):
    page.goto(job_url, wait_until="domcontentloaded")
    title = page.locator("h1").first.inner_text(timeout=3000) if page.locator("h1").count() else ""
    body = page.locator("body").inner_text(timeout=3000)
    score = score_text((title or "") + " " + body, profile["skills"])
    action = decide(score)

    if action == "skip":
        upsert_job(PLATFORM, job_url, "skipped_low_score", title=title, score=score, reason="score_baixo")
        return
    if not page.locator("text=Candidatura Rápida").count():
        upsert_job(PLATFORM, job_url, "needs_manual", title=title, score=score, reason="nao_rapida")
        return
    if action == "needs_manual":
        upsert_job(PLATFORM, job_url, "needs_manual", title=title, score=score, reason="score_medio")
        return

    btn = page.locator("button:has-text('Candidatar')").first
    if not btn.count():
        upsert_job(PLATFORM, job_url, "needs_manual", title=title, score=score, reason="botao_nao_achado")
        return

    btn.click()
    page.wait_for_timeout(1500)
    if page.locator("text=Teste").count() or page.locator("textarea").count():
        upsert_job(PLATFORM, job_url, "needs_manual", title=title, score=score, reason="perguntas_extras")
        return
    upsert_job(PLATFORM, job_url, "applied", title=title, score=score)

```

## src/drivers/linkedin_easy_apply.py
```
from src.core.db import upsert_job
from src.core.scoring import score_text, decide
PLATFORM = "linkedin"

def process_job(page, job_url, profile):
    try:
        page.goto(job_url, wait_until="domcontentloaded", timeout=30000)
    except Exception as e:
        upsert_job(PLATFORM, job_url, "error_load", reason=str(e))
        return

    # Extract info safely
    title = page.locator("h1").first.inner_text(timeout=5000) if page.locator("h1").count() else "Unknown"
    desc_loc = page.locator("div.jobs-description")
    if not desc_loc.count():
        # Fallback selector
        desc_loc = page.locator("article")

    desc = desc_loc.first.inner_text(timeout=3000) if desc_loc.count() else ""

    score = score_text((title or "") + " " + desc, profile["skills"])
    action = decide(score)

    if action == "skip":
        upsert_job(PLATFORM, job_url, "skipped_low_score", title=title, score=score, reason="score_baixo")
        return

    easy = page.locator("button:has-text('Candidatura simplificada')").first
    if not easy.count():
        upsert_job(PLATFORM, job_url, "skipped_external_apply", title=title, score=score, reason="externo")
        return

    if action == "needs_manual":
        upsert_job(PLATFORM, job_url, "needs_manual", title=title, score=score, reason="score_medio")
        return

    try:
        easy.click()
        page.wait_for_timeout(2000)

        # Robust Modal Handling Loop
        max_steps = 15
        for _ in range(max_steps):
            # Check for success/submit
            submit_btn = page.locator("button:has-text('Enviar candidatura')").first
            if submit_btn.count() and submit_btn.is_visible():
                submit_btn.click()
                page.wait_for_timeout(2000)
                # Verify closure or success message
                if page.locator("text=Sua candidatura foi enviada").count():
                    upsert_job(PLATFORM, job_url, "applied", title=title, score=score)
                    return
                # Assume success if modal closes or changes state
                upsert_job(PLATFORM, job_url, "applied", title=title, score=score)
                return

            # Check for "Review" (Revisar) which often precedes Submit
            review_btn = page.locator("button:has-text('Revisar')").first
            if review_btn.count() and review_btn.is_visible():
                review_btn.click()
                page.wait_for_timeout(1000)
                continue

            # Check for "Next" (Avançar)
            nxt = page.locator("button:has-text('Avançar')").first
            if nxt.count() and nxt.is_visible():
                # Here we could inject logic to fill phone number if error exists
                # For now, just click
                nxt.click()
                page.wait_for_timeout(1000)

                # Check for error blocking progress
                if page.locator(".artdeco-inline-feedback--error").count():
                    upsert_job(PLATFORM, job_url, "needs_manual", title=title, score=score, reason="erro_formulario")
                    return
                continue

            # If no buttons found, maybe we are stuck or done
            break

        upsert_job(PLATFORM, job_url, "needs_manual", title=title, score=score, reason="loop_ou_erro_modal")

    except Exception as e:
        upsert_job(PLATFORM, job_url, "error_applying", title=title, score=score, reason=str(e))

```

## src/main.py
```
import time
import random
import sys
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text
from rich.markdown import Markdown
from collections import deque

from src.modules.onboarding import OnboardingAgent
from src.modules.job_intelligence import JobScanner
from src.modules.profile_optimizer import ProfileOptimizer
from src.modules.resume_generator import ResumeGenerator
from src.modules.applier import ApplicationBot
from src.modules.interview_prep import InterviewCoach
from src.modules.decision_engine import StrategyEngine
from src.modules.monitoring import FollowUpAgent
from src.modules.networking import NetworkAgent
from src.modules.reporting import ReportGenerator
from src.modules.interview_simulator.simulator import InterviewSimulator
from src.modules.email_helper.generator import EmailGenerator
from src.modules.resume_improver.improver import ResumeImprover
from src.modules.market_trends.analyzer import MarketAnalyzer
from src.modules.skills_assessment.quiz import SkillsQuiz
from src.modules.negotiation.advisor import SalaryAdvisor
from src.modules.calendar.integration import CalendarManager
from src.core.persistence import PersistenceManager

console = Console()

class HubDeVagas:
    def __init__(self):
        self.persistence = PersistenceManager()
        self.onboarding = OnboardingAgent()
        self.scanner = JobScanner()
        self.optimizer = ProfileOptimizer()
        self.resume_gen = ResumeGenerator()
        self.applier = ApplicationBot()
        self.coach = InterviewCoach()
        self.strategy_engine = StrategyEngine()
        self.monitoring = FollowUpAgent()
        self.networker = NetworkAgent()
        self.reporter = ReportGenerator()
        self.simulator = InterviewSimulator()
        self.email_gen = EmailGenerator()
        self.resume_improver = ResumeImprover()
        self.market_analyzer = MarketAnalyzer()
        self.skills_quiz = SkillsQuiz()
        self.salary_advisor = SalaryAdvisor()
        self.calendar = CalendarManager()

        self.profile = None
        self.metrics = {
            "scanned": 0,
            "matched": 0,
            "applied": 0,
            "interviews": 0,
            "followups": 0,
            "networking": 0
        }
        self.last_strategy_update = "Inicializando..."
        self.logs = deque(maxlen=8)

    def load_state(self):
        """Loads state from disk if available."""
        p, m, apps = self.persistence.load_data()
        if p:
            self.profile = p
            console.print("[green]Perfil carregado do disco.[/green]")
        else:
            self.profile = self.onboarding.load_default_profile()
            console.print("[yellow]Perfil padrão carregado.[/yellow]")

        if m:
            self.metrics = m
            if "networking" not in self.metrics: self.metrics["networking"] = 0
            if "followups" not in self.metrics: self.metrics["followups"] = 0

        if apps:
            self.applier.application_history = apps

    def save_state(self):
        """Saves current state."""
        self.persistence.save_data(self.profile, self.metrics, self.applier.application_history)

    def log(self, message):
        """Adds a message to the live log."""
        timestamp = time.strftime("%H:%M:%S")
        self.logs.append(f"[{timestamp}] {message}")

    def start(self):
        self.load_state()

        # Simple menu for mode selection
        console.clear()
        console.print(Panel("[bold cyan]Hub de Vagas - Central de Comando[/bold cyan]"))
        console.print("1. Iniciar Ciclo Automático (Dashboard)")
        console.print("2. Simulador de Entrevista (Interativo)")
        console.print("3. Gerador de E-mail (Ferramenta)")
        console.print("4. Analisador de Currículo (IA)")
        console.print("5. Tendências de Mercado")
        console.print("6. Teste de Competências (Quiz)")
        console.print("7. Consultor de Salário")
        choice = console.input("\n[bold]Escolha uma opção:[/bold] ")

        if choice == "2":
            self.simulator.run_session()
            sys.exit(0)
        elif choice == "3":
            self.run_email_tool()
            sys.exit(0)
        elif choice == "4":
            text = console.input("Cole o texto do seu currículo aqui: ")
            self.resume_improver.analyze_resume(text)
            sys.exit(0)
        elif choice == "5":
            self.market_analyzer.show_trends()
            sys.exit(0)
        elif choice == "6":
            self.skills_quiz.run_quiz()
            sys.exit(0)
        elif choice == "7":
            role = console.input("Cargo alvo: ")
            level = console.input("Nível (Junior/Pleno/Senior): ")
            self.salary_advisor.advise(role, level)
            sys.exit(0)

        # Default to Dashboard Loop
        layout = self.make_layout()

        try:
            with Live(layout, refresh_per_second=4, screen=True):
                while True:
                    # 1. Update Header
                    layout["header"].update(Panel(Text("HUB DE VAGAS AUTOMÁTICO - OPERANDO", style="bold green", justify="center")))

                    # 2. Decision Engine Analysis
                    strategy_msg = self.strategy_engine.analyze_performance(self.metrics, [])
                    self.last_strategy_update = strategy_msg

                    # 3. Scan
                    layout["main"].update(Panel(Text("Escaneando oportunidades...", style="yellow")))
                    time.sleep(1)

                    keywords = [s.name for s in self.profile.skills]
                    jobs = self.scanner.scan_opportunities(keywords)
                    self.metrics["scanned"] += len(jobs)

                    # 4. Match
                    high_match_jobs = []
                    for job in jobs:
                        score = self.scanner.calculate_match_score(self.profile, job)
                        if score > 50:
                            high_match_jobs.append(job)
                            job.match_score = score

                    self.metrics["matched"] += len(high_match_jobs)

                    # Display Jobs
                    job_table = Table(title="Oportunidades Recentes")
                    job_table.add_column("Empresa", style="cyan")
                    job_table.add_column("Cargo", style="magenta")
                    job_table.add_column("Match %", justify="right")

                    for job in high_match_jobs[-5:]:
                        job_table.add_row(job.company, job.title, f"{job.match_score:.1f}%")

                    layout["main"].update(Panel(job_table))
                    time.sleep(1)

                    # 5. Apply & Interview Simulation
                    for job in high_match_jobs:
                        # Optimize
                        opt_profile = self.optimizer.optimize_for_job(self.profile, job)
                        # Resume
                        resume = self.resume_gen.generate_resume(opt_profile, job)
                        # Apply
                        app = self.applier.apply(opt_profile, job, resume)
                        self.metrics["applied"] += 1

                        # Update Log
                        status_color = "green" if app.status == "Aplicado" else "red"
                        self.log(f"Candidatura: {job.company} ({job.title}) - [{status_color}]{app.status}[/{status_color}]")

                        # Networking Action
                        net_action = self.networker.attempt_connection(job.company)
                        if net_action:
                            self.metrics["networking"] += 1
                            self.log(f"[cyan]Networking:[/cyan] {net_action}")
                            time.sleep(0.5)

                        # SIMULATE INTERVIEW
                        if random.random() < 0.1:
                            self.metrics["interviews"] += 1
                            questions = self.coach.generate_questions(job)
                            self.log(f"[magenta]Entrevista Agendada:[/magenta] {job.company}")

                            # Add to Calendar
                            ics_file = self.calendar.add_event(f"Entrevista {job.company}", f"Cargo: {job.title}", datetime.now())
                            self.log(f"[green]📅 Evento criado:[/green] {ics_file}")

                            q_text = "\n".join([f"- {q}" for q in questions])
                            layout["main"].update(Panel(f"[bold]Preparação para {job.company}:[/bold]\n{q_text}", title="MÓDULO DE ENTREVISTAS", style="bold white on blue"))
                            time.sleep(2)

                        # Update Footer
                        log_text = "\n".join(self.logs)
                        layout["footer"].update(Panel(log_text, title="Log de Eventos em Tempo Real", style="white"))

                        time.sleep(0.5)
                        self.save_state()

                    # 6. Monitoring & Follow-up
                    follow_ups = self.monitoring.check_for_follow_up(self.applier.application_history)
                    if follow_ups:
                        self.metrics["followups"] += len(follow_ups)
                        for action in follow_ups:
                             self.log(f"[yellow]Monitoramento:[/yellow] {action}")
                             time.sleep(0.5)

                    # Update Side Panel
                    stats_text = f"""
                    [bold]MÉTRICAS OPERACIONAIS[/bold]

                    Escaneados: {self.metrics['scanned']}
                    Compatíveis: {self.metrics['matched']}
                    Candidaturas: {self.metrics['applied']}
                    Entrevistas: {self.metrics['interviews']}
                    Follow-ups: {self.metrics['followups']}
                    Networking: {self.metrics['networking']}

                    [bold]Estratégia Ativa:[/bold]
                    {self.strategy_engine.get_current_strategy()}
                    [italic]{self.last_strategy_update}[/italic]
                    """
                    layout["side"].update(Panel(stats_text))

                    # Pause before next cycle
                    time.sleep(2)

        except KeyboardInterrupt:
            console.print("[bold red]Sistema Encerrando... Gerando Relatório.[/bold red]")
            report_file = self.reporter.generate_daily_report(
                self.profile, self.metrics, self.applier.application_history, self.strategy_engine.get_current_strategy()
            )
            self.save_state()
            console.print(f"[bold green]Relatório salvo em: {report_file}[/bold green]")
            sys.exit(0)

    def run_email_tool(self):
        console.print("[bold]Gerador de E-mail para Networking[/bold]\n")
        recruiter = console.input("Nome do Recrutador: ")
        company = console.input("Empresa: ")
        role = console.input("Cargo: ")
        email = self.email_gen.generate_cold_email(recruiter, company, role)
        console.print(Panel(email, title="Template Gerado", style="green"))

    def make_layout(self) -> Layout:
        layout = Layout()
        layout.split(
            Layout(name="header", size=3),
            Layout(name="body", ratio=1),
            Layout(name="footer", size=10)
        )
        layout["body"].split_row(
            Layout(name="side", ratio=1),
            Layout(name="main", ratio=3)
        )
        return layout

if __name__ == "__main__":
    hub = HubDeVagas()
    hub.start()

```

## src/modules/__init__.py
```

```

## src/modules/applier.py
```
from src.core.models import Application, JobOpportunity, Resume, CandidateProfile
from datetime import datetime
import random

class ApplicationBot:
    def __init__(self):
        self.application_history = []

    def apply(self, profile: CandidateProfile, job: JobOpportunity, resume: Resume) -> Application:
        """
        Simulates the application process.
        """
        # Simulate network latency or processing time? Not needed for simple logic.

        # Determine success probability (mocking captcha failures or form errors)
        status = "Aplicado"
        if random.random() < 0.05:
             status = "Falha" # 5% failure rate

        app = Application(
            job_id=job.id,
            profile_id=profile.id,
            resume_id=resume.id,
            status=status,
            platform=job.source,
            notes=f"Aplicado com versão de currículo {resume.version_tag}"
        )

        self.application_history.append(app)
        return app

```

## src/modules/calendar/integration.py
```
from ics import Calendar, Event
from datetime import datetime, timedelta
import os

class CalendarManager:
    def __init__(self):
        self.calendar = Calendar()
        self.filename = "data/entrevistas.ics"
        self._load()

    def _load(self):
        if os.path.exists(self.filename):
            try:
                with open(self.filename, 'r') as f:
                    self.calendar = Calendar(f.read())
            except:
                pass

    def add_event(self, title, description, start_time, duration_minutes=60):
        e = Event()
        e.name = title
        e.description = description
        e.begin = start_time
        e.duration = timedelta(minutes=duration_minutes)
        self.calendar.events.add(e)
        self._save()
        return self.filename

    def _save(self):
        os.makedirs("data", exist_ok=True)
        with open(self.filename, 'w') as f:
            f.writelines(self.calendar)

```

## src/modules/decision_engine.py
```
from typing import Dict, List

class StrategyEngine:
    def __init__(self):
        self.current_strategy = "Aplicação Agressiva"
        self.focus_areas = ["Geral"]

    def analyze_performance(self, metrics: Dict[str, int], recent_applications: List[str]) -> str:
        """
        Analyzes metrics and returns a strategy update message.
        """
        conversion_rate = 0
        if metrics["applied"] > 0:
            conversion_rate = metrics["interviews"] / metrics["applied"]

        # Simple logic to switch strategies
        if conversion_rate < 0.1 and metrics["applied"] > 10:
            self.current_strategy = "Qualidade sobre Quantidade"
            return "Taxa de conversão baixa detectada. Mudando para foco em alta relevância."

        elif metrics["matched"] > 50 and metrics["applied"] < 10:
             self.current_strategy = "Sprint de Alto Volume"
             return "Muitos matches encontrados. Aumentando velocidade de aplicação."

        else:
            self.current_strategy = "Abordagem Equilibrada"
            return "Desempenho dentro dos parâmetros normais. Mantendo o curso."

    def get_current_strategy(self) -> str:
        return self.current_strategy

```

## src/modules/email_helper/generator.py
```
class EmailGenerator:
    def __init__(self):
        pass

    def generate_cold_email(self, recruiter_name, company_name, job_title):
        """Generates a cold email template."""
        return f"""
Assunto: Interesse na vaga de {job_title} - {company_name}

Olá {recruiter_name},

Espero que esta mensagem o encontre bem.

Meu nome é [Seu Nome] e acompanho o trabalho da {company_name} com admiração. Vi a oportunidade para {job_title} e acredito que minha experiência em [Sua Área] pode agregar muito ao time.

Gostaria muito de conversar brevemente sobre como posso contribuir com os desafios da equipe.

Atenciosamente,
[Seu Nome]
[Seu LinkedIn]
"""

    def generate_follow_up(self, recruiter_name, days_since_apply):
        """Generates a follow-up email template."""
        return f"""
Assunto: Follow-up: Candidatura para [Vaga]

Olá {recruiter_name},

Estou escrevendo para reiterar meu grande interesse na posição, para a qual me candidatei há {days_since_apply} dias.

Continuo muito entusiasmado com a possibilidade de integrar o time. Caso precisem de qualquer informação adicional, estou à disposição.

Obrigado pela atenção,
[Seu Nome]
"""

```

## src/modules/interview_prep.py
```
from src.core.models import JobOpportunity, CandidateProfile
import random

class InterviewCoach:
    def __init__(self):
        self.common_questions = [
            "Fale um pouco sobre você.",
            "Por que você quer trabalhar na {company}?",
            "Qual é o seu maior ponto forte?",
            "Descreva uma situação desafiadora que você enfrentou."
        ]
        self.tech_questions_pool = [
            "Explique como você projetaria um sistema escalável para {topic}.",
            "Como você lida com dívida técnica?",
            "Qual é a sua experiência com {skill}?",
            "Descreva uma vez que você otimizou uma consulta lenta."
        ]

    def generate_questions(self, job: JobOpportunity) -> list[str]:
        """
        Generates a list of interview questions tailored to the job.
        """
        questions = []

        # Add a behavioral question customized to the company
        questions.append(random.choice(self.common_questions).format(company=job.company))

        # Add technical questions based on requirements
        for req in job.requirements[:2]: # Take first 2 requirements
            questions.append(f"Como você utilizou {req} em um ambiente de produção?")

        # Add a random system design or general tech question
        topic = job.title.split()[-1] if job.title else "software"
        questions.append(random.choice(self.tech_questions_pool).format(topic=topic, skill=random.choice(job.requirements) if job.requirements else "Python"))

        return questions

    def simulate_feedback(self) -> str:
        """
        Simulates feedback after a mock interview.
        """
        feedbacks = [
            "Boa comunicação. Elabore mais nos detalhes técnicos.",
            "Boa profundidade técnica. Tente ser mais conciso.",
            "Excelente fit cultural. Pronto para a entrevista real.",
            "Precisa de mais preparação em conceitos de design de sistemas."
        ]
        return random.choice(feedbacks)

```

## src/modules/interview_simulator/simulator.py
```
import time
import random
from rich.panel import Panel
from rich.console import Console
from rich.prompt import Prompt
from src.core.llm import LLMClient

console = Console()

class InterviewSimulator:
    def __init__(self):
        self.llm = LLMClient()
        self.questions_db = {
            "Junior": [
                "O que é uma lista em Python?",
                "Como você aprende novas tecnologias?",
                "Explique o conceito de API REST.",
                "Qual a diferença entre SQL e NoSQL?"
            ],
            "Pleno": [
                "Como você lidaria com um bug em produção?",
                "Explique o ciclo de vida de uma thread.",
                "Quais os benefícios de usar Docker?",
                "Descreva sua experiência com CI/CD."
            ],
            "Senior": [
                "Desenhe uma arquitetura escalável para milhões de usuários.",
                "Como você mentora desenvolvedores mais júnior?",
                "Explique o Teorema CAP.",
                "Como você decide entre Monolito e Microsserviços?"
            ]
        }

    def run_session(self):
        """Runs an interactive interview session in the terminal."""
        console.clear()
        console.print(Panel("[bold cyan]Simulador de Entrevista Pro - Hub de Vagas[/bold cyan]", expand=False))

        # Difficulty Selection
        console.print("\n[bold]Selecione o Nível da Entrevista:[/bold]")
        console.print("1. Junior")
        console.print("2. Pleno")
        console.print("3. Senior")
        choice = Prompt.ask("Opção", choices=["1", "2", "3"], default="2")

        level_map = {"1": "Junior", "2": "Pleno", "3": "Senior"}
        level = level_map[choice]

        console.print(f"\n[green]Iniciando simulação nível {level}...[/green]\n")

        questions = random.sample(self.questions_db[level], 3)
        history = []

        for i, q in enumerate(questions, 1):
            console.print(f"[bold yellow]Pergunta {i}:[/bold yellow] {q}")
            answer = Prompt.ask("[italic]Sua resposta[/italic]")

            # Mock analysis simulation
            with console.status("[bold green]Analisando resposta (NLP)...[/bold green]", spinner="dots"):
                time.sleep(1.5)

            feedback = self._generate_feedback(answer, level)
            console.print(f"[bold magenta]Feedback da IA:[/bold magenta] {feedback}\n")
            history.append({"q": q, "a": answer, "f": feedback})
            time.sleep(1)

        console.print(Panel("[bold green]Sessão Finalizada![/bold green] Otimize suas respostas e tente novamente."))
        return history

    def _generate_feedback(self, answer, level):
        """Generates feedback using LLM if available, otherwise mock logic."""
        if self.llm.is_active():
            prompt = f"Avalie a seguinte resposta de um candidato para uma vaga nível {level}. Seja construtivo e breve.\nResposta: {answer}"
            feedback = self.llm.generate_response(prompt, system_role="Você é um recrutador técnico experiente.")
            if feedback: return feedback

        # Fallback Logic
        word_count = len(answer.split())

        if word_count < 10:
            return "Muito superficial. Em uma entrevista técnica, detalhe o 'como' e o 'porquê'."

        if level == "Senior" and word_count < 30:
            return "Para nível Sênior, espera-se uma visão mais arquitetural e detalhada. Aprofunde."

        if "depende" in answer.lower() and level == "Senior":
            return "Ótimo uso do 'depende'. Seniores sabem que não há bala de prata."

        if word_count > 100:
            return "Resposta detalhada, muito bom. Tente manter o foco para não divagar."

        return "Boa resposta. Demonstrou conhecimento do fundamento."

```

## src/modules/job_intelligence.py
```
from typing import List
from src.core.models import JobOpportunity
from faker import Faker
import random

fake = Faker('pt_BR')

class JobScanner:
    def __init__(self):
        pass

    def scan_opportunities(self, keywords: List[str]) -> List[JobOpportunity]:
        """
        Simulates scanning job boards (LinkedIn, Indeed, etc.) for opportunities.
        Returns a list of mock JobOpportunity objects.
        """
        opportunities = []
        # Generate some random jobs
        for _ in range(random.randint(5, 10)):
            job_title = fake.job()
            # Ensure some jobs match the keywords for demo purposes
            if random.random() > 0.5 and keywords:
                job_title = f"{random.choice(keywords)} {job_title}"

            requirements = [fake.word() for _ in range(4)]
            # Add matching keywords to requirements occasionally
            if keywords:
                 requirements.extend(random.sample(keywords, k=min(2, len(keywords))))

            job = JobOpportunity(
                id=fake.uuid4(),
                title=job_title,
                company=fake.company(),
                description=fake.catch_phrase(),
                requirements=requirements,
                url=fake.url(),
                source=random.choice(["LinkedIn", "Indeed", "Glassdoor", "Gupy"]),
                match_score=0.0 # To be calculated later
            )
            opportunities.append(job)

        return opportunities

    def calculate_match_score(self, profile, job: JobOpportunity) -> float:
        """
        Calculates a simple match score based on keyword overlap.
        """
        score = 0.0
        # Check title relevance (simplified)
        for skill in profile.skills:
            if skill.name.lower() in job.title.lower():
                score += 30.0
            if skill.name.lower() in [req.lower() for req in job.requirements]:
                score += 10.0

        # Check experience title relevance
        for exp in profile.experiences:
             if exp.title.lower() in job.title.lower():
                 score += 20.0

        # Cap at 100
        return min(100.0, score)

```

## src/modules/market_trends/analyzer.py
```
import random
from rich.console import Console
from rich.table import Table

console = Console()

class MarketAnalyzer:
    def __init__(self):
        self.trending_skills = {
            "IA Generativa": 98,
            "Python": 95,
            "Cloud Computing": 92,
            "Data Engineering": 88,
            "DevSecOps": 85
        }
        self.hot_roles = [
            "Engenheiro de IA",
            "Arquiteto de Soluções",
            "Engenheiro de Dados Sênior",
            "Desenvolvedor Full Stack (Python/React)"
        ]

    def show_trends(self):
        """Displays simulated market trends."""
        console.clear()
        console.print("[bold cyan]Análise de Tendências de Mercado[/bold cyan]\n")

        # Skills Table
        table = Table(title="Habilidades em Alta (Últimos 30 dias)")
        table.add_column("Habilidade", style="green")
        table.add_column("Índice de Demanda", justify="right", style="magenta")

        for skill, score in self.trending_skills.items():
            # Simulate slight fluctuation
            current_score = min(100, score + random.randint(-2, 2))
            table.add_row(skill, f"{current_score}/100")

        console.print(table)

        # Roles
        console.print("\n[bold yellow]Cargos com Maior Volume de Vagas:[/bold yellow]")
        for role in self.hot_roles:
            console.print(f"- {role}")

        console.print("\n[italic]Dados baseados em análise simulada de agregadores de vagas.[/italic]")

```

## src/modules/monitoring.py
```
from src.core.models import Application
from datetime import datetime, timedelta
import random

class FollowUpAgent:
    def __init__(self):
        pass

    def check_for_follow_up(self, applications: list[Application]) -> list[str]:
        """
        Checks applications that need a follow-up action.
        Returns a list of messages describing the actions taken.
        """
        actions = []
        for app in applications:
            # Simulate "Applied" applications that are older than X (simulated) seconds
            # In real life this would be days.
            # We don't have a real time delta in this simulation loop, so we'll use random chance
            # for demo purposes to simulate "time passing" or just trigger on a few.

            if app.status == "Aplicado" and random.random() < 0.1:
                # Simulate sending a follow-up email
                actions.append(f"Follow-up enviado para a vaga {app.job_id} na plataforma {app.platform}.")
                app.notes += " | Follow-up enviado."

        return actions

```

## src/modules/negotiation/advisor.py
```
from rich.console import Console
from rich.panel import Panel

console = Console()

class SalaryAdvisor:
    def __init__(self):
        # Mock database of salary ranges (BRL)
        self.salary_db = {
            "junior": {"min": 3000, "max": 5000},
            "pleno": {"min": 6000, "max": 9000},
            "senior": {"min": 10000, "max": 16000},
            "tech_lead": {"min": 18000, "max": 25000}
        }

    def advise(self, role, level):
        console.clear()
        console.print(Panel("[bold cyan]Consultor de Negociação Salarial[/bold cyan]", expand=False))

        level_key = level.lower()
        if level_key not in self.salary_db:
            level_key = "pleno" # Default

        data = self.salary_db[level_key]
        avg = (data["min"] + data["max"]) / 2

        console.print(f"\n[bold]Cargo:[/bold] {role} ({level})")
        console.print(f"[bold]Faixa Estimada (BR):[/bold] R$ {data['min']} - R$ {data['max']}")
        console.print(f"[bold]Média de Mercado:[/bold] R$ {avg}\n")

        console.print("[bold yellow]Estratégia de Negociação:[/bold yellow]")
        console.print("1. Nunca diga um número primeiro. Pergunte o budget da vaga.")
        console.print(f"2. Se pressionado, dê um intervalo: 'Estou buscando algo entre R$ {int(avg)} e R$ {data['max']}'.")
        console.print("3. Valorize benefícios (PLR, Saúde, Remoto) como parte do pacote total.")
        console.print("4. Pesquise a empresa no Glassdoor antes da reunião.")

        console.print(Panel("Lembre-se: O 'não' você já tem. Negocie com confiança baseada em dados.", style="green"))

```

## src/modules/networking.py
```
import random
from faker import Faker

fake = Faker('pt_BR')

class NetworkAgent:
    def __init__(self):
        pass

    def attempt_connection(self, company_name: str) -> str:
        """
        Simulates finding a recruiter at the target company and sending a connection request.
        """
        # Simulate finding a recruiter
        recruiter_name = fake.name()
        role = random.choice(["Tech Recruiter", "Talent Acquisition", "Gerente de RH", "Head de Pessoas"])

        # Simulate action
        if random.random() < 0.3: # 30% chance of "action" per cycle it's called
             return f"Conexão enviada para {recruiter_name} ({role}) na {company_name}."

        return None

    def send_message(self, recruiter_name: str) -> str:
        """Simulates sending a networking message."""
        return f"Mensagem de introdução enviada para {recruiter_name}."

```

## src/modules/notifications/telegram_bot.py
```
import os
import requests

class TelegramBot:
    def __init__(self):
        self.token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID")
        self.api_url = f"https://api.telegram.org/bot{self.token}/sendMessage"

    def send_notification(self, message):
        """Sends a message to the configured Telegram chat."""
        if not self.token or not self.chat_id:
            return False

        try:
            payload = {
                "chat_id": self.chat_id,
                "text": message,
                "parse_mode": "Markdown"
            }
            response = requests.post(self.api_url, json=payload, timeout=5)
            return response.status_code == 200
        except:
            return False

```

## src/modules/onboarding.py
```
from src.core.models import CandidateProfile, Experience, Education, Skill
from datetime import date
from faker import Faker
import random

fake = Faker('pt_BR')

class OnboardingAgent:
    def __init__(self):
        self.profile = None

    def load_default_profile(self) -> CandidateProfile:
        """Loads a hardcoded default profile for demonstration in PT-BR."""
        self.profile = CandidateProfile(
            name="Alex Desenvolvedor",
            email="alex.dev@exemplo.com.br",
            phone="+55 11 99999-9999",
            summary="Engenheiro de Software Sênior com 8 anos de experiência em Python e Arquiteturas em Nuvem.",
            experiences=[
                Experience(
                    title="Engenheiro Backend Sênior",
                    company="TechCorp Brasil",
                    start_date=date(2020, 1, 15),
                    description="Liderando migração de microsserviços e otimizando consultas de banco de dados."
                ),
                Experience(
                    title="Desenvolvedor de Software",
                    company="Inova Startup",
                    start_date=date(2016, 6, 1),
                    end_date=date(2019, 12, 31),
                    description="Desenvolvimento Full stack usando Django e React."
                )
            ],
            education=[
                Education(
                    institution="Universidade Tecnológica",
                    degree="Bacharelado",
                    field_of_study="Ciência da Computação",
                    start_date=date(2012, 8, 1),
                    end_date=date(2016, 5, 20)
                )
            ],
            skills=[
                Skill(name="Python", level="Especialista"),
                Skill(name="Docker", level="Intermediário"),
                Skill(name="AWS", level="Avançado")
            ],
            linkedin_url="https://linkedin.com/in/alexdev"
        )
        return self.profile

    def create_fake_profile(self) -> CandidateProfile:
        """Generates a random fake profile."""
        self.profile = CandidateProfile(
            name=fake.name(),
            email=fake.email(),
            phone=fake.phone_number(),
            summary=fake.text(),
            experiences=[
                Experience(
                    title=fake.job(),
                    company=fake.company(),
                    start_date=fake.date_between(start_date='-5y', end_date='-1y'),
                    description=fake.text()
                )
            ],
            education=[
                Education(
                    institution=fake.company(),
                    degree="Bacharelado",
                    field_of_study="Ciência da Computação",
                    start_date=fake.date_between(start_date='-10y', end_date='-6y'),
                    end_date=fake.date_between(start_date='-6y', end_date='-5y')
                )
            ],
            skills=[Skill(name=fake.word(), level="Intermediário") for _ in range(3)]
        )
        return self.profile

```

## src/modules/profile_optimizer.py
```
from src.core.models import CandidateProfile, JobOpportunity

class ProfileOptimizer:
    def optimize_for_job(self, profile: CandidateProfile, job: JobOpportunity) -> CandidateProfile:
        """
        Optimizes the candidate profile for a specific job opportunity.
        In a real scenario, this would use LLM to rewrite the summary and experiences.
        Here, we will simulate it by appending relevant keywords.
        """
        optimized_profile = profile.model_copy(deep=True)

        # Simulated optimization logic
        keywords = job.requirements

        # Append missing keywords to summary to "optimize"
        added_keywords = [k for k in keywords if k.lower() not in optimized_profile.summary.lower()]

        if added_keywords:
            optimized_profile.summary += f"\n\nÁreas de foco otimizadas: {', '.join(added_keywords)}."

        return optimized_profile

    def update_linkedin_headline(self, profile: CandidateProfile) -> str:
        """Generates a new LinkedIn headline based on skills."""
        top_skills = [s.name for s in profile.skills[:3]]
        return f"{profile.experiences[0].title} | {' | '.join(top_skills)} | Aberto a oportunidades"

```

## src/modules/reporting.py
```
import os
from datetime import datetime
from src.core.models import CandidateProfile, Application

class ReportGenerator:
    def __init__(self):
        pass

    def generate_daily_report(self, profile: CandidateProfile, metrics: dict, applications: list[Application], strategy: str):
        """Generates a markdown report of the system's operation."""
        filename = f"relatorio_operacional_{datetime.now().strftime('%Y%m%d')}.md"

        with open(filename, "w", encoding="utf-8") as f:
            f.write(f"# RELATÓRIO OPERACIONAL HUB DE VAGAS - {datetime.now().strftime('%d/%m/%Y')}\n\n")

            f.write("## 1. RESUMO EXECUTIVO\n")
            f.write(f"- **Perfil Ativo:** {profile.name}\n")
            f.write(f"- **Estratégia Atual:** {strategy}\n")
            f.write(f"- **Status:** Operacional\n\n")

            f.write("## 2. MÉTRICAS DO CICLO\n")
            f.write("| Métrica | Valor |\n")
            f.write("|---|---|\n")
            f.write(f"| Vagas Escaneadas | {metrics.get('scanned', 0)} |\n")
            f.write(f"| Vagas Compatíveis | {metrics.get('matched', 0)} |\n")
            f.write(f"| Candidaturas Enviadas | {metrics.get('applied', 0)} |\n")
            f.write(f"| Entrevistas Agendadas | {metrics.get('interviews', 0)} |\n")
            f.write(f"| Ações de Networking | {metrics.get('networking', 0)} |\n\n")

            f.write("## 3. REGISTRO DE CANDIDATURAS (Últimas 10)\n")
            if not applications:
                f.write("_Nenhuma candidatura registrada._\n")
            else:
                for app in applications[-10:]:
                    f.write(f"- **{app.applied_at.strftime('%H:%M')}**: {app.job_id} via {app.platform} - Status: {app.status}\n")

            f.write("\n## 4. PRÓXIMOS PASSOS AUTOMÁTICOS\n")
            f.write("- Manter varredura de vagas.\n")
            f.write("- Acompanhar retornos de networking.\n")
            f.write("- Otimizar currículo baseado em feedback (simulado).\n")

        return filename

```

## src/modules/resume_generator.py
```
from src.core.models import CandidateProfile, JobOpportunity, Resume
from datetime import datetime

class ResumeGenerator:
    def generate_resume(self, profile: CandidateProfile, job: JobOpportunity) -> Resume:
        """
        Generates a tailored resume for a specific job.
        """
        # Create a header
        content = f"CURRÍCULO: {profile.name}\n"
        content += f"Contato: {profile.email} | {profile.phone}\n"
        content += f"LinkedIn: {profile.linkedin_url}\n\n"

        # Tailored Summary
        content += "RESUMO PROFISSIONAL\n"
        # In a real system, this would rewrite the summary based on job.description
        content += f"{profile.summary}\n"
        content += f"Entusiasta por vagas de {job.title} na {job.company}.\n\n"

        # Skills (Highlighting matching ones)
        content += "HABILIDADES\n"
        skills_list = [s.name for s in profile.skills]
        # Bolding/Highlighting matching skills (simulated with *)
        formatted_skills = []
        for skill in skills_list:
            if skill.lower() in [r.lower() for r in job.requirements]:
                formatted_skills.append(f"*{skill}*")
            else:
                formatted_skills.append(skill)
        content += ", ".join(formatted_skills) + "\n\n"

        # Experience
        content += "EXPERIÊNCIA\n"
        for exp in profile.experiences:
            content += f"{exp.title} na {exp.company} ({exp.start_date} - {exp.end_date if exp.end_date else 'Atualmente'})\n"
            content += f"- {exp.description}\n"

        content += "\nFORMAÇÃO ACADÊMICA\n"
        for edu in profile.education:
            content += f"{edu.degree} em {edu.field_of_study}, {edu.institution}\n"

        return Resume(
            profile_id=profile.id,
            job_id=job.id,
            content=content,
            version_tag=f"v1-{job.company}-{datetime.now().strftime('%Y%m%d')}"
        )

```

## src/modules/resume_improver/improver.py
```
import re
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from src.core.llm import LLMClient

console = Console()

class ResumeImprover:
    def __init__(self):
        self.llm = LLMClient()
        # Weighted keywords for better scoring
        self.keywords = {
            "Python": 5, "SQL": 4, "AWS": 5, "Docker": 4, "Kubernetes": 5,
            "API": 3, "REST": 3, "Git": 3, "CI/CD": 4, "Data Science": 5,
            "Machine Learning": 5, "Terraform": 5, "React": 3, "Node.js": 3
        }
        self.essential_sections = ["Experiência", "Educação", "Habilidades", "Projetos", "Resumo"]

    def analyze_resume(self, text):
        """Analyzes resume text using weighted scoring and section detection."""
        console.clear()
        console.print(Panel("[bold cyan]Analisador de Currículo Avançado (Hub de Vagas)[/bold cyan]", expand=False))

        # 0. Check for LLM
        if self.llm.is_active():
            with console.status("[bold green]Analisando com IA Generativa (OpenAI)...[/bold green]"):
                analysis = self.llm.generate_response(
                    f"Analise este currículo e dê feedback detalhado sobre pontos fortes, fracos e compatibilidade com vagas de tecnologia:\n\n{text}"
                )
            if analysis:
                console.print(Panel(analysis, title="Análise Profunda (LLM)", style="magenta"))
                return

        # 1. Section Analysis (Fallback Logic)
        found_sections = []
        missing_sections = []
        for section in self.essential_sections:
            if re.search(f"(?i){section}", text):
                found_sections.append(section)
            else:
                missing_sections.append(section)

        # 2. Keyword & Density Analysis
        score = 0
        max_score = sum(self.keywords.values())
        found_keywords = []
        missing_keywords = []

        for kw, weight in self.keywords.items():
            # Check for keyword existence (case insensitive)
            if re.search(f"(?i)\\b{re.escape(kw)}\\b", text):
                score += weight
                found_keywords.append(kw)
            else:
                missing_keywords.append(kw)

        # Normalize score to 100
        final_score = min(100, int((score / max_score) * 100))

        # Penalize for missing sections
        if missing_sections:
            final_score = max(0, final_score - (len(missing_sections) * 10))

        # --- DISPLAY RESULTS ---

        # Score Panel
        color = "green" if final_score >= 80 else "yellow" if final_score >= 50 else "red"
        console.print(Panel(f"[bold {color}]ATS Score: {final_score}/100[/bold {color}]", title="Pontuação de Compatibilidade"))

        # Sections Table
        table = Table(title="Estrutura do Currículo")
        table.add_column("Seção", style="cyan")
        table.add_column("Status", justify="center")

        for sec in self.essential_sections:
            status = "[green]Detectado[/green]" if sec in found_sections else "[red]Ausente[/red]"
            table.add_row(sec, status)
        console.print(table)

        # Keywords Analysis
        if found_keywords:
            console.print(f"\n[green]Competências Identificadas:[/green] {', '.join(found_keywords)}")

        if missing_keywords:
            console.print(f"\n[yellow]Oportunidades de Palavras-Chave (Tech Trending):[/yellow]")
            console.print(f"{', '.join(missing_keywords[:10])}")

        # Final Feedback
        feedback = []
        if final_score < 50:
            feedback.append("• Seu currículo está muito genérico. Adicione as palavras-chave listadas acima.")
        if missing_sections:
            feedback.append(f"• Estrutura incompleta. Adicione as seções: {', '.join(missing_sections)}.")
        if "Python" in found_keywords and "Git" not in found_keywords:
            feedback.append("• Dica: Desenvolvedores Python devem mencionar Git/Versionamento.")
        if not feedback:
            feedback.append("• Excelente currículo! Pronto para aplicação.")

        console.print(Panel("\n".join(feedback), title="Diagnóstico da IA", style="magenta"))

```

## src/modules/selenium_bot/config.py
```
import os

# Configuração do Perfil e Bot
PERFIL = {
    "nome_completo": "Nome Sobrenome",
    "email": "email@exemplo.com",
    "telefone": "11999999999",
    "cidade": "Ribeirão Preto",
    "cargo_atual": "Analista de Revenue Operations",
    # Tenta pegar do ambiente ou usa placeholder
    "senha_infojobs": os.getenv("INFOJOBS_PASSWORD", "SUA_SENHA_AQUI"),
    "senha_vagas": os.getenv("VAGAS_PASSWORD", "SUA_SENHA_AQUI"),

    "buscas": [
        "Revenue Operations",
        "Sales Operations",
        "Analista de Dados",
        "Salesforce",
        "HubSpot"
    ],

    "locais": [
        "Ribeirão Preto",
        "Home Office"
    ]
}

```

## src/modules/selenium_bot/human_bot.py
```
import time
import random
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.support.ui import WebDriverWait
from webdriver_manager.chrome import ChromeDriverManager

class HumanoBot:
    def __init__(self, headless=False):
        self.driver = None
        self.headless = headless
        self.wait = None

    def iniciar_driver(self):
        options = webdriver.ChromeOptions()
        if self.headless:
            options.add_argument("--headless=new")
            options.add_argument("--no-sandbox")
            options.add_argument("--disable-dev-shm-usage")
            options.add_argument("--disable-gpu")
            options.add_argument("--window-size=1920,1080")

        self.driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=options)
        self.wait = WebDriverWait(self.driver, 15)

    def dormir_aleatorio(self, min_seg=2, max_seg=5):
        """Pausa a execução por um tempo variável para imitar 'tempo de pensamento'."""
        tempo = random.uniform(min_seg, max_seg)
        time.sleep(tempo)

    def digitar_humanizado(self, elemento, texto):
        """Digita caractere por caractere com pausas variadas, como uma pessoa."""
        for letra in texto:
            elemento.send_keys(letra)
            time.sleep(random.uniform(0.05, 0.2)) # Velocidade de digitação variável

    def encerrar(self):
        if self.driver:
            print(">> 🏁 Sessão finalizada.")
            self.driver.quit()
            self.driver = None

```

## src/modules/selenium_bot/infojobs.py
```
import random
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from src.modules.selenium_bot.human_bot import HumanoBot
from src.modules.selenium_bot.config import PERFIL

class InfojobsBot(HumanoBot):
    def login(self):
        print(">> 🔓 Iniciando Login Infojobs Humano...")
        self.driver.get("https://www.infojobs.com.br/login.aspx")
        self.dormir_aleatorio(3, 5)

        # Campo Usuário
        user_field = self.wait.until(EC.element_to_be_clickable((By.ID, "Username")))
        self.digitar_humanizado(user_field, PERFIL["email"])
        self.dormir_aleatorio(1, 2)

        # Campo Senha
        pwd_field = self.driver.find_element(By.ID, "Password")
        self.digitar_humanizado(pwd_field, PERFIL["senha_infojobs"])
        self.dormir_aleatorio(1, 2)

        # Enter
        pwd_field.send_keys(Keys.RETURN)
        print(">> ✅ Login efetuado. Aguardando carregamento...")
        self.dormir_aleatorio(5, 8)

    def executar_busca(self):
        for local in PERFIL["locais"]:
            for cargo in PERFIL["buscas"]:
                print(f"\n>> 🔍 Buscando: '{cargo}' em '{local}'")

                # Monta a URL de busca direta
                termo_url = cargo.replace(" ", "+")
                local_url = local.replace(" ", "+")
                url = f"https://www.infojobs.com.br/empregos.aspx?Palabra={termo_url}&Campo=loc&Donde={local_url}"

                self.driver.get(url)
                self.dormir_aleatorio(4, 6) # Tempo para "ler" a lista de vagas

                self.processar_lista_vagas()

    def processar_lista_vagas(self):
        # Coleta links da primeira página
        vagas = self.driver.find_elements(By.CSS_SELECTOR, "div.vaga a.text-decoration-none")
        links = [v.get_attribute('href') for v in vagas if v.get_attribute('href')]

        # Embaralha a lista para não clicar sempre na ordem exata
        random.shuffle(links)

        print(f"   📄 Encontrei {len(links)} vagas. Analisando...")

        for i, link in enumerate(links):
            if i >= 5: break # Limite de segurança: 5 vagas por busca

            try:
                self.driver.get(link)
                self.dormir_aleatorio(3, 7) # Tempo para "ler" a descrição

                # Procura botão de candidatura (ID varia; usa XPath por padrão)
                botoes = self.driver.find_elements(By.XPATH, "//a[contains(@id, 'lbtnApply')]")

                if botoes and botoes[0].is_displayed():
                    btn = botoes[0]
                    texto_btn = btn.text.upper()

                    if "CANDIDATAR" in texto_btn:
                        # Rolar até o botão
                        self.driver.execute_script(
                            "arguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});",
                            btn
                        )
                        self.dormir_aleatorio(1, 3)

                        btn.click()
                        print(f"   [✅ CANDIDATURA] {link}")
                        self.dormir_aleatorio(2, 4)
                    else:
                        print(f"   [ℹ️ JÁ INSCRITO] {link}")
                else:
                    print("   [❌ BOTÃO NÃO ENCONTRADO]")

            except Exception as e:
                print(f"   [⚠️ ERRO] Pulei a vaga: {e}")

```

## src/modules/selenium_bot/runner.py
```
import time
import random
from datetime import datetime
from src.modules.selenium_bot.infojobs import InfojobsBot
from src.modules.selenium_bot.vagas import VagasBot

class BotRunner24h:
    def __init__(self):
        self.bot = None

    def run(self):
        print(f">> 🌙 Vigília 24h iniciada em: {datetime.now().strftime('%H:%M')}")

        while True:
            try:
                # Ciclo Infojobs
                print("\n>> Iniciando Ciclo Infojobs...")
                self.bot = InfojobsBot(headless=True) # Headless para servidor
                self.bot.iniciar_driver()
                self.bot.login()
                self.bot.executar_busca()
                self.bot.encerrar()
                self.bot = None

                # Poderia adicionar ciclo Vagas aqui

            except Exception as e:
                print(f"   [⚠️ ERRO NO CICLO] {e}")
                if self.bot:
                    self.bot.encerrar()
                    self.bot = None

            # O Intervalo "Humano" (Entre 45 min e 2 horas)
            # Para teste rápido, reduziremos, mas o código original pedia 2700-7200
            # Vamos manter o original se for produção, mas aqui é demo.
            # Vou usar um tempo menor para demonstração se fosse rodar, mas deixo o original comentado.

            # tempo_espera = random.randint(2700, 7200)
            tempo_espera = 3600 # 1 hora fixa para o exemplo do snippet "Dormindo por 1 hora..."

            proxima_ronda = time.time() + tempo_espera
            hora_proxima = time.strftime('%H:%M', time.localtime(proxima_ronda))

            print(f">> 💤 Modo Standby. Próxima ronda às: {hora_proxima}")
            time.sleep(tempo_espera)

if __name__ == "__main__":
    runner = BotRunner24h()
    try:
        runner.run()
    except KeyboardInterrupt:
        print(">> 🛑 Parada manual solicitada.")

```

## src/modules/selenium_bot/vagas.py
```
from selenium.webdriver.common.by import By
from src.modules.selenium_bot.human_bot import HumanoBot
from src.modules.selenium_bot.config import PERFIL

class VagasBot(HumanoBot):
    def executar_busca(self):
        # Nota: Vagas.com geralmente requer login manual prévio ou gestão de cookies complexa.
        # Este script foca na iteração de busca conforme o snippet fornecido.
        print(">> ⚠️ Nota: Para o Vagas.com, certifique-se de estar logado ou implemente o login.")

        for cargo in PERFIL["buscas"]:
            url = f"https://www.vagas.com.br/vagas-de-{cargo.replace(' ', '-')}"
            print(f"\n>> 🔍 Buscando no Vagas.com: {cargo}")

            self.driver.get(url)
            self.dormir_aleatorio(3, 5)

            vagas = self.driver.find_elements(By.CLASS_NAME, "vaga")
            links = []

            for vaga in vagas:
                try:
                    link_elem = vaga.find_element(By.TAG_NAME, "a")
                    links.append(link_elem.get_attribute('href'))
                except:
                    continue

            print(f"   Encontradas {len(links)} vagas.")

            for link in links[:5]: # Limite
                try:
                    self.processar_vaga(link)
                except Exception as e:
                    print(f"   Erro ao processar vaga: {e}")

    def processar_vaga(self, link):
        self.driver.get(link)
        self.dormir_aleatorio(2, 4)

        try:
            # Botão candidatar
            bts = self.driver.find_elements(By.CLASS_NAME, "bt-candidatura")
            if bts:
                bts[0].click()
                print(f"   [Tentativa de Candidatura] {link}")
                self.dormir_aleatorio(2, 3)
                # Aqui entraria lógica de confirmação específica do Vagas
            else:
                print(f"   [Botão não encontrado] {link}")
        except Exception as e:
            print(f"   [Erro] {e}")

```

## src/modules/skills_assessment/quiz.py
```
from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt

console = Console()

class SkillsQuiz:
    def __init__(self):
        self.quizzes = {
            "Python": [
                {"q": "Qual é a saída de print(2 ** 3)?", "options": ["5", "6", "8", "9"], "a": "3"},
                {"q": "Qual método adiciona um item ao final de uma lista?", "options": ["push()", "add()", "append()", "insert()"], "a": "3"},
                {"q": "O que é um decorador?", "options": ["Uma classe", "Uma função que modifica outra", "Um comentário", "Um erro"], "a": "2"}
            ],
            "SQL": [
                {"q": "Qual comando é usado para buscar dados?", "options": ["GET", "OPEN", "SELECT", "FETCH"], "a": "3"},
                {"q": "Qual cláusula filtra registros?", "options": ["WHERE", "FILTER", "LIMIT", "GROUP"], "a": "1"},
                {"q": "Como remover duplicatas?", "options": ["UNIQUE", "DISTINCT", "DIFFERENT", "REMOVE"], "a": "2"}
            ]
        }

    def run_quiz(self):
        console.clear()
        console.print(Panel("[bold cyan]Avaliação Técnica - Hub de Vagas[/bold cyan]", expand=False))

        topic = Prompt.ask("Escolha o tema", choices=list(self.quizzes.keys()), default="Python")
        questions = self.quizzes[topic]
        score = 0

        for i, item in enumerate(questions, 1):
            console.print(f"\n[bold yellow]{i}. {item['q']}[/bold yellow]")
            for idx, opt in enumerate(item['options'], 1):
                console.print(f"{idx}) {opt}")

            answer = Prompt.ask("Sua resposta", choices=["1", "2", "3", "4"])
            if answer == item['a']:
                console.print("[green]Correto![/green]")
                score += 1
            else:
                correct_text = item['options'][int(item['a'])-1]
                console.print(f"[red]Incorreto. A resposta certa era: {correct_text}[/red]")

        final_score = int((score / len(questions)) * 100)
        color = "green" if final_score >= 70 else "red"
        console.print(Panel(f"Pontuação Final: [bold {color}]{final_score}%[/bold {color}]", title="Resultado"))

```

## src/web/app.py
```
import streamlit as st
import pandas as pd
import sqlite3
import json
import os
from datetime import datetime

# Page Config
st.set_page_config(page_title="Hub de Vagas - Dashboard Web", page_icon="🚀", layout="wide")

# Sidebar
st.sidebar.title("Hub de Vagas")
st.sidebar.markdown("---")
page = st.sidebar.radio("Navegação", ["Dashboard", "Perfil", "Configurações"])

DB_PATH = "data/autoapply.db"
PROFILE_PATH = "profile_br.json"

def get_db_connection():
    if not os.path.exists(DB_PATH):
        return None
    return sqlite3.connect(DB_PATH)

if page == "Dashboard":
    st.title("📊 Monitoramento de Candidaturas")

    conn = get_db_connection()
    if conn:
        # Load Data
        df = pd.read_sql_query("SELECT * FROM jobs", conn)
        conn.close()

        # Metrics
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Mapeado", len(df))
        col2.metric("Aplicados", len(df[df['status'] == 'applied']))
        col3.metric("Taxa de Conversão", f"{len(df[df['status'] == 'applied']) / len(df) * 100:.1f}%" if len(df) > 0 else "0%")

        # Charts
        st.subheader("Atividade Recente")
        df['date'] = pd.to_datetime(df['created_at'])
        daily_counts = df.groupby(df['date'].dt.date).size()
        st.bar_chart(daily_counts)

        st.subheader("Status por Plataforma")
        status_counts = df.groupby(['platform', 'status']).size().unstack(fill_value=0)
        st.bar_chart(status_counts)

        # Table
        st.subheader("Últimas Vagas")
        st.dataframe(df.sort_values('created_at', ascending=False).head(20))

    else:
        st.warning("Banco de dados ainda não criado. Execute o runner primeiro.")

elif page == "Perfil":
    st.title("👤 Perfil do Candidato")

    if os.path.exists(PROFILE_PATH):
        with open(PROFILE_PATH, 'r', encoding='utf-8') as f:
            profile = json.load(f)

        # Display Profile
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Nome", profile['pessoal']['nome_completo'], disabled=True)
            st.text_input("Email", profile['pessoal']['email'], disabled=True)
        with col2:
            st.text_input("LinkedIn", profile['pessoal']['linkedin'], disabled=True)
            st.text_input("Telefone", profile['pessoal']['telefone'], disabled=True)

        st.subheader("Habilidades (Skills)")
        st.write(", ".join(profile['skills']))

        st.subheader("Preferências")
        st.json(profile['preferencias'])

        st.info("Para editar, modifique o arquivo profile_br.json diretamente.")
    else:
        st.error("Perfil não encontrado.")

elif page == "Configurações":
    st.title("⚙️ Configurações do Sistema")
    st.write("Variáveis de ambiente carregadas (.env):")

    st.text_input("HEADLESS", os.getenv("HEADLESS", "Não definido"), disabled=True)
    st.text_input("RUN_MODE", os.getenv("RUN_MODE", "Não definido"), disabled=True)

    if st.button("Limpar Cache de Sessão"):
        st.success("Cache limpo (Simulado).")

```
