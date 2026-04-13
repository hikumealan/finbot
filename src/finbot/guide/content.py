"""Guide section registry and full-text search."""
from __future__ import annotations

GUIDE_SECTIONS: list[dict[str, str]] = [
    {
        "title": "Getting Started",
        "content": """## Getting Started

### Prerequisites
- **macOS** (Apple Silicon recommended) or **Linux**
- **Python 3.11+**
- **Node.js 22+** (for the React frontend)
- **Ollama** -- download from [ollama.com](https://ollama.com)

### One-Command Setup
```bash
git clone <repo-url> && cd finbot
make setup
```

This installs Ollama, pulls the LLM model, installs Python + Node dependencies, and runs the onboarding wizard.

### Manual Setup
```bash
git clone <repo-url> && cd finbot
cp .env.example .env
uv sync
cd frontend && npm install && cd ..
finbot setup
finbot doctor
```

### First Import
```bash
finbot import ~/Downloads/bank-statement.pdf
```

The import pipeline detects the file type, parses transactions, shows a preview, and asks for confirmation before saving.

### Launch the Dashboard
```bash
make dev                    # Development: FastAPI + React dev server
finbot serve                # Production: single server on port 8000
```

The API docs are available at `http://localhost:8000/docs`.
""",
    },
    {
        "title": "Importing Data",
        "content": """## Importing Data

### Supported Formats
- **PDF** -- bank and brokerage statements (auto-detects tables and text)
- **CSV** -- exports from Chase, Bank of America, Capital One, and generic formats
- **OFX/QFX** -- Quicken-compatible files from most US banks

### Tax Documents
Upload W-2, 1040, 1099-DIV, 1099-INT, 1099-B, and K-1 forms:
```bash
finbot import-tax ~/Downloads/w2-2025.pdf
```
Tax documents can also be uploaded via the web dashboard at /tax.

### Deduplication
When you re-import a file, FinBot fingerprints each transaction (date + amount + description) and skips duplicates automatically.

### Batch Import
Import an entire directory:
```bash
finbot import ~/Downloads/statements/
```

### Manual Entry
For cash, Venmo, or Zelle transactions:
```bash
finbot add
```

### Import History
View and roll back previous imports:
```bash
finbot audit --last 20
```
Or use the Settings > Data tab in the web dashboard.
""",
    },
    {
        "title": "Expenses & Budgets",
        "content": """## Expenses & Budgets

### Expense Tracking
FinBot auto-categorizes transactions (groceries, dining, utilities, etc.) using pattern matching. View by category:
```bash
finbot expenses --month 2025-03
```

### Budget Targets
Set monthly limits per category:
```bash
finbot budget --set dining=500
finbot budget --set groceries=800
```
View variance with `finbot budget`. On the web dashboard, the Expenses page shows budget bars with green/red indicators.

### Recurring Subscriptions
FinBot detects recurring charges by matching descriptions and amounts across months:
```bash
finbot subscriptions
```

### Savings Rate
The most important Boglehead metric: (Income - Expenses) / Income. Target 20%+:
```bash
finbot savings-rate
```

### Transaction Editing
Edit categories, amounts, or descriptions for individual transactions on the web dashboard Expenses page (Transactions tab) or via the API:
```
PATCH /api/transactions/{id}
```

### Category Rules
Add custom categorization rules in Settings > Data > Category Rules. Rules use regex patterns and are applied to new imports and during bulk re-categorization.
""",
    },
    {
        "title": "Investments",
        "content": """## Investments

### Portfolio Tracking
Import brokerage statements to track holdings. FinBot calculates returns and compares against benchmarks.

### Rebalancing
FinBot alerts you when your allocation drifts more than 5% from target (configurable in Settings > Config). It suggests specific trades to rebalance:
```bash
finbot portfolio
```

### Fee Impact
See the 10/20/30-year cost of expense ratios:
```bash
finbot fees
```
A 0.85% ER fund costs dramatically more than a 0.03% index fund over decades. The web dashboard has an interactive fee impact calculator at /investments.

### Dividend Tracking
Dividend income is tracked from brokerage statements and contributes to your total return calculation.
""",
    },
    {
        "title": "Municipal Bonds",
        "content": """## Municipal Bonds

### Taxable Equivalent Yield (TEY)
Munis pay tax-exempt interest. To compare with taxable bonds, calculate TEY:
```
TEY = Coupon Rate / (1 - Combined Tax Rate)
```
The web dashboard has an interactive TEY calculator at /muni-bonds that uses your actual tax bracket from imported W2 data.

### State Tax Rules
- In-state munis are often double-exempt (federal + state)
- States like IL exempt ALL munis, not just in-state
- No-income-tax states (TX, FL, WA) -- in-state preference doesn't matter

### When Munis Make Sense
- **Only in taxable accounts** -- never in IRAs/401k
- Generally attractive at 32%+ federal marginal rate
- Use VTEAX/VTEB for low-cost national exposure

### Risks
- Interest rate risk (longer duration = more price volatility)
- Call risk (callable bonds may be redeemed early)
- AMT (private activity bonds may trigger AMT)
""",
    },
    {
        "title": "Debt Management",
        "content": """## Debt Management

### Adding Debts
Add debts through the CLI or the web dashboard at Settings > Goals & Debts:
```bash
finbot debts
```

### Payoff Strategies
- **Avalanche** -- pay highest interest rate first (saves the most money)
- **Snowball** -- pay smallest balance first (psychological wins)
```bash
finbot debts --strategy avalanche
```

### Extra Payment Modeling
The web dashboard at /debts has a slider to model how extra monthly payments accelerate payoff and reduce total interest.
""",
    },
    {
        "title": "Goals & Projections",
        "content": """## Goals & Projections

### Financial Goals
Create and track goals (retirement, emergency fund, house, college) in Settings > Goals & Debts or via the API:
```bash
finbot goals
```
The web dashboard at /goals shows progress bars with on-track/behind/ahead status.

### Monte Carlo Simulation
Project future growth with 1,000 randomized scenarios:
```bash
finbot project --years 30
```
Results show 5th/25th/50th/75th/95th percentile outcomes. The web dashboard at /projections has interactive sliders for starting balance, contribution, years, and inflation.

### Inflation Adjustment
Toggle between nominal and real (inflation-adjusted) values. Default inflation rate: 3% (configurable in Settings > Config).
""",
    },
    {
        "title": "Tax Optimization",
        "content": """## Tax Optimization

### Tax-Loss Harvesting
FinBot identifies holdings with unrealized losses. The 30-day wash sale rule is tracked -- recently sold symbols are flagged.

### Standard Deduction
Tax calculations apply the standard deduction ($15,000 single / $30,000 married joint for 2025) before computing bracket placement.

### Bracket Management
Know your marginal bracket and optimize Roth conversions, charitable giving timing:
```bash
finbot tax --year 2025
```

### Contribution Priority
Boglehead order: 401k match -> HSA -> Roth IRA -> remaining 401k -> taxable.

### Tax Document Upload
Upload W2, 1040, and 1099 forms via the web dashboard at /tax or CLI:
```bash
finbot import-tax ~/Downloads/w2-2025.pdf
```
""",
    },
    {
        "title": "AI Advisors",
        "content": """## AI Advisors

Three specialized advisors powered by a local LLM (Ollama). All data stays on your machine -- PII is sanitized before any text reaches the LLM.

### Boglehead Advisor
Investment guidance: asset allocation, fund selection, rebalancing.
```bash
finbot chat
```

### Tax Advisor
Tax-loss harvesting, bracket management, contribution strategy.
```bash
finbot tax-chat
```

### Municipal Bonds Advisor
TEY analysis, state-specific rules, credit quality guidance.
```bash
finbot muni-chat
```

### Unified Review
Cross-advisor analysis combining all perspectives:
```bash
finbot review
```

### Web Dashboard
The Advisor page at /advisor has tabs for all three advisors with persistent conversation history and a session sidebar for resuming past chats.

### Graceful Degradation
All data pages work without Ollama running. Only the chat advisors and report generation require it. Run `finbot doctor` to check Ollama status.
""",
    },
    {
        "title": "Boglehead Philosophy",
        "content": """## Boglehead Investment Philosophy

### Core Principles
1. **Develop a workable plan** -- set goals and a target asset allocation
2. **Invest early and often** -- time in the market beats timing the market
3. **Never bear too much or too little risk** -- match allocation to age and risk tolerance
4. **Diversify** -- total market index funds across US, international, and bonds
5. **Never try to time the market** -- stay invested through ups and downs
6. **Use index funds** -- low-cost, tax-efficient, broadly diversified
7. **Keep costs low** -- every basis point of fees compounds against you
8. **Minimize taxes** -- tax-advantaged accounts first, tax-efficient placement
9. **Invest with simplicity** -- the three-fund portfolio is all you need
10. **Stay the course** -- don't react to market volatility

### Three-Fund Portfolio
- **VTI** (VTSAX) -- Total US Stock Market
- **VXUS** (VTIAX) -- Total International Stock Market
- **BND** (VBTLX) -- Total US Bond Market

### Asset Allocation
A common starting point: "Your age in bonds." A 30-year-old might target 70% stocks / 30% bonds. Adjust based on risk tolerance (configurable in your profile).
""",
    },
    {
        "title": "Security & Privacy",
        "content": """## Security & Privacy

### Data Stays Local
FinBot makes ZERO outbound network calls. Ollama runs locally. The FastAPI server binds to localhost by default.

### Encryption
The database key is stored at `~/.finbot/key` with 600 permissions. The key hash is verified on every startup.

### PII Sanitizer
Before any text goes to the LLM, account numbers, SSNs, emails, and phone numbers are replaced with tokens like `[SSN_REDACTED]`.

### PIN Authentication
Set a session PIN via the web dashboard (Settings > Security) or CLI:
```bash
finbot pin set
finbot pin remove
```
When enabled, the web dashboard requires PIN entry and sessions auto-lock after a configurable timeout (default: 15 minutes).

### JWT Auth
The FastAPI backend issues JWT tokens stored in httpOnly cookies. API requests without a valid token return 401.

### Audit Log
Every import, edit, delete, and export is logged:
```bash
finbot audit --last 20
```
""",
    },
    {
        "title": "Mobile App",
        "content": """## Mobile App

The iOS app connects to your Mac over the local network. All data and LLM processing stay on the Mac.

### Setup
1. `finbot serve --lan` -- bind to your LAN IP
2. `finbot pair` -- generate a QR code / PIN
3. Open the FinBot iOS app and scan or enter the PIN

### Prerequisites
- Xcode installed on your Mac
- Device UDIDs registered in your provisioning profile
- Ad-hoc provisioning for distribution (up to 100 devices)

### Key Points
- The phone is a pure view layer with zero local persistence
- All data stays on your Mac
- Face ID / Touch ID lock available
- Provisioning profiles expire after 1 year
""",
    },
    {
        "title": "CLI Reference",
        "content": """## CLI Reference

All 33 commands support `--help` for detailed usage.

### Import
`finbot import <file_or_dir>`, `finbot import-tax <file>`, `finbot add`

### Analysis
`finbot expenses`, `finbot budget`, `finbot networth`, `finbot portfolio`, `finbot savings-rate`, `finbot subscriptions`, `finbot fees`

### Advisors
`finbot chat`, `finbot tax-chat`, `finbot muni-chat`, `finbot review`

### Tax & Bonds
`finbot tax`, `finbot munis`

### Data Management
`finbot clear --transactions/--holdings/--tax/--chats/--all`, `finbot pin set/remove`, `finbot export --format csv/pdf`

### Admin
`finbot doctor`, `finbot backup`, `finbot audit`, `finbot serve`, `finbot pair`, `finbot devices`

### Help
`finbot guide`, `finbot guide <topic>`, `finbot guide --search <query>`, `finbot help`
""",
    },
    {
        "title": "Troubleshooting",
        "content": """## Troubleshooting

### Ollama Not Running
```bash
ollama serve
ollama pull mistral:7b-instruct-v0.3-q4_K_M
```
All data pages work without Ollama -- only chat advisors and report generation need it.

### Import Failures
- Ensure PDF is text-based (not scanned images)
- CSV must have Date, Amount, and Description columns
- OFX files should end in .ofx or .qfx

### Database Issues
Restore from backup:
```bash
finbot backup --restore data/backups/finbot_backup_YYYYMMDD.db
```
Or use the web dashboard at Settings > Backup & Export.

### Clear and Reset
Delete specific data categories or reset everything:
```bash
finbot clear --transactions      # Just transactions
finbot clear --all               # Everything (backup created first)
```

### Slow LLM Responses
- Use a smaller quantized model (e.g., Q4_K_M)
- Mistral 7B is recommended for 24GB M4 Pro
- Switch models in Settings > Config or with `make pull-model MODEL=llama3:8b`

### API Not Starting
```bash
finbot doctor                    # Check all components
finbot serve --reload            # Start with auto-reload for debugging
```
API docs at `http://localhost:8000/docs` for testing endpoints.
""",
    },
    {
        "title": "Glossary",
        "content": """## Glossary

- **AMT** -- Alternative Minimum Tax; a parallel tax system that limits certain deductions
- **Basis Points (bps)** -- 1/100th of a percent; 100 bps = 1%
- **Cost Basis** -- the original purchase price of an investment
- **Duration** -- measure of bond price sensitivity to interest rate changes
- **Expense Ratio (ER)** -- annual fund management fee as a percentage of assets
- **IRR** -- Internal Rate of Return; annualized return accounting for cash flow timing
- **JWT** -- JSON Web Token; used for API authentication
- **Standard Deduction** -- amount subtracted from gross income before tax brackets apply ($15,000 single / $30,000 married joint for 2025)
- **TEY** -- Taxable Equivalent Yield; what a muni bond yields compared to taxable bonds at your tax rate
- **TLH** -- Tax-Loss Harvesting; selling losing positions to offset gains
- **TWR** -- Time-Weighted Return; return independent of cash flow timing
- **Wash Sale** -- IRS rule preventing claiming a loss if you rebuy the same security within 30 days
""",
    },
]


def search_guide(query: str) -> list[tuple[str, str]]:
    """Full-text search across all guide sections."""
    query_lower = query.lower()
    results = []
    for section in GUIDE_SECTIONS:
        content = section["content"]
        if query_lower in content.lower():
            idx = content.lower().index(query_lower)
            start = max(0, idx - 100)
            end = min(len(content), idx + 200)
            snippet = "..." + content[start:end] + "..."
            results.append((section["title"], snippet))
    return results
