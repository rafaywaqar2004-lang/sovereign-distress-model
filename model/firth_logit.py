"""
Firth's penalized (bias-reduced) logistic regression -- Firth (1993),
"Bias reduction of maximum likelihood estimates".

Why this exists: sovereign_default in the primary 10-factor spec
(distress_model.py) has only 2 positive events across 355 observations --
severe, real near-perfect separation. Ordinary logistic regression's MLE
either fails to converge or produces coefficients that blow up toward
+/-infinity in that regime; it is not usable as reported.

Firth's fix penalizes the likelihood with Jeffreys' invariant prior,
0.5*log|I(beta)|, which is the textbook remedy for exactly this problem
(rare events, quasi/complete separation) and is what R's `logistf` and
Python's `firthlogist` package implement. Neither was available in this
sandbox:
  - `firthlogist` (PyPI) requires Python <3.11; this environment runs
    3.11.15, confirmed via `pip install firthlogist` failing with no
    compatible version.
  - R's `logistf` (CRAN) could not be installed either -- CRAN
    (cloud.r-project.org) is blocked by this session's egress policy
    (403 on the CONNECT tunnel), a genuine sandbox constraint, not a
    bug to route around.

So this is a from-scratch implementation of the standard algorithm
(modified-score Newton-Raphson with step-halving), not a wrapper around
either package. It's cross-checked below against statsmodels' plain
Logit on a well-separated synthetic case where both should roughly agree,
since there's no real full-data case in this panel where plain MLE
converges to compare against directly. It's also independently
cross-validated in R (`r-validation/firth_validation.R`) -- since CRAN's
`logistf` couldn't be installed there either (same blocked-egress
constraint), that file is a second from-scratch implementation of this
same algorithm in base R, not a wrapper around `logistf`. It matches
this file's output on `sovereign_default` almost to the decimal.

Reference: Heinze & Schemper (2002), "A solution to the problem of
separation in logistic regression", Statistics in Medicine 21:2409-2419 --
the modified score function:

    U*(beta) = X' (y - pi + h * (0.5 - pi))

where pi is the fitted probability, W = diag(pi*(1-pi)), and h_i is the
i-th diagonal of the hat matrix pi_i*(1-pi_i) * x_i' (X'WX)^-1 x_i.

Inference: Wald (beta/se) is the default, matching this file's original
scope. Firth's own preferred inference -- the profile penalized
likelihood ratio test (what `logistf` actually reports by default,
because Wald intervals are known to behave poorly right where Firth's
fix matters most, i.e. exactly this kind of rare-event data) -- is now
also implemented (firth_profile_test, firth_profile_ci), not left as an
unimplemented gap. It works by re-maximizing the same penalized
likelihood with one coefficient clamped at a trial value: the score for
the clamped coordinate is simply zeroed out each iteration while the
full k x k Fisher information (and its penalty term) still enters the
other coordinates' updates exactly as Heinze & Schemper define the
profile -- not a reduced (k-1)-parameter sub-model, which would be a
different, non-equivalent quantity.
"""
import numpy as np
from scipy import stats, optimize


def _fit_stats(X, beta):
    eta = X @ beta
    eta = np.clip(eta, -30, 30)  # avoid overflow; real probs saturate at exp(+-30) anyway
    pi = 1.0 / (1.0 + np.exp(-eta))
    w = pi * (1.0 - pi)
    XtWX = X.T @ (X * w[:, None])
    return pi, w, XtWX


def _penalized_loglik(X, y, beta, XtWX):
    eta = np.clip(X @ beta, -30, 30)
    pi = 1.0 / (1.0 + np.exp(-eta))
    pi = np.clip(pi, 1e-12, 1 - 1e-12)
    loglik = np.sum(y * np.log(pi) + (1 - y) * np.log(1 - pi))
    sign, logdet = np.linalg.slogdet(XtWX)
    if sign <= 0:
        return -np.inf
    return loglik + 0.5 * logdet


