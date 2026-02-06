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
