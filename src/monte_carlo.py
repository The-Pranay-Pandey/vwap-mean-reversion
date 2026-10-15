import numpy as np
from src.config import seed, n_sims, risk_per_trade, ruin_level


def max_drawdown(curve):
    peak = np.maximum.accumulate(curve, axis=1)
    return ((curve - peak) / peak).min(axis=1)


def run_monte_carlo(trade_data):
    """Bootstrap / shuffle tests on the trade R-multiples. Prints stats and returns arrays for plotting."""
    rng = np.random.default_rng(seed=seed)
    net_r = trade_data['pnl'].to_numpy()
    n_trades = len(net_r)

    indx = rng.integers(0, n_trades, size=(n_sims, n_trades))
    returns_array = net_r[indx]
    equity = np.cumprod(1 + risk_per_trade * returns_array, axis=1)
    equity = np.hstack([np.ones((n_sims, 1)), equity])
    final_ret = equity[:, -1] - 1

    mdd = max_drawdown(equity)
    print(f'median return = {np.median(final_ret)}')
    print(f'5th pct return = {np.percentile(final_ret, 5)}')
    print(f'95th pct return = {np.percentile(final_ret, 95)}')

    print(f'median of max_drawdown = {np.median(mdd)}')
    print(f'95th pct of max_drawdown(95% drawdowns were better than this) = {np.percentile(mdd, 5)}')

    print(f'P(loss) = {(final_ret < 0).mean()}')
    print(f'P(profit) = {(final_ret > 0).mean()}')

    print(f'P(ruin) = {(mdd <= -ruin_level).mean()}')

    # shuffle test
    permutations = rng.permuted(np.tile(net_r, (n_sims, 1)), axis=1)
    permuted_equity = np.hstack([np.ones((n_sims, 1)), np.cumprod(1 + risk_per_trade * permutations, axis=1)])
    permutated_mdd = max_drawdown(permuted_equity)

    observed_equity = np.concatenate([[1.0], np.cumprod(1 + risk_per_trade * net_r)])
    observed_mdd = max_drawdown(observed_equity[None, :])[0]
    print(f'observed maximum drawdown = {observed_mdd}')
    print(f'shuffled order mdd, worst 5% (95% will be better than this) ={np.percentile(permutated_mdd, 5)}')
    print(f'P(shuffled dd atleast as bad as observed) = {(permutated_mdd <= observed_mdd).mean()}')

    # bootstrap significance test
    observed_mean = net_r.mean()
    centered_r = net_r - observed_mean
    bootstrap_means = rng.choice(centered_r, size=(n_sims, n_trades), replace=True).mean(axis=1)
    p_value = (np.sum(bootstrap_means >= observed_mean) + 1) / (n_sims + 1)
    ci = np.percentile(net_r[indx].mean(axis=1), [2.5, 97.5])
    print(f'mean r = {observed_mean}')
    print(f'95% ci = [{ci[0]}, {ci[1]}]')
    print(f"p_value = {p_value}")

    return equity, final_ret, mdd
