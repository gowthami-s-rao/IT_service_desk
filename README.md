# RelayDesk — Multi-Agent IT Service Desk

A production-structured Flask application implementing an AI-powered IT
Service Management system. A **Manager Agent** classifies every incoming
employee request and delegates it to four specialist agents — exactly as
specified:

```
Employee → Manager Agent → Troubleshooting Agent → Knowledge Agent → Database Agent
                                                                         │
                                                                 Problem solved?
                                                                 ┌───────┴───────┐
                                                                YES             NO
                                                                 │               │
                                                          Response Agent   Human Escalation
                                                                 └───────┬───────┘
                                                                    Close Ticket
```

Built with: **Flask · SQLite (SQLAlchemy) · Flask-Login (auth) · LangChain ·
LangGraph (agent orchestration) · Ollama (local LLM) · HTML/CSS/JS**.

---

## 1. Project structure

```
it_service_desk/
├── app/
│   ├── __init__.py            # App factory
│   ├── config.py               # Config (env-driven)
│   ├── extensions.py           # db, login_manager, csrf singletons
│   ├── models.py               # User, Device, KnowledgeArticle, Ticket, TicketMessage
│   ├── seed_data.py             # Demo accounts, devices, KB articles
│   ├── auth/
│   │   ├── forms.py             # Login/Register WTForms
│   │   └── routes.py            # /login /register /logout
│   ├── agents/                  # ← the 5 agents from the spec
│   │   ├── llm_config.py        # Ollama connection + mock fallback
│   │   ├── manager_agent.py     # classify & delegate
│   │   ├── troubleshooting_agent.py
│   │   ├── knowledge_agent.py   # searches KnowledgeArticle table
│   │   ├── database_agent.py    # checks employee/device/ticket records
│   │   ├── response_agent.py    # composes final answer, decides solved?
│   │   └── orchestrator.py      # LangGraph StateGraph wiring it all together
│   ├── main/routes.py           # page routes (dashboard, tickets, KB, admin)
│   ├── api/routes.py            # JSON API (tickets, knowledge, admin stats)
│   ├── templates/               # Jinja2 templates
│   └── static/{css,js}/         # design system + page scripts
├── requirements.txt
├── run.py                       # entrypoint (flask dev server / gunicorn target)
├── Dockerfile
├── docker-compose.yml           # app + Ollama, one command deploy
├── .env.example
└── .gitignore
```

---

## 2. What you need to do (setup checklist)

### A. Install Ollama and pull a model (for real AI responses)

