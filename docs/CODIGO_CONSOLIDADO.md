# CÓDIGO FONTE CONSOLIDADO - BIRTH HUB 360 (V3)

## .env
```
RUN_MODE=local
HEADLESS=0
TIMEZONE=America/Sao_Paulo
LINKEDIN_EMAIL=marcelinmark@gmail.com
LINKEDIN_PASSWORD=SUA_SENHA_AQUI
GUPY_EMAIL=marcelinmark@gmail.com
GUPY_PASSWORD=SUA_SENHA_AQUI

```

## requirements.txt
```
playwright==1.41.0
pydantic==2.5.3
python-dotenv==1.0.1
rich
faker
selenium
webdriver-manager

```

## profile_br.json
```
{
  "pessoal": {
    "nome_completo": "Marcelo Nascimento",
    "email": "marcelinmark@gmail.com",
    "telefone": "16999948479",
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
      fullName: "Marcelo Nascimento",
      email: "marcelinmark@gmail.com",
      phone: "16999948479",
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
mkdir BirthHub360
cd BirthHub360
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
WorkingDirectory=/home/ubuntu/BirthHub360
# Ajuste o caminho do python conforme seu venv
ExecStart=/home/ubuntu/BirthHub360/venv/bin/python -m src.core.runner
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
    <title>Birth Hub 360 Automático</title>
    <link rel="stylesheet" href="assets/css/style.css">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css">
</head>
<body>
    <header>
        <div class="container">
            <div class="logo">
                <i class="fas fa-rocket"></i> Birth Hub 360
            </div>
            <nav>
                <ul>
                    <li><a href="#projetos">Módulos</a></li>
                    <li><a href="#download">Download</a></li>
                    <li><a href="#docs">Documentação</a></li>
                    <li><a href="https://github.com/marcelinmark/birth-hub-360" target="_blank" class="btn-github"><i class="fab fa-github"></i> GitHub</a></li>
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
            <p>&copy; 2025 Birth Hub 360 Automático. Desenvolvido por Marcelo Nascimento.</p>
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

## src/__pycache__/__init__.cpython-312.pyc
```
\xcb
    mepi    \xe3                    \xf3   \x97 y )N\xa9 r   \xf3    \xfa/app/src/__init__.py\xda<module>r      s   \xf1r   
```

## src/__pycache__/main.cpython-312.pyc
```
\xcb
    \x85jpiN$  \xe3                   \xf3P  \x97 d dl Z d dlZd dlZd dlmZ d dlmZ d dlmZ d dl	m
Z
 d dlmZ d dlmZ d dlmZ d d	lmZ d d
lmZ d dlmZ d dlmZ d dlmZ d dlmZ d dlmZ d dlm Z  d dl!m"Z" d dl#m$Z$ d dl%m&Z&  e\xab       Z' G d\x84 d\xab      Z(e)dk(  r e(\xab       Z*e*jW                  \xab        yy)\xe9    N)\xdaConsole)\xdaLayout)\xdaPanel)\xdaLive)\xdaTable)\xdaText)\xdaMarkdown)\xdaOnboardingAgent)\xda
JobScanner)\xdaProfileOptimizer)\xdaResumeGenerator)\xdaApplicationBot)\xdaInterviewCoach)\xdaStrategyEngine)\xdaFollowUpAgent)\xdaNetworkAgent)\xdaReportGenerator)\xdaPersistenceManagerc                   \xf30   \x97 e Zd Zd\x84 Zd\x84 Zd\x84 Zd\x84 Zdefd\x84Zy)\xdaBirthHub360c                 \xf3\x94  \x97 t        \xab       | _        t        \xab       | _        t	        \xab       | _        t        \xab       | _        t        \xab       | _	        t        \xab       | _        t        \xab       | _        t        \xab       | _        t!        \xab       | _        t%        \xab       | _        t)        \xab       | _        d | _        ddddddd\x9c| _        d| _        d| _        y )Nr   )\xdascanned\xdamatched\xdaapplied\xda
interviews\xda	followups\xda
networkingzInicializando...zNenhuma entrevista agendada.)r   \xdapersistencer
   \xda
onboardingr   \xdascannerr   \xda	optimizerr   \xda
resume_genr   \xdaapplierr   \xdacoachr   \xdastrategy_enginer   \xda
monitoringr   \xda	networkerr   \xdareporter\xdaprofile\xdametrics\xdalast_strategy_update\xdainterview_prep_status\xa9\xdaselfs    \xfa/app/src/main.py\xda__init__zBirthHub360.__init__   s\xa3   \x80 \xdc-\xd3/\x88\xd4\xdc)\xd3+\x88\x8c\xdc!\x93|\x88\x8c\xdc)\xd3+\x88\x8c\xdc)\xd3+\x88\x8c\xdc%\xd3'\x88\x8c\xdc#\xd3%\x88\x8c
\xdc-\xd3/\x88\xd4\xdc'\x9b/\x88\x8c\xdc%\x9b\x88\x8c\xdc'\xd3)\x88\x8c\xe0\x88\x8c\xe0\xd8\xd8\xd8\xd8\xd8\xf1
\x88\x8c\xf0 %7\x88\xd4!\xd8%C\x88\xd5"\xf3    c                 \xf3\x94  \x97 | j                   j                  \xab       \  }}}|r|| _        t        j	                  d\xab       n4| j
                  j                  \xab       | _        t        j	                  d\xab       |rA|| _        d| j                  vrd| j                  d<   d| j                  vrd| j                  d<   |r|| j                  _	        yy)z#Loads state from disk if available.z)[green]Perfil carregado do disco.[/green]u*   [yellow]Perfil padrão carregado.[/yellow]r   r   r   N)
r   \xda	load_datar)   \xdaconsole\xdaprintr   \xdaload_default_profiler*   r#   \xdaapplication_history)r.   \xdap\xdam\xdaappss       r/   \xda
load_statezBirthHub360.load_state4   s\xa4   \x80 \xe0\xd7%\xd1%\xd7/\xd1/\xd31\x89
\x88\x881\x88d\xd9\xd8\x88D\x8cL\xdc\x8fM\x89M\xd0E\xd5F\xe0\x9f?\x99?\xd7?\xd1?\xd3A\x88D\x8cL\xdc\x8fM\x89M\xd0F\xd4G\xe1\xd8\x88D\x8cL\xe0\xa04\xa7<\xa1<\xd1/\xc8a\xb0\xb7\xb1\xb8l\xd11K\xd8\xa0$\xa7,\xa1,\xd1.\xc8A\xb0\xb7\xb1\xb8[\xd10I\xe1\xd8/3\x88D\x8fL\x89L\xd5,\xf0 r1   c                 \xf3\x8e   \x97 | j                   j                  | j                  | j                  | j                  j
                  \xab       y)zSaves current state.N)r   \xda	save_datar)   r*   r#   r7   r-   s    r/   \xda
save_statezBirthHub360.save_stateG   s,   \x80 \xe0\xd7\xd1\xd7"\xd1"\xa04\xa7<\xa1<\xb0\xb7\xb1\xb8t\xbf|\xb9|\xd7?_\xd1?_\xd5`r1   c                 \xf3z  \x97 | j                  \xab        | j                  \xab       }	 t        |dd\xac\xab      5  	 |d   j                  t	        t        ddd\xac\xab      \xab      \xab       | j                  j                  | j                  g \xab      }|| _	        |d	   j                  t	        t        d
d\xac\xab      \xab      \xab       t        j                  d\xab       | j                  j                  D \x8fcg c]  }|j                  \x91\x8c }}| j                  j!                  |\xab      }| j                  dxx   t#        |\xab      z  cc<   g }|D ]F  }| j                  j%                  | j                  |\xab      }|dkD  s\x8c/|j'                  |\xab       ||_        \x8cH | j                  dxx   t#        |\xab      z  cc<   t+        d\xac\xab      }	|	j-                  dd\xac\xab       |	j-                  dd\xac\xab       |	j-                  dd\xac\xab       |dd  D ]7  }|	j/                  |j0                  |j2                  |j(                  d\x9bd\x9d\xab       \x8c9 |d	   j                  t	        |	\xab      \xab       t        j                  d\xab       |D \x90]1  }| j4                  j7                  | j                  |\xab      }
| j8                  j;                  |
|\xab      }| j<                  j?                  |
||\xab      }| j                  dxx   dz  cc<   | j@                  jC                  |j0                  \xab      }|rL| j                  dxx   dz  cc<   |d   j                  t	        d |\x9b \x9d\xab      \xab       t        j                  d\xab       |d   j                  t	        d!|j0                  \x9b d"|j2                  \x9b d#|jD                  \x9b \x9d\xab      \xab       tG        jF                  \xab       d$k  r\xc5| j                  d%xx   dz  cc<   | jH                  jK                  |\xab      }d&jM                  |D \x8fcg c]  }d'|\x9b \x9d\x91\x8c	 c}\xab      }d(|j0                  \x9b d)|\x9b d*| jH                  jO                  \xab       \x9b \x9d| _(        |d	   j                  t	        | jP                  d+d,\xac-\xab      \xab       t        j                  d.\xab       t        j                  d/\xab       | jS                  \xab        \x90\x8c4 | jT                  jW                  | j<                  jX                  \xab      }|r\| j                  d0xx   t#        |\xab      z  cc<   |D ]7  }|d   j                  t	        d1|\x9b \x9d\xab      \xab       t        j                  d\xab       \x8c9 d2| j                  d   \x9b d3| j                  d   \x9b d4| j                  d   \x9b d5| j                  d%   \x9b d6| j                  d0   \x9b d7| j                  d   \x9b d8| j                  j[                  \xab       \x9b d9| j                  \x9b d:|r|d;   j2                  nd<\x9b d=\x9d}|d>   j                  t	        |\xab      \xab       t        j                  d?\xab       \x90\x8c\xb5c c}w c c}w # 1 sw Y   y xY w# t\        $ r\xb4 t^        ja                  d@\xab       | jb                  je                  | j                  | j                  | j<                  jX                  | j                  j[                  \xab       \xab      }| jS                  \xab        t^        ja                  dA|\x9b dB\x9d\xab       tg        jh                  dC\xab       Y y w xY w)DN\xe9   T)\xdarefresh_per_second\xdascreen\xdaheaderu$   BIRTH HUB 360 AUTOMÁTICO - OPERANDOz
bold green\xdacenter)\xdastyle\xdajustify\xdamainzEscaneando oportunidades...\xdayellow)rE   \xe9   r   \xe92   r   zOportunidades Recentes)\xdatitle\xdaEmpresa\xdacyan\xdaCargo\xdamagentazMatch %\xdaright)rF   \xe9\xfb\xff\xff\xffz.1f\xda%r   r   \xdafooterz#[bold cyan]NETWORKING:[/bold cyan] zCandidatura enviada para z - z | Status: g\x9a\x99\x99\x99\x99\x99\xb9?r   \xda
z- u   [bold]Preparação para z	:[/bold]
z

[italic]Feedback IA:[/italic] u   MÓDULO DE ENTREVISTAS ATIVOzbold white on blue)rK   rE   \xe9   g      \xe0?r   z*[bold yellow]MONITORAMENTO:[/bold yellow] un   
                    [bold]MÉTRICAS OPERACIONAIS[/bold]

                    Escaneados: u#   
                    Compatíveis: z#
                    Candidaturas: z"
                    Entrevistas: z!
                    Follow-ups: z!
                    Networking: u^   

                    [bold]Estratégia Ativa:[/bold]
                    z
                    [italic]u\x86   [/italic]

                    [bold]Última Ação de IA:[/bold]
                    Otimização de perfil para \xe9\xff\xff\xff\xffzN/Az
                    \xdaside\xe9   u>   [bold red]Sistema Encerrando... Gerando Relatório.[/bold red]u!   [bold green]Relatório salvo em: z[/bold green]r   )5r;   \xdamake_layoutr   \xdaupdater   r   r%   \xdaanalyze_performancer*   r+   \xdatime\xdasleepr)   \xdaskills\xdanamer    \xdascan_opportunities\xdalen\xdacalculate_match_score\xdaappend\xdamatch_scorer   \xda
add_column\xdaadd_row\xdacompanyrK   r!   \xdaoptimize_for_jobr"   \xdagenerate_resumer#   \xdaapplyr'   \xdaattempt_connection\xdastatus\xdarandomr$   \xdagenerate_questions\xdajoin\xdasimulate_feedbackr,   r>   r&   \xdacheck_for_follow_upr7   \xdaget_current_strategy\xdaKeyboardInterruptr4   r5   r(   \xdagenerate_daily_report\xdasys\xdaexit)r.   \xdalayout\xdastrategy_msg\xdas\xdakeywords\xdajobs\xdahigh_match_jobs\xdajob\xdascore\xda	job_table\xdaopt_profile\xdaresume\xdaapp\xda
net_action\xda	questions\xdaq\xdaq_text\xda
follow_ups\xdaaction\xda
stats_text\xdareport_files                        r/   \xdastartzBirthHub360.startK   sI  \x80 \xd8\x8f\x89\xd4\xe0\xd7!\xd1!\xd3#\x88\xf0p	\xdc\x90f\xb0\xb84\xd6@\xd8\xe0\x988\xd1$\xd7+\xd1+\xacE\xb4$\xd07]\xd0eq\xf0  |D\xf4  3E\xf3  -F\xf4  G\xf0 $(\xd7#7\xd1#7\xd7#K\xd1#K\xc8D\xcfL\xc9L\xd0Z\\xd3#]\x90L\xd80<\x90D\xd4-\xf0 \x986\x91N\xd7)\xd1)\xac%\xb4\xd05R\xd0Zb\xd40c\xd3*d\xd4e\xdc\x97J\x91J\x98q\x94M\xe004\xb7\xb1\xd70C\xd20C\xd3D\xd10C\xa81\xa0\xa7\xa3\xd00C\x90H\xd0D\xd8\x9f<\x99<\xd7:\xd1:\xb88\xd3D\x90D\xd8\x97L\x91L\xa0\xd3+\xacs\xb04\xaby\xd18\xd3+\xf0 ')\x90O\xdb#\x98\xd8 $\xa7\xa1\xd7 B\xd1 B\xc04\xc7<\xc1<\xd0QT\xd3 U\x98\xd8 \xa02\x9b:\xd8+\xd72\xd12\xb03\xd47\xd8.3\x98C\x9dO\xf0	  $\xf0 \x97L\x91L\xa0\xd3+\xacs\xb0?\xd3/C\xd1C\xd3+\xf4 !&\xd0,D\xd4 E\x90I\xd8\xd7(\xd1(\xa8\xb8&\xd0(\xd4A\xd8\xd7(\xd1(\xa8\xb8	\xd0(\xd4B\xd8\xd7(\xd1(\xa8\xb8G\xd0(\xd4D\xe0.\xa8r\xa8s\xd33\x98\xd8!\xd7)\xd1)\xa8#\xaf+\xa9+\xb0s\xb7y\xb1y\xc0S\xc7_\xc1_\xd0UX\xd0DY\xd0YZ\xd0B[\xd5\\xf0  4\xf0 \x986\x91N\xd7)\xd1)\xac%\xb0	\xd3*:\xd4;\xdc\x97J\x91J\x98q\x94M\xf4  /\x98\xe0&*\xa7n\xa1n\xd7&E\xd1&E\xc0d\xc7l\xc1l\xd0TW\xd3&X\x98\xe0!%\xa7\xa1\xd7!@\xd1!@\xc0\xc8c\xd3!R\x98\xe0"\x9fl\x99l\xd70\xd10\xb0\xb8c\xc06\xd3J\x98\xd8\x9f\x99\xa0Y\xd3/\xb01\xd14\xd3/\xf0 &*\xa7^\xa1^\xd7%F\xd1%F\xc0s\xc7{\xc1{\xd3%S\x98
\xd9%\xd8 \x9fL\x99L\xa8\xd36\xb8!\xd1;\xd36\xd8"\xa08\xd1,\xd73\xd13\xb4E\xd0<_\xd0`j\xd0_k\xd0:l\xd34m\xd4n\xdc \x9fJ\x99J\xa0q\x9cM\xf0 \x98x\xd1(\xd7/\xd1/\xb4\xd08Q\xd0RU\xd7R]\xd1R]\xd0Q^\xd0^a\xd0be\xd7bk\xd1bk\xd0al\xd0lw\xd0x{\xf7  yC\xf1  yC\xf0  xD\xf0  7E\xf3  1F\xf4  G\xf4 "\x9f=\x99=\x9b?\xa8S\xd20\xd8 \x9fL\x99L\xa8\xd36\xb8!\xd1;\xd36\xd8(,\xaf
\xa9
\xd7(E\xd1(E\xc0c\xd3(J\x98I\xd8%)\xa7Y\xa1Y\xc1)\xd3/L\xc1)\xb8Q\xb0"\xb0Q\xb0C\xb2\xc0)\xd1/L\xd3%M\x98F\xd8;S\xd0TW\xd7T_\xd1T_\xd0S`\xd0`j\xd0kq\xd0jr\xf0  sU\xf0  VZ\xf7  V`\xf1  V`\xf7  Vr\xf1  Vr\xf3  Vt\xf0  Uu\xf0  :v\x98D\xd46\xf0 #\xa06\x99N\xd71\xd11\xb4%\xb8\xd78R\xd18R\xd0Zx\xf0  AU\xf4  3V\xf4  W\xdc \x9fJ\x99J\xa0q\x9cM\xe4\x9f
\x99
\xa03\x9c\xd8\x9f\x99\xd6)\xf0?  /\xf0D "&\xa7\xa1\xd7!D\xd1!D\xc0T\xc7\\xc1\\xd7Ee\xd1Ee\xd3!f\x90J\xd9!\xd8\x9f\x99\xa0[\xd31\xb4S\xb8\xb3_\xd1D\xd31\xdb&0\x98F\xd8#\xa0H\xd1-\xd74\xd14\xb4U\xd0=g\xd0hn\xd0go\xd0;p\xd35q\xd4r\xdc!\x9fZ\x99Z\xa8\x9d]\xf0 '1\xf0
&!\xf0 "&\xa7\xa1\xa8i\xd1!8\xd0 9\xf0 :#\xd8#'\xa7<\xa1<\xb0	\xd1#:\xd0";\xf0 <#\xd8#'\xa7<\xa1<\xb0	\xd1#:\xd0";\xf0 <"\xd8"&\xa7,\xa1,\xa8|\xd1"<\xd0!=\xf0 >!\xd8!%\xa7\xa1\xa8k\xd1!:\xd0 ;\xf0 <!\xd8!%\xa7\xa1\xa8l\xd1!;\xd0 <\xf0 =\xf0 \xd7)\xd1)\xd7>\xd1>\xd3@\xd0A\xf0 B\xd8!\xd76\xd16\xd07\xf0 81\xf1 O^\xb0\xc0\xd11D\xd71J\xd21J\xd0ch\xd00i\xf0 j\xf0"\x90J\xf0" \x986\x91N\xd7)\xd1)\xac%\xb0
\xd3*;\xd4<\xf4 \x97J\x91J\x98q\x94M\xf1K \xf9\xf2  E\xf9\xf2d 0M\xf7 A\xd0@\xfb\xf4P !\xf2 	\xdc\x8fM\x89M\xd0Z\xd4[\xd8\x9f-\x99-\xd7=\xd1=\xd8\x97\x91\x98d\x9fl\x99l\xa8D\xafL\xa9L\xd7,L\xd1,L\xc8d\xd7Nb\xd1Nb\xd7Nw\xd1Nw\xd3Ny\xf3\x88K\xf0 \x8fO\x89O\xd4\xdc\x8fM\x89M\xd0=\xb8k\xb8]\xc8-\xd0X\xd4Y\xdc\x8fH\x89H\x90Q\x8eK\xf0	\xfasK   \xa2W= \xb0B-W1\xc3W'\xc30A/W1\xc5 I;W1\xcfW,\xcf'H
W1\xd71W:\xd76W= \xd7:W= \xd7=B:Z:\xda9Z:\xdareturnc                 \xf3\xd8   \x97 t        \xab       }|j                  t        dd\xac\xab      t        dd\xac\xab      t        dd\xac\xab      \xab       |d   j                  t        dd\xac\xab      t        d	d\xac\xab      \xab       |S )
NrC   rU   )r_   \xdasize\xdabodyrI   )r_   \xdaratiorS   rW   rG   )r   \xdasplit\xda	split_row)r.   rw   s     r/   rY   zBirthHub360.make_layout\xc2   sb   \x80 \xdc\x93\x88\xd8\x8f\x89\xdc\x98\xa0q\xd4)\xdc\x98\xa0a\xd4(\xdc\x98\xa0q\xd4)\xf4
\xf0
 	\x88v\x89\xd7 \xd1 \xdc\x98\xa0a\xd4(\xdc\x98\xa0a\xd4(\xf4
\xf0 \x88r1   N)	\xda__name__\xda
__module__\xda__qualname__r0   r;   r>   r\x8b   r   rY   \xa9 r1   r/   r   r      s&   \x84 \xf2D\xf224\xf2&a\xf2u\xf0n\x98V\xf4 r1   r   \xda__main__),r\   rm   ru   \xdarich.consoler   \xdarich.layoutr   \xda
rich.panelr   \xda	rich.liver   \xda
rich.tabler   \xda	rich.textr   \xdarich.markdownr	   \xdasrc.modules.onboardingr
   \xdasrc.modules.job_intelligencer   \xdasrc.modules.profile_optimizerr   \xdasrc.modules.resume_generatorr   \xdasrc.modules.applierr   \xdasrc.modules.interview_prepr   \xdasrc.modules.decision_enginer   \xdasrc.modules.monitoringr   \xdasrc.modules.networkingr   \xdasrc.modules.reportingr   \xdasrc.core.persistencer   r4   r   r\x93   \xdahubr\x8b   r\x96   r1   r/   \xda<module>r\xab      sw   \xf0\xdb \xdb \xdb 
