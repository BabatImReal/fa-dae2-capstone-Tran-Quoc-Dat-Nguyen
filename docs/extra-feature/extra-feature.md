**Extra Feature: Hybrid Search + Chainlit UI + Metabase Analytics**

- **Overview:** Concise reference for the hybrid search implementation (semantic + lexical RRF), recommended Chainlit UI elements for the AI agent, and Metabase analytics guidance for mart-layer business metrics.

**Hybrid Search (RRF Hybrid)**:
- **Description:** Combines dense (semantic) and sparse (lexical) search, then re-ranks documents using Reciprocal Rank Fusion (RRF). Implementation located in `ai-agent/tools/rag_combined_tools.py` as `hybrid_search_documents`.
- **Key behavior:**
  - Runs dense semantic search (embedding + vector query) and sparse lexical search (sparse embedding + sparse query).
  - Collects top `k` (default `rrf_k=60`) from each and builds rank maps.
  - Keeps only documents returned by BOTH searches (high confidence) and computes RRF score: `1/(k + dense_rank) + 1/(k + sparse_rank)`.
  - Returns top `top_k` results with `rrf_score`, ranks, scores, excerpt, source, and chunk id.
- **Inputs:**
  - `query` (string) — user query
  - `top_k` (int, default 3) — results to return
  - `rrf_k` (int, default 60) — RRF constant used in formula
- **Outputs (summary):** `results` array of objects with `rank`, `rrf_score`, `dense_rank`, `sparse_rank`, `dense_score`, `sparse_score`, `content`, `source`, `chunk_id`.
- **Environment / Prereqs:**
  - Pinecone API keys and index names set in env: `PINECONE_API_KEY`, `PINECONE_DENSE_INDEX_NAME`, `PINECONE_SPARSE_INDEX_NAME`.
  - Embedding models used in code: `llama-text-embed-v2` (dense) and `pinecone-sparse-english-v0` (sparse) — adjust to your stack if different.
- **Usage tips:**
  - Tune `rrf_k` based on corpus size (larger corpora → larger `k`).
  - Consider returning some docs that appear in only one search when coverage is low (optional flag) to increase recall.
  - Show both `dense_score` and `sparse_score` to users for transparency.

**Chainlit UI Integration**:
- **Goal:** Present hybrid search results in a chat-style UI; allow follow-ups, source-citation, and expanded context preview.
- **Recommended components / elements:**
  - **Chat messages:** default conversation UI for user query and assistant answers.
  - **Result cards:** For each hybrid result, show short excerpt, `rrf_score`, `source`, and two actions: `Show more` and `Cite`. Use collapsible panels for full chunk text.
  - **Buttons:** `Open source` (link to original doc), `More context` (fetch adjacent chunks), `Ask about this chunk` (send chunk back as context for LLM).
  - **Metadata display:** Small tag area for `dense_score`, `sparse_score`, `chunk_id`, and `source`.
  - **Inline tool calling:** Wire a Chainlit tool call to `hybrid_search_documents(query, top_k, rrf_k)` and render results as cards.
  - **Feedback controls:** `Helpful` / `Not helpful` to collect training signals; optionally store feedback to DB.
  - **Cite & Trace:** When composing answers, include short citations in the reply (e.g., `(source: SalesMart—chunk-123)`) and an optional expanded sources panel.
- **Suggested UX flow:**
  1. User asks question in chat.
  2. Agent calls hybrid search tool.
  3. Render top results as cards with `Show more` and `Cite` actions.
  4. If user asks follow-up, pass chosen chunk(s) as context for the LLM; allow multi-turn refinement.
- **Implementation notes:**
  - Keep tool calls async to avoid blocking UI; show loading placeholders.
  - Rate-limit or cache embeddings/queries for repeated or similar queries.
  - Respect privacy and access controls when linking to sources.

**Metabase — Data Analytics for Mart Layers**:
- **Objective:** Use Metabase to analyze business metrics derived from mart-layer tables (marts), and surface insights inside dashboards and links the AI agent can reference.
- **Recommended dashboards / KPIs:**
  - **Sales Overview:** total revenue, average order value, orders by mart (daily/weekly/monthly), top products.
  - **Customer Health / Retention:** cohort retention, churn rate, LTV estimates.
  - **Operational Metrics:** ETL freshness, data latency, failed loads per mart.
  - **Business Value Reports:** revenue by region/segment, margin by product line, campaign ROI.
- **Technical integration:**
  - Ensure marts are materialized and accessible to Metabase with a read-only DB user.
  - Build SQL questions in Metabase referencing mart tables (staging → intermediate → marts pattern).
  - Use Metabase Cards and Dashboards; set up scheduled email reports or public links (if safe).
- **Embedding in AI agent UI:**
  - Provide dashboard links in the agent UI and allow the user to open dashboards in a new tab.
  - Optionally, expose summarized KPIs in the chat (agent queries the DB or an API to fetch small numeric summaries and returns them inline).
- **Security / Governance:**
  - Limit Metabase dashboard visibility to appropriate roles.
  - Avoid exposing PII in public links or automated agent responses.

**Files & Code references**
- **Hybrid search implementation:** `ai-agent/tools/rag_combined_tools.py` (function `hybrid_search_documents`).
- **Chainlit UI files:** (where you implement UI) `ai-agent/chainlit/` — create renderers and tool hooks that call the hybrid search tool.
- **Metabase guidance:** store queries in your `capstone_project` or document SQL queries in `docs/` for reproducibility.

**Next steps**
- Wire `hybrid_search_documents` to a Chainlit tool wrapper and implement result card rendering.
- Create a small Metabase dashboard for primary KPIs; add dashboard links to the agent UI.

---

If you want, I can now:
- Implement a Chainlit tool wrapper and sample UI components that call `hybrid_search_documents` and render cards, or
- Create sample Metabase SQL queries for specific mart tables (tell me which mart tables/metrics you care about).
