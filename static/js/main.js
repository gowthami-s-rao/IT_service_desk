// Shared helpers used across pages.
// Note: /api/* endpoints are authenticated via the Flask-Login session cookie
// (SameSite=Lax) rather than a CSRF token, since every call here is a
// same-origin fetch() from our own JS.

async function apiFetch(url, options = {}) {
  const opts = Object.assign({ headers: {} }, options);
  opts.headers["Content-Type"] = "application/json";
  const res = await fetch(url, opts);
  if (!res.ok) {
    let msg = "Request failed";
    try {
      const data = await res.json();
      msg = data.error || msg;
    } catch (e) { /* noop */ }
    throw new Error(msg);
  }
  return res.json();
}

function timeAgo(isoString) {
  if (!isoString) return "";
  const diffMs = Date.now() - new Date(isoString + "Z").getTime();
  const mins = Math.floor(diffMs / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  return `${days}d ago`;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str == null ? "" : str;
  return div.innerHTML;
}
