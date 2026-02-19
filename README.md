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

## Getting Started

This project follows **spec-driven development**. All specifications are in `docs/`:

- **[SPECIFICATION_INDEX.md](./docs/SPECIFICATION_INDEX.md)** — Complete guide to all specifications
- **[SCAFFOLDING_GUIDE.md](./docs/SCAFFOLDING_GUIDE.md)** — Step-by-step scaffolding instructions
- **[SPEC.md](./docs/SPEC.md)** — Product scope and MVP

For implementation details, see the [specifications](./docs/) directory.

## Documentation

All specifications are in `docs/`:

- **[BACKGROUND_AND_VISION.md](./docs/BACKGROUND_AND_VISION.md)** — Business problems and vision
- **[SPEC.md](./docs/SPEC.md)** — Product scope, flows, NFRs
- **[ARCHITECTURE.md](./docs/ARCHITECTURE.md)** — Services, APIs, deployment
- **[API_SCHEMAS.md](./docs/API_SCHEMAS.md)** — API request/response schemas
- **[BACKEND_SERVICES_SPEC.md](./docs/BACKEND_SERVICES_SPEC.md)** — Service interfaces and business logic
- **[DATA_MODEL.md](./docs/DATA_MODEL.md)** — Database schemas
- **[TECH_STACK.md](./docs/TECH_STACK.md)** — Technology choices

## Development

This project follows **spec-driven development**:

1. **Specs first**: All features are specified in `docs/` before implementation
2. **Implementation**: Code follows the specifications
3. **Validation**: Implementation is validated against spec checklists

See [SCAFFOLDING_GUIDE.md](./docs/SCAFFOLDING_GUIDE.md) for implementation instructions.

## License

MIT
