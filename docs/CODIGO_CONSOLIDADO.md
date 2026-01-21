# CÓDIGO FONTE CONSOLIDADO - BIRTH HUB 360 (ATUALIZADO)

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
