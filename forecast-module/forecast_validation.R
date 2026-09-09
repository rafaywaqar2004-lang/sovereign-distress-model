# Independent R validation of the panel AR(1) inflation forecast model --
# same discipline as everywhere else in this project: a separately written
# implementation (R's plm package) against the same real raw panel data
# (raw_panel.csv), not a restatement of the Python/linearmodels result.
#
# Growth model deliberately NOT validated here -- Python's own honest
# result already showed it has no real predictive power (loses to the
# naive baseline), so there's nothing worth independently confirming.
# Inflation is the one real finding worth cross-checking.

library(plm)

panel <- read.csv("raw_panel.csv")
pdata_full <- pdata.frame(panel, index = c("country_code", "year"))
pdata_full$inflation_lag <- plm::lag(pdata_full$inflation, 1)

# Match Python's training window exactly (2010-2023, holding out 2024 for
# its own backtest) -- fitting on the full panel here first gave a
# different coefficient (0.50 vs Python's 0.57) purely because the two
# were trained on different-sized samples, not because of a real
# disagreement. This is the correct, matched comparison. (Filtering on the
# numeric "year" column from the original data.frame, not the pdata.frame's
# index, which pdata.frame converts to a factor.)
train <- pdata_full[panel$year <= 2023, ]

fit <- plm(inflation ~ inflation_lag, data = train, model = "within", effect = "individual")
cat("=== Independent R panel AR(1) fit (plm, fixed effects) ===\n\n")
print(summary(fit, vcov = vcovHC(fit, cluster = "group")))

cat("\nCompare the 'inflation_lag' coefficient above against Python's own\n")
cat("linearmodels PanelOLS output for inflation (lag coefficient 0.5744) --\n")
cat("a genuinely separate implementation, not the same arithmetic re-run.\n")
