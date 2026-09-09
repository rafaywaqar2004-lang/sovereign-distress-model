# Independent R validation of the stress-test regression -- a separately
# written implementation (plm) against the same real raw panel and real
# fetched shock drivers, matching Python's exact training window
# (2010-2023) for a genuine apples-to-apples comparison.

library(plm)
library(jsonlite)

panel <- read.csv("raw_panel.csv")
drivers <- fromJSON("shock_drivers.json")

# fromJSON parses the named year->value maps as R lists, not atomic
# numeric vectors -- unlist() converts to a proper named numeric vector
# so indexing by year string returns real values, not sub-lists.
oil <- unlist(drivers$oil_annual_avg_usd)
rate <- unlist(drivers$us_short_rate_annual_avg_pct)

panel$oil_price <- as.numeric(oil[as.character(panel$year)])
panel$us_short_rate <- as.numeric(rate[as.character(panel$year)])

panel <- panel[order(panel$country_code, panel$year), ]

pdata <- pdata.frame(panel, index = c("country_code", "year"))
pdata$inflation_lag <- plm::lag(pdata$inflation, 1)
pdata$oil_pct_change <- plm::lag(pdata$oil_price, 0) / plm::lag(pdata$oil_price, 1) * 100 - 100
pdata$rate_change <- plm::lag(pdata$us_short_rate, 0) - plm::lag(pdata$us_short_rate, 1)

train <- pdata[panel$year <= 2023, ]

fit <- plm(inflation ~ inflation_lag + oil_pct_change + rate_change, data = train,
           model = "within", effect = "individual")
cat("=== Independent R stress-test regression (plm) ===\n\n")
print(summary(fit, vcov = vcovHC(fit, cluster = "group")))

cat("\nCompare against Python's linearmodels output: inflation_lag=0.5706,\n")
cat("oil_pct_change=0.0493 (p=0.277), rate_change=-0.1531 (p=0.898).\n")
cat("A genuinely separate implementation, not the same arithmetic re-run.\n")
