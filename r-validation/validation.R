# Sovereign Distress Model -- Independent Validation in R
#
# Reproduces the PRIMARY imf_program_entry model (10 factors, excludes
# debt_to_gdp) independently in R -- a separately written implementation
# (R's own glm() with sandwich/cluster-robust SEs) against the same
# panel.csv, not a restatement of the Python/statsmodels result.

library(sandwich)
library(lmtest)

panel <- read.csv("../data/panel.csv")

primary_factors <- c(
  "current_account_pct_gdp", "reserves_months_imports", "gdp_growth",
  "inflation", "currency_depreciation_pct", "political_stability",
  "government_effectiveness", "rule_of_law", "regulatory_quality",
  "control_of_corruption"
)

complete <- panel[complete.cases(panel[, c(primary_factors, "imf_program_entry")]), ]
cat("Complete-case observations:", nrow(complete), "of", nrow(panel), "\n")
cat("Positive events retained:", sum(complete$imf_program_entry), "of",
    sum(panel$imf_program_entry), "real events in the full panel\n\n")

fmla <- as.formula(paste("imf_program_entry ~", paste(primary_factors, collapse = " + ")))
fit <- glm(fmla, data = complete, family = binomial(link = "logit"))

# Cluster-robust SEs by country -- same correction Python's statsmodels
# cov_type="cluster" applies, computed here via an independent R package.
clustered_se <- vcovCL(fit, cluster = complete$country_code)
cat("=== Independent R reproduction (glm + cluster-robust SEs) ===\n\n")
print(coeftest(fit, vcov = clustered_se))

cat("\n=== Read against the Python/statsmodels output ===\n")
cat("Compare coefficient signs and rough magnitudes against\n")
cat("model/distress_model.py's PRIMARY MODEL output for imf_program_entry --\n")
cat("this is a genuinely separate implementation (R's glm/sandwich vs.\n")
cat("Python's statsmodels.Logit), not the same code re-run.\n")
