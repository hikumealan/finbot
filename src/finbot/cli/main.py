"""FinBot CLI — local offline financial analyst."""
from __future__ import annotations

import typer
from rich.console import Console
from rich.table import Table

app = typer.Typer(
    name="finbot",
    help="Local offline LLM-powered financial analyst with Boglehead-guided advice.",
    no_args_is_help=True,
)
console = Console()


@app.command()
def setup(edit: bool = typer.Option(False, "--edit", help="Edit existing profile")):
    """Run the first-time onboarding wizard (or edit your profile)."""
    from finbot.db.database import get_session, init_db
    from finbot.db.seed import seed_all
    from finbot.models.user_profile import UserProfile

    init_db()
    with get_session() as session:
        results = seed_all(session)
        for table, count in results.items():
            if count:
                console.print(f"  Seeded {count} rows into [bold]{table}[/bold]")

        profile = session.query(UserProfile).first()
        if profile and not edit:
            console.print("[green]Profile already configured.[/green] Use --edit to modify.")
            return

        console.print("\n[bold]FinBot Setup[/bold]\n")
        age = typer.prompt("Your age", type=int)
        state = typer.prompt("State of residence (2-letter code)", type=str)
        risk = typer.prompt("Risk tolerance (1=conservative, 10=aggressive)", type=int, default=5)
        retire_age = typer.prompt("Target retirement age", type=int, default=65)
        filing = typer.prompt(
            "Filing status (single/married_joint/married_separate/head_of_household)",
            type=str,
            default="single",
        )
        match_pct = typer.prompt("Employer 401k match % (0 if none)", type=float, default=0)

        if profile:
            profile.age = age
            profile.state_of_residence = state.upper()
            profile.risk_tolerance = risk
            profile.retirement_target_age = retire_age
            profile.filing_status = filing
            profile.employer_match_pct = match_pct
        else:
            profile = UserProfile(
                age=age,
                state_of_residence=state.upper(),
                risk_tolerance=risk,
                retirement_target_age=retire_age,
                filing_status=filing,
                employer_match_pct=match_pct,
            )
            session.add(profile)

        session.commit()
        console.print("\n[green]Profile saved.[/green]")


@app.command(name="import")
def import_cmd(
    path: str = typer.Argument(..., help="File or directory to import"),
    yes: bool = typer.Option(False, "--yes", "-y", help="Skip confirmation"),
):
    """Import financial statement(s) — PDF, CSV, OFX/QFX."""
    import pathlib

    from finbot.analysis.categorizer import categorize_description
    from finbot.db.database import get_session, init_db
    from finbot.models.account import Account
    from finbot.models.transaction import Transaction
    from finbot.parsers import detect_and_parse
    from finbot.parsers.dedup import (
        compute_fingerprint,
        detect_transfers,
        find_duplicates,
    )
    from finbot.security.audit import create_audit_entry

    init_db()
    target = pathlib.Path(path).expanduser()

    files = sorted(target.iterdir()) if target.is_dir() else [target]
    files = [f for f in files if f.is_file() and not f.name.startswith(".")]

    if not files:
        console.print("[red]No files found to import.[/red]")
        raise typer.Exit(1)

    for file_path in files:
        console.print(f"\n[bold]Parsing:[/bold] {file_path.name}")
        result = detect_and_parse(file_path)

        if result.warnings:
            for w in result.warnings:
                console.print(f"  [yellow]Warning:[/yellow] {w}")

        if not result.transactions and not result.holdings:
            console.print("  [dim]No transactions or holdings found.[/dim]")
            continue

        console.print(f"  Transactions: [bold]{len(result.transactions)}[/bold]")
        if result.date_range:
            console.print(f"  Date range: {result.date_range[0]} to {result.date_range[1]}")
        console.print(f"  Total debits: [red]${abs(result.total_debits):,.2f}[/red]")
        console.print(f"  Total credits: [green]${result.total_credits:,.2f}[/green]")
        console.print(f"  Institution: {result.account_institution or 'Unknown'}")

        if not yes:
            if not typer.confirm("  Import this file?", default=True):
                console.print("  [dim]Skipped.[/dim]")
                continue

        with get_session() as session:
            account = session.query(Account).filter_by(
                institution=result.account_institution or "Unknown",
                name=result.account_name or "Primary",
            ).first()
            if not account:
                account = Account(
                    institution=result.account_institution or "Unknown",
                    name=result.account_name or "Primary",
                    account_type=result.account_type or "checking",
                )
                session.add(account)
                session.flush()

            new_txs, dupes = find_duplicates(session, account.id, result.transactions)

            added = 0
            for ptx in new_txs:
                cat, subcat = categorize_description(ptx.description, session)
                if cat and cat.lower() in ("income", "salary", "payroll"):
                    ptx.tx_type = "income"
                tx = Transaction(
                    account_id=account.id,
                    date=ptx.date,
                    amount=ptx.amount,
                    description=ptx.description,
                    category=ptx.category or cat,
                    subcategory=ptx.subcategory or subcat,
                    tx_type=ptx.tx_type,
                    fingerprint_hash=compute_fingerprint(account.id, ptx.date, ptx.amount, ptx.description),
                    source_file=file_path.name,
                )
                session.add(tx)
                added += 1

            holdings_added = 0
            if result.holdings:
                from datetime import date as date_cls

                from finbot.models.holding import Holding

                for ph in result.holdings:
                    holding = Holding(
                        account_id=account.id,
                        symbol=ph.symbol,
                        shares=ph.shares,
                        cost_basis=ph.cost_basis,
                        current_price=ph.current_price,
                        price_as_of=ph.price_as_of or date_cls.today(),
                        date=date_cls.today(),
                        asset_class=ph.asset_class,
                    )
                    session.add(holding)
                    holdings_added += 1

            transfers = detect_transfers(session)

            create_audit_entry(session, "import", "file", None, {
                "file": file_path.name,
                "transactions_added": added,
                "holdings_added": holdings_added,
                "duplicates": len(dupes),
                "transfers_linked": transfers,
            })
            session.commit()

            console.print(f"  [green]Imported {added} transactions[/green]")
            if holdings_added:
                console.print(f"  [green]Imported {holdings_added} holdings[/green]")
            if dupes:
                console.print(f"  [dim]Skipped {len(dupes)} duplicates[/dim]")
            if transfers:
                console.print(f"  [dim]Linked {transfers} transfer pair(s)[/dim]")


