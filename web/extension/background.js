// Runs only when clicked. activeTab grants temporary access to this tab;
// no host list, telemetry, storage or network requests.
chrome.action.onClicked.addListener(async (tab) => {
  try {
    await chrome.scripting.insertCSS({ target: { tabId: tab.id }, files: ['fonts.css'] });
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id }, files: ['content.js'],
    });
    const enabled = results[0].result.enabled;
    await chrome.action.setBadgeText({ tabId: tab.id, text: enabled ? 'ON' : '' });
    await chrome.action.setTitle({ tabId: tab.id, title: enabled ? 'Restore hex hashes' : 'Show hashes as sigils' });
  } catch (error) {
    console.error('Sigil could not modify this tab:', error);
    await chrome.action.setBadgeText({ tabId: tab.id, text: '!' });
    await chrome.action.setTitle({ tabId: tab.id, title: 'This page could not be changed. See the extension console for details.' });
  }
});
chrome.tabs.onUpdated.addListener((tabId, change) => {
  if (change.status === 'loading') {
    chrome.action.setBadgeText({ tabId, text: '' });
    chrome.action.setTitle({ tabId, title: 'Show hashes as sigils / restore hex' });
  }
});
