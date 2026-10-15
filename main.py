from src.data import fetch_data, load_data
from src.indicators import build_features
from src.backtest import run_backtest
from src.metrics import print_metrics
from src.monte_carlo import run_monte_carlo
from src.plots import plot_trade_equity, plot_monte_carlo

# Uncomment on first run to download the data
# fetch_data()


def main():
    data = load_data()
    data = build_features(data)

    trade_data = run_backtest(data)
    trade_data.to_csv('trades.csv', index=False)

    print_metrics(trade_data)
    plot_trade_equity(trade_data)

    equity, final_ret, mdd = run_monte_carlo(trade_data)
    plot_monte_carlo(equity, final_ret, mdd)


if __name__ == "__main__":
    main()
