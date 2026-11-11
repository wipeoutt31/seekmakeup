// Cloudflare Pages Function: saves contact-form messages to the SIGNUPS KV namespace under "msg:".
const REASONS = ["Remove my email", "I own a store", "Report a change to a listing", "Question", "Report a problem", "Featured listing", "Other"];

export async function onRequestPost({ request, env }) {
  const form = await request.formData();

  // Honeypot: real visitors never fill this hidden field.
  if (form.get("company")) {
    return Response.redirect(new URL("/message-sent.html", request.url), 303);
  }

  const clean = (v, max) => String(v || "").trim().slice(0, max);
  const reason = REASONS.includes(form.get("reason")) ? form.get("reason") : "Other";
  const name = clean(form.get("name"), 100);
  const email = clean(form.get("email"), 254).toLowerCase();
  const message = clean(form.get("message"), 4000);

  if (!/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) || (!message && reason !== "Remove my email")) {
    return new Response("Please go back and enter a valid email address and a message.", {
      status: 400,
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  }

  const sentAt = new Date().toISOString();
  await env.SIGNUPS.put(
    `msg:${sentAt}:${crypto.randomUUID().slice(0, 8)}`,
    JSON.stringify({ sentAt, reason, name, email, message })
  );

  return Response.redirect(new URL("/message-sent.html", request.url), 303);
}
