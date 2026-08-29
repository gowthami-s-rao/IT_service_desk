document.addEventListener("DOMContentLoaded", async () => {
  try {
    const stats = await apiFetch("/api/admin/stats");
    document.getElementById("stat-total").textContent = stats.total_tickets;
    document.getElementById("stat-resolved").textContent = stats.resolved;
    document.getElementById("stat-escalated").textContent = stats.escalated;
    document.getElementById("stat-open").textContent = stats.open + stats.in_progress;
    document.getElementById("stat-users").textContent = stats.users_count;

    const catContainer = document.getElementById("category-bars");
    const entries = Object.entries(stats.by_category);
    const max = Math.max(1, ...entries.map(([, v]) => v));
    catContainer.innerHTML = entries.length
      ? entries.map(([cat, count]) => `
          <div class="cat-bar-row">
            <span>${cat.charAt(0).toUpperCase() + cat.slice(1)}</span>
            <div class="cat-bar-track"><div class="cat-bar-fill" style="width:${(count / max) * 100}%"></div></div>
            <span>${count}</span>
          </div>
        `).join("")
      : `<div class="empty-state"><p>No tickets yet.</p></div>`;
  } catch (err) {
    console.error(err);
  }

  try {
    const tickets = await apiFetch("/api/tickets");
    const latest = tickets.slice(0, 8);
    const container = document.getElementById("latest-tickets");
    container.innerHTML = latest.length
      ? latest.map(t => `
          <a href="/tickets/${t.id}" class="ticket-row">
            <div class="ticket-row-main">
              <div class="ticket-subject">${escapeHtml(t.subject)}</div>
              <div class="ticket-meta">#${t.id} · ${escapeHtml(t.category)} · ${escapeHtml(t.employee_name || "")} · ${timeAgo(t.created_at)}</div>
            </div>
            <span class="status-pill status-${t.status}">${t.status.replace("_", " ")}</span>
          </a>
        `).join("")
      : `<div class="empty-state"><p>No tickets yet.</p></div>`;
  } catch (err) {
    console.error(err);
  }
});
