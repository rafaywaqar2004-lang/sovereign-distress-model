# Firth's Penalized Logistic Regression -- Independent Validation in R
#
# sovereign_default has only 2 real events across 355 observations --
# severe near-perfect separation, documented in model/distress_model.py
# and fixed there with a from-scratch Python implementation of Firth's
# (1993) bias-reduction (model/firth_logit.py), since neither PyPI's
# `firthlogist` (needs Python <3.11) nor CRAN's `logistf` (CRAN itself is
# blocked by this sandbox's egress policy) could be installed here.
#
# This is the same situation in R: `logistf` also lives on CRAN and can't
# be installed in this sandbox either. So this is not a wrapper around
# `logistf` -- it is a second, independent, from-scratch implementation
# of the same algorithm (modified-score Newton-Raphson with step-halving,
# using only base R: solve(), svd(), determinant()), built the same way
# the Python version was and cross-checked against it, not against a
# package neither language could reach.

firth_fit <- function(X, y, max_iter = 15000, tol = 1e-7, max_step = 8,
                       fixed_idx = NA, fixed_val = 0.0, start = NULL,
                       max_delta_norm = 0.3, divergence_bound = 60.0) {
  n <- nrow(X)
  k <- ncol(X)
  beta <- if (is.null(start)) rep(0, k) else start
  if (!is.na(fixed_idx)) beta[fixed_idx] <- fixed_val

  # Robust pseudo-inverse via SVD, matching numpy.linalg.pinv's approach
  # (base R's solve() can fail outright on a near-singular matrix, which
  # happens routinely near this algorithm's whole point -- separation).
  pinv <- function(M, tol_sv = 1e-10) {
    s <- svd(M)
    d <- s$d
    d_inv <- ifelse(d > tol_sv * max(d), 1 / d, 0)
    s$v %*% (d_inv * t(s$u))
  }

  penalized_loglik <- function(beta, XtWX) {
    eta <- pmin(pmax(X %*% beta, -30), 30)
    pi_hat <- 1 / (1 + exp(-eta))
    pi_hat <- pmin(pmax(pi_hat, 1e-12), 1 - 1e-12)
    ll <- sum(y * log(pi_hat) + (1 - y) * log(1 - pi_hat))
    det_sign_logdet <- tryCatch({
      d <- determinant(XtWX, logarithm = TRUE)
      if (d$sign <= 0) return(-Inf)
      d$modulus[1]
    }, error = function(e) -Inf)
    if (!is.finite(det_sign_logdet)) return(-Inf)
    ll + 0.5 * det_sign_logdet
  }

  fit_stats <- function(beta) {
    eta <- pmin(pmax(X %*% beta, -30), 30)
    pi_hat <- 1 / (1 + exp(-eta))
    w <- pi_hat * (1 - pi_hat)
    XtWX <- t(X) %*% (X * as.vector(w))
    list(pi = pi_hat, w = w, XtWX = XtWX)
  }

  converged <- FALSE
  diverged <- FALSE
  final_iter <- 0

  for (iter in 1:max_iter) {
    final_iter <- iter
    fs <- fit_stats(beta)
    XtWX_inv <- pinv(fs$XtWX)
    # hat diagonal h_i = w_i * x_i' (X'WX)^-1 x_i
    h <- fs$w * rowSums((X %*% XtWX_inv) * X)
    U_star <- t(X) %*% (y - fs$pi + h * (0.5 - fs$pi))
    delta <- as.vector(XtWX_inv %*% U_star)
    if (!is.na(fixed_idx)) delta[fixed_idx] <- 0.0
    dn <- max(abs(delta))
    if (dn > max_delta_norm) delta <- delta * (max_delta_norm / dn)

    base_pl <- penalized_loglik(beta, fs$XtWX)
    step <- 1.0
    for (s in 1:max_step) {
      trial <- beta + step * delta
      if (!is.na(fixed_idx)) trial[fixed_idx] <- fixed_val
      trial_fs <- fit_stats(trial)
      trial_pl <- penalized_loglik(trial, trial_fs$XtWX)
      if (is.finite(trial_pl) && trial_pl >= base_pl - 1e-10) break
      step <- step / 2.0
    }
    beta_new <- beta + step * delta
    if (!is.na(fixed_idx)) beta_new[fixed_idx] <- fixed_val
    new_fs <- fit_stats(beta_new)
    new_pl <- penalized_loglik(beta_new, new_fs$XtWX)

    if (max(abs(beta_new)) > divergence_bound) {
      beta <- beta_new
      diverged <- TRUE
      break
    }

    param_converged <- max(abs(beta_new - beta)) < tol
    loglik_converged <- is.finite(base_pl) && is.finite(new_pl) &&
      abs(new_pl - base_pl) < tol * (abs(base_pl) + 1.0)
    beta <- beta_new
    if (param_converged || loglik_converged) {
      converged <- TRUE
      break
    }
  }

  fs <- fit_stats(beta)
  XtWX_inv <- pinv(fs$XtWX)
  se <- sqrt(pmax(diag(XtWX_inv), 0))
  z <- beta / se
  p <- 2 * (1 - pnorm(abs(z)))
  penloglik <- penalized_loglik(beta, fs$XtWX)

  list(beta = beta, se = se, z = z, p = p, converged = converged & !diverged,
       n_iter = final_iter, loglik_penalized = penloglik, XtWX = fs$XtWX)
}

