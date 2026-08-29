document.addEventListener("DOMContentLoaded", () => {
  const closeBtn = document.getElementById("close-ticket-btn");
  if (!closeBtn) return;

  closeBtn.addEventListener("click", async () => {
    const ticketId = closeBtn.dataset.ticketId;
    closeBtn.disabled = true;
    closeBtn.textContent = "Closing…";
    try {
      await apiFetch(`/api/tickets/${ticketId}/close`, { method: "POST" });
      window.location.reload();
    } catch (err) {
      alert("Failed to close ticket: " + err.message);
      closeBtn.disabled = false;
      closeBtn.textContent = "Mark ticket as closed";
    }
  });
});
