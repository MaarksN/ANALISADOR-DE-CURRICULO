import { sleep, log } from './utils.js';

export async function runVagasBot() {
    log("Iniciando Bot Vagas.com...");

    // Check if we are on a search list or a single job page
    if (document.querySelector('.vaga')) {
        log("Lista de vagas detectada. Iterando...");
        const jobLinks = document.querySelectorAll('a.link-detalhes-vaga');

        // Note: Vagas.com opens new tabs/windows for jobs usually.
        // A Content Script cannot easily control multiple tabs without Background script coordination.
        // For MVP, we will only log that we found links.
        log(`Encontrados ${jobLinks.length} links de vagas. O bot atual funciona melhor na página da vaga individual.`);

    } else {
        // Single Job Page
        const applyBtn = document.querySelector('button[name="btCandidatura"]');
        // Vagas.com selectors vary often.

        if (applyBtn) {
            log("Botão de candidatura encontrado.");
            applyBtn.click();
            await sleep(2000);

            // Handle follow-up questions often presented as a list of checkboxes/radios
            // ...
        } else {
            log("Botão de Candidatura não identificado.");
        }
    }
}