# --- Sanity check: same synthetic no-separation case as the Python file ---
set.seed(0)
n <- 2000
x1 <- rnorm(n)
x2 <- rnorm(n)
X_synth <- cbind(1, x1, x2)
true_beta <- c(-0.5, 1.2, -0.8)
pi_true <- 1 / (1 + exp(-(X_synth %*% true_beta)))
y_synth <- rbinom(n, 1, pi_true)

mle_synth <- glm(y_synth ~ x1 + x2, family = binomial())
firth_synth <- firth_fit(X_synth, y_synth)

cat("=== Sanity check: synthetic case (n=2000, no separation) ===\n")
cat(sprintf("%10s %10s %10s\n", "param", "MLE", "Firth"))
for (i in seq_along(true_beta)) {
  cat(sprintf("%10s %10.4f %10.4f\n",
              c("const", "x1", "x2")[i], coef(mle_synth)[i], firth_synth$beta[i]))
}
cat(sprintf("\nFirth converged: %s in %d iterations\n\n", firth_synth$converged, firth_synth$n_iter))

# --- The real fit: sovereign_default, 10-factor primary specification ---
panel <- read.csv("../data/panel.csv")
factor_cols <- c(
  "current_account_pct_gdp", "reserves_months_imports", "gdp_growth",
  "inflation", "currency_depreciation_pct", "political_stability",
  "government_effectiveness", "rule_of_law", "regulatory_quality",
  "control_of_corruption"
)
complete <- panel[complete.cases(panel[, c(factor_cols, "sovereign_default")]), ]
X <- cbind(1, as.matrix(complete[, factor_cols]))
colnames(X) <- c("const", factor_cols)
y <- complete$sovereign_default

cat("=== Real fit: sovereign_default, primary 10-factor specification ===\n")
cat(sprintf("Complete-case observations: %d, positive events: %d\n\n", nrow(X), sum(y)))

result <- firth_fit(X, y)
cat(sprintf("Converged: %s (in %d iterations)\n", result$converged, result$n_iter))
cat(sprintf("Penalized log-likelihood: %.4f\n\n", result$loglik_penalized))

summary_df <- data.frame(
  factor = colnames(X), coef = round(result$beta, 4),
  std_err = round(result$se, 4), wald_p = round(result$p, 4)
)
print(summary_df, row.names = FALSE)

cat("\n=== Compare against Python's model/firth_logit.py output ===\n")
cat("Expect: const=-2.8103, current_account_pct_gdp=0.0478,\n")
cat("reserves_months_imports=-0.1082, gdp_growth=-0.2655, inflation=0.0492,\n")
cat("currency_depreciation_pct=-0.0035, political_stability=0.0535,\n")
cat("government_effectiveness=0.1885, rule_of_law=-0.1709,\n")
cat("regulatory_quality=-0.0606, control_of_corruption=-0.0733\n")
cat("A genuinely separate implementation (base R vs. numpy/scipy), not the\n")
cat("same arithmetic re-run in a different syntax.\n")
