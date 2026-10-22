(async () => {
  const result = document.getElementById('result');
  let count = 0;
  const check = (value, message) => { if (!value) throw new Error(message); count++; };
  const pause = () => new Promise((resolve) => setTimeout(resolve, 0));
  const bytes = (hex) => Uint8Array.from(hex.match(/../g) ?? [], (b) => parseInt(b, 16));
  const hexOf = (data) => Array.from(data, (b) => b.toString(16).padStart(2, '0')).join('');
  try {
    const vectors = await (await fetch('../vectors.json')).json();
    for (const v of vectors.good) {
      check(SigilCode.encode(bytes(v.data)) === v.text, `bundle encode ${v.data}`);
      check(hexOf(SigilCode.decode(v.text, v.data.length / 2)) === v.data, 'bundle decode');
    }
    for (const v of vectors.variants) check(hexOf(SigilCode.decode(v.text, v.data.length / 2)) === v.data, 'bundle variant');
    for (const v of vectors.bad) {
      let kind = null;
      try { SigilCode.decode(v.text, v.length); } catch (e) { kind = e.kind; }
      check(kind === v.error, 'bundle error');
    }

    const root = document.getElementById('fixtures');
    const full = 'af1349b9f5f9a1a6a0404dea36dcc9499bcb25c9adc112b7cc9a93cae41f3262';
    const commit = '716c98ca9f4336a45f51c15eeff0c9608c1002ae';
    root.innerHTML = '<p id="full"></p><a id="link"></a><a id="short"></a><a id="even"></a><a id="invalid"></a><p id="ordinary"></p><p id="boundary"></p><div contenteditable="true"><span id="edit"></span></div><textarea id="input"></textarea><button id="button"></button><div hidden id="hidden"></div><div style="display:none" id="csshidden"></div><p id="attribute"></p>';
    const $ = (id) => document.getElementById(id);
    $('full').textContent = `(${full}), ${full.toUpperCase()}`;
    $('link').textContent = full;
    $('link').href = `https://github.com/example/repo/commit/${full}`;
    $('short').textContent = commit.slice(0, 7);
    $('short').href = `https://github.com/johnservil/sigil/commit/${commit}`;
    $('even').textContent = commit.slice(0, 8);
    $('even').href = $('short').href;
    $('invalid').textContent = commit.slice(0, 7);
    $('invalid').setAttribute('href', 'http://[');
    $('ordinary').textContent = '1234567 abcdef1';
    $('boundary').textContent = `x${full} ${full}0 α${full} ${full}β`;
    for (const id of ['edit', 'button', 'hidden', 'csshidden']) $(id).textContent = full;
    $('input').value = full;
    $('attribute').title = full;
    const before = root.innerHTML;
    const href = $('link').href;
    check(SigilPage.toggle(root).enabled, 'enable');
    check($('full').querySelectorAll('[data-sigil-hex]').length === 2, 'two complete hashes');
    check($('full').firstElementChild.textContent === SigilCode.encode(bytes(full)), 'replacement matches codec');
    check($('link').href === href, 'link destination preserved');
    check($('short').firstElementChild.textContent === SigilCode.encode(bytes('0' + commit.slice(0, 7))), 'odd short ID pads a zero nibble');
    check($('short').firstElementChild.title.includes('Abbreviated commit (7 hex digits'), 'short ID is labelled');
    check($('even').firstElementChild.textContent === SigilCode.encode(bytes(commit.slice(0, 8))), 'even short ID');
    for (const id of ['invalid', 'ordinary', 'boundary', 'edit', 'button', 'hidden', 'csshidden']) check(!$(id).querySelector('[data-sigil-hex]'), `skip ${id}`);
    check($('input').value === full, 'form value unchanged');
    check($('attribute').title === full, 'attribute unchanged');

    const dynamic = document.createElement('p');
    dynamic.textContent = full;
    root.append(dynamic);
    await pause();
    check(dynamic.firstElementChild?.dataset.sigilHex === full, 'new content observed');
    dynamic.textContent = commit;
    await pause();
    check(dynamic.firstElementChild?.dataset.sigilHex === commit, 'changed content observed');
    dynamic.remove();
    check(!SigilPage.toggle(root).enabled, 'disable');
    check(root.innerHTML === before, 'exact HTML restored');
    check($('input').value === full, 'form value survives restoration');

    // Exercise the exact generated script used for repeated extension clicks.
    const inject = () => new Promise((resolve, reject) => {
      const script = document.createElement('script');
      script.src = 'extension/content.js';
      script.onload = () => { script.remove(); resolve(); };
      script.onerror = reject;
      document.head.append(script);
    });
    await inject();
    check(!!$('short').querySelector('[data-sigil-hex]'), 'extension bundle enables');
    await inject();
    check(root.innerHTML === before, 'reinjection restores without double wrapping');

    // Extension shell: API wiring and minimal permissions, with Chrome APIs mocked.
    const manifest = await (await fetch('extension/manifest.json')).json();
    check(manifest.permissions.join(',') === 'activeTab,scripting' && !manifest.host_permissions, 'temporary tab permissions only');
    let click, navigation, active = false;
    const badges = [];
    const fakeChrome = {
      action: {
        onClicked: { addListener(fn) { click = fn; } },
        async setBadgeText(value) { badges.push(value.text); },
        async setTitle() {},
      },
      scripting: {
        async insertCSS(request) { check(request.target.tabId === 7 && request.files[0] === 'fonts.css', 'local extension fonts'); },
        async executeScript(request) {
          check(request.target.tabId === 7 && request.files[0] === 'content.js', 'click injects content bundle');
          active = !active;
          return [{ result: { enabled: active } }];
        },
      },
      tabs: { onUpdated: { addListener(fn) { navigation = fn; } } },
    };
    new Function('chrome', await (await fetch('extension/background.js')).text())(fakeChrome);
    await click({ id: 7 });
    check(badges.at(-1) === 'ON', 'extension enabled badge');
    await click({ id: 7 });
    check(badges.at(-1) === '', 'extension disabled badge');
    navigation(7, { status: 'loading' });
    check(badges.at(-1) === '', 'navigation clears badge');

    // Real playground UI in a same-origin frame.
    const frame = document.createElement('iframe');
    frame.src = '../play.html';
    document.getElementById('frames').append(frame);
    await new Promise((resolve) => { frame.onload = resolve; });
    const doc = frame.contentDocument;
    const field = (id) => doc.getElementById(id);
    check(field('sigil').textContent === SigilCode.encode(bytes(full)), 'playground initial answer');
    const ethiopic = await doc.fonts.load('32px "Noto Sans Ethiopic"', 'ሀ');
    const canadian = await doc.fonts.load('32px "Noto Sans Canadian Aboriginal"', 'ᕖ');
    check(ethiopic.length > 0 && canadian.length > 0, 'bundled script fonts load');
    field('hex').value = '00';
    field('hex').dispatchEvent(new Event('input'));
    check(field('sigil').textContent === '00', 'playground leading zero');
    check(field('length').value === '1' && field('decoded').textContent === '00', 'playground roundtrip');
    field('reading').value = '01';
    field('reading').dispatchEvent(new Event('input'));
    check(field('decode-status').textContent.startsWith('check:'), 'playground rejects changed sigil');
    field('hex').value = 'xyz';
    field('hex').dispatchEvent(new Event('input'));
    check(field('copy').disabled && field('sigil').textContent === '', 'invalid input clears stale output');
    field('random').click();
    check(field('hex').value.length === 64 && field('sigil').textContent.length === 26, 'random example');
    field('toggle').click();
    check(!!doc.querySelector('#hashes [data-sigil-hex]'), 'playground toggle');
    field('toggle').click();
    check(!doc.querySelector('#hashes [data-sigil-hex]'), 'playground restore');
    result.textContent = `PASS: ${count} checks`;
  } catch (error) {
    result.textContent = `FAIL: ${error.stack || error}`;
  }
})();