def _fit_penalized(X, y, max_iter=15000, tol=1e-7, max_step=8, fixed_idx=None, fixed_val=0.0,
                    start=None, max_delta_norm=0.3, divergence_bound=60.0):
    """The actual Firth IRLS loop. With fixed_idx given, coordinate
    fixed_idx is clamped at fixed_val throughout (its score/delta zeroed
    each step) while every other coordinate is still updated using the
    FULL k x k modified score and Fisher information -- this is exactly
    Heinze & Schemper's profile penalized likelihood, not a smaller
    sub-model fit on the remaining columns.

    max_delta_norm caps each raw Newton step before step-halving even
    starts: with a coordinate clamped, the remaining (k-1)-dimensional
    surface can develop a numerically unstable direction where an
    uncapped step pushes several coefficients toward +-1e9+ in a single
    iteration -- eta then saturates at the +-30 clip for effectively
    every observation, W collapses toward 0, and the step-halving check
    above (which compares penalized log-likelihoods) stops being a
    reliable guard once floating-point noise dominates at that scale.
    Capping the raw step keeps every accepted move small enough that
    step-halving's own real-improvement check still means what it says.
    divergence_bound flags the same failure mode after the fact: a fit
    that still ends up with any |beta| beyond it is reported as
    unconverged, not as a real estimate -- this is real data with only 2
    positive events, and profile likelihood at some fixed values may
    genuinely have no finite maximizer; disclosing that as a failed fit
    is the honest outcome, not a number that merely looks plausible."""
    n, k = X.shape
    beta = np.zeros(k) if start is None else start.copy()
    if fixed_idx is not None:
        beta[fixed_idx] = fixed_val

    converged = False
    diverged = False
    iteration = 0
    for iteration in range(max_iter):
        pi, w, XtWX = _fit_stats(X, beta)
        XtWX_inv = np.linalg.pinv(XtWX)
        h = w * np.einsum("ij,jk,ik->i", X, XtWX_inv, X)
        U_star = X.T @ (y - pi + h * (0.5 - pi))
        delta = XtWX_inv @ U_star
        if fixed_idx is not None:
            delta[fixed_idx] = 0.0
        delta_norm = np.max(np.abs(delta))
        if delta_norm > max_delta_norm:
            delta = delta * (max_delta_norm / delta_norm)

        step = 1.0
        base_penloglik = _penalized_loglik(X, y, beta, XtWX)
        for _ in range(max_step):
            trial = beta + step * delta
            if fixed_idx is not None:
                trial[fixed_idx] = fixed_val
            _, _, trial_XtWX = _fit_stats(X, trial)
            trial_penloglik = _penalized_loglik(X, y, trial, trial_XtWX)
            if np.isfinite(trial_penloglik) and trial_penloglik >= base_penloglik - 1e-10:
                break
            step /= 2.0
        beta_new = beta + step * delta
        if fixed_idx is not None:
            beta_new[fixed_idx] = fixed_val
        _, _, new_XtWX = _fit_stats(X, beta_new)
        new_penloglik = _penalized_loglik(X, y, beta_new, new_XtWX)

        if np.max(np.abs(beta_new)) > divergence_bound:
            beta = beta_new
            diverged = True
            break

        # Two convergence checks: parameters stop moving, or the penalized
        # log-likelihood stops improving in relative terms. Near-perfect
        # separation makes the likelihood surface very flat close to the
        # optimum, so parameter movement alone can stay just above a tight
        # tolerance for hundreds of iterations even though the fit itself
        # has essentially stopped changing -- the loglik check catches that.
        param_converged = np.max(np.abs(beta_new - beta)) < tol
        loglik_converged = (
            np.isfinite(base_penloglik)
            and np.isfinite(new_penloglik)
            and abs(new_penloglik - base_penloglik) < tol * (abs(base_penloglik) + 1.0)
        )
        beta = beta_new
        if param_converged or loglik_converged:
            converged = True
            break

    pi, w, XtWX = _fit_stats(X, beta)
    penloglik = _penalized_loglik(X, y, beta, XtWX)
    return beta, penloglik, converged, iteration + 1, XtWX