\xdd  \xdd \xdd \xdd \xdd \xdd \xdd "\xe5 2\xdd 3\xdd :\xdd 8\xdd .\xdd 5\xdd 6\xdd 0\xdd /\xdd 1\xdd 3\xe1
\x8b)\x80\xf7s\xf1 s\xf0j \x88z\xd2\xd9
\x8b-\x80C\xd8\x87I\x81I\x85K\xf0 r1   
```

## src/core/__init__.py
```

```

## src/core/__pycache__/__init__.cpython-312.pyc
```
\xcb
    mepi    \xe3                    \xf3   \x97 y )N\xa9 r   \xf3    \xfa/app/src/core/__init__.py\xda<module>r      s   \xf1r   
```

## src/core/__pycache__/browser.cpython-312.pyc
```
\xcb
    Ԥpi\xc3  \xe3                   \xf38   \x97 d dl mZ d dlmZ d\x84 Zdededz  fd\x84Zy)\xe9    )\xdaPath)\xdasync_playwrightc                 \xf3v   \x97 | j                   j                  }|dv r| j                  \xab       S | j                  \xab       S )N)\xdaimage\xdafont\xda
stylesheet\xdamedia)\xdarequest\xdaresource_type\xdaabort\xda	continue_)\xdaroute\xdarts     \xfa/app/src/core/browser.py\xda_route_block_heavyr      s3   \x80 \xd8	\x8f\x89\xd7	$\xd1	$\x80B\xd8	\xd05\xd15\xd8\x8f{\x89{\x8b}\xd0\xd8\x8f?\x89?\xd3\xd0\xf3    \xdaheadless\xdastorage_state_pathNc                 \xf3>  \x97 t        \xab       j                  \xab       }|j                  j                  | \xac\xab      }|r,|j	                  \xab       r|j                  t        |\xab      \xac\xab      }n|j                  \xab       }|j                  dt        \xab       |j                  \xab       }||||fS )N)r   )\xdastorage_statez**/*)
r   \xdastart\xdachromium\xdalaunch\xdaexists\xdanew_context\xdastrr   r   \xdanew_page)r   r   \xdap\xdabrowser\xdacontext\xdapages         r   \xdaopen_contextr"   
   s\x8c   \x80 \xdc\xd3\xd7\xd1\xd3!\x80A\xd8\x8fj\x89j\xd7\xd1\xa8\xd0\xd32\x80G\xd9\xd00\xd77\xd17\xd49\xd8\xd7%\xd1%\xb4C\xd08J\xd34K\xd0%\xd3L\x89\xe0\xd7%\xd1%\xd3'\x88\xd8\x87M\x81M\x90&\xd4,\xd4-\xd8\xd7\xd1\xd3\x80D\xd8\x88g\x90w\xa0\xd0$\xd0$r   )\xdapathlibr   \xdaplaywright.sync_apir   r   \xdaboolr"   \xa9 r   r   \xda<module>r'      s'   \xf0\xdd \xdd /\xf2\xf0	%\x984\xf0 	%\xb0T\xb8D\xb1[\xf4 	%r   
```

## src/core/__pycache__/db.cpython-312.pyc
```
\xcb
    Ťpi\xaf  \xe3                   \xf3B   \x97 d dl Z d dlmZ  ed\xab      dz  Zd\x84 Zdd\x84Zd\x84 Zy)	\xe9    N)\xdaPath\xdadatazautoapply.dbc                  \xf3\xe4   \x97 t         j                  j                  dd\xac\xab       t        j                  t         \xab      5 } | j                  d\xab       | j                  \xab        d d d \xab       y # 1 sw Y   y xY w)NT)\xdaparents\xdaexist_oka\xfa  
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
        )\xdaDB_PATH\xdaparent\xdamkdir\xdasqlite3\xdaconnect\xdaexecute\xdacommit)\xdacons    \xfa/app/src/core/db.py\xdainit_dbr      sO   \x80 \xdc\x87N\x81N\xd7\xd1\xa0\xb0\xd0\xd45\xdc	\x8f\x89\x9c\xd4	!\xa0S\xd8\x8f\x89\xf0 \xf4 	\xf0 	\x8f
\x89
\x8c\xf7! 
"\xd7	!\xd1	!\xfas   \xbb"A&\xc1&A/c                 \xf3\xb4   \x97 t        j                  t        \xab      5 }|j                  d| |||||||f\xab       |j	                  \xab        d d d \xab       y # 1 sw Y   y xY w)Na\xc2  
            INSERT INTO jobs (platform, job_url, title, company, location, score, status, reason)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(platform, job_url) DO UPDATE SET
                title=excluded.title,
                company=excluded.company,
                location=excluded.location,
                score=excluded.score,
                status=excluded.status,
                reason=excluded.reason;
        )r   r   r   r   r   )	\xdaplatform\xdajob_url\xdastatus\xdatitle\xdacompany\xdalocation\xdascore\xdareasonr   s	            r   \xda
upsert_jobr      sO   \x80 \xdc	\x8f\x89\x9c\xd4	!\xa0S\xd8\x8f\x89\xf0 
\xf0 \x98\xa0\xa8\xb0\xb85\xc0&\xc8&\xd0Q\xf4
	S\xf0 	\x8f
\x89
\x8c\xf7 
"\xd7	!\xd1	!\xfas   \x9a+A\xc1Ac                 \xf3\xba   \x97 t        j                  t        \xab      5 }|j                  d| |f\xab      }|j	                  \xab       }|r|d   nd cd d d \xab       S # 1 sw Y   y xY w)Nz6SELECT status FROM jobs WHERE platform=? AND job_url=?r   )r   r   r   r   \xdafetchone)r   r   r   \xdacur\xdarows        r   \xdaseenr    )   sJ   \x80 \xdc	\x8f\x89\x9c\xd4	!\xa0S\xd8\x8fk\x89k\xd0R\xd0U]\xd0_f\xd0Tg\xd3h\x88\xd8\x8fl\x89l\x8bn\x88\xd9\x88s\x901\x8av\xa0$\xf7 
"\xd7	!\xd2	!\xfas   \x9a-A\xc1A)NNNr   N)r   \xdapathlibr   r   r   r   r    \xa9 \xf3    r   \xda<module>r$      s(   \xf0\xdb \xdd \xe1
\x88v\x8b,\x98\xd1
'\x80\xf2\xf3(\xf3'r#   
```

## src/core/__pycache__/export.cpython-312.pyc
```
\xcb
    \xe0\xa4pi\xfe  \xe3                   \xf3B   \x97 d dl Z d dlZd dlmZ d dlmZ dedefd\x84Zd\x84 Zy)\xe9    N)\xdaPath)\xdadatetime\xdadb_path\xdaout_pathc                 \xf3\x94  \x97 |j                   j                  dd\xac\xab       t        j                  | \xab      5 }|j	                  d\xab      j                  \xab       }d d d \xab       |j                  ddd\xac\xab      5 }t        j                  |\xab      }|j                  g d\xa2\xab       |j                  \xab       d d d \xab       y # 1 sw Y   \x8c`xY w# 1 sw Y   y xY w)	NT)\xdaparents\xdaexist_okz\xa6
            SELECT platform, job_url, title, company, location, score, status, reason, created_at
            FROM jobs
            ORDER BY created_at DESC
        \xdaw\xda zutf-8)\xdanewline\xdaencoding)	\xdaplatform\xdajob_url\xdatitle\xdacompany\xdalocation\xdascore\xdastatus\xdareason\xda
created_at)\xdaparent\xdamkdir\xdasqlite3\xdaconnect\xdaexecute\xdafetchall\xdaopen\xdacsv\xdawriter\xdawriterow\xda	writerows)r   r   \xdacon\xdarows\xdafr
   s         \xfa/app/src/core/export.py\xdaexport_dailyr&      s\xa1   \x80 \xd8\x87O\x81O\xd7\xd1\xa0$\xb0\xd0\xd46\xdc	\x8f\x89\x98\xd4	!\xa0S\xd8\x8f{\x89{\xf0 \xf3 \xf7 \x89X\x8bZ\xf0	 	\xf7 
"\xf0 
\x8f\x89\x90s\xa0B\xb0\x88\xd4	9\xb8Q\xdc\x8fJ\x89J\x90q\x8bM\x88\xd8	\x8f
\x89
\xd2u\xd4v\xd8	\x8f\x89\x90D\xd4\xf7 
:\xd0	9\xf7 
"\xd0	!\xfa\xf7 
:\xd0	9\xfas   \xb3 B2\xc1/:B>\xc22B;\xc2>Cc                  \xf3H   \x97 t        j                  \xab       j                  d\xab      S )Nzout/daily_export_%Y-%m-%d.csv)r   \xdanow\xdastrftime\xa9 \xf3    r%   \xdadaily_filenamer,      s   \x80 \xdc\x8f<\x89<\x8b>\xd7"\xd1"\xd0#B\xd3C\xd0Cr+   )r   r   \xdapathlibr   r   r&   r,   r*   r+   r%   \xda<module>r.      s*   \xf0\xdb 
\xdb \xdd \xdd \xf0\x98$\xf0 \xa8$\xf3 \xf3Dr+   
```

## src/core/__pycache__/models.cpython-312.pyc
```
\xcb
    \xadepiQ  \xe3                   \xf3\xe2   \x97 d dl mZmZmZ d dlmZmZ d dlmZmZ d dl	m
Z
mZ  G d\x84 de\xab      Z G d\x84 de\xab      Z G d	\x84 d
e\xab      Z G d\x84 de\xab      Z G d\x84 de\xab      Z G d\x84 de\xab      Z G d\x84 de\xab      Zy)\xe9    )\xdaList\xdaOptional\xdaDict)\xda	BaseModel\xdaField)\xdadatetime\xdadate)\xdauuid4\xdaUUIDc                   \xf3J   \x97 e Zd ZU eed<   eed<   eed<   dZee   ed<   eed<   y)\xda
Experience\xdatitle\xdacompany\xda
start_dateN\xdaend_date\xdadescription\xa9\xda__name__\xda
__module__\xda__qualname__\xdastr\xda__annotations__r	   r   r   \xa9 \xf3    \xfa/app/src/core/models.pyr   r      s&   \x85 \xd8\x83J\xd8\x83L\xd8\xd3\xd8#\x80H\x88h\x90t\x89n\xd3#\xd8\xd4r   r   c                   \xf3J   \x97 e Zd ZU eed<   eed<   eed<   dZee   ed<   eed<   y)\xda	Education\xdainstitution\xdadegreer   Nr   \xdafield_of_studyr   r   r   r   r   r      s'   \x85 \xd8\xd3\xd8\x83K\xd8\xd3\xd8#\x80H\x88h\x90t\x89n\xd3#\xd8\xd4r   r   c                   \xf3"   \x97 e Zd ZU eed<   eed<   y)\xdaSkill\xdaname\xdalevelN)r   r   r   r   r   r   r   r   r"   r"      s   \x85 \xd8
\x83I\xd8\x84Jr   r"   c                   \xf3\xb6   \x97 e Zd ZU  ee\xac\xab      Zeed<   eed<   eed<   eed<   eed<   g Z	e
e   ed<   g Ze
e   ed<   g Ze
e   ed	<   d
Zee   ed<   d
Zee   ed<   y
)\xdaCandidateProfile\xa9\xdadefault_factory\xdaidr#   \xdaemail\xdaphone\xdasummary\xdaexperiences\xda	education\xdaskillsN\xdalinkedin_url\xdaportfolio_url)r   r   r   r   r
   r)   r   r   r   r-   r   r   r.   r   r/   r"   r0   r   r1   r   r   r   r&   r&      sl   \x85 \xd9\xa0U\xd4+\x80B\x88\xd3+\xd8
\x83I\xd8\x83J\xd8\x83J\xd8\x83L\xd8$&\x80K\x90\x90j\xd1!\xd3&\xd8!#\x80I\x88t\x90I\x89\xd3#\xd8\x80F\x88D\x90\x89K\xd3\xd8"&\x80L\x90(\x983\x91-\xd3&\xd8#'\x80M\x908\x98C\x91=\xd4'r   r&   c                   \xf3h   \x97 e Zd ZU eed<   eed<   eed<   eed<   ee   ed<   eed<   eed<   dZeed	<   y
)\xdaJobOpportunityr)   r   r   r   \xdarequirements\xdaurl\xdasourceg        \xdamatch_scoreN)r   r   r   r   r   r   r7   \xdafloatr   r   r   r3   r3   $   s5   \x85 \xd8\x83G\xd8\x83J\xd8\x83L\xd8\xd3\xd8\x90s\x91)\xd3\xd8	\x83H\xd8\x83K\xd8\x80K\x90\xd4r   r3   c                   \xf3\x82   \x97 e Zd ZU  ee\xac\xab      Zeed<   eed<   eed<   eed<    ee	j                  \xac\xab      Ze	ed<   eed<   y)	\xdaResumer'   r)   \xda
profile_id\xdajob_id\xdacontent\xda
created_at\xdaversion_tagN)r   r   r   r   r
   r)   r   r   r   r   \xdanowr>   r   r   r   r:   r:   .   s:   \x85 \xd9\xa0U\xd4+\x80B\x88\xd3+\xd8\xd3\xd8\x83K\xd8\x83L\xd9 \xb0\xb7\xb1\xd4>\x80J\x90\xd3>\xd8\xd4r   r:   c                   \xf3\xa4   \x97 e Zd ZU  ee\xac\xab      Zeed<   eed<   eed<   eed<   dZ	eed<    ee
j                  \xac\xab      Ze
ed<   eed	<   d
Zee   ed<   y
)\xdaApplicationr'   r)   r<   r;   \xda	resume_id\xdaApplied\xdastatus\xda
applied_at\xdaplatformN\xdanotes)r   r   r   r   r
   r)   r   r   r   rE   r   r@   rF   rH   r   r   r   r   rB   rB   6   sQ   \x85 \xd9\xa0U\xd4+\x80B\x88\xd3+\xd8\x83K\xd8\xd3\xd8\x83O\xd8\x80F\x88C\xd3\xd9 \xb0\xb7\xb1\xd4>\x80J\x90\xd3>\xd8\x83M\xd8\x80E\x888\x90C\x89=\xd4r   rB   N)\xdatypingr   r   r   \xdapydanticr   r   r   r	   \xdauuidr
   r   r   r   r"   r&   r3   r:   rB   r   r   r   \xda<module>rL      sh   \xf0\xdf '\xd1 '\xdf %\xdf #\xdf \xf4\x90\xf4 \xf4\x90	\xf4 \xf4\x88I\xf4 \xf4
(\x90y\xf4 
(\xf4\x90Y\xf4 \xf4\x88Y\xf4 \xf4 \x90)\xf5  r   
```

## src/core/__pycache__/persistence.cpython-312.pyc
```
\xcb
    Kjpi\x81	  \xe3                   \xf3\xf8   \x97 d dl Z d dlZd dlmZmZmZ d dlmZmZ dZ	ej                  j                  e	d\xab      Zej                  j                  e	d\xab      Zej                  j                  e	d\xab      Z G d\x84 d	\xab      Zy)
\xe9    N)\xdaDict\xdaList\xdaAny)\xdaCandidateProfile\xdaApplication\xdadatazprofile.jsonzmetrics.jsonzapplications.jsonc                   \xf3<   \x97 e Zd Zd\x84 Zdedeeef   dee	   fd\x84Z
d\x84 Zy)\xdaPersistenceManagerc                 \xf3~   \x97 t         j                  j                  t        \xab      st        j                  t        \xab       y y )N)\xdaos\xdapath\xdaexists\xdaDATA_DIR\xdamakedirs)\xdaselfs    \xfa/app/src/core/persistence.py\xda__init__zPersistenceManager.__init__   s#   \x80 \xdc\x8fw\x89w\x8f~\x89~\x9ch\xd4'\xdc\x8fK\x89K\x9c\xd5!\xf0 (\xf3    \xdaprofile\xdametrics\xdaapplicationsc                 \xf3\xde  \x97 |r<t        t        dd\xac\xab      5 }|j                  |j                  d\xac\xab      \xab       ddd\xab       t        t        dd\xac\xab      5 }t        j                  ||d\xac\xab       ddd\xab       |D \x8fcg c]  }|j                  d\xac\xab      \x91\x8c }}t        t        dd\xac\xab      5 }t        j                  ||dd	\xac
\xab       ddd\xab       y# 1 sw Y   \x8c\x90xY w# 1 sw Y   \x8cixY wc c}w # 1 sw Y   yxY w)z)Saves current system state to JSON files.\xdaw\xfautf-8\xa9\xdaencoding\xe9   )\xdaindentN\xdajson)\xdamodeF)r   \xdaensure_ascii)	\xdaopen\xdaPROFILE_FILE\xdawrite\xdamodel_dump_json\xdaMETRICS_FILEr   \xdadump\xda
model_dump\xdaAPPLICATIONS_FILE)r   r   r   r   \xdaf\xdaapp\xdaapp_list_jsons          r   \xda	save_datazPersistenceManager.save_data   s\xc3   \x80 \xf1 \xdc\x94l\xa0C\xb0'\xd5:\xb8a\xd8\x97\x91\x98\xd7/\xd1/\xb0q\xd0/\xd39\xd4:\xf7 ;\xf4 \x94,\xa0\xa8g\xd56\xb8!\xdc\x8fI\x89I\x90g\x98q\xa8\xd5+\xf7 7\xf1 AM\xd3M\xc1\xb8\x98\x9f\x99\xa8V\x98\xd54\xc0\x88\xd0M\xdc\xd4#\xa0S\xb07\xd5;\xb8q\xdc\x8fI\x89I\x90m\xa0Q\xa8q\xb8u\xd5E\xf7 <\xd0;\xf7 ;\xd0:\xfa\xf7 7\xd06\xfc\xf2 N\xdf;\xd0;\xfas)   \x95"C\xc1C\xc16C\xc2#C#\xc3C\xc3C\xc3#C,c                 \xf3\xdc  \x97 d}d}g }t         j                  j                  t        \xab      r?t	        t        dd\xac\xab      5 }	 t        j                  |j                  \xab       \xab      }ddd\xab       t         j                  j                  t        \xab      r0t	        t        dd\xac\xab      5 }t        j                  |\xab      }ddd\xab       t         j                  j                  t        \xab      rSt	        t        dd\xac\xab      5 }	 t        j                  |\xab      }|D \x8fcg c]  }t        j                  |\xab      \x91\x8c }}ddd\xab       |||fS #  Y \x8c\xdaxY w# 1 sw Y   \x8c\xdexY w# 1 sw Y   \x8c\x97xY wc c}w #  Y \x8c5xY w# 1 sw Y   \x8c9xY w)z\x8e
        Loads system state. Returns tuple (profile, metrics, applications).
        Returns (None, None, None) if files don't exist.
        N\xdarr   r   )r   r   r   r#   r"   r   \xdamodel_validate_json\xdareadr&   r   \xdaloadr)   r   \xdamodel_validate)r   r   r   r   r*   \xdaraw_appsr+   s          r   \xda	load_datazPersistenceManager.load_data#   s   \x80 \xf0
 \x88\xd8\x88\xd8\x88\xe4\x8f7\x897\x8f>\x89>\x9c,\xd4'\xdc\x94l\xa0C\xb0'\xd5:\xb8a\xf0\xdc.\xd7B\xd1B\xc01\xc76\xc16\xc38\xd3L\x90G\xf7 ;\xf4 \x8f7\x897\x8f>\x89>\x9c,\xd4'\xdc\x94l\xa0C\xb0'\xd5:\xb8a\xdc\x9f)\x99)\xa0A\x9b,\x90\xf7 ;\xf4 \x8f7\x897\x8f>\x89>\xd4+\xd4,\xdc\xd4'\xa8\xb0w\xd5?\xc01\xf0\xdc#\x9fy\x99y\xa8\x9b|\x90H\xd9OW\xd3#X\xc9x\xc8\xa4K\xd7$>\xd1$>\xb8s\xd5$C\xc8x\x90L\xd0#X\xf7 @\xf0 \x98\xa0\xd0-\xd0-\xf8\xf0\xd9\xfa\xf7	 ;\xd0:\xfa\xf7 ;\xd0:\xfc\xf2 $Y\xf8\xf0\xd9\xfa\xf7 @\xd0?\xfasX   \xbcD>\xbe#D7\xc2E
\xc31E"\xc33E\xc4E\xc4(E\xc47D;\xc49D>\xc4>E\xc5
E\xc5E\xc5E\xc5E"\xc5"E+N)\xda__name__\xda
__module__\xda__qualname__r   r   r   \xdastr\xdaintr   r   r-   r5   \xa9 r   r   r
   r
      s:   \x84 \xf2"\xf0F\xd0!1\xf0 F\xb8D\xc0\xc0c\xc0\xb9N\xf0 F\xd0Z^\xd0_j\xd1Zk\xf3 F\xf3&.r   r
   )r   r   \xdatypingr   r   r   \xdasrc.core.modelsr   r   r   r   \xdajoinr#   r&   r)   r
   r;   r   r   \xda<module>r?      sa   \xf0\xdb \xdb 	\xdf "\xd1 "\xdf 9\xe0\x80\xd8\x8fw\x89w\x8f|\x89|\x98H\xa0n\xd35\x80\xd8\x8fw\x89w\x8f|\x89|\x98H\xa0n\xd35\x80\xd8\x97G\x91G\x97L\x91L\xa0\xd0+>\xd3?\xd0 \xf74.\xf2 4.r   
```

## src/core/__pycache__/runner.cpython-312.pyc
```
\xcb
    \xee\xa4pi\xc3  \xe3                   \xf36  \x97 d dl Z d dlZd dlZd dlZd dlZd dlmZ d dlmZmZ d dl	m
Z
mZmZmZ d dlmZmZ d dlmZ d dlmZmZ d dlmZ d dlmZ  ed	\xab      Z ed
\xab      dz  Z ed
\xab      dz  dz  Z ed
\xab      dz  dz  Zd\x84 Zd\x84 Z dd\x84Z!d\x84 Z"e#dk(  r e"\xab        yy)\xe9    N)\xdaPath)\xdadatetime\xdadate)\xdainit_db\xdaseen\xda
upsert_job\xdaDB_PATH)\xdaexport_daily\xdadaily_filename)\xdaopen_context)\xdaenqueue\xdaextract_gupy_links)\xdaprocess_jobzprofile_br.json\xdadatazqueue.jsonl\xdasessionszlinkedin_state.jsonzgupy_state.jsonc                  \xf3T   \x97 t        j                  t        j                  d\xac\xab      \xab      S \xa9Nzutf-8)\xdaencoding)\xdajson\xdaloads\xdaPROFILE_PATH\xda	read_text\xa9 \xf3    \xfa/app/src/core/runner.py\xdaload_profiler      s   \x80 \x9c4\x9f:\x99:\xa4l\xd7&<\xd1&<\xc0g\xd0&<\xd3&N\xd3O\xd0Or   c                  \xf3\xf6   \x97 dd l } t        j                  \xab       j                  \xab       }| j	                  t
        \xab      5 }|j                  d|f\xab      j                  \xab       }d d d \xab       r|d   S dS # 1 sw Y   \x8cxY w)Nr   zPSELECT COUNT(*) FROM jobs WHERE status='applied' AND substr(created_at, 1, 10)=?)\xdasqlite3r   \xdatoday\xda	isoformat\xdaconnectr	   \xdaexecute\xdafetchone)r   r   \xdacon\xdarows       r   \xdacount_applied_todayr&      sm   \x80 \xdb\xdc\x8fJ\x89J\x8bL\xd7"\xd1"\xd3$\x80E\xd8	\x8f\x89\x9c\xd4	!\xa0S\xd8\x8fk\x89k\xd0l\xd0ot\xd0nv\xd3w\xf7  A\xf1  A\xf3  C\x88\xf7 
"\xe1\x883\x88q\x896\xd0\x98a\xd0\xf7 
"\xd0	!\xfas   \xbc"A/\xc1/A8c                 \xf3\xe8   \x97 t         j                  \xab       sg S t         j                  d\xac\xab      j                  \xab       }g }|d |  D ]&  }|j	                  t        j                  |\xab      \xab       \x8c( |S #  Y \x8c/xY wr   )\xda
QUEUE_PATH\xdaexistsr   \xda
splitlines\xdaappendr   r   )\xdalimit\xdalines\xdaitems\xdalns       r   \xda
read_queuer0      sg   \x80 \xdc\xd7\xd1\xd4\xa0r\xa0	\xdc\xd7 \xd1 \xa8'\xd0 \xd32\xd7=\xd1=\xd3?\x80E\xd8\x80E\xd8\x90F\x90U\x8bm\x88\xd8\x8f\\x89\\x9c$\x9f*\x99*\xa0R\x9b.\xd5)\xf0 \xf0 \x80L\xf8\xf0 	\x91\xfas   \xc1$A-\xc1-A1c            	      \xf3  \x97 t        \xab        t        \xab       } t        j                  j	                  dd\xab      dk(  }| j	                  di \xab      j	                  dg \xab      D ]  }t        d|\xab       \x8c | j	                  di \xab      j	                  dg \xab      D ]  }t        d|\xab       \x8c t        | d   d	   \xab      }t        \xab       }t        d
||z
  \xab      }|d
k(  r"t        t        t        t        \xab       \xab      \xab       y d}t        t        d||z  \xab      d\xab      }t        |t        \xac\xab      \  }}	}
}t        |t         \xac\xab      \  }}}}	 t#        |\xab      D \x90]\xb9  }t        \xab       |k\  r \x90n\xa9t%        d\xac\xab      }t'        j(                  |\xab       d
}|D \x90]R  }||k\  r \x90nJ|j	                  d\xab      }|j	                  d\xab      }|s\x8c1t+        |dv r|nd|\xab      r\x8cD|dk(  rc|j-                  |d\xac\xab       |j/                  d\xab       t1        t3        j4                  d|j7                  \xab       \xab      \xab      D ]  }t        d|\xab       \x8c \x8c\xac|dk(  rR|j-                  |d\xac\xab       |j/                  d\xab       t9        |j7                  \xab       \xab      }|D ]  }t        d|\xab       \x8c \x90\x8c|dk(  r#t;        ||| \xab       t+        d|\xab      dk(  r|dz  }\x90\x8c+|dk(  s\x90\x8c2t=        ||| \xab       t+        d|\xab      dk(  r|dz  }\x90\x8cU t'        j>                  dd\xab      }tA        jB                  |\xab       \x90\x8c\xbc t        t        t        t        \xab       \xab      \xab       |
jE                  \xab        |	jE                  \xab        |jG                  \xab        |jE                  \xab        |jE                  \xab        |jG                  \xab        y # t        t        t        t        \xab       \xab      \xab       |
jE                  \xab        |	jE                  \xab        |jG                  \xab        |jE                  \xab        |jE                  \xab        |jG                  \xab        w xY w)N\xdaHEADLESS\xda1\xdaseeds\xdalinkedin_search_pages\xdalinkedin_search\xdagupy_search_pages\xdaweb_discovery\xdapreferencias\xdameta_candidaturas_diar   \xe9
   \xe9   \xe9   )\xdaheadless\xdastorage_state_pathi\x90  )r,   \xdaplatform\xdaurl)\xdalinkedin\xdagupy\xdasource\xdadomcontentloaded)\xda
wait_untili\xb0  z(https://www\.linkedin\.com/jobs/view/\d+rB   rC   \xdaappliedi  i   )$r   r   \xdaos\xdaenviron\xdagetr   \xdaintr&   \xdamaxr
   r	   r   r   \xdaminr   \xdaSTATE_LI\xda
STATE_GUPY\xdaranger0   \xdarandom\xdashuffler   \xdagoto\xdawait_for_timeout\xdaset\xdare\xdafindall\xdacontentr   \xda
li_process\xdagupy_process\xdarandint\xdatime\xdasleep\xdaclose\xdastop)\xdaprofiler>   rA   \xda
meta_daily\xdaapplied_today\xda	remaining\xdawindows\xda
per_window\xdap1\xdab1\xdac1\xdapage_li\xdap2\xdab2\xdac2\xda	page_gupy\xdaw\xdaqueue\xdaapplied_in_window\xdaitemr@   \xdam\xdalinks\xdalk\xdasleep_ss                            r   \xdamainrv   &   sX  \x80 \xdc\x84I\xdc\x8bn\x80G\xdc\x8fz\x89z\x8f~\x89~\x98j\xa8#\xd3.\xb0#\xd15\x80H\xe0\x8f{\x89{\x987\xa0B\xd3'\xd7+\xd1+\xd0,C\xc0R\xd6H\x88\xdc\xd0!\xa03\xd5'\xf0 I\xe0\x8f{\x89{\x987\xa0B\xd3'\xd7+\xd1+\xd0,?\xc0\xd6D\x88\xdc\x90\xa0\xd5%\xf0 E\xf4 \x90W\x98^\xd1,\xd0-D\xd1E\xd3F\x80J\xdc'\xd3)\x80M\xdc\x90A\x90z\xa0M\xd11\xd32\x80I\xe0\x90A\x82~\xdc\x94W\x9cd\xa4>\xd3#3\xd34\xd45\xd8\xe0\x80G\xdc\x94S\x98\x98I\xa8\xd10\xd31\xb01\xd35\x80J\xe4&\xb0\xccX\xd4V\xd1\x80B\x88\x88B\x90\xdc(\xb0(\xccz\xd4Z\xd1\x80B\x88\x88B\x90	\xf0)*\xdc\x90w\x97\x88A\xdc"\xd3$\xa8
\xd22\xb2E\xdc\xa0S\xd4)\x88E\xdc\x8fN\x89N\x985\xd4!\xd8 !\xd0\xdc\x90\xd8$\xa8
\xd22\xb2E\xd8\x9f8\x998\xa0J\xd3/\x90\xd8\x97h\x91h\x98u\x93o\x90\xd9\x98H\xdc\xa0H\xd00D\xd1$D\x99\xc8(\xd0TW\xd4X\xd0Zb\xe0\xd00\xd20\xd8\x97L\x91L\xa0\xd01C\x90L\xd4D\xd8\xd7,\xd1,\xa8T\xd42\xdc \xa4\xa7\xa1\xd0,W\xd0Y`\xd7Yh\xd1Yh\xd3Yj\xd3!k\xd6l\x98\xdc\xa0
\xa8A\xd5.\xf0 m\xe0\xe0\x98\xd2.\xd8\x97N\x91N\xa03\xd03E\x90N\xd4F\xd8\xd7.\xd1.\xa8t\xd44\xdc.\xa8y\xd7/@\xd1/@\xd3/B\xd3C\x90E\xdb#\x98\xa4W\xa8V\xb0R\xd5%8\x98e\xd9\xe0\x98z\xd2)\xdc\x98w\xa8\xa8W\xd45\xdc\x98J\xa8\xd3,\xb0	\xd29\xd0;L\xd0PQ\xd1;Q\xd0;L\xd9\xe0\x98v\xd4%\xdc \xa0\xa8C\xb0\xd49\xdc\x98F\xa0C\xd3(\xa8I\xd25\xd07H\xc8A\xd17M\xd07H\xd9\xf0; \xf4< \x97n\x91n\xa0T\xa84\xd30\x88G\xdc\x8fJ\x89J\x90w\xd6\xf0I  \xf4L 	\x94W\x9cd\xa4>\xd3#3\xd34\xd45\xd8
\x8f\x89\x8c
\x90B\x97H\x91H\x94J\xa0\xa7\xa1\xa4	\xd8
\x8f\x89\x8c
\x90B\x97H\x91H\x94J\xa0\xa7\xa1\xa5	\xf8\xf4 	\x94W\x9cd\xa4>\xd3#3\xd34\xd45\xd8
\x8f\x89\x8c
\x90B\x97H\x91H\x94J\xa0\xa7\xa1\xa4	\xd8
\x8f\x89\x8c
\x90B\x97H\x91H\x94J\xa0\xa7\xa1\xa5	\xfas   \xc47E4N \xca-AN \xceBP\xda__main__)\xe9\xc8   )$r   rH   rQ   r\   rV   \xdapathlibr   r   r   \xdasrc.core.dbr   r   r   r	   \xdasrc.core.exportr
   r   \xdasrc.core.browserr   \xdasrc.core.sourcesr   r   \xdasrc.drivers.linkedin_easy_applyr   rY   \xdasrc.drivers.gupy_fast_applyrZ   r   r(   rN   rO   r   r&   r0   rv   \xda__name__r   r   r   \xda<module>r\x81      s\x98   \xf0\xdb \xdb 	\xdb \xdb \xdb 	\xdd \xdf #\xdf :\xd3 :\xdf 8\xdd )\xdf 8\xdd E\xdd C\xe1\xd0%\xd3&\x80\xd9\x90&\x8b\\x98M\xd1)\x80
\xd9\x90\x8b<\x98*\xd1$\xd0'<\xd1<\x80\xd9\x90&\x8b\\x98J\xd1&\xd0):\xd1:\x80
\xe2 O\xf2 \xf3\xf2A*\xf0F \x88z\xd2\xd9\x85F\xf0 r   
```

## src/core/__pycache__/scoring.cpython-312.pyc
```
\xcb
    Τpi  \xe3                   \xf3.   \x97 d e dee    defd\x84Zdede fd\x84Zy)\xdatext\xdakeywords\xdareturnc                 \xf3T   \x87\x97 | xs dj                  \xab       \x8at        \x88fd\x84|D \xab       \xab      S )N\xda c              3   \xf3H   \x95K  \x97 | ]  }|j                  \xab       \x89v s\x8cd \x96\x97 \x8c y\xadw)\xe9   N)\xdalower)\xda.0\xdak\xdats     \x80\xfa/app/src/core/scoring.py\xda	<genexpr>zscore_text.<locals>.<genexpr>   s   \xf8\xe8 \xf8\x80 \xd05\x99(\x90Q\xa0a\xa7g\xa1g\xa3i\xb01\xa2n\x8cq\x99(\xf9s   \x83"\x9b")r	   \xdasum)r   r   r   s     @r   \xda
score_textr      s&   \xf8\x80 \xd8	\x8a\x90\xd7\xd1\xd3\x80A\xdc\xd35\x99(\xd35\xd35\xd05\xf3    \xdascorec                 \xf3   \x97 | dk\  ry| dk\  ryy)N\xe9   \xdaapply\xe9   \xdaneeds_manual\xdaskip\xa9 )r   s    r   \xdadecider      s   \x80 \xd8\x90\x82z\x98'\xd8\x90\x82z\x98.\xd8r   N)\xdastr\xdalist\xdaintr   r   r   r   r   \xda<module>r      s6   \xf0\xf06\x90S\xf0 6\xa0D\xa8\xa1I\xf0 6\xb0#\xf3 6\xf0\x90#\xf0 \x98#\xf4 r   
```

## src/core/__pycache__/sources.cpython-312.pyc
```
\xcb
    ڤpiC  \xe3                   \xf3   \x97 d dl Z d dlZd dlmZ d dlmZ  ed\xab      dz  Zej                  j                  dd\xac\xab       dde	d	e	d
e
dz  fd\x84Zddee	   de	fd\x84Z ej                  dej                  \xab      Zde	dee	   fd\x84Zy)\xe9    N)\xdaPath)\xdaquote\xdadatazqueue.jsonlT)\xdaparents\xdaexist_ok\xdaplatform\xdaurl\xdametac           	      \xf3\xc2   \x97 |xs i }t         j                  dd\xac\xab      5 }|j                  t        j                  | ||d\x9cd\xac\xab      dz   \xab       d d d \xab       y # 1 sw Y   y xY w)N\xdaazutf-8)\xdaencoding)r   r	   r
   F)\xdaensure_ascii\xda
)\xda
QUEUE_PATH\xdaopen\xdawrite\xdajson\xdadumps)r   r	   r
   \xdafs       \xfa/app/src/core/sources.py\xdaenqueuer   	   sN   \x80 \xd8\x8a:\x902\x80D\xdc	\x8f\x89\x98\xa0w\x88\xd4	/\xb01\xd8	\x8f\x89\x94\x97
\x91
\xa8\xb8\xc0d\xd1K\xd0Z_\xd4`\xd0cg\xd1g\xd4h\xf7 
0\xd7	/\xd1	/\xfas   \x9e.A\xc1A\xdaqueries\xdageoc                 \xf3X   \x97 g }| D ]"  }|j                  dt        |\xab      \x9b d|\x9b \x9d\xab       \x8c$ |S )Nz/https://www.linkedin.com/jobs/search/?keywords=z&locationId=)\xdaappendr   )r   r   \xdaurls\xdaqs       r   \xdalinkedin_search_urlsr      s6   \x80 \xd8\x80D\xdb\x88\xd8\x8f\x89\xd0E\xc4e\xc8A\xc3h\xc0Z\xc8|\xd0\_\xd0[`\xd0a\xd5b\xf0 \xe0\x80K\xf3    z*https?://[a-z0-9\-]+\.gupy\.io/[^\s\"'>)]+\xdatext\xdareturnc                 \xf3l   \x97 t        t        j                  t        j	                  | xs d\xab      \xab      \xab      S )N\xda )\xdalist\xdadict\xdafromkeys\xdaGUPY_RE\xdafindall)r    s    r   \xdaextract_gupy_linksr)      s#   \x80 \xdc\x94\x97\x91\x9cg\x9fo\x99o\xa8d\xaaj\xb0b\xd39\xd3:\xd3;\xd0;r   )N)\xda	106057199)r   \xdare\xdapathlibr   \xdaurllib.parser   r   \xdaparent\xdamkdir\xdastrr%   r   r$   r   \xdacompile\xda
IGNORECASEr'   r)   \xa9 r   r   \xda<module>r4      s\xa1   \xf0\xdb \xdb 	\xdd \xdd \xe1\x90&\x8b\\x98M\xd1)\x80
\xd8 
\xd7 \xd1 \xd7 \xd1 \xa0\xa8t\xd0 \xd4 4\xf1i\x90c\xf0 i\xa0\xf0 i\xa84\xb0$\xa9;\xf3 i\xf1
\xa0$\xa0s\xa1)\xf0 \xb0#\xf3 \xf0 \x88"\x8f*\x89*\xd0B\xc0B\xc7M\xc1M\xd3
R\x80\xf0<\x98S\xf0 <\xa0T\xa8#\xa1Y\xf4 <r   
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
from src.core.db import init_db, seen, upsert_job, DB_PATH
from src.core.export import export_daily, daily_filename
from src.core.browser import open_context
from src.core.sources import enqueue, extract_gupy_links
from src.drivers.linkedin_easy_apply import process_job as li_process
from src.drivers.gupy_fast_apply import process_job as gupy_process

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
    profile = load_profile()
    headless = os.environ.get("HEADLESS", "1") == "1"

    for url in profile.get("seeds", {}).get("linkedin_search_pages", []):
        enqueue("linkedin_search", url)
    for url in profile.get("seeds", {}).get("gupy_search_pages", []):
        enqueue("web_discovery", url)

    meta_daily = int(profile["preferencias"]["meta_candidaturas_dia"])
    applied_today = count_applied_today()
    remaining = max(0, meta_daily - applied_today)

    if remaining == 0:
        export_daily(DB_PATH, Path(daily_filename()))
        return

    windows = 10
    per_window = min(max(1, remaining // windows), 6)

    p1, b1, c1, page_li = open_context(headless=headless, storage_state_path=STATE_LI)
    p2, b2, c2, page_gupy = open_context(headless=headless, storage_state_path=STATE_GUPY)

    try:
        for w in range(windows):
            if count_applied_today() >= meta_daily: break
            queue = read_queue(limit=400)
            random.shuffle(queue)
            applied_in_window = 0
            for item in queue:
                if applied_in_window >= per_window: break
                platform = item.get("platform")
                url = item.get("url")
                if not url: continue
                if seen(platform if platform in ("linkedin", "gupy") else "source", url): continue

                if platform == "linkedin_search":
                    page_li.goto(url, wait_until="domcontentloaded")
                    page_li.wait_for_timeout(1200)
                    for m in set(re.findall(r"https://www\.linkedin\.com/jobs/view/\d+", page_li.content())):
                        enqueue("linkedin", m)
                    continue

                if platform == "web_discovery":
                    page_gupy.goto(url, wait_until="domcontentloaded")
                    page_gupy.wait_for_timeout(1200)
                    links = extract_gupy_links(page_gupy.content())
                    for lk in links: enqueue("gupy", lk)
                    continue

                if platform == "linkedin":
                    li_process(page_li, url, profile)
                    if seen("linkedin", url) == "applied": applied_in_window += 1
                    continue

                if platform == "gupy":
                    gupy_process(page_gupy, url, profile)
                    if seen("gupy", url) == "applied": applied_in_window += 1
                    continue
            sleep_s = random.randint(1800, 7200)
            time.sleep(sleep_s)
    finally:
        export_daily(DB_PATH, Path(daily_filename()))
        c1.close(); b1.close(); p1.stop()
        c2.close(); b2.close(); p2.stop()

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

## src/drivers/__pycache__/gupy_fast_apply.cpython-312.pyc
```
\xcb
    \xa5pi\xb0  \xe3                   \xf3*   \x97 d dl mZ d dlmZmZ dZd\x84 Zy)\xe9    )\xda
upsert_job)\xda
score_text\xdadecide\xdagupyc                 \xf3\xb6  \x97 | j                  |d\xac\xab       | j                  d\xab      j                  \xab       r+| j                  d\xab      j                  j	                  d\xac\xab      nd}| j                  d\xab      j	                  d\xac\xab      }t        |xs ddz   |z   |d	   \xab      }t        |\xab      }|d
k(  rt        t        |d||d\xac\xab       y | j                  d\xab      j                  \xab       st        t        |d||d\xac\xab       y |dk(  rt        t        |d||d\xac\xab       y | j                  d\xab      j                  }|j                  \xab       st        t        |d||d\xac\xab       y |j                  \xab        | j                  d\xab       | j                  d\xab      j                  \xab       s| j                  d\xab      j                  \xab       rt        t        |d||d\xac\xab       y t        t        |d||\xac\xab       y )N\xdadomcontentloaded)\xda
wait_until\xdah1i\xb8  )\xdatimeout\xda \xdabody\xda \xdaskills\xdaskip\xdaskipped_low_score\xdascore_baixo)\xdatitle\xdascore\xdareasonu   text=Candidatura Rápida\xdaneeds_manual\xda
nao_rapida\xdascore_mediozbutton:has-text('Candidatar')\xdabotao_nao_achadoi\xdc  z
text=Teste\xdatextarea\xdaperguntas_extras\xdaapplied)r   r   )\xdagoto\xdalocator\xdacount\xdafirst\xda
inner_textr   r   r   \xdaPLATFORM\xdaclick\xdawait_for_timeout)\xdapage\xdajob_url\xdaprofiler   r   r   \xdaaction\xdabtns           \xfa#/app/src/drivers/gupy_fast_apply.py\xdaprocess_jobr+      s\x93  \x80 \xd8\x87I\x81I\x88g\xd0"4\x80I\xd45\xd8AE\xc7\xc1\xc8d\xd3AS\xd7AY\xd1AY\xd4A[\x88D\x8fL\x89L\x98\xd3\xd7$\xd1$\xd7/\xd1/\xb8\xd0/\xd4=\xd0ac\x80E\xd8\x8f<\x89<\x98\xd3\xd7*\xd1*\xb04\xd0*\xd38\x80D\xdc\x98\x9a\xa0\xa0s\xd1*\xa8T\xd11\xb07\xb88\xd13D\xd3E\x80E\xdc\x90E\x8b]\x80F\xe0\x90\xd2\xdc\x948\x98W\xd0&9\xc0\xc8e\xd0\i\xd5j\xd8\xd8\x8f<\x89<\xd02\xd33\xd79\xd19\xd4;\xdc\x948\x98W\xa0n\xb8E\xc8\xd0Wc\xd5d\xd8\xd8\x90\xd2\xdc\x948\x98W\xa0n\xb8E\xc8\xd0Wd\xd5e\xd8\xe0
\x8f,\x89,\xd06\xd3
7\xd7
=\xd1
=\x80C\xd8\x8f9\x899\x8c;\xdc\x948\x98W\xa0n\xb8E\xc8\xd0Wi\xd5j\xd8\xe0\x87I\x81I\x84K\xd8\xd7\xd1\x98$\xd4\xd8\x87|\x81|\x90L\xd3!\xd7'\xd1'\xd4)\xa8T\xaf\\xa9\\xb8*\xd3-E\xd7-K\xd1-K\xd4-M\xdc\x948\x98W\xa0n\xb8E\xc8\xd0Wi\xd5j\xd8\xdc\x8cx\x98\xa0)\xb05\xc0\xd6F\xf3    N)\xdasrc.core.dbr   \xdasrc.core.scoringr   r   r"   r+   \xa9 r,   r*   \xda<module>r0      s   \xf0\xdd "\xdf /\xd8\x80\xf3Gr,   
```

## src/drivers/__pycache__/linkedin_easy_apply.cpython-312.pyc
```
\xcb
    \xa5pi\x8a  \xe3                   \xf3*   \x97 d dl mZ d dlmZmZ dZd\x84 Zy)\xe9    )\xda
upsert_job)\xda
score_text\xdadecide\xdalinkedinc           	      \xf3`  \x97 | j                  |d\xac\xab       | j                  d\xab      j                  \xab       r+| j                  d\xab      j                  j	                  d\xac\xab      nd}| j                  d\xab      j                  \xab       r+| j                  d\xab      j                  j	                  d\xac\xab      nd}t        |xs ddz   |z   |d	   \xab      }t        |\xab      }|d
k(  rt        t        |d||d\xac\xab       y | j                  d\xab      j                  }|j                  \xab       st        t        |d||d\xac\xab       y |dk(  rt        t        |d||d\xac\xab       y |j                  \xab        | j                  d\xab       t        d\xab      D ]\xb9  }| j                  d\xab      j                  \xab       r5| j                  d\xab      j                  \xab        t        t        |d||\xac\xab        y | j                  d\xab      j                  }	|	j                  \xab       r"|	j                  \xab        | j                  d\xab       \x8c\xa4t        t        |d||d\xac\xab        y  y )N\xdadomcontentloaded)\xda
wait_until\xdah1i\xb8  )\xdatimeout\xda zdiv.jobs-description\xda \xdaskills\xdaskip\xdaskipped_low_score\xdascore_baixo)\xdatitle\xdascore\xdareasonz+button:has-text('Candidatura simplificada')\xdaskipped_external_apply\xdaexterno\xdaneeds_manual\xdascore_medioi\xb0  \xe9
   z%button:has-text('Enviar candidatura')\xdaapplied)r   r   u   button:has-text('Avançar')i\x84  \xdaloop_ou_erro_modal)\xdagoto\xdalocator\xdacount\xdafirst\xda
inner_textr   r   r   \xdaPLATFORM\xdaclick\xdawait_for_timeout\xdarange)
\xdapage\xdajob_url\xdaprofiler   \xdadescr   \xdaaction\xdaeasy\xda_\xdanxts
             \xfa'/app/src/drivers/linkedin_easy_apply.py\xdaprocess_jobr.      s\xda  \x80 \xd8\x87I\x81I\x88g\xd0"4\x80I\xd45\xd8AE\xc7\xc1\xc8d\xd3AS\xd7AY\xd1AY\xd4A[\x88D\x8fL\x89L\x98\xd3\xd7$\xd1$\xd7/\xd1/\xb8\xd0/\xd4=\xd0ac\x80E\xd8RV\xd7R^\xd1R^\xd0_u\xd3Rv\xd7R|\xd1R|\xd4R~\x884\x8f<\x89<\xd0.\xd3/\xd75\xd15\xd7@\xd1@\xc8\xd0@\xd4N\xf0  EG\x80D\xdc\x98\x9a\xa0\xa0s\xd1*\xa8T\xd11\xb07\xb88\xd13D\xd3E\x80E\xdc\x90E\x8b]\x80F\xe0\x90\xd2\xdc\x948\x98W\xd0&9\xc0\xc8e\xd0\i\xd5j\xd8\xe0\x8f<\x89<\xd0E\xd3F\xd7L\xd1L\x80D\xd8\x8f:\x89:\x8c<\xdc\x948\x98W\xd0&>\xc0e\xd0SX\xd0aj\xd5k\xd8\xe0\x90\xd2\xdc\x948\x98W\xa0n\xb8E\xc8\xd0Wd\xd5e\xd8\xe0\x87J\x81J\x84L\xd8\xd7\xd1\x98$\xd4\xdc\x902\x8eY\x88\xd8\x8f<\x89<\xd0?\xd3@\xd7F\xd1F\xd4H\xd8\x8fL\x89L\xd0@\xd3A\xd7G\xd1G\xd4I\xdc\x94x\xa0\xa8)\xb85\xc8\xd5N\xd9\xd8\x8fl\x89l\xd08\xd39\xd7?\xd1?\x88\xd8\x8f9\x899\x8c;\xd8\x8fI\x89I\x8cK\xd8\xd7!\xd1!\xa0#\xd4&\xd8\xdc\x948\x98W\xa0n\xb8E\xc8\xd0Wk\xd5l\xd9\xf1 \xf3    N)\xdasrc.core.dbr   \xdasrc.core.scoringr   r   r!   r.   \xa9 r/   r-   \xda<module>r3      s   \xf0\xdd "\xdf /\xd8\x80\xf3!r/   
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
    page.goto(job_url, wait_until="domcontentloaded")
    title = page.locator("h1").first.inner_text(timeout=3000) if page.locator("h1").count() else ""
    desc = page.locator("div.jobs-description").first.inner_text(timeout=3000) if page.locator("div.jobs-description").count() else ""
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

    easy.click()
    page.wait_for_timeout(1200)
    for _ in range(10):
        if page.locator("button:has-text('Enviar candidatura')").count():
            page.locator("button:has-text('Enviar candidatura')").click()
            upsert_job(PLATFORM, job_url, "applied", title=title, score=score)
            return
        nxt = page.locator("button:has-text('Avançar')").first
        if nxt.count():
            nxt.click()
            page.wait_for_timeout(900)
            continue
        upsert_job(PLATFORM, job_url, "needs_manual", title=title, score=score, reason="loop_ou_erro_modal")
        return

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
from src.core.persistence import PersistenceManager

console = Console()

class BirthHub360:
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
        self.interview_prep_status = "Nenhuma entrevista agendada."

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
            # Ensure new metrics keys exist if loaded from old file
            if "networking" not in self.metrics: self.metrics["networking"] = 0
            if "followups" not in self.metrics: self.metrics["followups"] = 0

        if apps:
            self.applier.application_history = apps

    def save_state(self):
        """Saves current state."""
        self.persistence.save_data(self.profile, self.metrics, self.applier.application_history)

    def start(self):
        self.load_state()

        # Simple menu for mode selection
        console.clear()
        console.print(Panel("[bold cyan]Birth Hub 360 - Central de Comando[/bold cyan]"))
        console.print("1. Iniciar Ciclo Automático (Dashboard)")
        console.print("2. Simulador de Entrevista (Interativo)")
        console.print("3. Gerador de E-mail (Ferramenta)")
        choice = console.input("\n[bold]Escolha uma opção:[/bold] ")

        if choice == "2":
            self.simulator.run_session()
            sys.exit(0)
        elif choice == "3":
            self.run_email_tool()
            sys.exit(0)

        # Default to Dashboard Loop
        layout = self.make_layout()

        try:
            with Live(layout, refresh_per_second=4, screen=True):
                while True:
                    # 1. Update Header
                    layout["header"].update(Panel(Text("BIRTH HUB 360 AUTOMÁTICO - OPERANDO", style="bold green", justify="center")))

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

                        # Networking Action (New Module)
                        net_action = self.networker.attempt_connection(job.company)
                        if net_action:
                            self.metrics["networking"] += 1
                            layout["footer"].update(Panel(f"[bold cyan]NETWORKING:[/bold cyan] {net_action}"))
                            time.sleep(1)

                        # Update Log
                        layout["footer"].update(Panel(f"Candidatura enviada para {job.company} - {job.title} | Status: {app.status}"))

                        # SIMULATE INTERVIEW (10% chance for demo)
                        if random.random() < 0.1:
                            self.metrics["interviews"] += 1
                            questions = self.coach.generate_questions(job)
                            q_text = "\n".join([f"- {q}" for q in questions])
                            self.interview_prep_status = f"[bold]Preparação para {job.company}:[/bold]\n{q_text}\n\n[italic]Feedback IA:[/italic] {self.coach.simulate_feedback()}"

                            # Show interview prep in main temporarily
                            layout["main"].update(Panel(self.interview_prep_status, title="MÓDULO DE ENTREVISTAS ATIVO", style="bold white on blue"))
                            time.sleep(3) # Let user read

                        time.sleep(0.5)
                        self.save_state() # Save continuously

                    # 6. Monitoring & Follow-up
                    follow_ups = self.monitoring.check_for_follow_up(self.applier.application_history)
                    if follow_ups:
                        self.metrics["followups"] += len(follow_ups)
                        for action in follow_ups:
                             layout["footer"].update(Panel(f"[bold yellow]MONITORAMENTO:[/bold yellow] {action}"))
                             time.sleep(1)

                    # Update Side Panel with Strategy & Metrics
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

                    [bold]Última Ação de IA:[/bold]
                    Otimização de perfil para {high_match_jobs[-1].title if high_match_jobs else 'N/A'}
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
            Layout(name="footer", size=3)
        )
        layout["body"].split_row(
            Layout(name="side", ratio=1),
            Layout(name="main", ratio=3)
        )
        return layout

if __name__ == "__main__":
    hub = BirthHub360()
    hub.start()

```

## src/modules/__init__.py
```

```

## src/modules/__pycache__/__init__.cpython-312.pyc
```
\xcb
    mepi    \xe3                    \xf3   \x97 y )N\xa9 r   \xf3    \xfa/app/src/modules/__init__.py\xda<module>r      s   \xf1r   
```

## src/modules/__pycache__/applier.cpython-312.pyc
```
\xcb
    ipi\xf0  \xe3                   \xf3D   \x97 d dl mZmZmZmZ d dlmZ d dlZ G d\x84 d\xab      Zy)\xe9    )\xdaApplication\xdaJobOpportunity\xdaResume\xdaCandidateProfile)\xdadatetimeNc                   \xf3*   \x97 e Zd Zd\x84 Zdedededefd\x84Zy)\xdaApplicationBotc                 \xf3   \x97 g | _         y )N)\xdaapplication_history)\xdaselfs    \xfa/app/src/modules/applier.py\xda__init__zApplicationBot.__init__   s
   \x80 \xd8#%\x88\xd5 \xf3    \xdaprofile\xdajob\xdaresume\xdareturnc           	      \xf3\xfe   \x97 d}t        j                   \xab       dk  rd}t        |j                  |j                  |j                  ||j                  d|j                  \x9b \x9d\xac\xab      }| j
                  j                  |\xab       |S )z4
        Simulates the application process.
        \xdaAplicadog\x9a\x99\x99\x99\x99\x99\xa9?\xdaFalhau#   Aplicado com versão de currículo )\xdajob_id\xda
profile_id\xda	resume_id\xdastatus\xdaplatform\xdanotes)\xdarandomr   \xdaid\xdasource\xdaversion_tagr   \xdaappend)r   r   r   r   r   \xdaapps         r   \xdaapplyzApplicationBot.apply	   sq   \x80 \xf0 \x88\xdc\x8f=\x89=\x8b?\x98T\xd2!\xd8\x88V\xe4\xd8\x976\x916\xd8\x97z\x91z\xd8\x97i\x91i\xd8\xd8\x97Z\x91Z\xd87\xb8\xd78J\xd18J\xd07K\xd0L\xf4
\x88\xf0 	\xd7 \xd1 \xd7'\xd1'\xa8\xd4,\xd8\x88
r   N)	\xda__name__\xda
__module__\xda__qualname__r   r   r   r   r   r#   \xa9 r   r   r	   r	      s*   \x84 \xf2&\xf0\xd0-\xf0 \xb0N\xf0 \xc8F\xf0 \xd0Wb\xf4 r   r	   )\xdasrc.core.modelsr   r   r   r   r   r   r	   r'   r   r   \xda<module>r)      s   \xf0\xdf Q\xd3 Q\xdd \xdb \xf7\xf2 r   
```

## src/modules/__pycache__/decision_engine.cpython-312.pyc
```
\xcb
    ipi\xd5  \xe3                   \xf3(   \x97 d dl mZmZ  G d\x84 d\xab      Zy)\xe9    )\xdaDict\xdaListc                   \xf3B   \x97 e Zd Zd\x84 Zdeeef   dee   defd\x84Zdefd\x84Z	y)\xdaStrategyEnginec                 \xf3"   \x97 d| _         dg| _        y )Nu   Aplicação Agressiva\xdaGeral)\xdacurrent_strategy\xdafocus_areas\xa9\xdaselfs    \xfa#/app/src/modules/decision_engine.py\xda__init__zStrategyEngine.__init__   s   \x80 \xd8 7\x88\xd4\xd8#\x989\x88\xd5\xf3    \xdametrics\xdarecent_applications\xdareturnc                 \xf3\x96   \x97 d}|d   dkD  r|d   |d   z  }|dk  r|d   dkD  rd| _         y|d   d	kD  r|d   dk  rd
| _         yd| _         y)zI
        Analyzes metrics and returns a strategy update message.
        r   \xdaapplied\xda
interviewsg\x9a\x99\x99\x99\x99\x99\xb9?\xe9
   zQualidade sobre QuantidadeuJ   Taxa de conversão baixa detectada. Mudando para foco em alta relevância.\xdamatched\xe92   zSprint de Alto VolumeuA   Muitos matches encontrados. Aumentando velocidade de aplicação.zAbordagem Equilibradau<   Desempenho dentro dos parâmetros normais. Mantendo o curso.\xa9r	   )r   r   r   \xdaconversion_rates       r   \xdaanalyze_performancez"StrategyEngine.analyze_performance   s|   \x80 \xf0 \x88\xd8\x909\xd1\xa0\xd2!\xd8%\xa0l\xd13\xb0g\xb8i\xd16H\xd1H\x88O\xf0 \x98S\xd2 \xa0W\xa8Y\xd1%7\xb8"\xd2%<\xd8$@\x88D\xd4!\xd8_\xe0\x90Y\xd1\xa0"\xd2$\xa8\xb0\xd1);\xb8b\xd2)@\xd8%<\x88T\xd4"\xd8W\xf0 %<\x88D\xd4!\xd8Qr   c                 \xf3   \x97 | j                   S )Nr   r   s    r   \xdaget_current_strategyz#StrategyEngine.get_current_strategy   s   \x80 \xd8\xd7$\xd1$\xd0$r   N)
\xda__name__\xda
__module__\xda__qualname__r   r   \xdastr\xdaintr   r   r   \xa9 r   r   r   r      sA   \x84 \xf2%\xf0R\xa84\xb0\xb0S\xb0\xa9>\xf0 R\xd0PT\xd0UX\xd1PY\xf0 R\xd0^a\xf3 R\xf0*%\xa0c\xf4 %r   r   N)\xdatypingr   r   r   r#   r   r   \xda<module>r%      s   \xf0\xdf \xf7%\xf2 %r   
```

## src/modules/__pycache__/interview_prep.cpython-312.pyc
```
\xcb
    ipi  \xe3                   \xf30   \x97 d dl mZmZ d dlZ G d\x84 d\xab      Zy)\xe9    )\xdaJobOpportunity\xdaCandidateProfileNc                   \xf34   \x97 e Zd Zd\x84 Zdedee   fd\x84Zdefd\x84Zy)\xdaInterviewCoachc                 \xf3(   \x97 g d\xa2| _         g d\xa2| _        y )N)u   Fale um pouco sobre você.u*   Por que você quer trabalhar na {company}?u    Qual é o seu maior ponto forte?u8   Descreva uma situação desafiadora que você enfrentou.)uB   Explique como você projetaria um sistema escalável para {topic}.u%   Como você lida com dívida técnica?u'   Qual é a sua experiência com {skill}?u7   Descreva uma vez que você otimizou uma consulta lenta.)\xdacommon_questions\xdatech_questions_pool)\xdaselfs    \xfa"/app/src/modules/interview_prep.py\xda__init__zInterviewCoach.__init__   s   \x80 \xf2!
\x88\xd4\xf2$
\x88\xd5 \xf3    \xdajob\xdareturnc                 \xf3  \x97 g }|j                  t        j                  | j                  \xab      j	                  |j
                  \xac\xab      \xab       |j                  dd D ]  }|j                  d|\x9b d\x9d\xab       \x8c |j                  r|j                  j                  \xab       d   nd}|j                  t        j                  | j                  \xab      j	                  ||j                  rt        j                  |j                  \xab      nd\xac	\xab      \xab       |S )
zN
        Generates a list of interview questions tailored to the job.
        )\xdacompanyN\xe9   u   Como você utilizou u    em um ambiente de produção?\xe9\xff\xff\xff\xff\xdasoftware\xdaPython)\xdatopic\xdaskill)
\xdaappend\xdarandom\xdachoicer   \xdaformatr   \xdarequirements\xdatitle\xdasplitr	   )r
   r   \xda	questions\xdareqr   s        r   \xdagenerate_questionsz!InterviewCoach.generate_questions   s\xf3   \x80 \xf0 \x88	\xf0 	\xd7\xd1\x9c\x9f\x99\xa0t\xd7'<\xd1'<\xd3=\xd7D\xd1D\xc8S\xcf[\xc9[\xd0D\xd3Y\xd4Z\xf0 \xd7#\xd1#\xa0B\xa0Q\xd3'\x88C\xd8\xd7\xd1\xd03\xb0C\xb05\xd08V\xd0W\xd5X\xf0 (\xf0 *-\xaf\xaa\x90\x97	\x91	\x97\x91\xd3!\xa0"\xd2%\xb8
\x88\xd8\xd7\xd1\x9c\x9f\x99\xa0t\xd7'?\xd1'?\xd3@\xd7G\xd1G\xc8e\xf0  B\xf7  O\xf2  O\xd4[a\xd7[h\xd1[h\xd0il\xd7iy\xd1iy\xd4[z\xf0  U]\xd0G\xf3  ^\xf4  	_\xe0\xd0r   c                 \xf34   \x97 g d\xa2}t        j                  |\xab      S )z<
        Simulates feedback after a mock interview.
        )u7   Boa comunicação. Elabore mais nos detalhes técnicos.u2   Boa profundidade técnica. Tente ser mais conciso.z6Excelente fit cultural. Pronto para a entrevista real.u@   Precisa de mais preparação em conceitos de design de sistemas.)r   r   )r
   \xda	feedbackss     r   \xdasimulate_feedbackz InterviewCoach.simulate_feedback&   s   \x80 \xf2
\x88	\xf4 \x8f}\x89}\x98Y\xd3'\xd0'r   N)	\xda__name__\xda
__module__\xda__qualname__r   r   \xdalist\xdastrr!   r$   \xa9 r   r   r   r      s*   \x84 \xf2
\xf0\xa0n\xf0 \xb8\xb8c\xb9\xf3 \xf0&
(\xa03\xf4 
(r   r   )\xdasrc.core.modelsr   r   r   r   r*   r   r   \xda<module>r,      s   \xf0\xdf <\xdb \xf7,(\xf2 ,(r   
```

## src/modules/__pycache__/job_intelligence.cpython-312.pyc
```
\xcb
    \xf6hpi\x99  \xe3                   \xf3T   \x97 d dl mZ d dlmZ d dlmZ d dlZ ed\xab      Z G d\x84 d\xab      Zy)\xe9    )\xdaList)\xdaJobOpportunity)\xdaFakerN\xdapt_BRc                   \xf3>   \x97 e Zd Zd\x84 Zdee   dee   fd\x84Zdedefd\x84Z	y)\xda
JobScannerc                  \xf3   \x97 y )N\xa9 )\xdaselfs    \xfa$/app/src/modules/job_intelligence.py\xda__init__zJobScanner.__init__	   s   \x80 \xd8\xf3    \xdakeywords\xdareturnc                 \xf3\xba  \x97 g }t        t        j                  dd\xab      \xab      D \x90]0  }t        j	                  \xab       }t        j                  \xab       dkD  r|rt        j
                  |\xab      \x9b d|\x9b \x9d}t        d\xab      D \x8fcg c]  }t        j                  \xab       \x91\x8c }}|r9|j                  t        j                  |t        dt        |\xab      \xab      \xac\xab      \xab       t        t        j                  \xab       |t        j                  \xab       t        j                  \xab       |t        j                  \xab       t        j
                  g d\xa2\xab      d	\xac
\xab      }|j!                  |\xab       \x90\x8c3 |S c c}w )z\x92
        Simulates scanning job boards (LinkedIn, Indeed, etc.) for opportunities.
        Returns a list of mock JobOpportunity objects.
        \xe9   \xe9
   g      \xe0?\xda \xe9   \xe9   )\xdak)\xdaLinkedIn\xdaIndeed\xda	Glassdoor\xdaGupy\xe7        )\xdaid\xdatitle\xdacompany\xdadescription\xdarequirements\xdaurl\xdasource\xdamatch_score)\xdarange\xdarandom\xdarandint\xdafake\xdajob\xdachoice\xdaword\xdaextend\xdasample\xdamin\xdalenr   \xdauuid4r   \xdacatch_phraser"   \xdaappend)r   r   \xdaopportunities\xda_\xda	job_titler!   r)   s          r   \xdascan_opportunitieszJobScanner.scan_opportunities   s  \x80 \xf0
 \x88\xe4\x94v\x97~\x91~\xa0a\xa8\xd3,\xd7-\x88A\xdc\x9f\x99\x9b
\x88I\xe4\x8f}\x89}\x8b\xa0\xd2$\xa9\xdc%\x9f}\x99}\xa8X\xd36\xd07\xb0q\xb8\xb8\xd0D\x90	\xe416\xb0q\xb4\xd3:\xb1\xa8A\x9cD\x9fI\x99I\x9dK\xb0\x88L\xd0:\xe1\xd8\xd7$\xd1$\xa4V\xa7]\xa1]\xb08\xbcs\xc01\xc4c\xc8(\xc3m\xd3?T\xd4%U\xd4V\xe4 \xdc\x97:\x91:\x93<\xd8\xdc\x9f\x99\x9b\xdc \xd7-\xd1-\xd3/\xd8)\xdc\x97H\x91H\x93J\xdc\x97}\x91}\xd2%P\xd3Q\xd8\xf4	\x88C\xf0 \xd7 \xd1 \xa0\xd6%\xf0+ .\xf0. \xd0\xf9\xf2# ;s   \xc1:Er)   c                 \xf3\xe2  \x97 d}|j                   D ]\x83  }|j                  j                  \xab       |j                  j                  \xab       v r|dz  }|j                  j                  \xab       |j                  D \x8fcg c]  }|j                  \xab       \x91\x8c c}v s\x8c|dz  }\x8c\x85 |j
                  D ]<  }|j                  j                  \xab       |j                  j                  \xab       v s\x8c8|dz  }\x8c> t        d|\xab      S c c}w )zK
        Calculates a simple match score based on keyword overlap.
        r   g      >@g      $@g      4@g      Y@)\xdaskills\xdaname\xdalowerr   r!   \xdaexperiencesr.   )r   \xdaprofiler)   \xdascore\xdaskill\xdareq\xdaexps          r   \xdacalculate_match_scorez JobScanner.calculate_match_score,   s\xc9   \x80 \xf0 \x88\xe0\x97^\x94^\x88E\xd8\x8fz\x89z\xd7\xd1\xd3!\xa0S\xa7Y\xa1Y\xa7_\xa1_\xd3%6\xd16\xd8\x98\x91\x90\xd8\x8fz\x89z\xd7\xd1\xd3!\xb8S\xd7=M\xd2=M\xd3%N\xd1=M\xb0c\xa0c\xa7i\xa1i\xa5k\xd0=M\xd1%N\xd2N\xd8\x98\x91\x91\xf0	 $\xf0 \xd7&\xd4&\x88C\xd8\x97	\x91	\x97\x91\xd3!\xa0S\xa7Y\xa1Y\xa7_\xa1_\xd3%6\xd26\xd8\x98$\x91\x91\xf0 '\xf4
 \x905\x98%\xd3 \xd0 \xf9\xf2 &Os   \xc12C,N)
\xda__name__\xda
__module__\xda__qualname__r   r   \xdastrr   r6   \xdafloatrA   r
   r   r   r   r      s7   \x84 \xf2\xf0\xa84\xb0\xa99\xf0 \xb8\xb8n\xd19M\xf3 \xf0@!\xb0.\xf0 !\xc0U\xf4 !r   r   )	\xdatypingr   \xdasrc.core.modelsr   \xdafakerr   r&   r(   r   r
   r   r   \xda<module>rJ      s$   \xf0\xdd \xdd *\xdd \xdb \xe1\x88W\x83~\x80\xf76!\xf2 6!r   
```

## src/modules/__pycache__/monitoring.cpython-312.pyc
```
\xcb
    ipi9  \xe3                   \xf3<   \x97 d dl mZ d dlmZmZ d dlZ G d\x84 d\xab      Zy)\xe9    )\xdaApplication)\xdadatetime\xda	timedeltaNc                   \xf3.   \x97 e Zd Zd\x84 Zdee   dee   fd\x84Zy)\xdaFollowUpAgentc                  \xf3   \x97 y )N\xa9 )\xdaselfs    \xfa/app/src/modules/monitoring.py\xda__init__zFollowUpAgent.__init__   s   \x80 \xd8\xf3    \xdaapplications\xdareturnc                 \xf3\xea   \x97 g }|D ]k  }|j                   dk(  s\x8ct        j                  \xab       dk  s\x8c+|j                  d|j                  \x9b d|j                  \x9b d\x9d\xab       |xj
                  dz  c_        \x8cm |S )z\x84
        Checks applications that need a follow-up action.
        Returns a list of messages describing the actions taken.
        \xdaAplicadog\x9a\x99\x99\x99\x99\x99\xb9?zFollow-up enviado para a vaga z na plataforma \xda.z | Follow-up enviado.)\xdastatus\xdarandom\xdaappend\xdajob_id\xdaplatform\xdanotes)r
   r   \xdaactions\xdaapps       r   \xdacheck_for_follow_upz!FollowUpAgent.check_for_follow_up	   sm   \x80 \xf0
 \x88\xdb\x88C\xf0 \x8fz\x89z\x98Z\xd3'\xacF\xafM\xa9M\xabO\xb8c\xd3,A\xe0\x97\x91\xd0!?\xc0\xc7
\xc1
\xb8|\xc8?\xd0[^\xd7[g\xd1[g\xd0Zh\xd0hi\xd0j\xd4k\xd8\x97	\x92	\xd04\xd14\x96	\xf0  \xf0 \x88r   N)\xda__name__\xda
__module__\xda__qualname__r   \xdalistr   \xdastrr   r	   r   r   r   r      s#   \x84 \xf2\xf0\xb0\xb0[\xd10A\xf0 \xc0d\xc83\xc1i\xf4 r   r   )\xdasrc.core.modelsr   r   r   r   r   r	   r   r   \xda<module>r"      s   \xf0\xdd '\xdf (\xdb \xf7\xf2 r   
```

## src/modules/__pycache__/networking.cpython-312.pyc
```
\xcb
    Xjpi\x89  \xe3                   \xf3<   \x97 d dl Z d dlmZ  ed\xab      Z G d\x84 d\xab      Zy)\xe9    N)\xdaFaker\xdapt_BRc                   \xf32   \x97 e Zd Zd\x84 Zdedefd\x84Zdedefd\x84Zy)\xdaNetworkAgentc                  \xf3   \x97 y )N\xa9 )\xdaselfs    \xfa/app/src/modules/networking.py\xda__init__zNetworkAgent.__init__   s   \x80 \xd8\xf3    \xdacompany_name\xdareturnc                 \xf3\xa0   \x97 t         j                  \xab       }t        j                  g d\xa2\xab      }t        j                  \xab       dk  rd|\x9b d|\x9b d|\x9b d\x9dS y)zg
        Simulates finding a recruiter at the target company and sending a connection request.
        )zTech RecruiterzTalent AcquisitionzGerente de RHzHead de Pessoasg333333\xd3?u   Conexão enviada para z (z) na \xda.N)\xdafake\xdaname\xdarandom\xdachoice)r	   r   \xdarecruiter_name\xdaroles       r
   \xdaattempt_connectionzNetworkAgent.attempt_connection
   sN   \x80 \xf4
 \x9f\x99\x9b\x88\xdc\x8f}\x89}\xd2i\xd3j\x88\xf4 \x8f=\x89=\x8b?\x98S\xd2 \xd8,\xa8^\xd0,<\xb8B\xb8t\xb8f\xc0E\xc8,\xc8\xd0WX\xd0Y\xd0Y\xe0r   r   c                 \xf3   \x97 d|\x9b d\x9dS )z'Simulates sending a networking message.u&   Mensagem de introdução enviada para r   r   )r	   r   s     r
   \xdasend_messagezNetworkAgent.send_message   s   \x80 \xe07\xb8\xd07G\xc0q\xd0I\xd0Ir   N)\xda__name__\xda
__module__\xda__qualname__r   \xdastrr   r   r   r   r
   r   r      s0   \x84 \xf2\xf0\xa8s\xf0 \xb0s\xf3 \xf0J\xa83\xf0 J\xb03\xf4 Jr   r   )r   \xdafakerr   r   r   r   r   r
   \xda<module>r      s    \xf0\xdb \xdd \xe1\x88W\x83~\x80\xf7J\xf2 Jr   
```

## src/modules/__pycache__/onboarding.cpython-312.pyc
```
\xcb
    \xeehpi  \xe3                   \xf3`   \x97 d dl mZmZmZmZ d dlmZ d dlmZ d dl	Z	 ed\xab      Z
 G d\x84 d\xab      Zy)\xe9    )\xdaCandidateProfile\xda
Experience\xda	Education\xdaSkill)\xdadate)\xdaFakerN\xdapt_BRc                   \xf3*   \x97 e Zd Zd\x84 Zdefd\x84Zdefd\x84Zy)\xdaOnboardingAgentc                 \xf3   \x97 d | _         y )N)\xdaprofile\xa9\xdaselfs    \xfa/app/src/modules/onboarding.py\xda__init__zOnboardingAgent.__init__	   s	   \x80 \xd8\x88\x8d\xf3    \xdareturnc                 \xf3X  \x97 t        ddddt        ddt        ddd	\xab      d
\xac\xab      t        ddt        ddd\xab      t        ddd\xab      d\xac\xab      gt        dddt        ddd\xab      t        ddd\xab      \xac\xab      gt	        dd\xac\xab      t	        d d!\xac\xab      t	        d"d#\xac\xab      gd$\xac%\xab      | _        | j
                  S )&z=Loads a hardcoded default profile for demonstration in PT-BR.zAlex Desenvolvedorzalex.dev@exemplo.com.brz+55 11 99999-9999u\   Engenheiro de Software Sênior com 8 anos de experiência em Python e Arquiteturas em Nuvem.u   Engenheiro Backend SêniorzTechCorp Brasili\xe4  \xe9   \xe9   uQ   Liderando migração de microsserviços e otimizando consultas de banco de dados.\xa9\xdatitle\xdacompany\xda
start_date\xdadescriptionzDesenvolvedor de SoftwarezInova Startupi\xe0  \xe9   i\xe3  \xe9   \xe9   z1Desenvolvimento Full stack usando Django e React.)r   r   r   \xdaend_dater   u   Universidade Tecnológica\xdaBacharelado\xf5   Ciência da Computaçãoi\xdc  \xe9   \xe9   \xe9   \xa9\xdainstitution\xdadegree\xdafield_of_studyr   r   \xdaPython\xdaEspecialista\xa9\xdaname\xdalevel\xdaDocker\xf5   Intermediário\xdaAWSu	   Avançadozhttps://linkedin.com/in/alexdev)r,   \xdaemail\xdaphone\xdasummary\xdaexperiences\xda	education\xdaskills\xdalinkedin_url)r   r   r   r   r   r   r   s    r   \xdaload_default_profilez$OnboardingAgent.load_default_profile   s\xd0   \x80 \xe4'\xd8%\xd8+\xd8%\xd8r\xe4\xd86\xd8-\xdc#\xa0D\xa8!\xa8R\xd30\xd8 s\xf4	\xf4 \xd85\xd8+\xdc#\xa0D\xa8!\xa8Q\xd3/\xdc!\xa0$\xa8\xa8B\xd3/\xd8 S\xf4\xf0\xf4  \xd8 ;\xd8(\xd8#=\xdc#\xa0D\xa8!\xa8Q\xd3/\xdc!\xa0$\xa8\xa82\xd3.\xf4\xf0\xf4 \x988\xa8>\xd4:\xdc\x988\xd0+;\xd4<\xdc\x985\xa8\xd44\xf0\xf0
 ;\xf4E#
\x88\x8c\xf0H \x8f|\x89|\xd0r   c                 \xf3\x92  \x97 t        t        j                  \xab       t        j                  \xab       t        j	                  \xab       t        j                  \xab       t        t        j                  \xab       t        j                  \xab       t        j                  dd\xac\xab      t        j                  \xab       \xac\xab      gt        t        j                  \xab       ddt        j                  dd\xac\xab      t        j                  dd\xac\xab      \xac	\xab      gt        d
\xab      D \x8fcg c]!  }t        t        j                  \xab       d\xac\xab      \x91\x8c# c}\xac\xab      | _        | j                  S c c}w )z Generates a random fake profile.z-5yz-1y)r   r   r   r    r!   z-10yz-6yr%   \xe9   r/   r+   )r,   r1   r2   r3   r4   r5   r6   )r   \xdafaker,   r1   \xdaphone_number\xdatextr   \xdajobr   \xdadate_betweenr   \xdaranger   \xdawordr   )r   \xda_s     r   \xdacreate_fake_profilez#OnboardingAgent.create_fake_profile4   s\xef   \x80 \xe4'\xdc\x97\x91\x93\xdc\x97*\x91*\x93,\xdc\xd7#\xd1#\xd3%\xdc\x97I\x91I\x93K\xe4\xdc\x9f(\x99(\x9b*\xdc \x9fL\x99L\x9bN\xdc#\xd70\xd10\xb8E\xc8E\xd00\xd3R\xdc $\xa7	\xa1	\xa3\xf4	\xf0\xf4 \xdc $\xa7\xa1\xa3\xd8(\xd8#=\xdc#\xd70\xd10\xb8F\xc8U\xd00\xd3S\xdc!\xd7.\xd1.\xb8%\xc8%\xd0.\xd3P\xf4\xf0\xf4 NS\xd0ST\xccX\xd3V\xc9X\xc8\x94E\x9ct\x9fy\x99y\x9b{\xd02B\xd6C\xc8X\xd1V\xf4-
\x88\x8c\xf00 \x8f|\x89|\xd0\xf9\xf2 Ws   \xc4&EN)\xda__name__\xda
__module__\xda__qualname__r   r   r8   rC   \xa9 r   r   r   r      s"   \x84 \xf2\xf0&\xd0&6\xf3 &\xf0P\xd0%5\xf4 r   r   )\xdasrc.core.modelsr   r   r   r   \xdadatetimer   \xdafakerr   \xdarandomr;   r   rG   r   r   \xda<module>rL      s)   \xf0\xdf J\xd3 J\xdd \xdd \xdb \xe1\x88W\x83~\x80\xf7F\xf2 Fr   
```

## src/modules/__pycache__/profile_optimizer.cpython-312.pyc
```
\xcb
    ipi\xcf  \xe3                   \xf3(   \x97 d dl mZmZ  G d\x84 d\xab      Zy)\xe9    )\xdaCandidateProfile\xdaJobOpportunityc                   \xf30   \x97 e Zd Zdededefd\x84Zdedefd\x84Zy)\xdaProfileOptimizer\xdaprofile\xdajob\xdareturnc                 \xf3  \x97 |j                  d\xac\xab      }|j                  }|D \x8fcg c]/  }|j                  \xab       |j                  j                  \xab       vs\x8c.|\x91\x8c1 }}|r(|xj                  ddj	                  |\xab      \x9b d\x9dz  c_        |S c c}w )z\xea
        Optimizes the candidate profile for a specific job opportunity.
        In a real scenario, this would use LLM to rewrite the summary and experiences.
        Here, we will simulate it by appending relevant keywords.
        T)\xdadeepu   

Áreas de foco otimizadas: z, \xda.)\xda
model_copy\xdarequirements\xdalower\xdasummary\xdajoin)\xdaselfr   r   \xdaoptimized_profile\xdakeywords\xdak\xdaadded_keywordss          \xfa%/app/src/modules/profile_optimizer.py\xdaoptimize_for_jobz!ProfileOptimizer.optimize_for_job   s\x8e   \x80 \xf0 $\xd7.\xd1.\xb0D\xd0.\xd39\xd0\xf0 \xd7#\xd1#\x88\xf1 &.\xd3d\xa1X\xa0\xb0\xb7\xb1\xb3\xd0BS\xd7B[\xd1B[\xd7Ba\xd1Ba\xd3Bc\xd21c\x9a!\xa0X\x88\xd0d\xe1\xd8\xd7%\xd2%\xd0+J\xc84\xcf9\xc99\xd0Uc\xd3Kd\xd0Je\xd0ef\xd0)g\xd1g\xd5%\xe0 \xd0 \xf9\xf2 es   \xa3/B\xc1Bc                 \xf3\xb4   \x97 |j                   dd D \x8fcg c]  }|j                  \x91\x8c }}|j                  d   j                  \x9b ddj	                  |\xab      \x9b d\x9dS c c}w )z2Generates a new LinkedIn headline based on skills.N\xe9   r   z | z | Aberto a oportunidades)\xdaskills\xdaname\xdaexperiences\xdatitler   )r   r   \xdas\xda
top_skillss       r   \xdaupdate_linkedin_headlinez)ProfileOptimizer.update_linkedin_headline   s\   \x80 \xe0&-\xa7n\xa1n\xb0R\xb0a\xd1&8\xd39\xd1&8\xa0\x90a\x97f\x93f\xd0&8\x88
\xd09\xd8\xd7%\xd1%\xa0a\xd1(\xd7.\xd1.\xd0/\xa8s\xb05\xb7:\xb1:\xb8j\xd33I\xd02J\xd0Jc\xd0d\xd0d\xf9\xf2 :s   \x92AN)\xda__name__\xda
__module__\xda__qualname__r   r   r   \xdastrr!   \xa9 \xf3    r   r   r      s5   \x84 \xf0!\xd0(8\xf0 !\xb8~\xf0 !\xd0Rb\xf3 !\xf0&e\xd00@\xf0 e\xc0S\xf4 er'   r   N)\xdasrc.core.modelsr   r   r   r&   r'   r   \xda<module>r)      s   \xf0\xdf <\xf7e\xf2 er'   
```

## src/modules/__pycache__/reporting.cpython-312.pyc
```
\xcb
    fjpi'  \xe3                   \xf3<   \x97 d dl Z d dlmZ d dlmZmZ  G d\x84 d\xab      Zy)\xe9    N)\xdadatetime)\xdaCandidateProfile\xdaApplicationc                   \xf30   \x97 e Zd Zd\x84 Zdededee   defd\x84Z	y)\xdaReportGeneratorc                  \xf3   \x97 y )N\xa9 )\xdaselfs    \xfa/app/src/modules/reporting.py\xda__init__zReportGenerator.__init__   s   \x80 \xd8\xf3    \xdaprofile\xdametrics\xdaapplications\xdastrategyc                 \xf3  \x97 dt        j                  \xab       j                  d\xab      \x9b d\x9d}t        |dd\xac\xab      5 }|j	                  dt        j                  \xab       j                  d\xab      \x9b d	\x9d\xab       |j	                  d
\xab       |j	                  d|j
                  \x9b d\x9d\xab       |j	                  d|\x9b d\x9d\xab       |j	                  d\xab       |j	                  d\xab       |j	                  d\xab       |j	                  d\xab       |j	                  d|j                  dd\xab      \x9b d\x9d\xab       |j	                  d|j                  dd\xab      \x9b d\x9d\xab       |j	                  d|j                  dd\xab      \x9b d\x9d\xab       |j	                  d|j                  dd\xab      \x9b d\x9d\xab       |j	                  d|j                  dd\xab      \x9b d\x9d\xab       |j	                  d\xab       |s|j	                  d \xab       n_|d!d" D ]W  }|j	                  d#|j                  j                  d$\xab      \x9b d%|j                  \x9b d&|j                  \x9b d'|j                  \x9b d\x9d	\xab       \x8cY |j	                  d(\xab       |j	                  d)\xab       |j	                  d*\xab       |j	                  d+\xab       d"d"d"\xab       |S # 1 sw Y   |S xY w),z6Generates a markdown report of the system's operation.\xdarelatorio_operacional_z%Y%m%dz.md\xdawzutf-8)\xdaencodingu)   # RELATÓRIO OPERACIONAL BIRTH HUB 360 - z%d/%m/%Yz

z## 1. RESUMO EXECUTIVO
z- **Perfil Ativo:** \xda
u   - **Estratégia Atual:** z- **Status:** Operacional

u   ## 2. MÉTRICAS DO CICLO
u   | Métrica | Valor |
z
|---|---|
z| Vagas Escaneadas | \xdascannedr   z |
u   | Vagas Compatíveis | \xdamatchedz| Candidaturas Enviadas | \xdaappliedz| Entrevistas Agendadas | \xda
interviewsu   | Ações de Networking | \xda
networkingz |

u-   ## 3. REGISTRO DE CANDIDATURAS (Últimas 10)
z"_Nenhuma candidatura registrada._
i\xf6\xff\xff\xffNz- **z%H:%Mz**: z via z - Status: u%   
## 4. PRÓXIMOS PASSOS AUTOMÁTICOS
z- Manter varredura de vagas.
z%- Acompanhar retornos de networking.
u6   - Otimizar currículo baseado em feedback (simulado).
)r   \xdanow\xdastrftime\xdaopen\xdawrite\xdaname\xdaget\xda
applied_at\xdajob_id\xdaplatform\xdastatus)r
   r   r   r   r   \xdafilename\xdaf\xdaapps           r   \xdagenerate_daily_reportz%ReportGenerator.generate_daily_report	   sI  \x80 \xe0+\xacH\xafL\xa9L\xabN\xd7,C\xd1,C\xc0H\xd3,M\xd0+N\xc8c\xd0R\x88\xe4\x90(\x98C\xa8'\xd52\xb0a\xd8\x8fG\x89G\xd0?\xc4\xc7\xc1\xc3\xd7@W\xd1@W\xd0Xb\xd3@c\xd0?d\xd0dh\xd0i\xd4j\xe0\x8fG\x89G\xd0.\xd4/\xd8\x8fG\x89G\xd0*\xa87\xaf<\xa9<\xa8.\xb8\xd0;\xd4<\xd8\x8fG\x89G\xd0/\xb0\xa8z\xb8\xd0<\xd4=\xd8\x8fG\x89G\xd03\xd45\xe0\x8fG\x89G\xd00\xd41\xd8\x8fG\x89G\xd0,\xd4-\xd8\x8fG\x89G\x90M\xd4"\xd8\x8fG\x89G\xd0+\xa8G\xafK\xa9K\xb8	\xc01\xd3,E\xd0+F\xc0d\xd0K\xd4L\xd8\x8fG\x89G\xd0-\xa8g\xafk\xa9k\xb8)\xc0Q\xd3.G\xd0-H\xc8\xd0M\xd4N\xd8\x8fG\x89G\xd00\xb0\xb7\xb1\xb8Y\xc8\xd31J\xd00K\xc84\xd0P\xd4Q\xd8\x8fG\x89G\xd00\xb0\xb7\xb1\xb8\\xc81\xd31M\xd00N\xc8d\xd0S\xd4T\xd8\x8fG\x89G\xd00\xb0\xb7\xb1\xb8\\xc81\xd31M\xd00N\xc8f\xd0U\xd4V\xe0\x8fG\x89G\xd0D\xd4E\xd9\xd8\x97\x91\xd0=\xd5>\xe0'\xa8\xa8\xd3-\x90C\xd8\x97G\x91G\x98d\xa03\xa7>\xa1>\xd7#:\xd1#:\xb87\xd3#C\xd0"D\xc0D\xc8\xcf\xc9\xc8\xd0TY\xd0Z]\xd7Zf\xd1Zf\xd0Yg\xd0gr\xd0sv\xd7s}\xd1s}\xd0r~\xf0  A\xf0  B\xf5  C\xf0 .\xf0 \x8fG\x89G\xd0=\xd4>\xd8\x8fG\x89G\xd04\xd45\xd8\x8fG\x89G\xd0<\xd4=\xd8\x8fG\x89G\xd0M\xd4N\xf77 3\xf0: \x88\xf7; 3\xf0: \x88\xfas   \xb6IJ\xcaJN)
\xda__name__\xda
__module__\xda__qualname__r   r   \xdadict\xdalistr   \xdastrr)   r	   r   r   r   r      s1   \x84 \xf2\xf0!\xd0-=\xf0 !\xc8\xf0 !\xd0\`\xd0al\xd1\m\xf0 !\xd0y|\xf4 !r   r   )\xdaosr   \xdasrc.core.modelsr   r   r   r	   r   r   \xda<module>r2      s   \xf0\xdb 	\xdd \xdf 9\xf7%\xf2 %r   
```

## src/modules/__pycache__/resume_generator.cpython-312.pyc
```
\xcb
    \xfchpi\xa5  \xe3                   \xf38   \x97 d dl mZmZmZ d dlmZ  G d\x84 d\xab      Zy)\xe9    )\xdaCandidateProfile\xdaJobOpportunity\xdaResume)\xdadatetimec                   \xf3    \x97 e Zd Zdededefd\x84Zy)\xdaResumeGenerator\xdaprofile\xdajob\xdareturnc                 \xf3d  \x97 d|j                   \x9b d\x9d}|d|j                  \x9b d|j                  \x9b d\x9dz  }|d|j                  \x9b d\x9dz  }|dz  }||j                  \x9b d\x9dz  }|d|j
                  \x9b d	|j                  \x9b d
\x9dz  }|dz  }|j                  D \x8fcg c]  }|j                   \x91\x8c }}g }|D ]a  }|j                  \xab       |j                  D \x8fcg c]  }|j                  \xab       \x91\x8c c}v r|j                  d|\x9b d\x9d\xab       \x8cQ|j                  |\xab       \x8cc |dj                  |\xab      dz   z  }|dz  }|j                  D ]\  }	||	j
                  \x9b d	|	j                  \x9b d|	j                  \x9b d|	j                  r|	j                  nd\x9b d\x9dz  }|d|	j                  \x9b d\x9dz  }\x8c^ |dz  }|j                   D ].  }
||
j"                  \x9b d|
j$                  \x9b d|
j&                  \x9b d\x9dz  }\x8c0 t)        |j*                  |j*                  |d|j                  \x9b dt-        j.                  \xab       j1                  d\xab      \x9b \x9d\xac\xab      S c c}w c c}w )zA
        Generates a tailored resume for a specific job.
        u   CURRÍCULO: \xda
z	Contato: z | z
LinkedIn: z

zRESUMO PROFISSIONAL
zEntusiasta por vagas de z na z.

zHABILIDADES
\xda*z, u   EXPERIÊNCIA
z (z - \xda
Atualmentez)
z- u   
FORMAÇÃO ACADÊMICA
z em zv1-\xda-z%Y%m%d)\xda
profile_id\xdajob_id\xdacontent\xdaversion_tag)\xdaname\xdaemail\xdaphone\xdalinkedin_url\xdasummary\xdatitle\xdacompany\xdaskills\xdalower\xdarequirements\xdaappend\xdajoin\xdaexperiences\xda
start_date\xdaend_date\xdadescription\xda	education\xdadegree\xdafield_of_study\xdainstitutionr   \xdaidr   \xdanow\xdastrftime)\xdaselfr	   r
   r   \xdas\xdaskills_list\xdaformatted_skills\xdaskill\xdar\xdaexp\xdaedus              \xfa$/app/src/modules/resume_generator.py\xdagenerate_resumezResumeGenerator.generate_resume   sK  \x80 \xf0
 !\xa0\xa7\xa1\xa0\xa8b\xd01\x88\xd8\x90Y\x98w\x9f}\x99}\x98o\xa8S\xb0\xb7\xb1\xb0\xb8r\xd0B\xd1B\x88\xd8\x90Z\xa0\xd7 4\xd1 4\xd05\xb0T\xd0:\xd1:\x88\xf0 	\xd0*\xd1*\x88\xe0\x90g\x97o\x91o\xd0&\xa0b\xd0)\xd1)\x88\xd8\xd0-\xa8c\xafi\xa9i\xa8[\xb8\xb8S\xbf[\xb9[\xb8M\xc8\xd0O\xd1O\x88\xf0 	\x90?\xd1"\x88\xd8'.\xa7~\xa2~\xd36\xa1~\xa0!\x90q\x97v\x93v\xa0~\x88\xd06\xe0\xd0\xdb \x88E\xd8\x8f{\x89{\x8b}\xb0C\xd74D\xd24D\xd3 E\xd14D\xa8q\xa0\xa7\xa1\xa5\xd04D\xd1 E\xd1E\xd8 \xd7'\xd1'\xa8!\xa8E\xa87\xb0!\xa8\xd55\xe0 \xd7'\xd1'\xa8\xd5.\xf0	 !\xf0
 	\x904\x979\x919\xd0-\xd3.\xb0\xd17\xd17\x88\xf0 	\xd0#\xd1#\x88\xd8\xd7&\xd4&\x88C\xd8\x98#\x9f)\x99)\x98\xa0D\xa8\xaf\xa9\xa8\xb0R\xb8\xbf\xb9\xd07G\xc0s\xd0[^\xd7[g\xd2[g\xc83\xcf<\xca<\xd0my\xd0Jz\xd0z}\xd0~\xd1~\x88G\xd8\x98\x98C\x9fO\x99O\xd0,\xa8B\xd0/\xd1/\x89G\xf0 '\xf0 	\xd0.\xd1.\x88\xd8\xd7$\xd4$\x88C\xd8\x98#\x9f*\x99*\x98\xa0T\xa8#\xd7*<\xd1*<\xd0)=\xb8R\xc0\xc7\xc1\xd0?P\xd0PR\xd0S\xd1S\x89G\xf0 %\xf4 \xd8\x97z\x91z\xd8\x976\x916\xd8\xd8\x98c\x9fk\x99k\x98]\xa8!\xacH\xafL\xa9L\xabN\xd7,C\xd1,C\xc0H\xd3,M\xd0+N\xd0O\xf4	
\xf0 
\xf9\xf2) 7\xf9\xf2 !Fs   \xc2H(\xc3H-N)\xda__name__\xda
__module__\xda__qualname__r   r   r   r5   \xa9 \xf3    r4   r   r      s   \x84 \xf0*
\xd0'7\xf0 *
\xb8n\xf0 *
\xd0QW\xf4 *
r:   r   N)\xdasrc.core.modelsr   r   r   r   r   r9   r:   r4   \xda<module>r<      s   \xf0\xdf D\xd1 D\xdd \xf7+
\xf2 +
r:   
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

console = Console()

class InterviewSimulator:
    def __init__(self):
        self.questions_db = [
            "Fale um pouco sobre você.",
            "Por que você quer trabalhar nesta empresa?",
            "Qual foi seu maior desafio técnico até hoje?",
            "Como você lida com prazos apertados?",
            "Onde você se vê daqui a 5 anos?"
        ]

    def run_session(self):
        """Runs an interactive interview session in the terminal."""
        console.clear()
        console.print(Panel("[bold cyan]Simulador de Entrevista - Birth Hub 360[/bold cyan]", expand=False))
        console.print("O sistema fará perguntas e avaliará suas respostas (Simulado).\n")

        questions = random.sample(self.questions_db, 3)
        history = []

        for i, q in enumerate(questions, 1):
            console.print(f"[bold yellow]Pergunta {i}:[/bold yellow] {q}")
            answer = Prompt.ask("[italic]Sua resposta[/italic]")

            # Mock analysis simulation
            with console.status("[bold green]Analisando resposta...[/bold green]", spinner="dots"):
                time.sleep(1.5)

            feedback = self._generate_feedback(answer)
            console.print(f"[bold magenta]Feedback da IA:[/bold magenta] {feedback}\n")
            history.append({"q": q, "a": answer, "f": feedback})
            time.sleep(1)

        console.print(Panel("[bold green]Sessão Finalizada![/bold green] Resumo salvo no histórico."))
        return history

    def _generate_feedback(self, answer):
        """Generates simple mock feedback based on answer length."""
        if len(answer) < 20:
            return "Sua resposta foi muito curta. Tente elaborar mais sobre suas experiências usando o método STAR."
        elif len(answer) > 200:
            return "Boa profundidade, mas cuidado para não ser prolixo. Tente ser mais direto."
        else:
            return "Resposta equilibrada. Bons pontos levantados."

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
            f.write(f"# RELATÓRIO OPERACIONAL BIRTH HUB 360 - {datetime.now().strftime('%d/%m/%Y')}\n\n")

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

## src/modules/selenium_bot/__pycache__/config.cpython-312.pyc
```
\xcb
    H\x9dpi\xa2  \xe3            
       \xf3p   \x97 d dl Z ddddd e j                  dd\xab       e j                  d	d\xab      g d
\xa2ddgd\x9c	Zy)\xe9    NzMarcelo Nascimentozmarcelinmark@gmail.com\xda16999948479u   Ribeirão PretozAnalista de Revenue Operations\xdaINFOJOBS_PASSWORD\xdaSUA_SENHA_AQUI\xdaVAGAS_PASSWORD)zRevenue OperationszSales OperationszAnalista de Dados\xda
Salesforce\xdaHubSpotzHome Office)	\xdanome_completo\xdaemail\xdatelefone\xdacidade\xdacargo_atual\xdasenha_infojobs\xdasenha_vagas\xdabuscas\xdalocais)\xdaos\xdagetenv\xdaPERFIL\xa9 \xf3    \xfa'/app/src/modules/selenium_bot/config.py\xda<module>r      sV   \xf0\xdb 	\xf0 *\xd8%\xd8\xd8\xd83\xe0\x90b\x97i\x91i\xd0 3\xd05E\xd3F\xd8\x902\x979\x919\xd0-\xd0/?\xd3@\xf2\xf0 	\xd8\xf0\xf1%
\x81r   
```

## src/modules/selenium_bot/__pycache__/human_bot.cpython-312.pyc
```
\xcb
    P\x9dpi&  \xe3                   \xf3X   \x97 d dl Z d dlZd dlmZ d dlmZ d dlmZ d dlm	Z	  G d\x84 d\xab      Z
y)\xe9    N)\xda	webdriver)\xdaService)\xdaWebDriverWait)\xdaChromeDriverManagerc                   \xf3.   \x97 e Zd Zdd\x84Zd\x84 Zdd\x84Zd\x84 Zd\x84 Zy)	\xda	HumanoBotc                 \xf3.   \x97 d | _         || _        d | _        y )N)\xdadriver\xdaheadless\xdawait)\xdaselfr   s     \xfa*/app/src/modules/selenium_bot/human_bot.py\xda__init__zHumanoBot.__init__	   s   \x80 \xd8\x88\x8c\xd8 \x88\x8c\xd8\x88\x8d	\xf3    c                 \xf3\x9a  \x97 t        j                  \xab       }| j                  rU|j                  d\xab       |j                  d\xab       |j                  d\xab       |j                  d\xab       |j                  d\xab       t        j                  t        t        \xab       j                  \xab       \xab      |\xac\xab      | _        t        | j                  d\xab      | _
        y )Nz--headless=newz--no-sandboxz--disable-dev-shm-usagez--disable-gpuz--window-size=1920,1080)\xdaservice\xdaoptions\xe9   )r   \xdaChromeOptionsr   \xdaadd_argument\xdaChromer   r   \xdainstallr
   r   r   )r   r   s     r   \xdainiciar_driverzHumanoBot.iniciar_driver   s\x99   \x80 \xdc\xd7)\xd1)\xd3+\x88\xd8\x8f=\x8a=\xd8\xd7 \xd1 \xd0!1\xd42\xd8\xd7 \xd1 \xa0\xd40\xd8\xd7 \xd1 \xd0!:\xd4;\xd8\xd7 \xd1 \xa0\xd41\xd8\xd7 \xd1 \xd0!:\xd4;\xe4\xd7&\xd1&\xacw\xd47J\xd37L\xd77T\xd17T\xd37V\xd3/W\xd0ah\xd4i\x88\x8c\xdc!\xa0$\xa7+\xa1+\xa8r\xd32\x88\x8d	r   c                 \xf3Z   \x97 t        j                  ||\xab      }t        j                  |\xab       y)uL   Pausa a execução por um tempo variável para imitar 'tempo de pensamento'.N)\xdarandom\xdauniform\xdatime\xdasleep)r   \xdamin_seg\xdamax_seg\xdatempos       r   \xdadormir_aleatoriozHumanoBot.dormir_aleatorio   s   \x80 \xe4\x97\x91\x98w\xa8\xd30\x88\xdc\x8f