@app.command(name="import-tax")
def import_tax_cmd(
    path: str = typer.Argument(..., help="Tax document to import (PDF)"),
):
    """Import a tax document — W2, 1040, 1099, K-1."""
    import pathlib

    from finbot.db.database import get_session, init_db
    from finbot.models.tax_document import TaxDocument, TaxLineItem
    from finbot.parsers.tax_parser import TaxDocParser
    from finbot.security.audit import create_audit_entry

    init_db()
    file_path = pathlib.Path(path).expanduser()
    parser = TaxDocParser()

    console.print(f"\n[bold]Parsing tax document:[/bold] {file_path.name}")
    result = parser.parse(file_path)

    console.print(f"  Form type: [bold]{result.doc_type}[/bold]")
    console.print(f"  Tax year: {result.tax_year or 'Unknown'}")
    console.print(f"  Fields extracted: {len(result.fields)}")
    console.print(f"  Confidence: {result.confidence:.0%}")

    for w in result.warnings:
        console.print(f"  [yellow]Warning:[/yellow] {w}")

    for key, value in result.fields.items():
        console.print(f"    {key}: ${float(value):,.2f}" if value.replace(".", "").isdigit() else f"    {key}: {value}")

    with get_session() as session:
        doc = TaxDocument(
            tax_year=result.tax_year or 0,
            doc_type=result.doc_type,
            source_file=file_path.name,
        )
        session.add(doc)
        session.flush()

        for key, value in result.fields.items():
            session.add(TaxLineItem(
                tax_document_id=doc.id,
                field_key=key,
                field_label=key.replace("_", " ").title(),
                value=value,
                data_type="currency" if value.replace(".", "").replace("-", "").isdigit() else "text",
            ))

        create_audit_entry(session, "import", "tax_document", doc.id, {
            "file": file_path.name,
            "doc_type": result.doc_type,
            "fields": len(result.fields),
        })
        session.commit()
        console.print(f"  [green]Saved as document #{doc.id}[/green]")


@app.command()
def add():
    """Manually add a transaction."""
    from datetime import date, datetime

    from finbot.analysis.categorizer import categorize_description
    from finbot.db.database import get_session, init_db
    from finbot.models.account import Account
    from finbot.models.transaction import Transaction
    from finbot.parsers.dedup import compute_fingerprint

    init_db()

    tx_date_str = typer.prompt("Date (YYYY-MM-DD)", default=date.today().isoformat())
    tx_date = datetime.strptime(tx_date_str, "%Y-%m-%d").date()
    amount = typer.prompt("Amount (negative for expense)", type=float)
    description = typer.prompt("Description")
    account_name = typer.prompt("Account name", default="Cash")

    with get_session() as session:
        account = session.query(Account).filter_by(name=account_name).first()
        if not account:
            account = Account(institution="Manual", name=account_name, account_type="checking")
            session.add(account)
            session.flush()

        cat, subcat = categorize_description(description, session)
        tx_type = "income" if amount > 0 else "expense"

        tx = Transaction(
            account_id=account.id,
            date=tx_date,
            amount=amount,
            description=description,
            category=cat,
            subcategory=subcat,
            tx_type=tx_type,
            fingerprint_hash=compute_fingerprint(account.id, tx_date, amount, description),
            source_file="manual",
        )
        session.add(tx)
        session.commit()
        console.print(f"[green]Transaction added: {description} ${amount:,.2f}[/green]")


