document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("kb-form");
  const listEl = document.getElementById("kb-admin-list");

  async function loadList() {
    listEl.innerHTML = `<p style="color:var(--text-muted); font-size:13px;">Loading…</p>`;
    try {
      const articles = await apiFetch("/api/knowledge");
      listEl.innerHTML = articles.length ? articles.map(a => `
        <div class="kb-admin-item">
          <div>
            <div class="kb-admin-item-title">${escapeHtml(a.title)}</div>
            <div class="kb-admin-item-cat">${escapeHtml(a.category)}</div>
          </div>
          <button class="kb-delete-btn" data-id="${a.id}">Delete</button>
        </div>
      `).join("") : `<p style="color:var(--text-muted); font-size:13px;">No articles yet.</p>`;

      listEl.querySelectorAll(".kb-delete-btn").forEach(btn => {
        btn.addEventListener("click", async () => {
          if (!confirm("Delete this article?")) return;
          await apiFetch(`/api/admin/knowledge/${btn.dataset.id}`, { method: "DELETE" });
          loadList();
        });
      });
    } catch (err) {
      listEl.innerHTML = `<p style="color:var(--red); font-size:13px;">${escapeHtml(err.message)}</p>`;
    }
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    const payload = {
      title: document.getElementById("kb-title").value.trim(),
      category: document.getElementById("kb-category").value,
      keywords: document.getElementById("kb-keywords").value.trim(),
      content: document.getElementById("kb-content").value.trim(),
      steps: document.getElementById("kb-steps").value.trim(),
    };
    try {
      await apiFetch("/api/admin/knowledge", { method: "POST", body: JSON.stringify(payload) });
      form.reset();
      loadList();
    } catch (err) {
      alert("Failed to add article: " + err.message);
    }
  });

  loadList();
});