The agents call a local LLM through [Ollama](https://ollama.com). Without it,
the app still runs and produces sensible rule-based responses (mock mode),
but for actual AI-generated classification/troubleshooting/responses:

```bash
# Install Ollama (see https://ollama.com/download for your OS)
curl -fsSL https://ollama.com/install.sh | sh

# Pull a model (llama3.1 is the default — pick any model you like)
ollama pull llama3.1

# Ollama runs its API on http://localhost:11434 automatically
```

If you'd rather use a different model, set `OLLAMA_MODEL` in `.env` to match.

### B. Set up the Python environment

```bash
cd it_service_desk
python3 -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

### C. Configure environment variables

```bash
cp .env.example .env
# then edit .env:
#   - SECRET_KEY: generate one with `python -c "import secrets; print(secrets.token_hex(32))"`
#   - OLLAMA_MODEL: the model you pulled above
#   - AGENT_MOCK_MODE: set to "true" if you want to demo without Ollama installed
```

### D. Run it

```bash
python run.py
```

Visit **http://localhost:5000**. The database and demo data are created
automatically on first run (SQLite file at `instance/servicedesk.db`).

**Demo accounts** (seeded automatically):
| Role     | Username | Password       |
|----------|----------|----------------|
| Employee | jsmith   | Employee@123   |
| Admin    | admin    | Admin@12345    |

Change/remove these before any real deployment.

---

## 3. How the multi-agent pipeline works

Every ticket submission (`POST /api/tickets`) runs synchronously through
`app/agents/orchestrator.py`, a compiled **LangGraph** `StateGraph`:

1. **Manager Agent** — LLM call classifies the request into
   `network / hardware / software / account / other` with a priority.
2. **Troubleshooting Agent** — LLM call generates 3-6 concrete diagnostic steps.
3. **Knowledge Agent** — queries the `knowledge_articles` SQLite table,
   scoring articles by keyword/category match (no LLM call needed here —
   it's a database search, per the spec).
4. **Database Agent** — queries `devices` and `tickets` tables for the
   employee: flagged/offline devices, duplicate open tickets, ticket history.
5. **Decision node** — "Problem solved?" — currently a transparent heuristic
   (no flagged devices + no unresolved duplicate + some KB/step coverage ⇒
   solved). This is the one place you'd wire in real diagnostic polling or
   a follow-up question to the employee in a fuller production build.
6. **Response Agent** (YES branch) — LLM call composes the final message.
   **Human Escalation** (NO branch) — creates the escalation message and
   flags the ticket `status = escalated`.
7. Every step is logged as a `TicketMessage` row, so the full trace is
   visible on the ticket detail page — this is what the UI's animated
   pipeline panel is replaying.

All five agent modules are independent, pure Python functions — swapping the
orchestration layer for CrewAI or AutoGen later only requires rewriting
`orchestrator.py`; the agents themselves don't change.

If Ollama is unreachable, `llm_config.call_llm()` catches the exception and
falls back to a rule-based mock so the demo never hard-fails.

---

## 4. Authentication

- Session-based auth via **Flask-Login**, passwords hashed with Werkzeug's
  `generate_password_hash` (PBKDF2).
- CSRF protection (Flask-WTF) on all HTML forms; the JSON `/api/*` routes are
  same-origin `fetch()` calls authenticated by the (HttpOnly, SameSite=Lax)
  session cookie, so they're exempted from the form-token CSRF check.
- Two roles: `employee` (submit/view own tickets) and `admin` (view all
  tickets, stats, manage the knowledge base). Promote a user to admin by
  editing their `role` column directly, or extend the admin UI to do it.

---

## 5. Deployment

### Option A — Docker Compose (recommended, includes Ollama)

```bash
cp .env.example .env   # edit SECRET_KEY at minimum
docker compose up -d --build

# then pull a model into the Ollama container:
docker exec -it relaydesk-ollama ollama pull llama3.1
```

The app is on `http://localhost:5000`, backed by gunicorn (3 workers) and
talking to the `ollama` service over the compose network.

### Option B — Bare metal / VM with gunicorn + nginx

```bash
pip install -r requirements.txt
gunicorn --workers 3 --bind 0.0.0.0:5000 --timeout 120 run:app
```

Put nginx in front as a reverse proxy (TLS termination + static file
caching):

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /path/to/it_service_desk/app/static/;
        expires 7d;
    }

    location / {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

Then obtain a cert with `certbot --nginx`, and run Ollama on the same host
(or point `OLLAMA_BASE_URL` at a dedicated GPU host).

### Production checklist

- [ ] Set a strong random `SECRET_KEY`
- [ ] Switch `DATABASE_URL` to PostgreSQL for multi-worker write concurrency
      if ticket volume grows (SQLite is fine for small/medium teams; it's a
      single-writer database)
- [ ] Put the app behind HTTPS (nginx/caddy + certbot, or your cloud LB)
- [ ] Remove/rotate the seeded demo accounts
- [ ] Set `AGENT_MOCK_MODE=false` and confirm `ollama pull <model>` has run
- [ ] Back up `instance/servicedesk.db` (or your Postgres instance) regularly
- [ ] Put gunicorn behind a process supervisor (systemd, Docker restart
      policy — already set to `unless-stopped` in the compose file)

---

## 6. Extending it

- **More agents**: add a new file under `app/agents/`, add a node + edge in
  `orchestrator.py`'s `build_graph()`.
- **Real human escalation**: wire `escalation_node` in `orchestrator.py` to
  email/Slack/webhook a human technician instead of just logging.
- **Streaming pipeline UI**: currently the API call is synchronous and the
  frontend animates the pipeline visually in parallel; for very slow LLMs,
  switch `POST /api/tickets` to return immediately and stream progress over
  Server-Sent Events, updating the same `pipeline-step` elements as real
  events arrive instead of a timed animation.
- **CrewAI/AutoGen**: the agent functions in `app/agents/*.py` are framework
  agnostic — you can wrap each one as a CrewAI `Agent`/`Task` or an AutoGen
  `ConversableAgent` and swap `orchestrator.py`'s LangGraph graph for a Crew
  or GroupChat without touching the Flask routes or the database layer.
