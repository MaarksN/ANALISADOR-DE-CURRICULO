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
