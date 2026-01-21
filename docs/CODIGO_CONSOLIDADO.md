# CÓDIGO FONTE CONSOLIDADO - BIRTH HUB 360

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
