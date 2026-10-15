def print_metrics(trade_data):
    print(f"minimum balance: {trade_data['pnl'].cumsum().min()}")
    print(f"maximum balance: {trade_data['pnl'].cumsum().max()}")
    print(f'number of trades: {len(trade_data)}')
    print(f"biggest loss: {trade_data['pnl'].min()}")
    print(f"biggest win: {trade_data['pnl'].max()}")
    print(f"win rate: {(trade_data['pnl'] > 0).mean()}")
    print(f"average return: {trade_data['pnl'].mean()}")

    total_profit = trade_data[trade_data['pnl'] > 0]['pnl'].sum()
    total_loss = trade_data[trade_data['pnl'] < 0]['pnl'].sum()

    profit_factor = total_profit / abs(total_loss) if total_loss != 0 else float('inf')
    print(f"profit factor: {profit_factor}")
    print(f"Sharpe Ratio: {trade_data['pnl'].mean() / trade_data['pnl'].std()}")
