"""Social Security benefit estimator and claiming strategy optimizer."""
from __future__ import annotations

from dataclasses import dataclass

# 2025 PIA formula bend points
_BEND_1 = 1226
_BEND_2 = 7391

# Full retirement age for those born 1960+
_FRA = 67

# SS tax wage base 2025
SS_WAGE_BASE = 168600

# Early/late claiming adjustment factors per month
_EARLY_REDUCTION_FIRST_36 = 5 / 900  # 5/9 of 1% per month for first 36 months
_EARLY_REDUCTION_AFTER_36 = 5 / 1200  # 5/12 of 1% per month beyond 36
_DELAYED_CREDIT_PER_MONTH = 2 / 300  # 2/3 of 1% per month (8% per year)


@dataclass
class SSEstimate:
    claiming_age: int
    monthly_benefit: float
    annual_benefit: float
    adjustment_pct: float


@dataclass
class SSOptimization:
    estimates: list[SSEstimate]
    break_even_ages: dict[str, int | None]
    optimal_age: int
    optimal_monthly: float
    lifetime_benefits: dict[int, float]
    recommendation: str
    spousal_benefit: float | None


def compute_aime(annual_salary: float, years_worked: int) -> float:
    """Simplified AIME: assumes constant real salary over career."""
    credited_years = min(years_worked, 35)
    total_earnings = annual_salary * credited_years
    aime = total_earnings / 420  # 35 years * 12 months
    return aime


def compute_pia(aime: float) -> float:
    """Apply the 2025 PIA bend-point formula."""
    if aime <= _BEND_1:
        return aime * 0.90
    elif aime <= _BEND_2:
        return _BEND_1 * 0.90 + (aime - _BEND_1) * 0.32
    else:
        return _BEND_1 * 0.90 + (_BEND_2 - _BEND_1) * 0.32 + (aime - _BEND_2) * 0.15


def claiming_adjustment(claiming_age: int) -> float:
    """Return the adjustment factor (1.0 = FRA, <1.0 = early, >1.0 = delayed)."""
    months_from_fra = (claiming_age - _FRA) * 12

    if months_from_fra == 0:
        return 1.0
    elif months_from_fra < 0:
        early_months = abs(months_from_fra)
        if early_months <= 36:
            reduction = early_months * _EARLY_REDUCTION_FIRST_36
        else:
            reduction = 36 * _EARLY_REDUCTION_FIRST_36 + (early_months - 36) * _EARLY_REDUCTION_AFTER_36
        return 1.0 - reduction
    else:
        delayed_months = months_from_fra
        credit = delayed_months * _DELAYED_CREDIT_PER_MONTH
        return 1.0 + credit


def estimate_benefits(
    annual_salary: float,
    years_worked: int,
    birth_year: int | None = None,
) -> list[SSEstimate]:
    """Estimate monthly SS benefit at each claiming age from 62 to 70."""
    aime = compute_aime(annual_salary, years_worked)
    pia = compute_pia(aime)

    estimates = []
    for age in range(62, 71):
        factor = claiming_adjustment(age)
        monthly = round(pia * factor, 2)
        estimates.append(SSEstimate(
            claiming_age=age,
            monthly_benefit=monthly,
            annual_benefit=round(monthly * 12, 2),
            adjustment_pct=round((factor - 1.0) * 100, 1),
        ))
    return estimates


def optimize_claiming(
    annual_salary: float,
    years_worked: int,
    current_age: int,
    life_expectancy: int = 85,
    spouse_salary: float | None = None,
    spouse_years_worked: int | None = None,
    other_annual_income: float = 0,
) -> SSOptimization:
    """Run full claiming strategy analysis."""
    estimates = estimate_benefits(annual_salary, years_worked)
    pia = compute_pia(compute_aime(annual_salary, years_worked))

    # Lifetime benefit comparison
    lifetime = {}
    for est in estimates:
        if est.claiming_age < current_age:
            continue
        years_collecting = life_expectancy - est.claiming_age
        lifetime[est.claiming_age] = round(est.annual_benefit * max(years_collecting, 0), 2)

    # Break-even: age 62 vs FRA, age 62 vs 70, FRA vs 70
    def _break_even(early_age: int, late_age: int) -> int | None:
        early_est = next((e for e in estimates if e.claiming_age == early_age), None)
        late_est = next((e for e in estimates if e.claiming_age == late_age), None)
        if not early_est or not late_est:
            return None
        cumulative_early = 0.0
        cumulative_late = 0.0
        for age in range(early_age, life_expectancy + 1):
            if age >= early_age:
                cumulative_early += early_est.annual_benefit
            if age >= late_age:
                cumulative_late += late_est.annual_benefit
            if cumulative_late > cumulative_early and age > late_age:
                return age
        return None

    break_evens = {
        "62_vs_67": _break_even(62, 67),
        "62_vs_70": _break_even(62, 70),
        "67_vs_70": _break_even(67, 70),
    }

    # Optimal = max lifetime benefits
    optimal_age = max(lifetime, key=lifetime.get) if lifetime else 67
    optimal_est = next((e for e in estimates if e.claiming_age == optimal_age), estimates[5])

    # Spousal benefit
    spousal = None
    if spouse_salary and spouse_years_worked:
        spouse_aime = compute_aime(spouse_salary, spouse_years_worked)
        spouse_pia = compute_pia(spouse_aime)
        if spouse_pia < pia * 0.5:
            spousal = round(pia * 0.5, 2)

    # Recommendation
    if optimal_age == 70:
        rec = (
            f"Delaying to age 70 maximizes your lifetime benefits (${lifetime.get(70, 0):,.0f} total). "
            f"Your monthly benefit increases from ${estimates[0].monthly_benefit:,.0f} at 62 to "
            f"${estimates[-1].monthly_benefit:,.0f} at 70 — a {estimates[-1].adjustment_pct:+.0f}% increase. "
            f"The break-even age vs claiming at 62 is {break_evens.get('62_vs_70', 'N/A')}. "
            "This aligns with the Boglehead approach of maximizing guaranteed inflation-adjusted income."
        )
    elif optimal_age == 67:
        rec = (
            f"Claiming at your full retirement age (67) provides ${optimal_est.monthly_benefit:,.0f}/month. "
            "This balances lifetime benefits with earlier access to funds. "
            "Consider delaying to 70 if you have other income sources to bridge the gap."
        )
    else:
        rec = (
            f"Based on your life expectancy of {life_expectancy}, claiming at {optimal_age} "
            f"maximizes total lifetime benefits (${lifetime.get(optimal_age, 0):,.0f}). "
            "Consider your health, other income sources, and whether you plan to continue working."
        )

    return SSOptimization(
        estimates=estimates,
        break_even_ages=break_evens,
        optimal_age=optimal_age,
        optimal_monthly=optimal_est.monthly_benefit,
        lifetime_benefits=lifetime,
        recommendation=rec,
        spousal_benefit=spousal,
    )
