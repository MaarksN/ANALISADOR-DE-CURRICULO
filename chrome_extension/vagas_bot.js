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
