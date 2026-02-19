# Vaultra

> AI agent that small business owners "hire" to proactively manage creditworthiness and funding readiness.

Vaultra doesn't wait for a user to ask for a loan. It continuously optimizes their financial profile so they're *instantly underwritable* when opportunity arises.

## What is Vaultra?

Vaultra is an AI financial agent that proactively monitors and optimizes your business's financial health for funding readiness. Think of it as a full-time financial operations manager focused on one job: keeping you *instantly underwritable*.

### Key Features

- **Proactive Optimization**: Continuously monitors your financial metrics and suggests improvements before you need funding
- **Unified Funding Readiness Score**: Single 0–100 score that shows how attractive your business is to lenders
- **Actionable Recommendations**: Daily, prioritized recommendations to improve your score (e.g., "Reduce chargebacks", "Stabilize revenue streams")
- **AI Agent**: Natural language Q&A that explains your metrics, recommendations, and funding readiness factors
- **Stripe Integration**: Connects to your Stripe account to analyze revenue, payouts, disputes, and chargebacks

## How It Works

1. **Connect Stripe**: Link your Stripe account (OAuth)
2. **Automatic Analysis**: Vaultra ingests your financial data and computes metrics hourly
3. **Score & Recommendations**: Get your funding readiness score and daily recommendations
4. **Ask Questions**: Chat with the AI agent about your financial health and what to improve

## Tech Stack

- **Frontend**: Astro (static site generation with React islands)
- **Backend**: Python / FastAPI (modular monolith)
- **AI Agent**: MCP (Model Context Protocol) + RAG with Pinecone
- **Database**: PostgreSQL (Cloud SQL)
- **Payments**: Stripe API (Connect Standard)
- **Infrastructure**: Docker, Kubernetes (GKE), Google Cloud

## License

MIT
