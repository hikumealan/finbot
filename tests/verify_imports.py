"""Quick verification that all modules import and basic computations work."""
from finbot.analysis.investments import fee_impact
from finbot.analysis.muni_bonds import quick_tey
from finbot.analysis.net_worth import compute_net_worth
from finbot.analysis.projections import compound_growth
from finbot.analysis.savings_rate import overall_savings_rate
from finbot.analysis.tax_optimizer import compute_tax_position
from finbot.db.database import get_session, init_db
from finbot.guide.content import GUIDE_SECTIONS, search_guide
from finbot.models import *  # noqa: F403

print("All modules imported successfully")
print(f"Guide sections: {len(GUIDE_SECTIONS)}")

tey = quick_tey(0.035, 0.32, 0.05)
print(f"TEY test (3.5% coupon, 32% fed, 5% state): {tey:.4f}")

impact = fee_impact(100000, 0.0085, 30)
print(f"Fee drag (0.85% vs 0.03%, 30y, $100k): ${impact['fee_drag']:,.0f}")

nominal, real = compound_growth(100000, 12000, 0.07, 30)
print(f"30-year nominal projection: ${nominal[-1]:,.0f}")
print(f"30-year real projection: ${real[-1]:,.0f}")

results = search_guide("tax loss")
print(f"Guide search 'tax loss': {len(results)} results")

# Verify with database
init_db()
with get_session() as session:
    nw = compute_net_worth(session)
    print(f"Net worth from DB: ${nw.net_worth:,.2f}")

    sr = overall_savings_rate(session)
    print(f"Savings rate: {sr:.1f}%")

    tax_pos = compute_tax_position(session, "single", "CA")
    print(f"Tax position computed (gross: ${tax_pos.gross_income:,.2f})")

print("\nAll verifications passed.")
