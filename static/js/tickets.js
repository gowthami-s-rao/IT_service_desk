document.addEventListener("DOMContentLoaded", () => {
  const container = document.getElementById("tickets-container");
  const tabs = document.querySelectorAll(".filter-tab");
  let currentStatus = "";

  async function load() {
    container.innerHTML = `<div class="empty-state"><p>Loading tickets…</p></div>`;
    try {
      const url = currentStatus ? `/api/tickets?status=${currentStatus}` : "/api/tickets";
      const tickets = await apiFetch(url);
      renderTickets(tickets);
    } catch (err) {
      container.innerHTML = `<div class="empty-state"><p>Failed to load tickets: ${escapeHtml(err.message)}</p></div>`;
    }
  }

  function renderTickets(tickets) {
    if (!tickets.length) {
      container.innerHTML = `<div class="empty-state"><div class="empty-icon">◇</div><p>No tickets match this filter.</p></div>`;
      return;
    }
    container.innerHTML = tickets.map(t => `
      <a href="/tickets/${t.id}" class="ticket-row">
        <div class="ticket-row-main">
          <div class="ticket-subject">${escapeHtml(t.subject)}</div>
          <div class="ticket-meta">#${t.id} · ${escapeHtml(t.category)} ${t.employee_name ? "· " + escapeHtml(t.employee_name) : ""} · ${timeAgo(t.created_at)}</div>
        </div>
        <span class="status-pill status-${t.status}">${t.status.replace("_", " ")}</span>
      </a>
    `).join("");
  }

  tabs.forEach(tab => {
    tab.addEventListener("click", () => {
      tabs.forEach(t => t.classList.remove("active"));
      tab.classList.add("active");
      currentStatus = tab.dataset.status;
      load();
    });
  });

  load();
});
