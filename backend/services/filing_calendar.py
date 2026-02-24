"""Generate BIR filing calendar based on registered tax obligations."""

from datetime import date, timedelta

# BIR filing deadlines (day of month, relative to period end)
FILING_RULES = [
    {
        "form": "BIR 2550M",
        "name": "Monthly VAT Declaration",
        "frequency": "monthly",
        "deadline_day": 20,  # 20th of following month
        "months_after": 1,
    },
    {
        "form": "BIR 2550Q",
        "name": "Quarterly VAT Return",
        "frequency": "quarterly",
        "deadline_day": 25,  # 25th of month following quarter
        "quarter_months": [1, 4, 7, 10],  # months when due (for Q4, Q1, Q2, Q3)
    },
    {
        "form": "BIR 1601-C",
        "name": "Monthly Withholding Tax on Compensation",
        "frequency": "monthly",
        "deadline_day": 10,
        "months_after": 1,
    },
    {
        "form": "BIR 0619-E",
        "name": "Monthly Expanded Withholding Tax",
        "frequency": "monthly",
        "deadline_day": 10,
        "months_after": 1,
    },
    {
        "form": "BIR 1601-EQ",
        "name": "Quarterly Expanded Withholding Tax",
        "frequency": "quarterly",
        "deadline_day": 25,  # last day of month following quarter (simplified to 25th)
        "quarter_months": [1, 4, 7, 10],
    },
    {
        "form": "BIR 1702Q",
        "name": "Quarterly Income Tax (Corporate)",
        "frequency": "quarterly",
        "deadline_day": 60,  # 60 days after quarter end (special handling)
        "quarter_months": [5, 8, 11],  # Q1(May), Q2(Aug), Q3(Nov) — Q4 is annual
        "special": "60_days_after_quarter",
    },
    {
        "form": "BIR 1702",
        "name": "Annual Income Tax (Corporate)",
        "frequency": "annual",
        "deadline_month": 4,
        "deadline_day": 15,
    },
    {
        "form": "BIR 1701",
        "name": "Annual Income Tax (Individual)",
        "frequency": "annual",
        "deadline_month": 4,
        "deadline_day": 15,
    },
    {
        "form": "BIR 0605",
        "name": "Annual Registration Fee",
        "frequency": "annual",
        "deadline_month": 1,
        "deadline_day": 31,
    },
    {
        "form": "BIR 1604-CF",
        "name": "Annual Information Return (Compensation)",
        "frequency": "annual",
        "deadline_month": 1,
        "deadline_day": 31,
    },
    {
        "form": "BIR 2316",
        "name": "Certificate of Compensation Payment/Tax Withheld",
        "frequency": "annual",
        "deadline_month": 1,
        "deadline_day": 31,
    },
]


def _last_day_of_month(year: int, month: int) -> int:
    """Return the last day of the given month."""
    if month == 12:
        return 31
    next_month = date(year, month + 1, 1)
    return (next_month - timedelta(days=1)).day


def generate_filing_calendar(
    year: int,
    months_ahead: int = 3,
) -> list[dict]:
    """Generate upcoming filing deadlines for a given year.

    Returns a list of filing events sorted by deadline date.
    """
    today = date.today()
    end_date = today + timedelta(days=months_ahead * 31)
    events: list[dict] = []

    for rule in FILING_RULES:
        freq = rule["frequency"]

        if freq == "monthly":
            # Generate for each month
            for month in range(1, 13):
                # Period is the previous month
                period_month = month - 1 if month > 1 else 12
                period_year = year if month > 1 else year - 1
                deadline_month = month
                deadline_year = year

                day = min(rule["deadline_day"], _last_day_of_month(deadline_year, deadline_month))
                deadline = date(deadline_year, deadline_month, day)

                if today - timedelta(days=30) <= deadline <= end_date:
                    events.append({
                        "form": rule["form"],
                        "name": rule["name"],
                        "period": f"{period_year}-{period_month:02d}",
                        "deadline": deadline.isoformat(),
                        "days_remaining": (deadline - today).days,
                        "status": "overdue" if deadline < today else "upcoming" if (deadline - today).days <= 7 else "scheduled",
                    })

        elif freq == "quarterly":
            quarter_months = rule.get("quarter_months", [1, 4, 7, 10])
            special = rule.get("special", "")

            for qm in quarter_months:
                deadline_year = year

                if special == "60_days_after_quarter":
                    # 60 days after quarter end
                    quarter_end_month = qm - 2  # e.g., May due → Q1 ends March
                    if quarter_end_month <= 0:
                        quarter_end_month += 12
                        deadline_year = year - 1
                    quarter_end = date(deadline_year, quarter_end_month, _last_day_of_month(deadline_year, quarter_end_month))
                    deadline = quarter_end + timedelta(days=60)
                else:
                    day = min(rule["deadline_day"], _last_day_of_month(deadline_year, qm))
                    deadline = date(deadline_year, qm, day)

                # Determine period
                period_quarter = (qm - 1) // 3  # rough quarter mapping
                period_label = f"{year} Q{max(period_quarter, 1)}"

                if today - timedelta(days=30) <= deadline <= end_date:
                    events.append({
                        "form": rule["form"],
                        "name": rule["name"],
                        "period": period_label,
                        "deadline": deadline.isoformat(),
                        "days_remaining": (deadline - today).days,
                        "status": "overdue" if deadline < today else "upcoming" if (deadline - today).days <= 7 else "scheduled",
                    })

        elif freq == "annual":
            dm = rule.get("deadline_month", 4)
            dd = min(rule.get("deadline_day", 15), _last_day_of_month(year, dm))
            deadline = date(year, dm, dd)

            if today - timedelta(days=30) <= deadline <= end_date:
                events.append({
                    "form": rule["form"],
                    "name": rule["name"],
                    "period": str(year - 1),  # Annual returns are for previous year
                    "deadline": deadline.isoformat(),
                    "days_remaining": (deadline - today).days,
                    "status": "overdue" if deadline < today else "upcoming" if (deadline - today).days <= 7 else "scheduled",
                })

    # Sort by deadline
    events.sort(key=lambda e: e["deadline"])
    return events
