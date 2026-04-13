# FinBot

A fully offline, local LLM-powered financial analyst that keeps all your data on your machine. FinBot ingests bank statements, brokerage reports, and tax documents, then provides expense tracking, budgeting, net worth monitoring, investment analysis, tax optimization, and municipal bond advisory -- all guided by Boglehead investment philosophy.

**Key value propositions:**

- **Fully offline** -- no cloud calls, no API keys, no subscriptions
- **Encrypted locally** -- key-protected database with PII sanitization before LLM context
- **Boglehead-guided** -- low-cost index funds, three-fund portfolio, stay the course
- **Tax-optimized** -- tax-loss harvesting, bracket management with standard deduction, asset location
- **Muni bond expertise** -- taxable equivalent yield, state-specific rules, credit analysis
- **Multiple interfaces** -- CLI (33 commands), React web dashboard (13 routes), iOS mobile app
- **Modern stack** -- FastAPI REST backend, TanStack Start + shadcn/ui frontend

## Privacy and Security

All data stays on your local machine. FinBot makes **zero outbound network calls** -- the Ollama LLM runs locally and the database is protected by a locally generated encryption key. The FastAPI backend binds to `127.0.0.1` by default. PIN-based JWT authentication is enforced when `FINBOT_REQUIRE_PIN=true`.

Before any text is sent to the LLM, the PII sanitizer strips account numbers, SSNs, emails, phone numbers, and long numeric identifiers, replacing them with tokens like `[SSN_REDACTED]`.

## Prerequisites

