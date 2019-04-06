import numpy as np
import pandas as pd
import itertools
import matplotlib.pyplot as plt
from scipy.stats import norm, poisson, lognorm
from pyrolite.data.Aitchison import *
from pyrolite.util.plot import share_axes, subaxes
from pyrolite.util.distributions import lognorm_to_norm, norm_to_lognorm

# %% Data
# pyrolite comes with a few datasets from Aitchison (1984) built in:
df = load_kongite()
# %% Simple Means and covariance
# Say you want to know the average ratio between A and B
A_on_B = df["A"] / df["B"]
A_on_B.mean()  # 2.8265837788402983
# Equally, you could have chosen to calculate the average ratio between B and A
B_on_A = df["B"] / df["A"]
B_on_A.mean()  # 0.4709565704852008
# You expect these to be invertable, such that A_on_B = 1 / B_on_A; but not so!
A_on_B.mean() / (1 / B_on_A.mean())  # 1.3311982026717262
# Similarly, the relative variances are different:
np.std(A_on_B) / A_on_B.mean()  # 0.6295146309597085
np.std(B_on_A) / B_on_A.mean()  # 0.5020948201979953
# This improves when using logratios in place of simple ratios, prior to exponentiating means
logA_on_B = (df["A"] / df["B"]).apply(np.log)
logB_on_A = (df["B"] / df["A"]).apply(np.log)
# The logratios are invertible:
np.exp(logA_on_B.mean())  # 2.4213410747400514
1 / np.exp(logB_on_A.mean())  # 2.421341074740052
# The logratios also have the same variance:
(np.std(logA_on_B) / logA_on_B.mean()) ** 2  # 0.36598579018127086
(np.std(logB_on_A) / logB_on_A.mean()) ** 2  # 0.36598579018127086

# %% Ratios of Poisson Data
means = [[10, 10], [10, 20], [20, 100], [1000, 50]]
fig, ax = plt.subplots(len(means), 3, figsize=(9, 8))
ax[-1, 0].set_xlabel("A")
ax[-1, 1].set_xlabel("B")
ax[-1, 2].set_xlabel("B/A")
for ix, (m1, m2) in enumerate(means):
    p1, p2 = poisson(mu=m1), poisson(mu=m2)
    y1, y2 = p1.rvs(2000), p2.rvs(2000)
    ratios = y2[y1 > 0] / y1[y1 > 0]

    y1min, y1max = y1.min(), y1.max()
    y2min, y2max = y2.min(), y2.max()
    ax[ix, 0].hist(
        y1,
        color="0.5",
        alpha=0.6,
        label="A",
        bins=np.linspace(y1min - 0.5, y1max + 0.5, (y1max - y1min) + 1),
    )
    ax[ix, 1].hist(
        y2,
        color="0.5",
        alpha=0.6,
        label="B",
        bins=np.linspace(y2min - 0.5, y2max + 0.5, (y2max - y2min) + 1),
    )
    H, binedges, patches = ax[ix, 2].hist(
        ratios, color="Purple", alpha=0.6, label="Ratios", bins=100
    )
    s, loc, scale = lognorm.fit(ratios, loc=0)
    pdf = lognorm.pdf(binedges, s, loc, scale)
    twin2 = ax[ix, 2].twinx()
    twin2.set_ylim(0, 1.1 * np.max(pdf))
    twin2.plot(
        binedges,
        lognorm.pdf(binedges, s, loc, scale),
        color="k",
        ls="--",
        label="Lognormal Fit",
    )
    for a in [*ax[ix, :], twin2]:
        a.set_yticks([])
    ax[ix, 2].legend(loc=(1.05, 0.8), frameon=False)
    twin2.legend(loc=(1.05, 0.6), frameon=False)

plt.tight_layout()
# %% Save Figure
from pyrolite.util.plot import save_figure

save_figure(fig, save_at="../../source/_static", name="PoissonLognormals")
# %% Compositional data distributions
# starting from a normal distribution, then creating similar non-normal distributions
mean, sd = 2.5, 1.5  #
logmu, logs = norm_to_lognorm(mean, sd)  # parameters for equival
normrv = norm(loc=mean, scale=sd)
lognormrv = lognorm(s=logs, scale=logmu)
poissonrv = poisson(mu=mean)

# we can visualise the similarities and differences between these distributions:
fig, ax = plt.subplots(2, 3, figsize=(8, 4))
ax = ax.flat
for a in ax:
    a.subax = subaxes(a, side="bottom")

share_axes(ax[:3], which="x")
share_axes(ax[3:], which="x")
ax[0].set_xlim(-2, 10)
ax[3].set_xscale("log")
ax[3].set_xlim(0.1, 10)

for a in ax:
    a.axvline(0, color="k", lw=0.5, ls="--")

# xs at which to evaluate the pdfs
x = np.linspace(-5, 15.0, 1001)

for ix, dist in enumerate([normrv, lognormrv, poissonrv]):
    _xs = dist.rvs(size=10000)  # random sample
    _ys = -0.05 + np.random.randn(10000) / 100  # random offsets for visualisation
    for a in [ax[ix], ax[ix + 3]]:
        a.annotate(
            "mu={:.2f}, var={:.2f}".format(np.mean(_xs), np.var(_xs)),
            xy=(0.05, 1.05),
            ha="left",
            va="bottom",
            xycoords=a.transAxes,
        )
        a.subax.scatter(_xs, _ys, s=2, color="k", alpha=0.01)
        if dist != poissonrv:  # cont. distribution
            a.plot(x, dist.pdf(x), color="Purple", alpha=0.6, label="pdf")
        else:  # discrete distribution
            a.vlines(
                x[x >= 0],
                0,
                dist.pmf(x[x >= 0]),
                color="Purple",
                alpha=0.6,
                label="pmf",
            )

fig.suptitle("Data Distributions: Normal, Lognormal, Poisson", y=1.1)
plt.tight_layout()
# %% Save Figure
from pyrolite.util.plot import save_figure

save_figure(fig, save_at="../../source/_static", name="CompositionalDistributions")

# %% Higher Dimensional Visualisation of Mean
from pyrolite.comp.codata import clr, inverse_clr, logratiomean

# This issue of accuracy/validity of means is also seen in higher dimensions:
df = load_kongite()

fig, ax = plt.subplots(2, 2, figsize=(12, 12))
ax = ax.flat

for columns, a in zip(itertools.combinations(["A", "B", "C", "D"], 3), ax):
    columns = list(columns)

    df.loc[:, columns].pyroplot.ternary(ax=a, color="k", label=df.name, no_ticks=True)

    df.mean().loc[columns].pyroplot.ternary(
        ax=a, color="red", label="Arithmetic Mean", no_ticks=True
    )

    logratiomean(df.loc[:, columns]).pyroplot.ternary(
        ax=a, s=30, color="green", label="Geometric Mean", axlabels=True, no_ticks=True
    )
    a.legend(frameon=False, facecolor=None, loc=(0.8, 0.5))
# %% Save Figure --
save_figure(fig, save_at="../../source/_static", name="LogRatioMeansTernary")