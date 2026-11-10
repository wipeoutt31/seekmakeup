// Cloudflare Pages Function: private CSV download of launch-list signups.
// Open /api/signups?key=YOUR_ADMIN_KEY. The key is stored as the ADMIN_KEY secret in Cloudflare.
export async function onRequestGet({ request, env }) {
  const key = new URL(request.url).searchParams.get("key") || "";
  if (!env.ADMIN_KEY || key.length !== env.ADMIN_KEY.length || key !== env.ADMIN_KEY) {
    return new Response("Not found", { status: 404 });
  }

  const rows = [];
  let cursor;
  do {
    const page = await env.SIGNUPS.list({ prefix: "email:", cursor });
    for (const k of page.keys) {
      const raw = await env.SIGNUPS.get(k.name);
      try {
        const r = JSON.parse(raw);
        rows.push([r.email, r.signedUpAt || "", r.city || ""]);
      } catch {
        rows.push([k.name.slice(6), "", ""]);
      }
    }
    cursor = page.list_complete ? undefined : page.cursor;
  } while (cursor);

  rows.sort((a, b) => (a[1] < b[1] ? -1 : 1));
  const esc = (v) => `"${String(v).replace(/"/g, '""')}"`;
  const csv = ["email,signed_up_at,city", ...rows.map((r) => r.map(esc).join(","))].join("\n");

  return new Response(csv, {
    headers: {
      "content-type": "text/csv; charset=utf-8",
      "content-disposition": `attachment; filename="seekmakeup-signups.csv"`,
      "cache-control": "no-store",
      "x-robots-tag": "noindex",
    },
  });
}
