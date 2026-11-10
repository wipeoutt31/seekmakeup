// Cloudflare Pages Function: private CSV download of contact-form messages.
// Open /api/messages?key=YOUR_ADMIN_KEY (same key as /api/signups).
export async function onRequestGet({ request, env }) {
  const key = new URL(request.url).searchParams.get("key") || "";
  if (!env.ADMIN_KEY || key.length !== env.ADMIN_KEY.length || key !== env.ADMIN_KEY) {
    return new Response("Not found", { status: 404 });
  }

  const rows = [];
  let cursor;
  do {
    const page = await env.SIGNUPS.list({ prefix: "msg:", cursor });
    for (const k of page.keys) {
      try {
        const r = JSON.parse(await env.SIGNUPS.get(k.name));
        rows.push([r.sentAt, r.reason, r.name, r.email, r.message]);
      } catch {}
    }
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);

  rows.sort((a, b) => (a[0] < b[0] ? 1 : -1)); // newest first
  const esc = (v) => `"${String(v ?? "").replace(/"/g, '""')}"`;
  const csv = ["sent_at,reason,name,email,message", ...rows.map((r) => r.map(esc).join(","))].join("\n");

  return new Response(csv, {
    headers: {
      "content-type": "text/csv; charset=utf-8",
      "content-disposition": `attachment; filename="seekmakeup-messages.csv"`,
      "cache-control": "no-store",
      "x-robots-tag": "noindex",
    },
  });
}