@app.command()
def doctor():
    """Check system health: Ollama, model, database, data freshness."""
    import httpx

    from finbot.config import settings
    from finbot.db.database import check_db_health

    console.print("[bold]FinBot System Check[/bold]\n")
    checks: list[tuple[str, bool, str]] = []

    # Database
    db_ok = check_db_health()
    checks.append(("Database", db_ok, str(settings.db_path) if db_ok else "Cannot connect"))

    # Encryption key
    key_ok = settings.key_file.exists()
    checks.append(("Encryption Key", key_ok, str(settings.key_file) if key_ok else "Not found"))

    # Ollama
    ollama_ok = False
    ollama_msg = "Not running"
    try:
        r = httpx.get(f"{settings.ollama_host}/api/tags", timeout=3)
        if r.status_code == 200:
            models = [m["name"] for m in r.json().get("models", [])]
            ollama_ok = True
            ollama_msg = f"{len(models)} model(s) available"
    except Exception:
        pass
    checks.append(("Ollama", ollama_ok, ollama_msg))

    # Model
    model_ok = False
    if ollama_ok:
        try:
            r = httpx.get(f"{settings.ollama_host}/api/tags", timeout=3)
            model_names = [m["name"] for m in r.json().get("models", [])]
            base_model = settings.ollama_model.split(":")[0]
            model_ok = any(base_model in m for m in model_names)
        except Exception:
            pass
    checks.append(("LLM Model", model_ok, settings.ollama_model if model_ok else "Not pulled"))

    table = Table(show_header=True)
    table.add_column("Component")
    table.add_column("Status")
    table.add_column("Details")
    for name, ok, detail in checks:
        status = "[green]OK[/green]" if ok else "[red]FAIL[/red]"
        table.add_row(name, status, detail)
    console.print(table)


@app.command(name="accounts")
def list_accounts():
    """List all accounts."""
    from finbot.db.database import get_session
    from finbot.models.account import Account

    with get_session() as session:
        accounts = session.query(Account).all()
        if not accounts:
            console.print("[dim]No accounts yet. Import a statement to get started.[/dim]")
            return
        table = Table(title="Accounts")
        table.add_column("ID", style="dim")
        table.add_column("Institution")
        table.add_column("Name")
        table.add_column("Type")
        table.add_column("Tax-Advantaged")
        for a in accounts:
            table.add_row(str(a.id), a.institution, a.name, a.account_type, "Yes" if a.is_tax_advantaged else "")
        console.print(table)


@app.command()
def audit(last: int = typer.Option(50, "--last", help="Number of entries to show")):
    """View recent audit log entries."""
    from finbot.db.database import get_session
    from finbot.models.audit_log import AuditLog

    with get_session() as session:
        entries = session.query(AuditLog).order_by(AuditLog.timestamp.desc()).limit(last).all()
        if not entries:
            console.print("[dim]No audit log entries yet.[/dim]")
            return
        table = Table(title=f"Last {last} Audit Entries")
        table.add_column("Time")
        table.add_column("Action")
        table.add_column("Entity")
        table.add_column("Details")
        for e in entries:
            table.add_row(
                str(e.timestamp)[:19],
                e.action,
                f"{e.entity_type}#{e.entity_id}" if e.entity_type else "",
                (e.details_json or "")[:60],
            )
        console.print(table)


@app.command()
def fees():
    """Show fee impact analysis across all holdings."""
    from finbot.analysis.investments import fee_impact
    from finbot.db.database import get_session
    from finbot.models.holding import Holding

    with get_session() as session:
        holdings = session.query(Holding).all()
        if not holdings:
            console.print("[dim]No holdings imported yet.[/dim]")
            return

        table = Table(title="Fee Impact Analysis (30-year projection)")
        table.add_column("Symbol")
        table.add_column("Balance", justify="right")
        table.add_column("Fee Drag", justify="right")
        for h in holdings:
            if not h.current_price:
                continue
            balance = float(h.current_price) * float(h.shares)
            impact = fee_impact(balance, 0.005, 30)
            table.add_row(h.symbol, f"${balance:,.0f}", f"${impact['fee_drag']:,.0f}")
        console.print(table)


@app.command()
def subscriptions():
    """List detected recurring charges."""
    from finbot.analysis.subscriptions import detect_subscriptions
    from finbot.db.database import get_session

    with get_session() as session:
        subs = detect_subscriptions(session, min_occurrences=2)
        if not subs:
            console.print("[dim]Not enough data to detect recurring charges (need 2+ months).[/dim]")
            return

        total = sum(s.amount for s in subs)
        console.print(f"\n[bold]Total Recurring: ${total:,.2f}/month[/bold]\n")

        table = Table(title="Recurring Charges")
        table.add_column("Description")
        table.add_column("Amount", justify="right")
        table.add_column("Months Seen", justify="right")
        for s in subs:
            table.add_row(s.description, f"${s.amount:,.2f}", str(s.frequency))
        console.print(table)


@app.command()
def serve(
    lan: bool = typer.Option(False, "--lan", help="Bind to LAN IP for mobile access"),
    port: int = typer.Option(8000, "--port", help="Port to listen on"),
    reload: bool = typer.Option(False, "--reload", help="Enable auto-reload for development"),
):
    """Start the FastAPI web server."""
    import uvicorn

    if lan:
        import socket

        hostname = socket.gethostname()
        local_ip = socket.gethostbyname(hostname)
        host = local_ip
        console.print(f"[bold]LAN mode:[/bold] binding to {local_ip}:{port}")
    else:
        host = "127.0.0.1"

    console.print(f"[bold]Starting FinBot API[/bold] at http://{host}:{port}")
    console.print("  API docs: http://{host}:{port}/docs")
    uvicorn.run("finbot.api.app:create_app", factory=True, host=host, port=port, reload=reload)


