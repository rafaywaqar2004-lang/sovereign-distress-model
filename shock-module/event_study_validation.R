# Independent R validation of event_study.py's correlation -- same
# discipline as the MENASA and Phase 1 R validations: a separately written
# implementation against the same real, already-fetched data
# (event_study_results.json), not a restatement of the Python result.

library(jsonlite)

results <- fromJSON("event_study_results.json")

usable <- results[!is.na(results$gdelt_avg_tone_post) & !is.na(results$fx_pct_change), ]
cat("Usable events (real GDELT signal + real FX data):", nrow(usable), "of", nrow(results), "\n\n")
print(usable[, c("country_code", "label", "gdelt_avg_tone_post", "fx_pct_change")])

r <- cor(usable$gdelt_avg_tone_post, usable$fx_pct_change)
cat(sprintf("\nIndependent R correlation (base cor()), n=%d: %.2f\n", nrow(usable), r))
cat("Compare against Python's manually-computed correlation in event_study.py's own output --\n")
cat("this is R's built-in cor() function against the same underlying JSON, a genuinely separate\n")
cat("implementation, not the same arithmetic re-run.\n\n")
cat("Same honest caveat as the Python side: n =", nrow(usable), "is not a sample size to draw a\n")
cat("statistical conclusion from -- this confirms the Python arithmetic is correct, not that the\n")
cat("underlying relationship is statistically validated.\n")