\x89
\x905\xd5r   c                 \xf3\x86   \x97 |D ]<  }|j                  |\xab       t        j                  t        j                  dd\xab      \xab       \x8c> y)zDDigita caractere por caractere com pausas variadas, como uma pessoa.g\x9a\x99\x99\x99\x99\x99\xa9?g\x9a\x99\x99\x99\x99\x99\xc9?N)\xda	send_keysr   r   r   r   )r   \xdaelemento\xdatexto\xdaletras       r   \xdadigitar_humanizadozHumanoBot.digitar_humanizado   s1   \x80 \xe3\x88E\xd8\xd7\xd1\x98u\xd4%\xdc\x8fJ\x89J\x94v\x97~\x91~\xa0d\xa8C\xd30\xd51\xf1 r   c                 \xf3v   \x97 | j                   r-t        d\xab       | j                   j                  \xab        d | _         y y )Nu   >> 🏁 Sessão finalizada.)r
   \xdaprint\xdaquit)r   s    r   \xdaencerrarzHumanoBot.encerrar%   s.   \x80 \xd8\x8f;\x8a;\xdc\xd0/\xd40\xd8\x8fK\x89K\xd7\xd1\xd4\xd8\x88D\x8dK\xf0 r   N)F)\xe9   \xe9   )\xda__name__\xda
