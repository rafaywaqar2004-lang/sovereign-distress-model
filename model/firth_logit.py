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
converges to compare against directly.

Reference: Heinze & Schemper (2002), "A solution to the problem of
separation in logistic regression", Statistics in Medicine 21:2409-2419 --
the modified score function:

    U*(beta) = X' (y - pi + h * (0.5 - pi))

where pi is the fitted probability, W = diag(pi*(1-pi)), and h_i is the
i-th diagonal of the hat matrix pi_i*(1-pi_i) * x_i' (X'WX)^-1 x_i.
Standard errors come from the observed-information inverse at convergence
(the same Wald approximation `logistf` reports by default); Firth's own
preferred inference (profile penalized likelihood ratio) is not
implemented here -- disclosed as a limitation below, not silently assumed
equivalent.
"""
import numpy as np
from scipy import stats


def firth_logit(X, y, max_iter=2000, tol=1e-8, max_step=8):
    """
    X: (n, k) array, should already include an intercept column.
    y: (n,) array of 0/1.
    Returns dict with beta, se, z, p, n_iter, converged, loglik_penalized.
    """
    X = np.asarray(X, dtype=float)
    y = np.asarray(y, dtype=float)
    n, k = X.shape
    beta = np.zeros(k)

    def fit_stats(b):
        eta = X @ b
        eta = np.clip(eta, -30, 30)  # avoid overflow; real probs saturate at exp(+-30) anyway
        pi = 1.0 / (1.0 + np.exp(-eta))
        w = pi * (1.0 - pi)
        XtWX = X.T @ (X * w[:, None])
        return pi, w, XtWX

    converged = False
    for iteration in range(max_iter):
        pi, w, XtWX = fit_stats(beta)
        XtWX_inv = np.linalg.pinv(XtWX)
        # hat diagonal: h_i = w_i * x_i' (X'WX)^-1 x_i
        h = w * np.einsum("ij,jk,ik->i", X, XtWX_inv, X)
        U_star = X.T @ (y - pi + h * (0.5 - pi))
        delta = XtWX_inv @ U_star

        # step-halving: Firth's modified score can overshoot far from the
        # optimum with this few events; halve the step until the penalized
        # log-likelihood actually improves, standard safeguard for this algorithm.
        step = 1.0
        base_penloglik = _penalized_loglik(X, y, beta, XtWX)
        for _ in range(max_step):
            trial = beta + step * delta
            _, _, trial_XtWX = fit_stats(trial)
            trial_penloglik = _penalized_loglik(X, y, trial, trial_XtWX)
            if np.isfinite(trial_penloglik) and trial_penloglik >= base_penloglik - 1e-10:
                break
            step /= 2.0
        beta_new = beta + step * delta
        _, _, new_XtWX = fit_stats(beta_new)
        new_penloglik = _penalized_loglik(X, y, beta_new, new_XtWX)

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

    pi, w, XtWX = fit_stats(beta)
    XtWX_inv = np.linalg.pinv(XtWX)
    se = np.sqrt(np.clip(np.diag(XtWX_inv), 0, None))
    z = beta / se
    p = 2 * (1 - stats.norm.cdf(np.abs(z)))
    penloglik = _penalized_loglik(X, y, beta, XtWX)

    return {
        "beta": beta,
        "se": se,
        "z": z,
        "p": p,
        "n_iter": iteration + 1,
        "converged": converged,
        "loglik_penalized": penloglik,
    }


def _penalized_loglik(X, y, beta, XtWX):
    eta = np.clip(X @ beta, -30, 30)
    pi = 1.0 / (1.0 + np.exp(-eta))
    pi = np.clip(pi, 1e-12, 1 - 1e-12)
    loglik = np.sum(y * np.log(pi) + (1 - y) * np.log(1 - pi))
    sign, logdet = np.linalg.slogdet(XtWX)
    if sign <= 0:
        return -np.inf
    return loglik + 0.5 * logdet


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