@app.command()
def pair():
    """Generate a QR code / PIN for mobile device pairing."""
    import secrets

    pin = secrets.randbelow(900000) + 100000
    console.print(f"\n[bold]Pairing PIN:[/bold] {pin}\n")
    console.print("Enter this PIN in the FinBot mobile app to pair.")
    console.print("The pairing is valid for this session only.\n")

    try:
        import qrcode

        qr = qrcode.QRCode(box_size=1, border=1)
        qr.add_data(f"finbot://pair?pin={pin}")
        qr.make(fit=True)
        qr.print_ascii(invert=True)
    except ImportError:
        pass


@app.command()
def devices():
    """List paired mobile devices."""
    console.print("[dim]No devices paired yet. Use 'finbot pair' to pair a device.[/dim]")


@app.command()
def review():
    """Run a unified cross-advisor financial review."""
    from finbot.db.database import get_session
    from finbot.llm.analyst import ask_advisor, build_financial_snapshot
    from finbot.llm.prompts import BOGLEHEAD_SYSTEM_PROMPT, MUNI_BONDS_SYSTEM_PROMPT, TAX_OPTIMIZER_SYSTEM_PROMPT

    with get_session() as session:
        snapshot = build_financial_snapshot(session)
        prompt = f"Provide a comprehensive financial review based on this data. Focus on actionable recommendations.\n\n{snapshot}"

        console.print("[bold]Unified Financial Review[/bold]\n")

        for name, sys_prompt in [
            ("Boglehead Advisor", BOGLEHEAD_SYSTEM_PROMPT),
            ("Tax Optimizer", TAX_OPTIMIZER_SYSTEM_PROMPT),
            ("Municipal Bonds", MUNI_BONDS_SYSTEM_PROMPT),
        ]:
            console.print(f"\n[bold blue]--- {name} ---[/bold blue]\n")
            response = ask_advisor(session, sys_prompt, prompt)
            console.print(response)


@app.command()
def guide(
    topic: str | None = typer.Argument(None, help="Topic to view"),
    search: str | None = typer.Option(None, "--search", help="Search guide content"),
):
    """Browse the in-app user guide."""
    from rich.markdown import Markdown

    from finbot.guide.content import GUIDE_SECTIONS, search_guide

    if search:
        results = search_guide(search)
        if not results:
            console.print(f"[dim]No results for '{search}'[/dim]")
            return
        for title, snippet in results:
            console.print(f"\n[bold]{title}[/bold]")
            console.print(snippet.strip())
        return

    if topic:
        topic_lower = topic.lower()
        section = next((s for s in GUIDE_SECTIONS if topic_lower in s["title"].lower()), None)
        if section:
            console.print(Markdown(section["content"]))
        else:
            console.print(f"[red]Topic '{topic}' not found.[/red] Available topics:")
            for s in GUIDE_SECTIONS:
                console.print(f"  - {s['title']}")
        return

    console.print("\n[bold]FinBot User Guide[/bold]\n")
    for i, s in enumerate(GUIDE_SECTIONS, 1):
        console.print(f"  {i:2d}. {s['title']}")
    console.print("\n  Usage: finbot guide <topic>  |  finbot guide --search <query>")


@app.command()
def expenses(month: str | None = typer.Option(None, "--month", help="Month in YYYY-MM format")):
    """Show expense report by category."""
    from datetime import date

    from finbot.analysis.expenses import expenses_by_category, total_expenses
    from finbot.db.database import get_session

    with get_session() as session:
        start = end = None
        if month:
            y, m = int(month[:4]), int(month[5:7])
            start = date(y, m, 1)
            end = date(y, m + 1, 1) if m < 12 else date(y + 1, 1, 1)

        cats = expenses_by_category(session, start, end)
        total = total_expenses(session, start, end)

        if not cats:
            console.print("[dim]No expenses recorded yet.[/dim]")
            return

        table = Table(title=f"Expenses{' for ' + month if month else ''}")
        table.add_column("Category")
        table.add_column("Amount", justify="right")
        table.add_column("% of Total", justify="right")
        for cat, amt in sorted(cats.items(), key=lambda x: -x[1]):
            pct = (amt / total * 100) if total > 0 else 0
            table.add_row(cat, f"${amt:,.2f}", f"{pct:.1f}%")
        table.add_row("[bold]Total[/bold]", f"[bold]${total:,.2f}[/bold]", "100%")
        console.print(table)


@app.command()
def budget(set_val: str | None = typer.Option(None, "--set", help="Set budget: category=amount")):
    """View or set budget targets."""
    from datetime import date

    from finbot.analysis.budget import get_budget_variance, set_budget
    from finbot.db.database import get_session

    current_month = date.today().strftime("%Y-%m")

    with get_session() as session:
        if set_val:
            parts = set_val.split("=")
            if len(parts) != 2:
                console.print("[red]Use format: --set category=amount[/red]")
                raise typer.Exit(1)
            cat, amt = parts[0].strip(), float(parts[1].strip())
            set_budget(session, cat, amt, current_month)
            session.commit()
            console.print(f"[green]Budget set: {cat} = ${amt:,.2f}/month[/green]")
            return

        variance = get_budget_variance(session, current_month)
        if not variance:
            console.print("[dim]No budgets set. Use --set category=amount.[/dim]")
            return

        table = Table(title=f"Budget Variance — {current_month}")
        table.add_column("Category")
        table.add_column("Budget", justify="right")
        table.add_column("Actual", justify="right")
        table.add_column("Variance", justify="right")
        table.add_column("Status")
        for v in variance:
            color = "red" if v.is_over else "green"
            status = f"[{color}]{'OVER' if v.is_over else 'OK'}[/{color}]"
            table.add_row(v.category, f"${v.budget:,.2f}", f"${v.actual:,.2f}", f"${v.variance:,.2f}", status)
        console.print(table)


