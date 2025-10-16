{
    "resume_md": "# LUIS SOLORZANO
Richmond, CA · [luis.e.solor@gmail.com](mailto:luis.e.solor@gmail.com) · github.com/lsolor · linkedin.com/in/lsolor

## Summary
Backend engineer (7+ years) shipping Python/FastAPI services and data pipelines on AWS. Strong with PostgreSQL, microservices, and production operations (Docker, Kubernetes/EKS, Terraform, CI/CD, observability). Bay Area–based; available on‑site.

## Core Skills
**Backend:** Python (FastAPI, asyncio), REST APIs, SQLAlchemy, Bash  
**Datastores & Messaging:** PostgreSQL, Alembic, Redis (cache + Lua), Amazon SQS  
**Cloud & Ops:** AWS (EKS, CloudWatch), Docker, Kubernetes, Terraform, Azure DevOps, Pytest, feature flags, SLOs/runbooks

## Experience
**Avanade — Senior Software Engineer** · Richmond, CA · Jan 2020–Present  
*Security scanning & reporting platform (AWS, EKS, Python/FastAPI, Postgres, Redis, SQS, Terraform, CloudWatch)*
- Scaled asset ingestion throughput **6× (300K → 1.7M)** by redesigning services with **asyncio** workers and **SQS back‑pressure** on **EKS**.
- Cut **P95 query latency ~30%** via targeted **PostgreSQL** indexes, plan fixes, and connection‑pool tuning.
- Raised detection precision from **~30% → ~92%** by adding **schema validation**, golden‑set **regressions**, and idempotent replays.
- Automated multi‑env promotions (**SBX → NPD → PRD**) with **Terraform** + **Azure DevOps**, saving **~120 hrs/year** and removing manual drift.
- Built **CloudWatch** dashboards/alerts and **SLO‑based runbooks**, improving on‑call triage and reducing incident recovery time.
- Mentored **4** engineers; elevated testing, code review quality, and operational readiness.

**Accenture — Software Engineer** · Nashville, TN · Jul 2018–Dec 2019  
- Delivered backend features and fixed high‑priority defects in Python/GCP services to maintain release cadence.

## Personal Project
**Kickback — Document Signals API** · Python/FastAPI, Postgres/SQLAlchemy, Redis, Alembic, Docker, Pytest
- API‑key service ingesting create/update/view signals with **100 req/min per‑key Redis token bucket**; cache‑aside reads, DB‑enforced uniqueness.
- CDC‑style projector converts raw signals to daily aggregates/leaderboard for read‑heavy endpoints.

## Education
**Oberlin College** — B.A., Computer Science
",
    "cover_md": "Hi Pump team,

Pump solves a painful loop I’ve seen: engineers pause product work to chase AWS bills. I want to help make savings automatic, safe, and measurable—so teams cut spend without risking reliability or trust.

On a recent platform, I grew throughput 6× (300K→1.7M assets) by moving to asyncio workers with SQS back‑pressure and tightening Postgres access patterns.

What I’d focus on:
- Design FastAPI services with idempotency and clear contracts; schema evolution that keeps backfills safe.
- Lower P95/P99 for pricing/recommendation paths with indexing, caching, and pagination; guardrails for spikes.
- End‑to‑end observability: traces for savings decisions, budget/SLO alerts, runbooks and rollback paths.

I work in small steps, with tests and tracing from day one, and I keep feedback loops tight with customers and support. Bay Area‑based and available five days on‑site.

— Luis Solorzano
Richmond, CA"
}