__module__\xda__qualname__r   r   r"   r(   r,   \xa9 r   r   r   r      s   \x84 \xf3\xf2

3\xf3\xf2
2\xf3r   r   )r   r   \xdaseleniumr   \xda!selenium.webdriver.chrome.servicer   \xdaselenium.webdriver.support.uir   \xdawebdriver_manager.chromer   r   r2   r   r   \xda<module>r7      s!   \xf0\xdb \xdb \xdd \xdd 5\xdd 7\xdd 8\xf7!\xf2 !r   
```

## src/modules/selenium_bot/__pycache__/infojobs.cpython-312.pyc
```
\xcb
    ]\x9dpi  \xe3                   \xf3^   \x97 d dl Z d dlmZ d dlmZ d dlmZ d dlm	Z	 d dl
mZ  G d\x84 de	\xab      Zy)	\xe9    N)\xdaBy)\xdaKeys)\xdaexpected_conditions)\xda	HumanoBot)\xdaPERFILc                   \xf3   \x97 e Zd Zd\x84 Zd\x84 Zd\x84 Zy)\xdaInfojobsBotc                 \xf3h  \x97 t        d\xab       | j                  j                  d\xab       | j                  dd\xab       | j                  j                  t        j                  t        j                  df\xab      \xab      }| j                  |t        d   \xab       | j                  dd\xab       | j                  j                  t        j                  d	\xab      }| j                  |t        d
   \xab       | j                  dd\xab       |j                  t        j                  \xab       t        d\xab       | j                  dd\xab       y )Nu*   >> 🔓 Iniciando Login Infojobs Humano...z&https://www.infojobs.com.br/login.aspx\xe9   \xe9   \xdaUsername\xdaemail\xe9   \xe9   \xdaPassword\xdasenha_infojobsu1   >> ✅ Login efetuado. Aguardando carregamento...\xe9   )\xdaprint\xdadriver\xdaget\xdadormir_aleatorio\xdawait\xdauntil\xdaEC\xdaelement_to_be_clickabler   \xdaID\xdadigitar_humanizador   \xdafind_element\xda	send_keysr   \xdaRETURN)\xdaself\xda
