// Cloudflare Pages Function: saves launch-list signups to the SIGNUPS KV namespace.
export async function onRequestPost({ request, env }) {
  const form = await request.formData();

  // Honeypot: real visitors never fill this hidden field.
  if (form.get("company")) {
    return Response.redirect(new URL("/thanks.html", request.url), 303);
  }

  const email = String(form.get("email") || "").trim().toLowerCase();
  const valid = /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email) && email.length <= 254;
  if (!valid) {
    return new Response("Please go back and enter a valid email address.", {
      status: 400,
      headers: { "content-type": "text/plain; charset=utf-8" },
    });
  }

  await env.SIGNUPS.put(
    `email:${email}`,
    JSON.stringify({ email, signedUpAt: new Date().toISOString(), city: "New York City" })
  );

  return Response.redirect(new URL("/thanks.html", request.url), 303);
}
