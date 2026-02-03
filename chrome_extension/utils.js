export function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

export function log(msg) {
    console.log(`[AutoApply] ${msg}`);
}
