"""Compute Yongsik's personal cash flow from data/ledger.json rules and monthly ad revenue.

Single source of money rules: opening balance, allowance, AdSense payout timing, 7:3 split,
monthly-average FX and recorded spending. No network or git.
"""
from decimal import Decimal, ROUND_HALF_UP


def won(value):
    return int(Decimal(str(value)).quantize(Decimal('1'), rounding=ROUND_HALF_UP))


def next_month(key):
    y, m = map(int, key.split('-'))
    return f'{y + (m == 12)}-{1 if m == 12 else m + 1:02d}'


def compute(monthly_rows, ledger):
    """Return {month: result} for rows sorted by month. Each row needs month and ad_revenue_usd."""
    rules = ledger['rules']
    opening, allowance_rule = rules['opening'], rules['allowance']
    adsense, split, fx = rules['adsense'], rules['split'], rules['fx']['krw_per_usd']
    spending = {}
    for item in ledger['spending']:
        spending[item['month']] = spending.get(item['month'], 0) + item['amount_krw']

    results = {}
    cash = 0
    unpaid = Decimal('0')
    scheduled = {}
    first_receipt_month = None
    received_total = yongsik_total = mother_total = 0
    for row in sorted(monthly_rows, key=lambda r: r['month']):
        key = row['month']
        # 1) payout at the end of this month (amount fixed at the previous month end)
        receipt = scheduled.pop(key, Decimal('0'))
        if receipt is None:
            receipt_usd = receipt_krw = to_yongsik = to_mother = None
        else:
            receipt_usd = float(receipt)
            receipt_krw = won(receipt * Decimal(str(fx[key]))) if receipt else 0
            to_yongsik = won(Decimal(receipt_krw) * Decimal(str(split['yongsik'])))
            to_mother = receipt_krw - to_yongsik
            if receipt and first_receipt_month is None:
                first_receipt_month = key
        # 2) allowance: received every month until the month of the first ad receipt
        allowance = allowance_rule['amount_krw'] if key >= allowance_rule['from_month'] and (
            first_receipt_month is None or key <= first_receipt_month) else 0
        opening_krw = opening['amount_krw'] if key == opening['date'][:7] else 0
        untracked_from = ledger.get('spending_untracked_from')
        spent = spending.get(key) if untracked_from and key >= untracked_from else spending.get(key, 0)
        if cash is not None and to_yongsik is not None and spent is not None:
            cash = cash + opening_krw + allowance + to_yongsik - spent
        else:
            cash = None
        if receipt_krw is not None and received_total is not None:
            received_total += receipt_krw
            yongsik_total += to_yongsik
            mother_total += to_mother
        else:
            received_total = yongsik_total = mother_total = None
        # 3) month-end AdSense balance and next payout
        revenue = row['ad_revenue_usd']
        if revenue is None or unpaid is None or receipt is None:
            unpaid = None
            scheduled[next_month(key)] = None
        else:
            unpaid = unpaid + Decimal(str(revenue)) - receipt
            if unpaid >= adsense['payout_threshold_usd']:
                scheduled[next_month(key)] = unpaid
        results[key] = {
            'scope': 'closed' if key <= ledger['closed_through'] else 'provisional',
            'opening_krw': opening_krw,
            'allowance_krw': allowance,
            'receipt_usd': receipt_usd,
            'fx_krw_per_usd': fx.get(key) if receipt_usd else None,
            'receipt_krw': receipt_krw,
            'fee_krw': adsense['fee_krw'] if receipt_usd else None,
            'to_yongsik_krw': to_yongsik,
            'to_mother_krw': to_mother,
            'spending_krw': spent,
            'cash_end_krw': cash,
            'unpaid_usd': float(unpaid) if unpaid is not None else None,
            'received_total_krw': received_total,
            'yongsik_received_total_krw': yongsik_total,
            'mother_received_total_krw': mother_total,
            'next_payout_usd': (float(scheduled[next_month(key)])
                                if scheduled.get(next_month(key)) is not None else
                                (None if next_month(key) in scheduled else 0.0)),
        }
    return results
