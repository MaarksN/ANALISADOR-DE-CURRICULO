(async () => {
    const src = chrome.runtime.getURL('content_router.js');
    const contentMain = await import(src);
})();
