// Pass rendered HTML and the private SQL output path outside the website.
import {readFileSync, writeFileSync} from 'node:fs';
import {createCipheriv, pbkdf2Sync, randomBytes} from 'node:crypto';
import {relative, resolve, isAbsolute, sep} from 'node:path';
import {fileURLToPath} from 'node:url';

const [source, privateSql] = process.argv.slice(2);
if (!source || !privateSql) throw new Error('Usage: node tools/lock-expander.mjs <private-html> <private-sql>');
const root = fileURLToPath(new URL('../', import.meta.url));
for (const path of [source, privateSql]) {
  const location = relative(root, resolve(path));
  if (!isAbsolute(location) && !location.startsWith('..' + sep)) {
    throw new Error('Use paths outside the public website.');
  }
}
const html = readFileSync(source, 'utf8');
if (!html.includes('class="article-content"')) throw new Error('Expected a rendered note.');
const password = randomBytes(9).toString('base64url');
const key = randomBytes(32);
const iterations = 600000;
function seal(data, secret) {
  const iv = randomBytes(12);
  const cipher = createCipheriv('aes-256-gcm', secret, iv);
  const data64 = Buffer.concat([cipher.update(data), cipher.final(), cipher.getAuthTag()]).toString('base64');
  return {iv: iv.toString('base64'), data: data64};
}
function wrap(passphrase) {
  const salt = randomBytes(16);
  return {salt: salt.toString('base64'), ...seal(key, pbkdf2Sync(passphrase, salt, iterations, 32, 'sha256'))};
}
const bundle = {iterations, article: seal(html, key), password: wrap(password)};
const schema = readFileSync(new URL('../supabase/site-owner.sql', import.meta.url), 'utf8');
const sql = schema.replace(/commit;\s*$/, `insert into site_private.owners (user_id)
values ('REPLACE_WITH_OWNER_USER_UUID') on conflict do nothing;
insert into public.locked_note_keys (slug, key_b64)
values ('quantum-expander', '${key.toString('base64')}')
on conflict (slug) do update set key_b64 = excluded.key_b64;
commit;\n`);
writeFileSync(privateSql, sql, {flag: 'wx', mode: 0o600});
writeFileSync(new URL('../assets/locked-expander.json', import.meta.url), JSON.stringify(bundle) + '\n');
console.log(password);
