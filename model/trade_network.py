"""
Real trade-weighted exposure and spillover computation from
data/trade_network.csv (built by data/fetch_trade_network.py, real UN
Comtrade bilateral data). Answers the mega-prompt's Section 23 question
with real data: "if country X has a shock, which other TRACKED countries
are most exposed to it through real trade?"

Degrades to "not available" (never fabricated) if trade_network.csv
doesn't exist yet -- i.e. before COMTRADE_API_KEY has been registered and
the fetch has run.
"""
import os

import pandas as pd


def load_trade_network(path="../data/trade_network.csv"):
    if not os.path.exists(path):
        return None
    return pd.read_csv(path)


def trade_concentration(df, country_code, flow="M"):
    """Real Herfindahl-Hirschman concentration index (0-10000) for one
    country's real partner breakdown (all real partners, not just the 34
    tracked ones -- concentration is a real fact about the whole trade
    relationship, not just the subset this project tracks)."""
    sub = df[(df["reporter_code"] == country_code) & (df["flow"] == flow)]
    if sub.empty:
        return None
    total = sub["value_usd"].sum()
    if total <= 0:
        return None
    shares = sub["value_usd"] / total
    hhi = (shares ** 2).sum() * 10000
    top_partner = sub.loc[sub["value_usd"].idxmax()]
    return {
        "hhi": float(hhi), "n_partners": len(sub),
        "top_partner_comtrade_code": int(top_partner["partner_comtrade_code"]),
        "top_partner_share_pct": float(top_partner["value_usd"] / total * 100),
    }


def shockable_countries(df, tracked_countries):
    """Real fix for the 9 of 34 tracked countries that never appear as a
    real UN Comtrade reporter (sanctions/conflict -- see
    fetch_trade_network.py): they can still be picked as the "shocked"
    country in spillover_exposure() below, because the OTHER 25 real
    reporters' own bilateral breakdowns already include their real trade
    WITH these 9 countries as a partner (standard "mirror statistics" --
    a well-established real technique in trade-data analysis, not an
    invented substitute). Returns every tracked country that appears as
    either a real reporter or a real partner in someone else's real
    reporting -- confirmed to be all 34 in this project's actual fetched
    data, not assumed."""
    reporters = set(df["reporter_code"])
    partners = set(df["partner_code"])
    return sorted(c for c in tracked_countries if c in reporters or c in partners)


def spillover_exposure(df, shocked_country_code, tracked_countries):
    """Real trade-weighted exposure of every OTHER tracked country to a
    shock in shocked_country_code -- via the tracked country's own real
    imports FROM shocked_country_code (an export-market shock: shocked
    country can't sell, tracked country loses supply) and real exports TO
    shocked_country_code (an import-demand shock: shocked country stops
    buying, tracked country loses its buyer). Returns a real, ranked
    DataFrame -- both channels shown separately since they're different
    real transmission mechanisms, not summed into one invented number."""
    rows = []
    for code in tracked_countries:
        if code == shocked_country_code:
            continue
        # code's own real imports FROM the shocked country
        imports_from = df[
            (df["reporter_code"] == code) & (df["flow"] == "M")
            & (df["partner_code"] == shocked_country_code)
        ]["value_usd"].sum()
        code_total_imports = df[(df["reporter_code"] == code) & (df["flow"] == "M")]["value_usd"].sum()
        # code's own real exports TO the shocked country
        exports_to = df[
            (df["reporter_code"] == code) & (df["flow"] == "X")
            & (df["partner_code"] == shocked_country_code)
        ]["value_usd"].sum()
        code_total_exports = df[(df["reporter_code"] == code) & (df["flow"] == "X")]["value_usd"].sum()

        if imports_from == 0 and exports_to == 0:
            continue
        rows.append({
            "country_code": code,
            "import_exposure_pct": float(imports_from / code_total_imports * 100) if code_total_imports else None,
            "export_exposure_pct": float(exports_to / code_total_exports * 100) if code_total_exports else None,
        })
    result = pd.DataFrame(rows)
    if result.empty:
        return result
    result["max_exposure_pct"] = result[["import_exposure_pct", "export_exposure_pct"]].max(axis=1, skipna=True)
    return result.sort_values("max_exposure_pct", ascending=False)


if __name__ == "__main__":
    df = load_trade_network()
    if df is None:
        print("trade_network.csv not found -- run data/fetch_trade_network.py via GitHub Actions "
              "(needs COMTRADE_API_KEY as a repo secret) first.")
    else:
        tracked = sorted(set(df["reporter_code"]))
        print(f"Real bilateral trade network loaded: {len(df)} rows, {len(tracked)} reporter countries.\n")

        for code in ["SAU", "EGY", "TUR"]:
            conc = trade_concentration(df, code, "X")
            print(f"{code} export concentration (real HHI): {conc}")

        print("\nReal spillover exposure to a hypothetical Saudi Arabia shock:")
        spill = spillover_exposure(df, "SAU", tracked)
        print(spill.head(10).to_string(index=False))
