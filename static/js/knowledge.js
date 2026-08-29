document.addEventListener("DOMContentLoaded", async () => {
  const grid = document.getElementById("kb-grid");
  try {
    const articles = await apiFetch("/api/knowledge");
    if (!articles.length) {
      grid.innerHTML = `<div class="empty-state"><p>No articles yet.</p></div>`;
      return;
    }
    grid.innerHTML = articles.map(a => `
      <div class="kb-card">
        <span class="kb-card-cat">${escapeHtml(a.category)}</span>
        <h3>${escapeHtml(a.title)}</h3>
        <p>${escapeHtml(a.content)}</p>
        ${a.steps && a.steps.length ? `<ul class="kb-steps">${a.steps.map(s => `<li>${escapeHtml(s)}</li>`).join("")}</ul>` : ""}
      </div>
    `).join("");
  } catch (err) {
    grid.innerHTML = `<div class="empty-state"><p>Failed to load: ${escapeHtml(err.message)}</p></div>`;
  }
});
