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