user_field\xda	pwd_fields      \xfa)/app/src/modules/selenium_bot/infojobs.py\xdaloginzInfojobsBot.login	   s\xe7   \x80 \xdc\xd0:\xd4;\xd8\x8f\x89\x8f\x89\xd0@\xd4A\xd8\xd7\xd1\x98a\xa0\xd4#\xf0 \x97Y\x91Y\x97_\x91_\xa4R\xd7%?\xd1%?\xc4\xc7\xc1\xc8
\xd0@S\xd3%T\xd3U\x88
\xd8\xd7\xd1\xa0
\xacF\xb07\xa9O\xd4<\xd8\xd7\xd1\x98a\xa0\xd4#\xf0 \x97K\x91K\xd7,\xd1,\xacR\xafU\xa9U\xb0J\xd3?\x88	\xd8\xd7\xd1\xa0	\xac6\xd02B\xd1+C\xd4D\xd8\xd7\xd1\x98a\xa0\xd4#\xf0 	\xd7\xd1\x9cD\x9fK\x99K\xd4(\xdc\xd0A\xd4B\xd8\xd7\xd1\x98a\xa0\xd5#\xf3    c           	      \xf32  \x97 t         d   D ]\x8b  }t         d   D ]}  }t        d|\x9b d|\x9b d\x9d\xab       |j                  dd\xab      }|j                  dd\xab      }d|\x9b d	|\x9b \x9d}| j                  j	                  |\xab       | j                  d
d\xab       | j                  \xab        \x8c \x8c\x8d y )N\xdalocais\xdabuscasu   
>> 🔍 Buscando: 'z' em '\xda'\xda \xda+z2https://www.infojobs.com.br/empregos.aspx?Palabra=z&Campo=loc&Donde=\xe9   \xe9   )r   r   \xdareplacer   r   r   \xdaprocessar_lista_vagas)r!   \xdalocal\xdacargo\xda	termo_url\xda	local_url\xdaurls         r$   \xdaexecutar_buscazInfojobsBot.executar_busca   s\x9b   \x80 \xdc\x98H\xd4%\x88E\xdc\xa0\xd4)\x90\xdc\xd0-\xa8e\xa8W\xb0F\xb85\xb8'\xc0\xd0C\xd4D\xf0 "\x9fM\x99M\xa8#\xa8s\xd33\x90	\xd8!\x9fM\x99M\xa8#\xa8s\xd33\x90	\xd8J\xc89\xc8+\xd0Uf\xd0gp\xd0fq\xd0r\x90\xe0\x97\x91\x97\x91\xa0\xd4$\xd8\xd7%\xd1%\xa0a\xa8\xd4+\xe0\xd7*\xd1*\xd5,\xf1 *\xf1 &r&   c                 \xf3\xb0  \x97 | j                   j                  t        j                  d\xab      }|D \x8fcg c]%  }|j	                  d\xab      s\x8c|j	                  d\xab      \x91\x8c' }}t        j                  |\xab       t        dt        |\xab      \x9b d\x9d\xab       t        |\xab      D \x90]  \  }}|dk\  r y 	 | j                   j                  |\xab       | j                  dd\xab       | j                   j                  t        j                  d\xab      }|r\xa4|d	   j                  \xab       r\x91|d	   }|j                  j                  \xab       }d
|v r_| j                   j!                  d|\xab       | j                  dd\xab       |j#                  \xab        t        d|\x9b \x9d\xab       | j                  dd\xab       nt        d|\x9b \x9d\xab       nt        d\xab       \x90\x8c y c c}w # t$        $ r}	t        d|	\x9b \x9d\xab       Y d }	~	\x90\x8c=d }	~	ww xY w)Nzdiv.vaga a.text-decoration-none\xdahrefu      📄 Encontrei z vagas. Analisando...r   r   \xe9   z//a[contains(@id, 'lbtnApply')]r   \xda
CANDIDATARzCarguments[0].scrollIntoView({behavior: 'smooth', block: 'center'});r   u      [✅ CANDIDATURA] r   r-   u      [ℹ️ JÁ INSCRITO] u      [❌ BOTÃO NÃO ENCONTRADO]u      [⚠️ ERRO] Pulei a vaga: )r   \xdafind_elementsr   \xdaCSS_SELECTOR\xdaget_attribute\xdarandom\xdashuffler   \xdalen\xda	enumerater   r   \xdaXPATH\xdais_displayed\xdatext\xdaupper\xdaexecute_script\xdaclick\xda	Exception)
r!   \xdavagas\xdav\xdalinks\xdai\xdalink\xdabotoes\xdabtn\xda	texto_btn\xdaes
             r$   r0   z!InfojobsBot.processar_lista_vagas,   s\x94  \x80 \xe0\x97\x91\xd7)\xd1)\xac"\xaf/\xa9/\xd0;\\xd3]\x88\xd927\xd3S\xb1%\xa8Q\xb81\xbf?\xb9?\xc86\xd5;R\x90\x97\x91\xa0\xd5(\xb0%\x88\xd0S\xf4 	\x8f\x89\x90u\xd4\xe4\xd0"\xa43\xa0u\xa3:\xa0,\xd0.C\xd0D\xd4E\xe4 \xa0\xd7'\x89G\x88A\x88t\xd8\x90A\x8av\x91u\xf0=\xd8\x97\x91\x97\x91\xa0\xd4%\xd8\xd7%\xd1%\xa0a\xa8\xd4+\xf0 \x9f\x99\xd72\xd12\xb42\xb78\xb18\xd0=^\xd3_\x90\xe1\x98f\xa0Q\x99i\xd74\xd14\xd46\xd8 \xa0\x99)\x90C\xd8 #\xa7\xa1\xa7\xa1\xd3 0\x90I\xe0#\xa0y\xd10\xe0\x9f\x99\xd72\xd12\xd8a\xd8\xf4\xf0 \xd7-\xd1-\xa8a\xb0\xd43\xe0\x9f	\x99	\x9c\xdc\xd0 5\xb0d\xb0V\xd0<\xd4=\xd8\xd7-\xd1-\xa8a\xb0\xd53\xe4\xd0 9\xb8$\xb8\xd0@\xd5A\xe4\xd0;\xd4<\xf9\xf19 (\xf9\xf2 T\xf8\xf4J \xf2 =\xdc\xd07\xb8\xb0s\xd0;\xd7<\xd2<\xfb\xf0=\xfas$   \xafF.\xc1F.\xc2"DF3\xc63	G\xc6<G\xc7GN)\xda__name__\xda
