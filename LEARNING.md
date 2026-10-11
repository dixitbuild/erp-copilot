# Learning notes

Notes on building ERP Copilot: what is left to do, in priority order.

## What's left (AI engineer roadmap)

### Next (small, already agreed)
- [ ] **Fix the retry wording in the ERP prompt.** It currently says "give up on failure", which stops the model from retrying a failed query.
- [ ] **Add column hints to SQL errors**, so the model can fix a bad query on the first retry.

### Core build (the "multi-agent" part)
- [ ] **API-fetch MCP server.** Wrap the `GET /sales-orders` etc. endpoints as tools. The endpoints exist but nothing uses them yet.
- [ ] **Orchestrator with specialist agents.** Today there is one guard and one ERP agent. Add a router that sends each question to a sales, purchase or work-order specialist, or to several in parallel.
- [ ] **Conversation memory.** `/chat` is stateless, so follow-ups like "and the shipped ones?" have no context. Send session history with each request.

### Quality and trust
- [ ] **Automated tests.** There are none in the repo yet. Use pytest with mocked Groq and Pinecone.
- [ ] **Evals.** A fixed list of questions with expected outcomes: does the guard block injections, does the model pick the right tool, is the SQL correct, is the answer grounded? This shows whether a prompt change helps or hurts.
- [ ] **Show sources in the UI.** Display the SQL that ran and the document passages used.
- [ ] **Retrieval improvements.** Reranking, deleting stale chunks, PDF and long-text chunking.

### Production concerns
- [ ] **Observability.** Log each tool call, latency, token use and cost. One chat can cost three Groq calls.
- [ ] **Security.** API authentication, rate limits, CORS, per-role table access, and treating tool results as untrusted. The LLM guard reduces injection risk but does not remove it.
- [ ] **Streaming replies**, so users see the answer as it is written.
- [ ] **Real data.** Replace the dummy SQLite data with the actual ERP database or API, with migrations.
- [ ] **Deployment.** Docker, CI, environment configuration.

### Later
- [ ] **Write actions** (create or cancel an order) with human approval before anything is changed.
- [ ] **Cost and speed tuning**, such as a smaller model for the guard and caching repeated questions.

### Suggested order
1. The two small fixes.
2. Tests and evals, so you can see what each change breaks once there are several agents.
3. API-fetch MCP server, conversation memory, then the orchestrator.