@app.command(name="savings-rate")
def savings_rate_cmd():
    """Show savings rate summary."""
    from finbot.analysis.savings_rate import monthly_savings_rates, overall_savings_rate
    from finbot.db.database import get_session

    with get_session() as session:
        overall = overall_savings_rate(session)
        monthly = monthly_savings_rates(session)

        if not monthly:
            console.print("[dim]No income or expense data yet.[/dim]")
            return

        console.print(f"\n[bold]Overall Savings Rate: {overall:.1f}%[/bold]")
        target_msg = "[green]Above 20% target[/green]" if overall >= 20 else "[yellow]Below 20% target[/yellow]"
        console.print(f"  {target_msg}\n")

        table = Table(title="Monthly Savings Rate")
        table.add_column("Month")
        table.add_column("Income", justify="right")
        table.add_column("Expenses", justify="right")
        table.add_column("Savings", justify="right")
        table.add_column("Rate", justify="right")
        for r in monthly[-12:]:
            color = "green" if r.rate >= 20 else ("yellow" if r.rate >= 0 else "red")
            table.add_row(r.month, f"${r.income:,.2f}", f"${r.expenses:,.2f}", f"${r.savings:,.2f}", f"[{color}]{r.rate:.1f}%[/{color}]")
        console.print(table)


@app.command()
def networth():
    """Show current net worth and emergency fund status."""
    from finbot.analysis.net_worth import compute_net_worth
    from finbot.db.database import get_session

    with get_session() as session:
        nw = compute_net_worth(session)
        console.print(f"\n[bold]Net Worth: ${nw.net_worth:,.2f}[/bold]")
        console.print(f"  Assets: ${nw.total_assets:,.2f}")
        console.print(f"  Liabilities: ${nw.total_liabilities:,.2f}")
        console.print(f"\n  Liquid Savings: ${nw.liquid_savings:,.2f}")
        console.print(f"  Avg Monthly Expenses: ${nw.avg_monthly_expenses:,.2f}")

        months = nw.emergency_fund_months
        if months == float("inf"):
            console.print("  Emergency Fund: [green]No expenses recorded[/green]")
        elif months >= 6:
            console.print(f"  Emergency Fund: [green]{months:.1f} months (6+ target met)[/green]")
        elif months >= 3:
            console.print(f"  Emergency Fund: [yellow]{months:.1f} months (below 6-month target)[/yellow]")
        else:
            console.print(f"  Emergency Fund: [red]{months:.1f} months (below 3-month minimum)[/red]")


@app.command()
def portfolio():
    """Show investment performance and rebalancing alerts."""
    from finbot.analysis.investments import portfolio_summary
    from finbot.analysis.rebalancer import check_rebalance
    from finbot.db.database import get_session

    with get_session() as session:
        ps = portfolio_summary(session)
        if ps.total_value == 0:
            console.print("[dim]No holdings imported yet.[/dim]")
            return

        console.print(f"\n[bold]Portfolio Value: ${ps.total_value:,.2f}[/bold]")
        console.print(f"  Cost Basis: ${ps.total_cost_basis:,.2f}")
        color = "green" if ps.total_gain_loss >= 0 else "red"
        console.print(f"  Gain/Loss: [{color}]${ps.total_gain_loss:,.2f} ({ps.total_return_pct:.1f}%)[/{color}]")

        if ps.allocation:
            console.print("\n  [bold]Allocation:[/bold]")
            for ac, pct in sorted(ps.allocation.items(), key=lambda x: -x[1]):
                console.print(f"    {ac}: {pct:.1f}%")

        rebalance = check_rebalance(session)
        if rebalance:
            console.print("\n  [yellow][bold]Rebalancing Needed:[/bold][/yellow]")
            for s in rebalance:
                console.print(f"    {s.asset_class}: {s.current_pct:.1f}% → {s.target_pct:.1f}% ({s.action} ${s.amount:,.0f})")


@app.command()
def debts(strategy: str = typer.Option("avalanche", "--strategy", help="avalanche or snowball")):
    """Show debt payoff plan."""
    from finbot.analysis.debts import compare_strategies
    from finbot.db.database import get_session

    with get_session() as session:
        comp = compare_strategies(session)
        if not comp.avalanche:
            console.print("[dim]No debts tracked yet.[/dim]")
            return

        results = comp.avalanche if strategy == "avalanche" else comp.snowball
        table = Table(title=f"Debt Payoff — {strategy.title()} Strategy")
        table.add_column("Debt")
        table.add_column("Months", justify="right")
        table.add_column("Interest", justify="right")
        table.add_column("Total Paid", justify="right")
        for r in results:
            table.add_row(r.name, str(r.months_to_payoff), f"${r.total_interest:,.2f}", f"${r.total_paid:,.2f}")
        console.print(table)
        console.print(f"\n  Avalanche total interest: ${comp.avalanche_total_interest:,.2f}")
        console.print(f"  Snowball total interest: ${comp.snowball_total_interest:,.2f}")
        console.print(f"  [green]Avalanche saves: ${comp.interest_saved:,.2f}[/green]")