__module__\xda__qualname__r%   r6   r0   \xa9 r&   r$   r	   r	      s   \x84 \xf2$\xf2(-\xf3)=r&   r	   )r>   \xdaselenium.webdriver.common.byr   \xdaselenium.webdriver.common.keysr   \xdaselenium.webdriver.supportr   r   \xda"src.modules.selenium_bot.human_botr   \xdasrc.modules.selenium_bot.configr   r	   rU   r&   r$   \xda<module>r[      s%   \xf0\xdb \xdd +\xdd /\xdd @\xdd 8\xdd 2\xf4M=\x90)\xf5 M=r&   
```

## src/modules/selenium_bot/__pycache__/runner.cpython-312.pyc
```
\xcb
    v\x9dpi\xae  \xe3                   \xf3\xae   \x97 d dl Z d dlZd dlmZ d dlmZ d dlmZ  G d\x84 d\xab      Zedk(  r e\xab       Z		 e	j                  \xab        yy# e$ r  ed\xab       Y yw xY w)	\xe9    N)\xdadatetime)\xdaInfojobsBot)\xdaVagasBotc                   \xf3   \x97 e Zd Zd\x84 Zd\x84 Zy)\xdaBotRunner24hc                 \xf3   \x97 d | _         y )N)\xdabot)\xdaselfs    \xfa'/app/src/modules/selenium_bot/runner.py\xda__init__zBotRunner24h.__init__   s	   \x80 \xd8\x88\x8d\xf3    c                 \xf3\xe8  \x97 t        dt        j                  \xab       j                  d\xab      \x9b \x9d\xab       	 	 t        d\xab       t	        d\xac\xab      | _        | j
                  j                  \xab        | j
                  j                  \xab        | j
                  j                  \xab        | j
                  j                  \xab        d | _        d}t        j                  \xab       |z   }t        j                  dt        j                  |\xab      \xab      }t        d|\x9b \x9d\xab       t        j                  |\xab       \x8c\xf2# t        $ rE}t        d|\x9b \x9d\xab       | j
                  r!| j
                  j                  \xab        d | _        Y d }~\x8c\xafd }~ww xY w)	Nu"   >> 🌙 Vigília 24h iniciada em: z%H:%MTz
