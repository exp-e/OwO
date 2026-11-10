(() => {
  const url = (localStorage.getItem('cfg_sb_url') || 'https://lrfqonbglpudxswvnepd.supabase.co')
    .trim().replace(/\/rest\/v1\/?$/, '').replace(/\/+$/, '');
  const key = (localStorage.getItem('cfg_sb_key') || 'sb_publishable_inNoR20jwxYt68Qm9lKIjQ_M4LlSB_y').trim();
  let client;
  try { client = window.supabase?.createClient(url, key); }
  catch { /* Keep public notes and the article password usable. */ }
  async function isOwner() {
    if (!client) return false;
    const {data: {session}} = await client.auth.getSession();
    if (!session) return false;
    const {data, error} = await client.rpc('is_site_owner');
    return !error && data === true;
  }
  async function signIn(email, password) {
    if (!client) throw new Error('登录服务暂不可用');
    const {error} = await client.auth.signInWithPassword({email, password});
    if (error) throw new Error('登录失败，请检查邮箱和密码');
    if (!(await isOwner())) {
      await client.auth.signOut({scope: 'local'});
      throw new Error('此账号没有博主权限');
    }
  }
  async function readNoteKey(slug) {
    if (!client) return null;
    const {data: {session}} = await client.auth.getSession();
    if (!session) return null;
    const {data, error} = await client.from('locked_note_keys').select('key_b64').eq('slug', slug).maybeSingle();
    if (error) throw error;
    return data?.key_b64 ?? null;
  }
  function promptOwnerLogin(onSuccess) {
    const dialog = document.createElement('dialog');
    dialog.innerHTML = '<form><strong>博主登录</strong><p><label>邮箱 <input type="email" name="email" autocomplete="username" required></label></p><p><label>密码 <input type="password" name="password" autocomplete="current-password" required></label></p><p role="status"></p><button type="submit">登录</button> <button type="button">取消</button></form>';
    const form = dialog.querySelector('form');
    const submit = form.querySelector('[type=submit]');
    dialog.querySelector('[type=button]').onclick = () => dialog.close();
    dialog.addEventListener('close', () => dialog.remove());
    form.onsubmit = async event => {
      event.preventDefault();
      submit.disabled = true;
      try {
        await signIn(form.elements.email.value.trim(), form.elements.password.value);
        dialog.close();
        await onSuccess();
      } catch (error) {
        form.querySelector('[role=status]').textContent = error.message;
      } finally {
        submit.disabled = false;
      }
    };
    document.body.append(dialog);
    dialog.showModal();
  }
  window.siteAuth = {url, key, client, isOwner, promptOwnerLogin, readNoteKey};
})();