@app.command()
def goals():
    """Show financial goal progress."""
    from finbot.analysis.goals import compute_goal_progress
    from finbot.db.database import get_session

    with get_session() as session:
        progress = compute_goal_progress(session)
        if not progress:
            console.print("[dim]No goals set yet. Use the web dashboard or setup to create goals.[/dim]")
            return

        for g in progress:
            color = {"on_track": "green", "ahead": "green", "behind": "yellow", "complete": "blue"}.get(g.status, "white")
            bar_filled = int(g.progress_pct / 5)
            bar = "█" * bar_filled + "░" * (20 - bar_filled)
            console.print(f"\n  [bold]{g.name}[/bold] ({g.goal_type})")
            console.print(f"    [{color}]{bar} {g.progress_pct:.0f}%[/{color}]")
            console.print(f"    ${g.current:,.2f} / ${g.target:,.2f}")
            if g.monthly_needed > 0:
                console.print(f"    Need ${g.monthly_needed:,.0f}/month to reach target")
            console.print(f"    Status: [{color}]{g.status.upper()}[/{color}]")


@app.command()
def project(years: int = typer.Option(30, "--years", help="Years to project")):
    """Show growth projection with Monte Carlo simulation."""
    from finbot.analysis.net_worth import compute_net_worth
    from finbot.analysis.projections import monte_carlo
    from finbot.db.database import get_session

    with get_session() as session:
        nw = compute_net_worth(session)

    result = monte_carlo(nw.total_assets, annual_contribution=12000, years=years)

    console.print(f"\n[bold]Growth Projection — {years} Years[/bold]")
    console.print(f"  Starting balance: ${nw.total_assets:,.2f}")
    console.print("  Annual contribution: $12,000\n")
    console.print("  [bold]Monte Carlo Outcomes (1,000 simulations):[/bold]")
    for pct, val in result.percentiles.items():
        console.print(f"    {pct}th percentile: ${val:,.0f}")
    console.print(f"\n  Median nominal: ${result.nominal[-1]:,.0f}")
    console.print(f"  Median real (inflation-adjusted): ${result.real[-1]:,.0f}")


@app.command()
def tax(year: int = typer.Option(2025, "--year", help="Tax year")):
    """Show tax position summary and optimization suggestions."""
    from finbot.analysis.tax_optimizer import compute_tax_position, find_tlh_candidates
    from finbot.db.database import get_session
    from finbot.models.user_profile import UserProfile

    with get_session() as session:
        profile = session.query(UserProfile).first()
        filing = profile.filing_status if profile else "single"
        state = profile.state_of_residence if profile else None

        pos = compute_tax_position(session, filing, state, year)
        if pos.gross_income == 0:
            console.print("[dim]No tax data imported yet. Use finbot import-tax to add W2/1040.[/dim]")
            return

        console.print(f"\n[bold]Tax Position — {year}[/bold]")
        console.print(f"  Gross Income: ${pos.gross_income:,.2f}")
        console.print(f"  Federal Effective Rate: {pos.federal_effective_rate:.1%}")
        console.print(f"  Federal Marginal Rate: {pos.federal_marginal_rate:.1%}")
        console.print(f"  State Rate: {pos.state_rate:.1%}")
        console.print(f"  Combined Marginal: {pos.combined_marginal_rate:.1%}")
        console.print(f"  Estimated Total Tax: ${pos.total_tax:,.2f}")
        console.print(f"  Effective Tax Rate: {pos.effective_rate:.1%}")

        tlh = find_tlh_candidates(session)
        if tlh:
            console.print("\n  [bold]Tax-Loss Harvesting Candidates:[/bold]")
            for c in tlh[:5]:
                console.print(f"    {c.symbol}: loss of ${c.unrealized_loss:,.2f}")


@app.command()
def munis():
    """Show municipal bond holdings with TEY analysis."""
    from finbot.analysis.muni_bonds import analyze_muni_holdings
    from finbot.analysis.tax_optimizer import compute_tax_position
    from finbot.db.database import get_session
    from finbot.models.user_profile import UserProfile

    with get_session() as session:
        profile = session.query(UserProfile).first()
        filing = profile.filing_status if profile else "single"
        state = profile.state_of_residence if profile else None

        pos = compute_tax_position(session, filing, state)
        holdings = analyze_muni_holdings(session, pos.federal_marginal_rate, state)

        if not holdings:
            console.print("[dim]No municipal bond holdings found.[/dim]")
            return

        table = Table(title="Municipal Bond Holdings")
        table.add_column("Symbol")
        table.add_column("Coupon", justify="right")
        table.add_column("TEY", justify="right")
        table.add_column("In-State")
        table.add_column("State Exempt")
        table.add_column("Rating")
        table.add_column("AMT")
        for h in holdings:
            table.add_row(
                h.symbol, f"{h.coupon_rate:.2%}", f"{h.tey:.2%}",
                "Yes" if h.is_in_state else "", "Yes" if h.is_state_exempt else "",
                h.credit_rating or "", "Yes" if h.is_amt_subject else "",
            )
        console.print(table)


