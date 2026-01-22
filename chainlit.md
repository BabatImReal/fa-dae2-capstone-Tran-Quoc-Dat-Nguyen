# Data Analytics AI Agent

Welcome! This Chainlit UI lets you chat with the Data Analytics AI Agent to explore your data warehouse and documents in natural language.

## What you can do
- Ask business questions and get SQL automatically generated and run on Snowflake marts (facts & dims)
- Explore streaming/staging data in PostgreSQL
- Search project docs with hybrid RAG (dense + sparse)
- Upload PDFs and search their contents after inline preview
- Keep HITL on to approve tool executions before they run

## How to use
1) Sign in (app enforces password auth)
2) Ask a question (e.g., "Top 5 customers by spend in 2025")
3) Review/approve tool calls when prompted
4) View results with generated SQL and returned rows
5) Upload PDFs anytime via the 📎 button; preview appears before processing

## Tips
- Use clear date ranges (e.g., "Q4 2025", "last 30 days")
- For customer attributes, mart uses surrogate keys; agent handles joins for you
- If you reject a tool call, adjust the question and retry
- Sessions persist; resume from the sidebar

## Need help?
- Docs: https://docs.chainlit.io
- Community: https://discord.gg/k73SQ3FyUh