def firth_logit(X, y, max_iter=2000, tol=1e-8, max_step=8):
    """
    X: (n, k) array, should already include an intercept column.
    y: (n,) array of 0/1.
    Returns dict with beta, se, z, p (Wald), n_iter, converged,
    loglik_penalized.
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)

    beta, penloglik, converged, n_iter, XtWX = _fit_penalized(
        X, y, max_iter=max_iter, tol=tol, max_step=max_step
    )

    XtWX_inv = np.linalg.pinv(XtWX)
    se = np.sqrt(np.clip(np.diag(XtWX_inv), 0, None))
    z = beta / se
    p = 2 * (1 - stats.norm.cdf(np.abs(z)))

    return {
        "beta": beta,
        "se": se,
        "z": z,
        "p": p,
        "n_iter": n_iter,
        "converged": converged,
        "loglik_penalized": penloglik,
    }


def firth_profile_test(X, y, beta_full=None, penloglik_full=None):
    """Firth's own preferred significance test (what `logistf` reports by
    default): for each coefficient, re-fit the penalized model with that
    coefficient clamped at 0 and compare penalized log-likelihoods. The
    resulting likelihood-ratio statistic is chi-square(1)-distributed
    under the null, and -- unlike the Wald p-values above -- doesn't rely
    on the same large-sample normal approximation that's shakiest in
    exactly the small/rare-event regime Firth's fix targets.

    Returns dict with lr_stat, p, and converged (one entry per
    coefficient, same order as X's columns). Where converged is False,
    lr_stat/p are NaN -- the constrained fit didn't reach a real optimum
    (see _fit_penalized's own docstring on why that can genuinely happen
    at this sample size), and a NaN is reported rather than a number
    computed from a fit that never actually settled.
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    n, k = X.shape

    if beta_full is None or penloglik_full is None:
        full = firth_logit(X, y)
        beta_full, penloglik_full = full["beta"], full["loglik_penalized"]

    lr_stats = np.full(k, np.nan)
    p_values = np.full(k, np.nan)
    converged_flags = np.zeros(k, dtype=bool)
    for j in range(k):
        start = beta_full.copy()
        start[j] = 0.0
        _, penloglik_constrained, conv, _, _ = _fit_penalized(X, y, fixed_idx=j, fixed_val=0.0, start=start)
        converged_flags[j] = conv
        if not conv:
            continue
        lr = 2.0 * (penloglik_full - penloglik_constrained)
        lr = max(lr, 0.0)  # numerical noise can push this a hair below 0 at the optimum
        lr_stats[j] = lr
        p_values[j] = 1.0 - stats.chi2.cdf(lr, df=1)

    return {"lr_stat": lr_stats, "p": p_values, "converged": converged_flags}


def firth_profile_ci(X, y, j, beta_full, penloglik_full, level=0.95, search_width=6.0, max_expand=6):
    """Profile penalized-likelihood confidence interval for coefficient j:
    the two values of beta_j where the profile penalized log-likelihood
    has dropped by half the chi-square(1) critical value from its maximum
    -- the standard profile-likelihood CI construction, found here by
    bisection rather than a closed form (none exists for this penalized
    likelihood). Returns (lower, upper); either bound is None if the
    search range had to be expanded past a sane limit without bracketing
    a root (can happen on the wide-open side of a still-fairly-flat
    likelihood with only 2 real events -- reported as None, not guessed)."""
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    crit = stats.chi2.ppf(level, df=1)
    target = penloglik_full - crit / 2.0

    def penloglik_at(c):
        start = beta_full.copy()
        start[j] = c
        _, pl, _, _, _ = _fit_penalized(X, y, fixed_idx=j, fixed_val=c, start=start)
        return pl

    def f(c):
        return penloglik_at(c) - target

    center = beta_full[j]
    bounds = []
    for direction in (-1.0, 1.0):
        width = search_width
        lo, hi = center, center + direction * width
        f_lo = f(lo)
        f_hi = f(hi)
        expand = 0
        while np.sign(f_lo) == np.sign(f_hi) and expand < max_expand:
            width *= 2.0
            hi = center + direction * width
            f_hi = f(hi)
            expand += 1
        if np.sign(f_lo) == np.sign(f_hi):
            bounds.append(None)
        else:
            root = optimize.brentq(f, min(lo, hi), max(lo, hi), xtol=1e-4)
            bounds.append(root)
    return bounds[0], bounds[1]


if __name__ == "__main__":
    # Sanity check against statsmodels on a case with enough events that
    # plain MLE converges cleanly -- Firth's estimates should sit close to
    # (slightly shrunk toward zero from) the unpenalized MLE, not wildly off.
    import statsmodels.api as sm

    rng = np.random.default_rng(0)
    n = 2000
    x1 = rng.normal(size=n)
    x2 = rng.normal(size=n)
    X = sm.add_constant(np.column_stack([x1, x2]))
    true_beta = np.array([-0.5, 1.2, -0.8])
    pi_true = 1 / (1 + np.exp(-X @ true_beta))
    y = rng.binomial(1, pi_true)

    mle = sm.Logit(y, X).fit(disp=0)
    firth = firth_logit(X, y)

    print("Cross-check on a well-behaved synthetic case (n=2000, no separation):")
    print(f"{'param':>10} {'MLE':>10} {'Firth':>10}")
    for i, name in enumerate(["const", "x1", "x2"]):
        print(f"{name:>10} {mle.params[i]:>10.4f} {firth['beta'][i]:>10.4f}")
    print(f"\nFirth converged: {firth['converged']} in {firth['n_iter']} iterations")
    print("(Firth's estimates should be close to MLE's here -- both should recover")
    print(f" the true betas {true_beta} reasonably well; this is the sanity check,")
    print(" not proof of correctness on the actual separated sovereign_default case.)")

    print("\nProfile penalized-LR test (should broadly agree with Wald p-values here,")
    print("since this synthetic case has no separation problem):")
    profile = firth_profile_test(X, y, firth["beta"], firth["loglik_penalized"])
    for i, name in enumerate(["const", "x1", "x2"]):
        print(f"{name:>10} Wald p={firth['p'][i]:.4f}  profile-LR p={profile['p'][i]:.4f}")

    print("\n95% profile CI for x1 (true value 1.2):")
    lo, hi = firth_profile_ci(X, y, 1, firth["beta"], firth["loglik_penalized"])
    print(f"  [{lo:.4f}, {hi:.4f}]  (point estimate {firth['beta'][1]:.4f})")
