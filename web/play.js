(() => {
  const $ = (id) => document.getElementById(id);
  const hexOf = (data) => Array.from(data, (b) => b.toString(16).padStart(2, '0')).join('');
  const KEYS = ['hex', 'handled', 'plain'];
  const NAMES = { hex: 'the hex', handled: 'the handled sigil', plain: 'the plain sigil' };
  let current = {};

  function decode() {
    $('decoded').textContent = '';
    try {
      const length = Number($('length').value);
      if (!Number.isInteger(length) || length < 8 || length > 256) throw new Error('Choose 8–256 bytes: Sigil encodes at least 8.');
      const data = SigilCode.decode($('reading').value, length);
      $('decoded').textContent = hexOf(data);
      $('decode-status').textContent = 'Decoded — the arithmetic check passes.';
      $('decode-status').className = '';
    } catch (error) {
      $('decode-status').textContent = error instanceof SigilCode.DecodeError ? `${error.kind}: ${error.message}` : error.message;
      $('decode-status').className = 'error';
    }
  }

  function encode() {
    const hex = $('hex').value.replace(/\s/g, '');
    current = {};
    $('encode-status').className = '';
    try {
      if (!/^(?:[a-fA-F0-9]{2})+$/.test(hex)) throw new Error('Enter complete hex bytes (two hex digits per byte).');
      if (hex.length > 512) throw new Error('Try up to 256 bytes in this playground. The library supports longer values.');
      const bytes = Uint8Array.from(hex.match(/../g), (b) => parseInt(b, 16));
      if (bytes.length < 8) throw new Error('Sigil encodes at least 8 bytes (16 hex digits).');
      current = { hex: hexOf(bytes), handled: SigilCode.encode(bytes, true), plain: SigilCode.encode(bytes, false) };
      $('encode-status').textContent = `${bytes.length} bytes. Double-click any of them to select it whole.`;
      $('reading').value = current.handled;
      $('length').value = bytes.length;
      decode();
    } catch (error) {
      $('encode-status').textContent = error.message;
      $('encode-status').className = 'error';
    }
    for (const key of KEYS) {
      const value = current[key] || '';
      $(`out-${key}`).textContent = value;
      // The left-to-right mark before a handle is invisible, so it goes uncounted.
      $(`n-${key}`).textContent = value ? `${Array.from(value).filter((c) => c !== SigilCode.MARK).length} characters` : '';
      document.querySelector(`[data-copy=${key}]`).disabled = !value;
    }
  }
  $('hex').addEventListener('input', encode);
  $('random').addEventListener('click', () => {
    $('hex').value = hexOf(crypto.getRandomValues(new Uint8Array(32)));
    encode();
  });
  $('reading').addEventListener('input', decode);
  $('length').addEventListener('input', decode);
  document.querySelectorAll('[data-copy]').forEach((button) => button.addEventListener('click', async () => {
    const key = button.dataset.copy;
    try {
      await navigator.clipboard.writeText(current[key]);
      $('encode-status').textContent = `Copied ${NAMES[key]}.`;
    } catch (error) {
      $('encode-status').textContent = `Clipboard access unavailable. Select ${NAMES[key]} and copy it.`;
    }
  }));
  $('toggle').addEventListener('click', () => {
    const { enabled } = SigilPage.toggle($('hashes'));
    $('toggle').textContent = enabled ? 'Restore hex' : 'Show sigils';
    $('toggle').setAttribute('aria-pressed', String(enabled));
  });
  encode();
})();
