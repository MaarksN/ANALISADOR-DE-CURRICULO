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

        // Sometimes a secondary confirmation or login modal appears
        // Example: "#ctl00_phMasterPage_cContent_ucApplyVacancy_lbtnApply"
        // Selectors vary by Infojobs page version.

        const confirmBtn = document.querySelector('a[id*="lbtnApply"]');
        if (confirmBtn) {
            log("Confirmando candidatura...");
            confirmBtn.click();
            await sleep(2000);
        } else {
            // Check for login requirement
            if (document.querySelector('.login-form')) {
                log("Necessário login. O bot não preenche senhas por segurança.");
            }
        }
    } else {
        log("Botão de candidatura não encontrado nesta página.");
    }
}
