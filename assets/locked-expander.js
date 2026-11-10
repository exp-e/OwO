(() => {
  const bundleUrl = new URL('locked-expander.json', document.currentScript.src);
  let bundlePromise;
  function bundle() {
    if (!bundlePromise) {
      bundlePromise = fetch(bundleUrl).then(response => {
        if (!response.ok) throw new Error('Note unavailable');
        return response.json();
      }).catch(error => { bundlePromise = undefined; throw error; });
    }
    return bundlePromise;
  }
  const decode = value => Uint8Array.from(atob(value), c => c.charCodeAt(0));
  async function decrypt(key, box) {
    return crypto.subtle.decrypt({name: 'AES-GCM', iv: decode(box.iv)}, key, decode(box.data));
  }
  async function unlock(note, mode, password) {
    if (!note[mode]) throw new Error('Authentication unavailable');
    const wrap = note[mode];
    const material = await crypto.subtle.importKey('raw', new TextEncoder().encode(password), 'PBKDF2', false, ['deriveKey']);
    const key = await crypto.subtle.deriveKey(
      {name: 'PBKDF2', salt: decode(wrap.salt), iterations: note.iterations, hash: 'SHA-256'},
      material, {name: 'AES-GCM', length: 256}, false, ['decrypt']);
    return decrypt(key, wrap);
  }
  window.lockedExpander = {
    async read(password) {
      const note = await bundle();
      const ownerKey = password === undefined ? await window.siteAuth.readNoteKey('quantum-expander') : null;
      if (password === undefined && !ownerKey) return null;
      const raw = ownerKey ? decode(ownerKey) : await unlock(note, 'password', password);
      const key = await crypto.subtle.importKey('raw', raw, 'AES-GCM', false, ['decrypt']);
      return new TextDecoder().decode(await decrypt(key, note.article));
    }
  };
})();