>> Iniciando Ciclo Infojobs...)\xdaheadlessu      [⚠️ ERRO NO CICLO] i  u*   >> 💤 Modo Standby. Próxima ronda às: )\xdaprintr   \xdanow\xdastrftimer   r	   \xdainiciar_driver\xdalogin\xdaexecutar_busca\xdaencerrar\xda	Exception\xdatime\xda	localtime\xdasleep)r
   \xdae\xdatempo_espera\xdaproxima_ronda\xdahora_proximas        r   \xdarunzBotRunner24h.run   s  \x80 \xdc\xd02\xb48\xb7<\xb1<\xb3>\xd73J\xd13J\xc87\xd33S\xd02T\xd0U\xd4V\xe0\xf0$\xe4\xd08\xd49\xdc&\xb0\xd45\x90\x94\xd8\x97\x91\xd7'\xd1'\xd4)\xd8\x97\x91\x97\x91\xd4 \xd8\x97\x91\xd7'\xd1'\xd4)\xd8\x97\x91\xd7!\xd1!\xd4#\xd8\x90\x94\xf0   \x88L\xe4 \x9fI\x99I\x9bK\xa8,\xd16\x88M\xdc\x9f=\x99=\xa8\xb4$\xb7.\xb1.\xc0\xd32O\xd3P\x88L\xe4\xd0>\xb8|\xb8n\xd0M\xd4N\xdc\x8fJ\x89J\x90|\xd4$\xf0? \xf8\xf4 \xf2 $\xdc\xd02\xb01\xb0#\xd06\xd47\xd8\x978\x928\xd8\x97H\x91H\xd7%\xd1%\xd4'\xd8#\x90D\x94H\xff\xf8\xf0	$\xfas   \xb2BD# \xc4#	E1\xc4,;E,\xc5,E1N)\xda__name__\xda