- **macOS** (Apple Silicon recommended) or **Linux**
- **Python 3.11+**
- **Node.js 22+** -- for the React frontend
- **Ollama** -- installed automatically by `make setup`, or manually from [ollama.com](https://ollama.com)
- **Xcode** -- only needed if building the iOS mobile app

## Installation

### One-Command Setup (Recommended)

```bash
git clone https://github.com/your-org/finbot.git
cd finbot
make setup
```

This runs `scripts/bootstrap.sh` which automatically:
1. Checks system requirements (RAM >= 8 GB, disk >= 10 GB, OS version)
2. Installs Ollama (brew on macOS, curl on Linux)
3. Pulls the recommended LLM model (~4 GB download)
4. Installs Python dependencies via uv
5. Runs the onboarding wizard (skippable with `--ci` flag)
6. Verifies everything with `finbot doctor`

### Manual Setup

```bash
git clone https://github.com/your-org/finbot.git
cd finbot
cp .env.example .env
uv sync
cd frontend && npm install && cd ..
finbot setup
finbot doctor
```

### Docker Setup

Three modes are available:

**Full Docker** (Linux with NVIDIA GPU, or CI environments):

```bash
docker compose --profile full up -d      # Start Ollama + FinBot
make docker-pull                          # Pull the LLM model
open http://localhost:8000                 # Open dashboard
```

**Hybrid mode** (macOS -- native Ollama with GPU, containerised FinBot):

```bash
ollama serve &
ollama pull mistral:7b-instruct-v0.3-q4_K_M
make docker-up-hybrid
```

**When to use which:**

| Mode | Best for | GPU acceleration |
|------|----------|-----------------|
| Native (`make setup`) | macOS daily use | Full Metal GPU |
| Hybrid (`make docker-up-hybrid`) | macOS + container isolation | Full Metal GPU |
| Full Docker | Linux with NVIDIA, CI | NVIDIA GPU (Linux) or CPU-only |

Note: Docker on macOS cannot pass through Apple Silicon GPUs. For the best LLM performance on a Mac, use native mode.

## Running FinBot

After installation (`make setup`), launch FinBot in the mode you need:

```bash
finbot <command>                      # CLI -- run any command directly
make dev                              # Web -- API at :8000 + React at :3000
finbot serve --lan                    # Mobile -- LAN server for iOS app
```

### Quick Start

```bash
finbot setup                          # 1. Configure your profile
finbot import ~/Downloads/statement.pdf  # 2. Import a statement
finbot expenses                       # 3. View expense breakdown
finbot networth                       # 4. Check net worth
finbot chat                           # 5. Chat with Boglehead advisor
make dev                              # 6. Open web dashboard
```

## CLI Reference

FinBot has 33 commands. Every command supports `--help` for detailed usage.

### Importing Data

```bash
finbot import <file_or_dir>           # Import statement(s) -- PDF/CSV/OFX/QFX
finbot import-tax <file>              # Import tax document -- W2/1040/1099/K-1
finbot add                            # Manually add a transaction
```

### Financial Overview

```bash
finbot accounts                       # List all accounts
finbot expenses [--month YYYY-MM]     # Expense report by category
finbot budget [--set category=amount] # View or set budget targets
finbot subscriptions                  # List detected recurring charges
finbot savings-rate                   # Income vs spending ratio
finbot networth                       # Net worth + emergency fund status
```

### Investments and Debt

```bash
finbot portfolio                      # Investment performance + rebalancing alerts
finbot fees                           # Fee impact analysis across holdings
finbot munis                          # Municipal bond holdings + TEY analysis
finbot debts [--strategy avalanche]   # Debt payoff plan (avalanche or snowball)
finbot goals                          # Financial goal progress
```

### Projections and Tax

```bash
finbot project [--years N]            # Growth projection (Monte Carlo simulation)
finbot tax [--year YYYY]              # Tax position + optimization suggestions
```

### AI Advisors

```bash
finbot chat                           # Boglehead investment advisor (persistent)
finbot tax-chat                       # Tax optimization advisor
finbot muni-chat                      # Municipal bonds advisor
finbot review                         # Unified cross-advisor financial review
```

### Data Management

```bash
finbot clear --transactions           # Delete all transactions
finbot clear --holdings               # Delete all holdings
finbot clear --tax                    # Delete all tax documents
finbot clear --chats                  # Delete all chat sessions
finbot clear --all                    # Delete everything (backup first)
finbot pin set                        # Set session PIN
finbot pin remove                     # Remove session PIN
finbot export --format csv            # Export transactions as CSV
finbot export --category holdings     # Export holdings specifically
```

### Reports and Admin

```bash
finbot report [--period Q1]           # Generate narrative report
finbot backup [--restore <file>]      # Backup or restore encrypted database
finbot doctor                         # System health check
finbot serve [--lan] [--port 8000]    # Start FastAPI web server
finbot serve --reload                 # Start with auto-reload (development)
finbot pair                           # Generate QR / PIN for mobile pairing
finbot devices                        # List paired mobile devices
finbot audit [--last N]               # View audit log entries
```

### Help and Documentation

```bash
finbot guide                          # List all user guide topics
finbot guide <topic>                  # View a specific guide topic
finbot guide --search <query>         # Search all guide content
finbot help [command]                 # Quick help for any command
```

## Web Dashboard

The web dashboard is a React application (TanStack Start) backed by a FastAPI REST API.

### Launch

```bash
make dev                              # Development: FastAPI (:8000) + React dev server (:3000)
finbot serve                          # Production: FastAPI serves built React from /static
finbot serve --lan                    # Bind to LAN IP (mobile access)
```

### API Documentation

FastAPI auto-generates interactive API docs:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

### Pages (React Routes)

1. **Dashboard** (`/`) -- net worth, savings rate, expense charts, dismissable alerts
2. **Expenses** (`/expenses`) -- category breakdown, budget variance, subscriptions, inline transaction editor
3. **Investments** (`/investments`) -- portfolio allocation, rebalancing alerts, fee impact calculator
4. **Muni Bonds** (`/muni-bonds`) -- TEY calculator, holdings table
5. **Debts** (`/debts`) -- payoff strategies with extra payment slider
6. **Goals** (`/goals`) -- progress cards with monthly savings needed
7. **Projections** (`/projections`) -- Monte Carlo simulation with what-if sliders
8. **Tax Center** (`/tax`) -- document upload, tax position, TLH candidates
9. **Advisor** (`/advisor`) -- chat with 3 advisor tabs (Boglehead, Tax, Muni)
10. **Settings** (`/settings`) -- 8 tabs: profile, data management, accounts, goals/debts, security, config, storage, backup/export
11. **User Guide** (`/guide`) -- searchable documentation (15 topics)

### Tech Stack

- **FastAPI** -- Python REST API with JWT auth, Pydantic schemas, 64 endpoints
- **TanStack Start** -- React meta-framework with file-based routing (Vite-powered)
- **TanStack Query** -- data fetching, caching, optimistic mutations
- **TanStack Table** -- headless tables for transactions, holdings, debts
- **shadcn/ui** -- accessible component primitives (Radix UI + Tailwind)
- **Recharts** -- pie, bar, line charts for dashboards and projections
- **Tailwind CSS v4** -- utility-first styling

## Mobile App (Ad-Hoc -- No App Store)

FinBot includes an iOS app distributed via ad-hoc provisioning, bypassing the App Store entirely. The app is a thin client that connects to your Mac over the local network -- all data and LLM processing stay on the Mac.

### Prerequisites

- Xcode installed on your Mac
- Each target device's UDID registered in your provisioning profile (up to 100 devices)

### Register Device UDIDs

1. Connect the iPhone/iPad to your Mac via USB
2. Open **Finder** (macOS 13+), select the device, click the serial number to reveal the UDID
3. Add the UDID to your ad-hoc provisioning profile in Xcode

### Build the IPA

```bash
cd mobile
npm install
npx cap sync ios
npx cap open ios
```

In Xcode:
1. Select your **Team** under Signing & Capabilities
2. Set the provisioning profile to **Ad Hoc**
3. Select **Product > Archive**
4. In the Organizer, click **Distribute App > Ad Hoc**
5. Export the `.ipa` file

### Install on Device

**Option A -- Direct USB (simplest):**

Connect the device and use Xcode: **Window > Devices and Simulators**, drag the `.ipa` onto the device.

**Option B -- Over-the-Air (OTA) on local network:**

Host the IPA on your Mac's local server and navigate to the install URL in Safari on the device. No internet required -- works entirely on your LAN.

### Connect to FinBot

Once the app is installed:

```bash
finbot serve --lan                    # Start the server on your Mac
finbot pair                           # Display a pairing PIN / QR code
```

Open the FinBot app on your device. It discovers your Mac automatically via Bonjour. Enter the PIN or scan the QR code to pair. Subsequent launches auto-connect without re-pairing.

### Key Points

- **No App Store review, no public listing** -- you control distribution entirely
- **100-device limit** per provisioning profile per year
- **Provisioning profiles expire after 1 year** -- rebuild and reinstall annually
- **All data stays on your Mac** -- the phone is a pure view layer with zero local persistence
- **Face ID / Touch ID** lock available via the Capacitor Biometrics plugin

See the in-app guide for more detail: `finbot guide mobile`

## Configuration

Copy `.env.example` to `.env` and customize. Settings can also be changed live from the web dashboard at Settings > Config (persisted to the database, no restart needed).

| Variable | Default | Description |
|----------|---------|-------------|
| `FINBOT_OLLAMA_MODEL` | `mistral:7b-instruct-v0.3-q4_K_M` | Ollama model to use |
| `FINBOT_OLLAMA_HOST` | `http://127.0.0.1:11434` | Ollama API endpoint |
| `FINBOT_SESSION_TIMEOUT_MINUTES` | `15` | Auto-lock timeout (minutes) |
| `FINBOT_REQUIRE_PIN` | `true` | Enforce PIN auth on web dashboard |
| `FINBOT_WATCH_FOLDER` | `~/finbot-inbox` | Watch folder for auto-import |
| `FINBOT_DEFAULT_INFLATION_RATE` | `0.03` | Inflation rate for projections |
| `FINBOT_REBALANCE_DRIFT_THRESHOLD` | `0.05` | Alert when allocation drifts 5%+ |
| `FINBOT_IMPORT_CLEANUP_DAYS` | `30` | Days before imported files are deleted |
| `FINBOT_KEY_DIR` | `~/.finbot` | Encryption key directory (set for Docker) |

## Development

### Makefile Targets

Run `make help` to see all targets. Key ones:

```bash
# Native (recommended for macOS)
make setup            # Full native setup (Ollama + Python + onboarding)
make dev              # Start FastAPI + React dev server with auto-reload
make test             # Run pytest (skips LLM-dependent tests)
make lint             # Ruff linter
make format           # Ruff auto-format
make status           # Show Ollama + DB health at a glance
make update           # Upgrade Ollama, sync deps, update model
make pull-model       # Pull/switch model (MODEL=llama3:8b)
make backup           # Create encrypted database backup
make restore          # Restore database from backup file
make reset            # Delete database only (keeps encryption key)

# Docker
make docker-build     # Build the FinBot Docker image
make docker-up        # Start full Docker stack (with Ollama)
make docker-up-hybrid # Start FinBot container only (use native Ollama)
make docker-down      # Stop all services
make docker-pull      # Pull model inside Ollama container
make docker-shell     # Shell into FinBot container
make docker-logs      # Tail all service logs
make docker-test      # Run pytest inside container

# Maintenance
make clean            # Remove build artifacts (safe)
make clean-all        # Remove ALL data + containers (destructive, confirms)
```

### Project Structure

```
src/finbot/
├── api/          # FastAPI REST API (18 route modules, 64 endpoints)
├── cli/          # Typer CLI (33 commands)
├── guide/        # User guide content (15 topics)
├── parsers/      # PDF, CSV, OFX, tax document parsers + dedup
├── models/       # SQLAlchemy ORM models (17 tables)
├── analysis/     # Financial computation engine (16 modules)
├── llm/          # Ollama client, 5 system prompts, memory, Pydantic validation
├── security/     # Encryption, PII sanitizer, audit log
├── db/           # Database engine, Alembic migrations, reference data seeding
└── export/       # CSV export, text reports, backup/restore

frontend/
├── src/routes/   # TanStack Router file-based routes (13 pages)
├── src/api/      # Typed API client (fetch wrapper with JWT)
├── src/hooks/    # TanStack Query hooks + auth
├── src/types/    # TypeScript types matching API schemas
└── app.config.ts # Vite + Tailwind + API proxy config
```

### Running Tests

```bash
make test                              # Standard run (skips LLM tests)
uv run pytest --cov=finbot             # With coverage
uv run pytest -m llm                   # LLM tests only (requires Ollama)
```

### Database Migrations

```bash
alembic revision --autogenerate -m "add new column"
alembic upgrade head
```

### Adding a New API Endpoint

1. Create or update a route module in `src/finbot/api/routes/`
2. Add Pydantic schemas to `src/finbot/api/schemas.py`
3. Register the router in `src/finbot/api/app.py`
4. Add the corresponding frontend route or API call

### Adding a New Guide Section

1. Add content to `GUIDE_SECTIONS` in `src/finbot/guide/content.py`
2. The section is automatically available via `/api/guide/sections` and the CLI

## License

MIT

## Disclaimer

FinBot provides informational financial analysis only. It is not a substitute for professional financial, tax, or legal advice. Always consult qualified professionals for financial decisions.
