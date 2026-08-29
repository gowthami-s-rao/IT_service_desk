document.addEventListener("DOMContentLoaded", () => {
  const form = document.getElementById("ticket-form");
  const submitBtn = document.getElementById("submit-btn");
  const statusEl = document.getElementById("pipeline-status");
  const resultEl = document.getElementById("pipeline-result");
  const steps = Array.from(document.querySelectorAll(".pipeline-step"));

  // Maps orchestrator log agent names -> visual step order
  const AGENT_ORDER = ["manager_agent", "troubleshooting_agent", "knowledge_agent", "database_agent", "response_agent"];

  function resetPipeline() {
    steps.forEach(s => s.classList.remove("active", "done"));
    resultEl.classList.add("hidden");
    resultEl.innerHTML = "";
    statusEl.textContent = "Waiting for request…";
    statusEl.classList.remove("active", "done");
  }

  function animateStepsSequentially(pipelineLog, onDone) {
    let i = 0;
    statusEl.textContent = "Processing…";
    statusEl.classList.add("active");

    function next() {
      // mark previous done
      if (i > 0) {
        const prevIdx = Math.min(i - 1, steps.length - 1);
        steps[prevIdx].classList.remove("active");
        steps[prevIdx].classList.add("done");
      }
      if (i >= steps.length) {
        statusEl.textContent = "Complete";
        statusEl.classList.remove("active");
        statusEl.classList.add("done");
        onDone();
        return;
      }
      steps[i].classList.add("active");
      i += 1;
      setTimeout(next, 650);
    }
    next();
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    resetPipeline();

    const subject = document.getElementById("subject").value.trim();
    const description = document.getElementById("description").value.trim();
    if (!subject || !description) return;

    submitBtn.disabled = true;
    submitBtn.textContent = "Submitting…";

    try {
      const dataPromise = apiFetch("/api/tickets", {
        method: "POST",
        body: JSON.stringify({ subject, description }),
      });

      animateStepsSequentially([], () => {}); // start visual animation immediately

      const data = await dataPromise;
      const ticket = data.ticket;

      // ensure animation has time to finish visually even if API was fast
      setTimeout(() => {
        resultEl.classList.remove("hidden");
        const escalated = ticket.status === "escalated";
        resultEl.innerHTML = `
          <div class="pipeline-result-title" style="color:${escalated ? 'var(--red)' : 'var(--green)'}">
            ${escalated ? "Escalated to a human technician" : "Resolved by the agent pipeline"}
          </div>
          <div class="pipeline-result-text">${escapeHtml(ticket.resolution || "")}</div>
          <a href="/tickets/${ticket.id}" class="btn-secondary" style="display:inline-block; text-decoration:none;">View full trace →</a>
        `;
        submitBtn.disabled = false;
        submitBtn.textContent = "Submit to agent pipeline →";
        form.reset();
      }, steps.length * 650 + 200);
    } catch (err) {
      statusEl.textContent = "Error";
      resultEl.classList.remove("hidden");
      resultEl.innerHTML = `<div class="pipeline-result-text" style="color:var(--red)">${escapeHtml(err.message)}</div>`;
      submitBtn.disabled = false;
      submitBtn.textContent = "Submit to agent pipeline →";
    }
  });
});