@app.command()
def chat():
    """Interactive Boglehead investment advisor chat."""
    from finbot.db.database import get_session
    from finbot.llm.analyst import ask_advisor
    from finbot.llm.memory import add_message, create_session
    from finbot.llm.prompts import BOGLEHEAD_SYSTEM_PROMPT

    console.print("[bold]Boglehead Advisor[/bold] — type 'quit' to exit\n")
    with get_session() as session:
        chat_sess = create_session(session, "boglehead", "CLI Chat")
        session.commit()

        while True:
            try:
                user_input = typer.prompt("You")
            except (KeyboardInterrupt, EOFError):
                break
            if user_input.lower() in ("quit", "exit", "q"):
                break

            add_message(session, chat_sess.id, "user", user_input)
            response = ask_advisor(session, BOGLEHEAD_SYSTEM_PROMPT, user_input)
            add_message(session, chat_sess.id, "assistant", response)
            session.commit()

            console.print(f"\n[bold green]Advisor:[/bold green] {response}\n")


@app.command(name="tax-chat")
def tax_chat():
    """Interactive tax optimization advisor chat."""
    from finbot.db.database import get_session
    from finbot.llm.analyst import ask_advisor
    from finbot.llm.memory import add_message, create_session
    from finbot.llm.prompts import TAX_OPTIMIZER_SYSTEM_PROMPT

    console.print("[bold]Tax Optimization Advisor[/bold] — type 'quit' to exit\n")
    with get_session() as session:
        chat_sess = create_session(session, "tax", "CLI Tax Chat")
        session.commit()

        while True:
            try:
                user_input = typer.prompt("You")
            except (KeyboardInterrupt, EOFError):
                break
            if user_input.lower() in ("quit", "exit", "q"):
                break

            add_message(session, chat_sess.id, "user", user_input)
            response = ask_advisor(session, TAX_OPTIMIZER_SYSTEM_PROMPT, user_input)
            add_message(session, chat_sess.id, "assistant", response)
            session.commit()

            console.print(f"\n[bold green]Advisor:[/bold green] {response}\n")


@app.command(name="muni-chat")
def muni_chat():
    """Interactive municipal bonds advisor chat."""
    from finbot.db.database import get_session
    from finbot.llm.analyst import ask_advisor
    from finbot.llm.memory import add_message, create_session
    from finbot.llm.prompts import MUNI_BONDS_SYSTEM_PROMPT

    console.print("[bold]Municipal Bonds Advisor[/bold] — type 'quit' to exit\n")
    with get_session() as session:
        chat_sess = create_session(session, "muni", "CLI Muni Chat")
        session.commit()

        while True:
            try:
                user_input = typer.prompt("You")
            except (KeyboardInterrupt, EOFError):
                break
            if user_input.lower() in ("quit", "exit", "q"):
                break

            add_message(session, chat_sess.id, "user", user_input)
            response = ask_advisor(session, MUNI_BONDS_SYSTEM_PROMPT, user_input)
            add_message(session, chat_sess.id, "assistant", response)
            session.commit()

            console.print(f"\n[bold green]Advisor:[/bold green] {response}\n")


@app.command()
def report(period: str = typer.Option("Q1", "--period", help="Report period")):
    """Generate a full narrative financial report."""
    from finbot.db.database import get_session
    from finbot.llm.analyst import ask_advisor, build_financial_snapshot
    from finbot.llm.prompts import REPORT_SYSTEM_PROMPT

    with get_session() as session:
        snapshot = build_financial_snapshot(session)
        prompt = f"Generate a {period} financial report based on this data:\n\n{snapshot}"
        response = ask_advisor(session, REPORT_SYSTEM_PROMPT, prompt)
        console.print(response)


@app.command()
def backup(restore: str | None = typer.Option(None, "--restore", help="Restore from backup file")):
    """Backup or restore the encrypted database."""
    import shutil
    from datetime import datetime

    from finbot.config import settings

    if restore:
        from pathlib import Path
        src = Path(restore)
        if not src.exists():
            console.print(f"[red]Backup file not found: {restore}[/red]")
            raise typer.Exit(1)
        shutil.copy2(src, settings.db_path)
        console.print(f"[green]Database restored from {restore}[/green]")
    else:
        settings.ensure_dirs()
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = settings.backups_dir / f"finbot_backup_{timestamp}.db"
        shutil.copy2(settings.db_path, dest)
        console.print(f"[green]Backup created: {dest}[/green]")


