// Deploy with TOKEN_SHA256 replaced by the SHA256 of the server-only random token.
// The token itself and Supabase service credentials never appear in this source.
const TOKEN_SHA256 = '__APA_TOKEN_SHA256__';
const BUCKET = 'apa-private-pdfs';
const LIMIT = 30 * 1024 * 1024;
const encoder = new TextEncoder();

function reply(status: number, message: string) {
  return new Response(JSON.stringify({message}), {status, headers: {
    'Content-Type':'application/json', 'Cache-Control':'no-store', 'X-Content-Type-Options':'nosniff'}});
}

Deno.serve(async (req: Request) => {
  const token = req.headers.get('Authorization')?.replace(/^Bearer /, '') || '';
  const digest = new Uint8Array(await crypto.subtle.digest('SHA-256', encoder.encode(token)));
  const hex = Array.from(digest, b => b.toString(16).padStart(2,'0')).join('');
  let mismatch = hex.length ^ TOKEN_SHA256.length;
  for (let i=0; i<hex.length; i++) mismatch |= hex.charCodeAt(i) ^ (TOKEN_SHA256.charCodeAt(i) || 0);
  if (mismatch || token.length < 40) return reply(401, 'Unauthorized');
  const root = Deno.env.get('SUPABASE_URL');
  const key = Deno.env.get('SUPABASE_SERVICE_ROLE_KEY');
  if (!root || !key) return reply(503, 'Storage unavailable');
  const headers = {'Authorization':`Bearer ${key}`, 'apikey':key};
  const url = new URL(req.url);
  try {
    if (req.method === 'POST' && url.searchParams.get('operation') === 'initialize') {
      const config = {id:BUCKET, name:BUCKET, public:false, file_size_limit:LIMIT, allowed_mime_types:['application/pdf']};
      const created = await fetch(`${root}/storage/v1/bucket`, {method:'POST',
        headers:{...headers,'Content-Type':'application/json'}, body:JSON.stringify(config)});
      if (!created.ok) {
        const existing = await fetch(`${root}/storage/v1/bucket/${BUCKET}`, {method:'PUT',
          headers:{...headers,'Content-Type':'application/json'}, body:JSON.stringify(config)});
        if (!existing.ok) return reply(503, 'Bucket configuration failed');
      }
      return reply(200, 'Private bucket ready');
    }
    const name = url.searchParams.get('name') || '';
    if (!/^[A-Za-z0-9_./-]+\.pdf$/.test(name) || name.split('/').some(p=>!p || p==='.' || p==='..')) {
      return reply(400, 'Invalid PDF name');
    }
    const path = name.split('/').map(encodeURIComponent).join('/');
    const object = `${root}/storage/v1/object/${BUCKET}/${path}`;
    if (req.method === 'PUT') {
      if (Number(req.headers.get('Content-Length')) > LIMIT) return reply(413, 'File too large');
      const reader = req.body?.getReader();
      if (!reader) return reply(400, 'Missing PDF');
      const chunks: Uint8Array[] = [];
      let size = 0;
      for (;;) {
        const {done, value} = await reader.read();
        if (done) break;
        size += value.length;
        if (size > LIMIT) { await reader.cancel(); return reply(413,'File too large'); }
        chunks.push(value);
      }
      const body = new Uint8Array(size);
      let offset=0;
      for (const chunk of chunks) { body.set(chunk,offset); offset+=chunk.length; }
      if (new TextDecoder().decode(body.subarray(0,5)) !== '%PDF-') return reply(400, 'Invalid PDF');
      const saved = await fetch(object, {method:'POST', headers:{...headers,'Content-Type':'application/pdf','x-upsert':'false'}, body});
      return saved.ok ? reply(200,'Saved') : reply(503,'Storage write failed');
    }
    if (req.method === 'GET' || req.method === 'HEAD') {
      const target = req.method === 'HEAD'
        ? `${root}/storage/v1/object/info/authenticated/${BUCKET}/${path}`
        : `${root}/storage/v1/object/authenticated/${BUCKET}/${path}`;
      const file = await fetch(target, {headers});
      if (!file.ok) {
        const error = await file.json().catch(()=>({}));
        return reply(file.status===404 || String(error.statusCode)==='404' || error.error==='not_found' ? 404:503,'Object unavailable');
      }
      if (req.method==='HEAD') { await file.body?.cancel(); return new Response(null,{status:200}); }
      return new Response(file.body,{status:200,headers:{'Content-Type':'application/pdf','Cache-Control':'no-store'}});
    }
    if (req.method === 'DELETE') {
      const deleted = await fetch(`${root}/storage/v1/object/${BUCKET}`, {method:'DELETE',
        headers:{...headers,'Content-Type':'application/json'}, body:JSON.stringify({prefixes:[name]})});
      return deleted.ok ? reply(200,'Deleted') : reply(503,'Storage delete failed');
    }
    return reply(405,'Method not allowed');
  } catch {
    return reply(503,'Storage unavailable');
  }
});