__module__\xda__qualname__r   r   \xa9 r   r   r   r      s   \x84 \xf2\xf3"%r   r   \xda__main__u!   >> 🛑 Parada manual solicitada.)r   \xdarandomr   \xda!src.modules.selenium_bot.infojobsr   \xdasrc.modules.selenium_bot.vagasr   r   r    \xdarunnerr   \xdaKeyboardInterruptr   r#   r   r   \xda<module>r*      s]   \xf0\xdb \xdb \xdd \xdd 9\xdd 3\xf7&%\xf1 &%\xf0P \x88z\xd2\xd9\x8b^\x80F\xf03\xd8\x8f
\x89
\x8d\xf0 \xf8\xf0 \xf2 3\xd9\xd01\xd62\xf03\xfas   \xb2A \xc1A\xc1A
```

## src/modules/selenium_bot/__pycache__/vagas.cpython-312.pyc
```
\xcb
    m\x9dpi\xf4  \xe3                   \xf3>   \x97 d dl mZ d dlmZ d dlmZ  G d\x84 de\xab      Zy)\xe9    )\xdaBy)\xda	HumanoBot)\xdaPERFILc                   \xf3   \x97 e Zd Zd\x84 Zd\x84 Zy)\xdaVagasBotc                 \xf3|  \x97 t        d\xab       t        d   D ]\xfa  }d|j                  dd\xab      \x9b \x9d}t        d|\x9b \x9d\xab       | j                  j	                  |\xab       | j                  dd\xab       | j                  j                  t        j                  d	\xab      }g }|D ]C  }	 |j                  t        j                  d
\xab      }|j                  |j                  d\xab      \xab       \x8cE t        dt        |\xab      \x9b d\x9d\xab       |d d D ]  }	 | j                  |\xab       \x8c \x8c\xfc y #  Y \x8c\x81xY w# t        $ r}t        d|\x9b \x9d\xab       Y d }~\x8c=d }~ww xY w)NuV   >> ⚠️ Nota: Para o Vagas.com, certifique-se de estar logado ou implemente o login.\xdabuscasz"https://www.vagas.com.br/vagas-de-\xda \xda-u    
>> 🔍 Buscando no Vagas.com: \xe9   \xe9   \xdavaga\xdaa\xdahrefz   Encontradas z vagas.z   Erro ao processar vaga: )\xdaprintr   \xdareplace\xdadriver\xdaget\xdadormir_aleatorio\xdafind_elementsr   \xda
CLASS_NAME\xdafind_element\xdaTAG_NAME\xdaappend\xdaget_attribute\xdalen\xdaprocessar_vaga\xda	Exception)	\xdaself\xdacargo\xdaurl\xdavagas\xdalinksr   \xda	link_elem\xdalink\xdaes	            \xfa&/app/src/modules/selenium_bot/vagas.py\xdaexecutar_buscazVagasBot.executar_busca   s'  \x80 \xf4 	\xd0f\xd4g\xe4\x98H\xd4%\x88E\xd86\xb0u\xb7}\xb1}\xc0S\xc8#\xd37N\xd06O\xd0P\x88C\xdc\xd05\xb0e\xb0W\xd0=\xd4>\xe0\x8fK\x89K\x8fO\x89O\x98C\xd4 \xd8\xd7!\xd1!\xa0!\xa0Q\xd4'\xe0\x97K\x91K\xd7-\xd1-\xacb\xafm\xa9m\xb8V\xd3D\x88E\xd8\x88E\xe3\x90\xf0\xd8 $\xd7 1\xd1 1\xb4"\xb7+\xb1+\xb8s\xd3 C\x90I\xd8\x97L\x91L\xa0\xd7!8\xd1!8\xb8\xd3!@\xd5A\xf0 \xf4 \x90O\xa4C\xa8\xa3J\xa0<\xa8w\xd07\xd48\xe0\x98b\x98q\x9b	\x90\xf0=\xd8\xd7'\xd1'\xa8\xd5-\xf1 "\xf1' &\xf8\xf0\xd9\xfb\xf4 !\xf2 =\xdc\xd07\xb8\xb0s\xd0;\xd7<\xd1<\xfb\xf0=\xfas%   \xc2A D\xc3=D\xc4D\xc4	D;\xc4#D6\xc46D;c                 \xf3\x84  \x97 | j                   j                  |\xab       | j                  dd\xab       	 | j                   j                  t        j
                  d\xab      }|r4|d   j                  \xab        t        d|\x9b \x9d\xab       | j                  dd\xab       y t        d|\x9b \x9d\xab       y # t        $ r}t        d|\x9b \x9d\xab       Y d }~y d }~ww xY w)	N\xe9   \xe9   zbt-candidaturar   z   [Tentativa de Candidatura] r   u      [Botão não encontrado] z
   [Erro] )	r   r   r   r   r   r   \xdaclickr   r   )r   r%   \xdabtsr&   s       r'   r   zVagasBot.processar_vaga$   s\xa6   \x80 \xd8\x8f\x89\x8f\x89\x98\xd4\xd8\xd7\xd1\x98a\xa0\xd4#\xf0	$\xe0\x97+\x91+\xd7+\xd1+\xacB\xafM\xa9M\xd0;K\xd3L\x88C\xd9\xd8\x90A\x91\x97\x91\x94\xdc\xd06\xb0t\xb0f\xd0=\xd4>\xd8\xd7%\xd1%\xa0a\xa8\xd5+\xf4 \xd04\xb0T\xb0F\xd0;\xd5<\xf8\xdc\xf2 	$\xdc\x90J\x98q\x98c\xd0"\xd7#\xd1#\xfb\xf0	$\xfas   \xafAB \xc2B \xc2	B?\xc2'B:\xc2:B?N)\xda__name__\xda
__module__\xda__qualname__r(   r   \xa9 \xf3    r'   r   r      s   \x84 \xf2=\xf3<$r2   r   N)\xdaselenium.webdriver.common.byr   \xda"src.modules.selenium_bot.human_botr   \xdasrc.modules.selenium_bot.configr   r   r1   r2   r'   \xda<module>r6      s   \xf0\xdd +\xdd 8\xdd 2\xf4.$\x88y\xf5 .$r2   
```

## src/modules/selenium_bot/config.py
```
import os

# Configuração do Perfil e Bot
PERFIL = {
    "nome_completo": "Marcelo Nascimento",
    "email": "marcelinmark@gmail.com",
    "telefone": "16999948479",
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
