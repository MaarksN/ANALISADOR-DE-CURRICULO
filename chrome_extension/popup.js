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
