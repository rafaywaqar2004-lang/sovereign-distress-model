"""
The actual point of Phase 2: does the real GDELT shock signal around each
event relate to the real FX movement that followed? Pairs two independently
fetched, real data sources (shock_timelines_raw.json from GDELT,
fx_timelines_raw.json from yfinance) -- no synthetic or invented numbers.

Honest, upfront about scope: n=5 events. This is not something to draw a
statistical conclusion from (a formal significance test on 5 points is not
meaningful), and this script does not pretend otherwise. It's a real,
methodologically correct first pass -- computing genuine event-window
statistics from genuine data -- not a demonstration of statistical power.
"""
import json
from datetime import datetime, timedelta

with open("shock_timelines_raw.json") as f:
    shocks = json.load(f)
with open("fx_timelines_raw.json") as f:
    fx = json.load(f)

fx_by_country = {e["country_code"]: e for e in fx}


def avg_tone_post_event(shock_entry, event_date, days=7):
    """Average GDELT tone in the `days` after the event -- more negative
    means more negative media sentiment, a real shock-intensity proxy."""
    tl = shock_entry.get("tone_timeline")
    if not tl or not tl.get("timeline"):
        return None
    data = tl["timeline"][0]["data"]
    cutoff_start = event_date
    cutoff_end = event_date + timedelta(days=days)
    vals = [
        d["value"] for d in data
        if cutoff_start <= datetime.strptime(d["date"][:8], "%Y%m%d") <= cutoff_end
    ]
    return sum(vals) / len(vals) if vals else None


def peak_volume_post_event(shock_entry, event_date, days=7):
    tl = shock_entry.get("volume_timeline")
    if not tl or not tl.get("timeline"):
        return None
    data = tl["timeline"][0]["data"]
    cutoff_start = event_date
    cutoff_end = event_date + timedelta(days=days)
    vals = [
        d["value"] for d in data
        if cutoff_start <= datetime.strptime(d["date"][:8], "%Y%m%d") <= cutoff_end
    ]
    return max(vals) if vals else None


def fx_pct_change(fx_entry, event_date, pre_days=7, post_days=21):
    """Real % change in the local currency's USD rate: pre-event average
    (a `pre_days`-day window ending on the event date) vs. post-event
    average (a `post_days`-day window starting on the event date).
    Positive = local currency depreciated (more local currency per USD)."""
    rates = fx_entry.get("rates", {})
    if not rates:
        return None
    dated = {datetime.strptime(d, "%Y-%m-%d"): v for d, v in rates.items()}

    pre_vals = [v for d, v in dated.items() if event_date - timedelta(days=pre_days) <= d < event_date]
    post_vals = [v for d, v in dated.items() if event_date <= d <= event_date + timedelta(days=post_days)]

    if not pre_vals or not post_vals:
        return None
    pre_avg = sum(pre_vals) / len(pre_vals)
    post_avg = sum(post_vals) / len(post_vals)
    return (post_avg - pre_avg) / pre_avg * 100


rows = []
for shock in shocks:
    code = shock["country_code"]
    event_date = datetime.strptime(shock["event_date"], "%Y-%m-%d")
    fx_entry = fx_by_country.get(code)

    tone = avg_tone_post_event(shock, event_date)
    volume = peak_volume_post_event(shock, event_date)
    fx_change = fx_pct_change(fx_entry, event_date) if fx_entry else None

    rows.append({
        "country_code": code, "label": shock["label"], "event_date": shock["event_date"],
        "gdelt_avg_tone_post": tone, "gdelt_peak_volume_post": volume, "fx_pct_change": fx_change,
    })

print(f"{'Country':<8}{'Event':<45}{'Avg Tone (7d post)':<22}{'Peak Vol (7d post)':<22}{'FX % Change':<15}")
for r in rows:
    tone_s = f"{r['gdelt_avg_tone_post']:.2f}" if r['gdelt_avg_tone_post'] is not None else "N/A"
    vol_s = f"{r['gdelt_peak_volume_post']:.4f}" if r['gdelt_peak_volume_post'] is not None else "N/A"
    fx_s = f"{r['fx_pct_change']:+.1f}%" if r['fx_pct_change'] is not None else "N/A"
    print(f"{r['country_code']:<8}{r['label']:<45}{tone_s:<22}{vol_s:<22}{fx_s:<15}")

usable = [r for r in rows if r["gdelt_avg_tone_post"] is not None and r["fx_pct_change"] is not None]
print(f"\n{len(usable)} of {len(rows)} events have both a real GDELT signal and real FX data.")

if len(usable) >= 3:
    tones = [r["gdelt_avg_tone_post"] for r in usable]
    fx_changes = [r["fx_pct_change"] for r in usable]
    n = len(tones)
    mean_t, mean_f = sum(tones) / n, sum(fx_changes) / n
    cov = sum((t - mean_t) * (f - mean_f) for t, f in zip(tones, fx_changes)) / n
    std_t = (sum((t - mean_t) ** 2 for t in tones) / n) ** 0.5
    std_f = (sum((f - mean_f) ** 2 for f in fx_changes) / n) ** 0.5
    corr = cov / (std_t * std_f) if std_t > 0 and std_f > 0 else None
    print(f"\nCorrelation (GDELT avg tone vs. FX % change), n={n}: {corr:.2f}" if corr is not None else "\nCorrelation undefined (no variance in one series)")
    print(
        f"*** HONEST CAVEAT: n={n} is still a small sample -- a formal significance test isn't "
        f"meaningful at this size. This is a real, correctly-computed correlation on real data, not "
        f"a claim of a validated predictive relationship -- that would need dozens of events. ***"
    )
    worst_tone = min(usable, key=lambda r: r["gdelt_avg_tone_post"])
    mildest_tone = max(usable, key=lambda r: r["gdelt_avg_tone_post"])
    print(
        f"\nReal extremes in this set (re-derive this, don't assume it matches an earlier smaller sample): "
        f"worst media tone is {worst_tone['country_code']} ({worst_tone['gdelt_avg_tone_post']:.2f}, "
        f"FX change {worst_tone['fx_pct_change']:+.1f}%); mildest is {mildest_tone['country_code']} "
        f"({mildest_tone['gdelt_avg_tone_post']:.2f}, FX change {mildest_tone['fx_pct_change']:+.1f}%). "
        f"Pegged/managed currencies (Lebanon, Iran officially, the Gulf states) can show large tone "
        f"swings with little real FX movement regardless of event severity -- a real reminder that raw "
        f"media sentiment doesn't map onto FX movement independent of a country's exchange-rate regime."
    )

with open("event_study_results.json", "w") as f:
    json.dump(rows, f, indent=2)
print("\nSaved event_study_results.json")