@app.command()
def clear(
    transactions: bool = typer.Option(False, "--transactions", help="Delete all transactions"),
    holdings: bool = typer.Option(False, "--holdings", help="Delete all holdings"),
    tax: bool = typer.Option(False, "--tax", help="Delete all tax documents"),
    chats: bool = typer.Option(False, "--chats", help="Delete all chat sessions"),
    budgets: bool = typer.Option(False, "--budgets", help="Delete budgets, goals, debts"),
    audit_log: bool = typer.Option(False, "--audit", help="Delete audit log"),
    all_data: bool = typer.Option(False, "--all", help="Delete everything (backup first)"),
):
    """Clear data from the database (selective or full)."""
    from finbot.db.database import get_session, init_db
    from finbot.models.audit_log import AuditLog
    from finbot.models.budget import Budget
    from finbot.models.chat_session import ChatMessage, ChatSession
    from finbot.models.debt import Debt
    from finbot.models.goal import Goal
    from finbot.models.holding import Holding, MuniBondDetail
    from finbot.models.snapshot import Snapshot
    from finbot.models.tax_document import TaxDocument, TaxLineItem
    from finbot.models.transaction import Transaction
    from finbot.security.audit import create_audit_entry

    init_db()

    if not any([transactions, holdings, tax, chats, budgets, audit_log, all_data]):
        console.print("[yellow]Specify what to clear: --transactions, --holdings, --tax, --chats, --budgets, --audit, or --all[/yellow]")
        raise typer.Exit(1)

    if all_data:
        console.print("[bold red]This will delete ALL financial data.[/bold red]")
        if not typer.confirm("Create a backup first?", default=True):
            raise typer.Abort()
        import shutil
        from datetime import datetime

        from finbot.config import settings
        settings.ensure_dirs()
        ts = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest = settings.backups_dir / f"pre_clear_{ts}.db"
        shutil.copy2(settings.db_path, dest)
        console.print(f"  Backup saved: {dest}")
        transactions = holdings = tax = chats = budgets = True

    if not typer.confirm("Are you sure?", default=False):
        raise typer.Abort()

    with get_session() as session:
        cleared = []
        if transactions:
            n = session.query(Transaction).delete()
            session.query(Snapshot).delete()
            cleared.append(f"transactions ({n})")
        if holdings:
            session.query(MuniBondDetail).delete()
            n = session.query(Holding).delete()
            cleared.append(f"holdings ({n})")
        if tax:
            session.query(TaxLineItem).delete()
            n = session.query(TaxDocument).delete()
            cleared.append(f"tax documents ({n})")
        if chats:
            session.query(ChatMessage).delete()
            n = session.query(ChatSession).delete()
            cleared.append(f"chat sessions ({n})")
        if budgets:
            session.query(Budget).delete()
            session.query(Goal).delete()
            session.query(Debt).delete()
            cleared.append("budgets/goals/debts")
        if audit_log:
            n = session.query(AuditLog).delete()
            cleared.append(f"audit log ({n})")
        else:
            create_audit_entry(session, "clear", details={"cleared": cleared})
        session.commit()

    console.print(f"[green]Cleared: {', '.join(cleared)}[/green]")


@app.command()
def pin(
    action: str = typer.Argument(..., help="set or remove"),
):
    """Manage session PIN (set or remove)."""
    from finbot.db.database import get_session, init_db
    from finbot.models.user_profile import UserProfile
    from finbot.web.auth import hash_pin

    init_db()

    if action == "set":
        new_pin = typer.prompt("Enter new PIN (4+ characters)", hide_input=True)
        confirm = typer.prompt("Confirm PIN", hide_input=True)
        if new_pin != confirm:
            console.print("[red]PINs do not match.[/red]")
            raise typer.Exit(1)
        if len(new_pin) < 4:
            console.print("[red]PIN must be at least 4 characters.[/red]")
            raise typer.Exit(1)
        with get_session() as session:
            p = session.query(UserProfile).first()
            if not p:
                p = UserProfile()
                session.add(p)
            p.pin_hash = hash_pin(new_pin)
            session.commit()
        console.print("[green]PIN set. Session auth enabled.[/green]")

    elif action == "remove":
        with get_session() as session:
            p = session.query(UserProfile).first()
            if p and p.pin_hash:
                p.pin_hash = None
                session.commit()
                console.print("[green]PIN removed. Session auth disabled.[/green]")
            else:
                console.print("[dim]No PIN was set.[/dim]")
    else:
        console.print("[red]Usage: finbot pin set  or  finbot pin remove[/red]")


@app.command()
def export(
    fmt: str = typer.Option("csv", "--format", help="csv or pdf"),
    category: str = typer.Option("transactions", "--category", help="transactions, holdings, or tax"),
):
    """Export data as CSV or generate a text report."""
    import pathlib

    from finbot.db.database import get_session, init_db
    from finbot.export.csv_export import export_holdings, export_tax_data, export_transactions
    from finbot.export.pdf_report import generate_report_text

    init_db()

    if fmt == "pdf":
        with get_session() as session:
            report = generate_report_text(session)
        out = pathlib.Path("finbot_report.md")
        out.write_text(report)
        console.print(f"[green]Report saved: {out}[/green]")
        return

    with get_session() as session:
        if category == "transactions":
            content = export_transactions(session)
            out = pathlib.Path("finbot_transactions.csv")
        elif category == "holdings":
            content = export_holdings(session)
            out = pathlib.Path("finbot_holdings.csv")
        elif category == "tax":
            content = export_tax_data(session)
            out = pathlib.Path("finbot_tax_data.csv")
        else:
            console.print(f"[red]Unknown category: {category}. Use transactions, holdings, or tax.[/red]")
            raise typer.Exit(1)

    out.write_text(content)
    console.print(f"[green]Exported: {out}[/green]")


@app.command(name="help")
def help_cmd(command: str | None = typer.Argument(None, help="Command to get help for")):
    """Show quick help for a CLI command."""
    import subprocess
    import sys

    if command:
        subprocess.run([sys.executable, "-m", "finbot.cli.main", command, "--help"])
    else:
        subprocess.run([sys.executable, "-m", "finbot.cli.main", "--help"])
