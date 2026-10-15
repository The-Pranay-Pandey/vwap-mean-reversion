import os
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from src.config import seed, n_sims

os.makedirs("results", exist_ok=True)


def plot_trade_equity(trade_data):
    fig, ax = plt.subplots(figsize=(8, 5))
    trade_data['pnl'].cumsum().plot(ax=ax)
    ax.set_title("Cumulative PnL (R)")
    ax.set_xlabel('Trade number')
    ax.set_ylabel('Cumulative R')
    plt.savefig('results/equity_curve_R.png')
    plt.show()
    plt.close()


def plot_monte_carlo(equity, final_ret, mdd):
    rng = np.random.default_rng(seed=seed)

    # equity curves
    fig, ax = plt.subplots(figsize=(8, 5))
    percentiles = np.percentile(equity, [5, 25, 50, 75, 95], axis=0)
    x_axis = np.arange(equity.shape[1])

    sample_indices = rng.choice(n_sims, size=100, replace=False)
    for idx in sample_indices:
        ax.plot(x_axis, equity[idx], alpha=0.5, linewidth=1)

    ax.fill_between(x_axis, percentiles[0], percentiles[4], alpha=0.2, label='5th - 95th percentile')
    ax.plot(x_axis, percentiles[2], label="Median Equity", )
    ax.set_title("Monte Carlo equity curves")
    ax.set_xlabel('Trade number')
    ax.set_ylabel('Equity Multiplier')
    ax.legend(loc='upper left')
    plt.savefig('results/monte_carlo_equity_curves.png')
    plt.show()
    plt.close()

    # final return distribution
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(final_ret, kde=True, ax=ax, bins=30)
    ax.axvline(np.median(final_ret), color='red', linestyle='--', label=f'Median: {np.median(final_ret):.2}')
    ax.set_title('Final Return distribution')
    ax.set_xlabel('final return')
    ax.set_ylabel('frequency')
    ax.legend(loc='upper right')
    plt.savefig('results/monte_carlo_final_returns.png')
    plt.show()
    plt.close()

    # max drawdown distribution
    fig, ax = plt.subplots(figsize=(8, 5))
    sns.histplot(mdd, kde=True, ax=ax, bins=30)
    ax.axvline(np.median(mdd), color='red', linestyle='--', label=f'Median: {np.median(mdd):.2}')
    ax.set_title('Max Drawdown distribution')
    ax.set_xlabel('Max Drawdown')
    ax.set_ylabel('frequency')
    ax.legend(loc='upper right')
    plt.savefig('results/monte_carlo_max_draw_down.png')
    plt.show()
    plt.close()
