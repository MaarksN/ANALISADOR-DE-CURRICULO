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
