"""Small statistics helpers (no statsmodels dependency): OLS with country-clustered standard errors."""
import numpy as np


def logit(p):
    p = np.clip(np.asarray(p, dtype=float), 0.005, 0.995)
    return np.log(p / (1 - p))


def inv_logit(z):
    return 1 / (1 + np.exp(-np.asarray(z, dtype=float)))


def ols_cluster(X, y, groups):
    """OLS with cluster-robust (CR1) standard errors. X includes the constant column."""
    X, y = np.asarray(X, float), np.asarray(y, float)
    n, k = X.shape
    xtx_inv = np.linalg.inv(X.T @ X)
    beta = xtx_inv @ X.T @ y
    u = y - X @ beta
    meat = np.zeros((k, k))
    ug = np.unique(groups)
    for g in ug:
        idx = groups == g
        s = X[idx].T @ u[idx]
        meat += np.outer(s, s)
    G = len(ug)
    adj = (G / (G - 1)) * ((n - 1) / (n - k))
    V = adj * xtx_inv @ meat @ xtx_inv
    se = np.sqrt(np.diag(V))
    ss_res, ss_tot = float(u @ u), float(((y - y.mean()) ** 2).sum())
    return dict(beta=beta, se=se, t=beta / se, r2=1 - ss_res / ss_tot, n=n, G=G, resid=u)
