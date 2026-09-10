# Independent R validation of the stress-test regression -- a separately
# written implementation (plm) against the same real raw panel and real
# fetched shock drivers, matching Python's exact training window
# (2010-2023) for a genuine apples-to-apples comparison.
#
# Extended to the same 4-driver specification as stress_test.py: oil,
# US short rate, VIX change, and US Dollar Index % change (the latter two
# from fetch_global_conditions.py -> global_conditions.json).

library(plm)
library(jsonlite)

panel <- read.csv("raw_panel.csv")
drivers <- fromJSON("shock_drivers.json")
global_conditions <- fromJSON("global_conditions.json")

# fromJSON parses the named year->value maps as R lists, not atomic
# numeric vectors -- unlist() converts to a proper named numeric vector
# so indexing by year string returns real values, not sub-lists.
oil <- unlist(drivers$oil_annual_avg_usd)
rate <- unlist(drivers$us_short_rate_annual_avg_pct)
vix <- unlist(global_conditions$vix)
dxy <- unlist(global_conditions$dollar_index)

panel$oil_price <- as.numeric(oil[as.character(panel$year)])
panel$us_short_rate <- as.numeric(rate[as.character(panel$year)])
panel$vix <- as.numeric(vix[as.character(panel$year)])
panel$dxy <- as.numeric(dxy[as.character(panel$year)])

panel <- panel[order(panel$country_code, panel$year), ]

pdata <- pdata.frame(panel, index = c("country_code", "year"))
pdata$inflation_lag <- plm::lag(pdata$inflation, 1)
pdata$oil_pct_change <- plm::lag(pdata$oil_price, 0) / plm::lag(pdata$oil_price, 1) * 100 - 100
pdata$rate_change <- plm::lag(pdata$us_short_rate, 0) - plm::lag(pdata$us_short_rate, 1)
pdata$vix_change <- plm::lag(pdata$vix, 0) - plm::lag(pdata$vix, 1)
pdata$dxy_pct_change <- plm::lag(pdata$dxy, 0) / plm::lag(pdata$dxy, 1) * 100 - 100

train <- pdata[panel$year <= 2023, ]

fit <- plm(inflation ~ inflation_lag + oil_pct_change + rate_change + vix_change + dxy_pct_change,
           data = train, model = "within", effect = "individual")
cat("=== Independent R stress-test regression (plm) ===\n\n")
print(summary(fit, vcov = vcovHC(fit, cluster = "group")))

cat("\nCompare against Python's linearmodels output: inflation_lag=0.5713,\n")
cat("oil_pct_change=0.0420 (p=0.283), rate_change=-0.2050 (p=0.868),\n")
cat("vix_change=-0.0644 (p=0.640), dxy_pct_change=-0.0487 (p=0.742).\n")
cat("A genuinely separate implementation, not the same arithmetic re-run.\n")
