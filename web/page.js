// Display-only experiment: complete hex tokens become reversible Sigil spans.
// No attributes, URLs, form values or network resources are changed.
(() => {
  if (globalThis.SigilPage) return;
  const HASH = /(?<![\p{L}\p{N}_])(?:[a-fA-F0-9]{128}|[a-fA-F0-9]{96}|[a-fA-F0-9]{64}|[a-fA-F0-9]{40}|[a-fA-F0-9]{32})(?![\p{L}\p{N}_])/gu;
  const SKIP = 'script,style,noscript,textarea,input,select,option,button,head,svg,math,[contenteditable]:not([contenteditable="false"]),[hidden],[aria-hidden="true"],[data-sigil-hex],[data-sigil-ignore]';
  let observer = null;
  let scope = null;

  // Short IDs need context, so ordinary seven-digit numbers remain untouched.
  function shortCommit(node, text) {
    const short = text.match(/^\s*([a-fA-F0-9]{7,12})\s*$/);
    const link = node.parentElement.closest('a[href]');
    if (!short || !link) return [];
    const target = link.pathname.match(/\/(?:commit|commits)\/([a-fA-F0-9]{7,64})(?:\/|$)/);
    if (!target || !target[1].toLowerCase().startsWith(short[1].toLowerCase())) return [];
    return [{ 0: short[1], index: text.indexOf(short[1]), short: true }];
  }

  function convert(node) {
    if (!node.isConnected || !node.parentElement || node.parentElement.closest(SKIP)) return;
    const text = node.data;
    const full = [...text.matchAll(HASH)];
    const matches = full.length ? full : shortCommit(node, text);
    if (!matches.length || !node.parentElement.getClientRects().length) return;
    const fragment = document.createDocumentFragment();
    let start = 0;
    for (const match of matches) {
      fragment.append(document.createTextNode(text.slice(start, match.index)));
      const hex = match[0];
      const padded = hex.length % 2 ? '0' + hex : hex;
      const bytes = Uint8Array.from(padded.match(/../g), (b) => parseInt(b, 16));
      const span = document.createElement('span');
      span.dataset.sigilHex = hex;
      span.textContent = globalThis.SigilCode.encode(bytes);
      const kind = match.short ? `Abbreviated commit (${hex.length} hex digits${hex.length % 2 ? '; one leading zero nibble padded' : ''})` : `Hex (${bytes.length} bytes)`;
      span.title = `${hex}\n${kind}, displayed as a sigil. Toggle to restore hex.`;
      span.style.cssText = 'white-space:nowrap;font-family:"Noto Sans Ethiopic", "Noto Sans Canadian Aboriginal", "Segoe UI", sans-serif;text-decoration:underline dotted;text-underline-offset:.2em';
      fragment.append(span);
      start = match.index + hex.length;
    }
    fragment.append(document.createTextNode(text.slice(start)));
    node.replaceWith(fragment);
  }

  function scan(root) {
    if (root.nodeType === Node.TEXT_NODE) {
      convert(root);
      return;
    }
    if (root.nodeType !== Node.ELEMENT_NODE || root.closest(SKIP)) return;
    const walker = document.createTreeWalker(root, NodeFilter.SHOW_TEXT);
    const nodes = [];
    while (walker.nextNode()) nodes.push(walker.currentNode);
    nodes.forEach(convert);
  }

  function toggle(root = document.body) {
    if (observer) {
      observer.disconnect();
      observer = null;
      scope.querySelectorAll('[data-sigil-hex]').forEach((span) => {
        span.replaceWith(document.createTextNode(span.dataset.sigilHex));
      });
      scope = null;
      return { enabled: false };
    }
    scope = root;
    scan(scope);
    observer = new MutationObserver((records) => {
      for (const record of records) {
        if (record.type === 'characterData') scan(record.target);
        else record.addedNodes.forEach(scan);
      }
    });
    observer.observe(scope, { childList: true, characterData: true, subtree: true });
    return { enabled: true };
  }
  globalThis.SigilPage = Object.freeze({ toggle });
})();
