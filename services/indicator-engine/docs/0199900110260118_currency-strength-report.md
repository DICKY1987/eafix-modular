---
doc_id: DOC-CONFIG-0101
---

#### Scalping Strategy Visualization and Analysis Framework

```python
def visualize_backtest_results(results, trades, strategy_params=None):
    """
    Create comprehensive visualizations for analyzing currency strength scalping backtest results.
    
    Parameters:
    results: DataFrame with backtest results (from backtest_scalping_strategy)
    trades: DataFrame with trade data (from backtest_scalping_strategy)
    strategy_params: Dictionary with strategy parameters used in backtesting
    
    Returns:
    Multiple figures with backtest analysis
    """
    # Setup
    if trades.empty:
        print("No trades to visualize.")
        return None
    
    # Convert timestamps to datetime if needed
    if not pd.api.types.is_datetime64_any_dtype(results['timestamp']):
        results['timestamp'] = pd.to_datetime(results['timestamp'])
    
    if not pd.api.types.is_datetime64_any_dtype(trades['entry_time']):
        trades['entry_time'] = pd.to_datetime(trades['entry_time'])
        trades['exit_time'] = pd.to_datetime(trades['exit_time'])
    
    # === Figure 1: Performance Overview ===
    fig1 = plt.figure(figsize=(14, 12))
    gs1 = fig1.add_gridspec(3, 2)
    
    # Plot 1: Equity Curve
    ax1 = fig1.add_subplot(gs1[0, :])
    ax1.plot(results['timestamp'], results['equity'], linewidth=2, color='blue')
    ax1.set_title('Equity Curve', fontsize=14)
    ax1.set_ylabel('Account Equity', fontsize=12)
    ax1.grid(True, alpha=0.3)
    
    # Add buy and sell markers
    for _, trade in trades.iterrows():
        marker_color = 'green' if trade['profit_money'] > 0 else 'red'
        entry_idx = results[results['timestamp'] == trade['entry_time']].index[0] if len(results[results['timestamp'] == trade['entry_time']]) > 0 else None
        exit_idx = results[results['timestamp'] == trade['exit_time']].index[0] if len(results[results['timestamp'] == trade['exit_time']]) > 0 else None
        
        if entry_idx is not None:
            ax1.scatter(trade['entry_time'], results['equity'].iloc[entry_idx], 
                       color=marker_color, marker='^' if trade['direction'] == 'long' else 'v', s=60)
    
    # Plot 2: Drawdown
    ax2 = fig1.add_subplot(gs1[1, 0])
    ax2.fill_between(results['timestamp'], results['drawdown'] * 100, 0, color='red', alpha=0.3)
    ax2.set_title('Drawdown (%)', fontsize=14)
    ax2.set_ylabel('Drawdown %', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Daily Returns
    if 'daily_returns' in results.columns:
        # Convert to daily frequency
        daily_data = results.set_index('timestamp').resample('D').last().dropna()
        
        if len(daily_data) > 1:
            ax3 = fig1.add_subplot(gs1[1, 1])
            ax3.bar(daily_data.index, daily_data['daily_returns'] * 100, color='blue', alpha=0.6)
            ax3.set_title('Daily Returns (%)', fontsize=14)
            ax3.set_ylabel('Return %', fontsize=12)
            ax3.grid(True, alpha=0.3)
    
    # Plot 4: Trade Outcomes
    ax4 = fig1.add_subplot(gs1[2, 0])
    trades['duration'] = (trades['exit_time'] - trades['entry_time']).dt.total_seconds() / 3600  # hours
    
    ax4.scatter(trades.index, trades['profit_pips'], 
               c=['green' if p > 0 else 'red' for p in trades['profit_pips']], 
               s=50, alpha=0.7)
    ax4.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    ax4.set_title('Trade Outcomes (pips)', fontsize=14)
    ax4.set_xlabel('Trade Number', fontsize=12)
    ax4.set_ylabel('Profit/Loss (pips)', fontsize=12)
    ax4.grid(True, alpha=0.3)
    
    # Plot 5: Trade Duration vs Profit
    ax5 = fig1.add_subplot(gs1[2, 1])
    scatter = ax5.scatter(trades['duration'], trades['profit_pips'], 
                         c=['green' if p > 0 else 'red' for p in trades['profit_pips']], 
                         s=50, alpha=0.7)
    ax5.axhline(y=0, color='k', linestyle='-', alpha=0.3)
    ax5.set_title('Trade Duration vs. Profit', fontsize=14)
    ax5.set_xlabel('Duration (hours)', fontsize=12)
    ax5.set_ylabel('Profit/Loss (pips)', fontsize=12)
    ax5.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # === Figure 2: Trade Analysis by Currency Pair ===
    fig2 = plt.figure(figsize=(14, 12))
    gs2 = fig2.add_gridspec(2, 2)
    
    # Plot 1: Performance by Pair
    ax1 = fig2.add_subplot(gs2[0, 0])
    
    # Group by pair and calculate metrics
    pair_metrics = trades.groupby('pair').agg({
        'profit_money': ['sum', 'mean', 'count'],
        'profit_pips': ['sum', 'mean']
    })
    
    # Create a horizontal bar chart for profit by pair
    pairs = pair_metrics.index
    profits = pair_metrics[('profit_money', 'sum')]
    colors = ['green' if p > 0 else 'red' for p in profits]
    
    ax1.barh(pairs, profits, color=colors)
    ax1.set_title('Total Profit by Currency Pair', fontsize=14)
    ax1.set_xlabel('Profit', fontsize=12)
    ax1.grid(True, alpha=0.3)
    
    # Plot 2: Win Rate by Pair
    ax2 = fig2.add_subplot(gs2[0, 1])
    
    # Calculate win rate for each pair
    win_rates = {}
    for pair in trades['pair'].unique():
        pair_trades = trades[trades['pair'] == pair]
        wins = len(pair_trades[pair_trades['profit_money'] > 0])
        total = len(pair_trades)
        win_rates[pair] = (wins / total * 100) if total > 0 else 0
    
    pairs = list(win_rates.keys())
    rates = list(win_rates.values())
    
    ax2.barh(pairs, rates, color='blue')
    ax2.set_title('Win Rate by Currency Pair (%)', fontsize=14)
    ax2.set_xlabel('Win Rate %', fontsize=12)
    ax2.set_xlim(0, 100)
    ax2.grid(True, alpha=0.3)
    
    # Plot 3: Trade Count by Trading Session
    ax3 = fig2.add_subplot(gs2[1, 0])
    
    # Determine trading session for each trade
    trades['hour'] = trades['entry_time'].dt.hour
    
    # Define sessions (UTC time)
    trades['session'] = 'N/A'
    trades.loc[(trades['hour'] >= 0) & (trades['hour'] < 8), 'session'] = 'Asian'
    trades.loc[(trades['hour'] >= 8) & (trades['hour'] < 16), 'session'] = 'London'
    trades.loc[(trades['hour'] >= 16) & (trades['hour'] < 24), 'session'] = 'New York'
    
    # Group by session
    session_counts = trades.groupby('session').size()
    
    ax3.bar(session_counts.index, session_counts.values, color='purple')
    ax3.set_title('Trade Count by Trading Session', fontsize=14)
    ax3.set_ylabel('Number of Trades', fontsize=12)
    ax3.grid(True, alpha=0.3)
    
    # Plot 4: Profit Distribution
    ax4 = fig2.add_subplot(gs2[1, 1])
    
    ax4.hist(trades['profit_pips'], bins=20, color='blue', alpha=0.7)
    ax4.axvline(x=0, color='r', linestyle='--')
    ax4.set_title('Profit Distribution (pips)', fontsize=14)
    ax4.set_xlabel('Profit/Loss (pips)', fontsize=12)
    ax4.set_ylabel('Frequency', fontsize=12)
    ax4.grid(True, alpha=0.3)
    
    plt.tight_layout()
    
    # === Figure 3: Strategy Parameter Analysis ===
    if strategy_params is not None:
        fig3 = plt.figure(figsize=(14, 6))
        
        # Create a table of strategy parameters
        param_list = [(k, v) for k, v in strategy_params.items()]
        param_table = plt.table(
            cellText=[[str(v)] for _, v in param_list],
            rowLabels=[k for k, _ in param_list],
            colWidths=[0.8],
            loc='center'
        )
        param_table.auto_set_font_size(False)
        param_table.set_fontsize(12)
        param_table.scale(1, 1.5)
        plt.axis('off')
        plt.title('Strategy Parameters', fontsize=16)
        
        plt.tight_layout()
    
    # Display key metrics in text
    total_trades = len(trades)
    winning_trades = len(trades[trades['profit_money'] > 0])
    win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
    
    avg_profit = trades[trades['profit_money'] > 0]['profit_money'].mean() if winning_trades > 0 else 0
    avg_loss = trades[trades['profit_money'] <= 0]['profit_money'].mean() if (total_trades - winning_trades) > 0 else 0
    
    profit_factor = abs(
        trades[trades['profit_money'] > 0]['profit_money'].sum() / 
        trades[trades['profit_money'] <= 0]['profit_money'].sum()
    ) if trades[trades['profit_money'] <= 0]['profit_money'].sum() != 0 else float('inf')
    
    total_return = (results['equity'].iloc[-1] / results['equity'].iloc[0] - 1) * 100
    max_drawdown = results['drawdown'].min() * 100
    
    metric_text = (
        f"Total Return: {total_return:.2f}%\n"
        f"Total Trades: {total_trades}\n"
        f"Win Rate: {win_rate:.2f}%\n"
        f"Profit Factor: {profit_factor:.2f}\n"
        f"Average Profit: {avg_profit:.2f}\n"
        f"Average Loss: {avg_loss:.2f}\n"
        f"Maximum Drawdown: {max_drawdown:.2f}%"
    )
    
    print(metric_text)
    
    return fig1, fig2, fig3 if strategy_params is not None else (fig1, fig2)

# Example usage (would be used with actual backtest results)
# performance_figs = visualize_backtest_results(backtest_results, trade_data, scalping_params)
```

#### Walk-Forward Optimization Framework for Scalping Strategies

```python
def walk_forward_optimization(strength_df, price_df, param_ranges, initial_capital=10000,
                             train_window=60, test_window=30, sliding_window=True):
    """
    Perform walk-forward optimization of currency strength scalping strategy parameters.
    
    Parameters:
    strength_df: DataFrame with currency strength data
    price_df: DataFrame with price data
    param_ranges: Dictionary with parameter ranges to test
    initial_capital: Starting capital
    train_window: Number of periods for training (30 periods = 15 hours with 30min data)
    test_window: Number of periods for testing (30 periods = 15 hours with 30min data)
    sliding_window: If True, use sliding window; if False, use anchored window
    
    Returns:
    Dictionary with optimization results
    """
    import itertools
    
    # Calculate total number of periods
    total_periods = len(strength_df)
    
    # Initialize results storage
    all_test_results = []
    optimal_params = []
    
    # Generate all parameter combinations to test
    param_names = list(param_ranges.keys())
    param_values = list(param_ranges.values())
    param_combinations = list(itertools.product(*param_values))
    
    print(f"Testing {len(param_combinations)} parameter combinations")
    
    # Walk forward through the data
    anchor = 0 if not sliding_window else None
    
    for i in range(train_window, total_periods - test_window, test_window):
        print(f"Processing window {i}/{total_periods}")
        
        # Define training and testing windows
        if sliding_window:
            train_start = i - train_window
            train_end = i
        else:
            train_start = anchor
            train_end = i
        
        test_start = i
        test_end = i + test_window
        
        # Slice the data
        train_strength = strength_df.iloc[train_start:train_end].copy()
        train_price = price_df.iloc[train_start:train_end].copy()
        
        test_strength = strength_df.iloc[test_start:test_end].copy()
        test_price = price_df.iloc[test_start:test_end].copy()
        
        # Store performance metrics for each parameter combination
        train_performance = []
        
        # Test each parameter combination on training data
        for combo_idx, combo in enumerate(param_combinations):
            # Create parameter dictionary
            params = {name: value for name, value in zip(param_names, combo)}
            
            # Run backtest on training data
            try:
                train_results, train_trades = backtest_scalping_strategy(
                    train_strength, train_price, 
                    strategy_params=params,
                    initial_capital=initial_capital
                )
                
                # Calculate performance metrics
                if not train_trades.empty:
                    total_return = (train_results['equity'].iloc[-1] / initial_capital - 1) * 100
                    sharpe_ratio = train_results['daily_returns'].mean() / train_results['daily_returns'].std() * np.sqrt(252) if train_results['daily_returns'].std() > 0 else 0
                    max_dd = train_results['drawdown'].min() * 100
                    
                    winning_trades = len(train_trades[train_trades['profit_money'] > 0])
                    total_trades = len(train_trades)
                    win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
                    
                    # Calculate profit factor
                    gross_profit = train_trades[train_trades['profit_money'] > 0]['profit_money'].sum()
                    gross_loss = abs(train_trades[train_trades['profit_money'] <= 0]['profit_money'].sum())
                    profit_factor = gross_profit / gross_loss if gross_loss > 0 else float('inf')
                    
                    # Store metrics
                    train_performance.append({
                        'params': params,
                        'return': total_return,
                        'sharpe': sharpe_ratio,
                        'max_drawdown': max_dd,
                        'win_rate': win_rate,
                        'profit_factor': profit_factor,
                        'trades': total_trades
                    })
                else:
                    # No trades generated
                    train_performance.append({
                        'params': params,
                        'return': 0,
                        'sharpe': 0,
                        'max_drawdown': 0,
                        'win_rate': 0,
                        'profit_factor': 0,
                        'trades': 0
                    })
            except Exception as e:
                print(f"Error with parameter combination {combo}: {e}")
                train_performance.append({
                    'params': params,
                    'return': float('-inf'),
                    'sharpe': float('-inf'),
                    'max_drawdown': float('-inf'),
                    'win_rate': 0,
                    'profit_factor': 0,
                    'trades': 0
                })
        
        # Find optimal parameters (those with highest Sharpe ratio)
        # Only consider parameter sets that generate at least 5 trades
        valid_performance = [p for p in train_performance if p['trades'] >= 5]
        
        if valid_performance:
            # Sort by Sharpe ratio (highest first)
            valid_performance.sort(key=lambda x: x['sharpe'], reverse=True)
            best_params = valid_performance[0]['params']
        else:
            # If no valid parameter sets, use default parameters
            best_params = {
                'strength_threshold': 0.25,
                'momentum_threshold': 0.15,
                'profit_target': 10,
                'stop_loss': 15,
                'trailing_stop': True,
                'trailing_distance': 5,
                'filter_volatility': True,
                'volatility_min': 0.1
            }
        
        # Store optimal parameters for this window
        optimal_params.append({
            'window_start': test_start,
            'window_end': test_end,
            'params': best_params
        })
        
        # Test optimal parameters on test window
        test_results, test_trades = backtest_scalping_strategy(
            test_strength, test_price,
            strategy_params=best_params,
            initial_capital=initial_capital
        )
        
        # Calculate test performance
        if not test_trades.empty:
            test_return = (test_results['equity'].iloc[-1] / initial_capital - 1) * 100
            test_sharpe = test_results['daily_returns'].mean() / test_results['daily_returns'].std() * np.sqrt(252) if test_results['daily_returns'].std() > 0 else 0
            test_max_dd = test_results['drawdown'].min() * 100
            
            test_winning = len(test_trades[test_trades['profit_money'] > 0])
            test_total = len(test_trades)
            test_win_rate = test_winning / test_total * 100 if test_total > 0 else 0
            
            # Calculate profit factor
            test_gross_profit = test_trades[test_trades['profit_money'] > 0]['profit_money'].sum()
            test_gross_loss = abs(test_trades[test_trades['profit_money'] <= 0]['profit_money'].sum())
            test_profit_factor = test_gross_profit / test_gross_loss if test_gross_loss > 0 else float('inf')
        else:
            test_return = 0
            test_sharpe = 0
            test_max_dd = 0
            test_win_rate = 0
            test_profit_factor = 0
            test_total = 0
        
        # Store test results
        all_test_results.append({
            'window_start': test_start,
            'window_end': test_end,
            'params': best_params,
            'return': test_return,
            'sharpe': test_sharpe,
            'max_drawdown': test_max_dd,
            'win_rate': test_win_rate,
            'profit_factor': test_profit_factor,
            'trades': test_total
        })
    
    # Consolidate results
    consolidated_results = {
        'test_windows': all_test_results,
        'optimal_params': optimal_params
    }
    
    # Print summary statistics
    if all_test_results:
        avg_return = np.mean([r['return'] for r in all_test_results])
        avg_sharpe = np.mean([r['sharpe'] for r in all_test_results])
        avg_win_rate = np.mean([r['win_rate'] for r in all_test_results])
        total_trades = sum([r['trades'] for r in all_test_results])
        
        print(f"=== Walk-Forward Optimization Summary ===")
        print(f"Number of test windows: {len(all_test_results)}")
        print(f"Average return: {avg_return:.2f}%")
        print(f"Average Sharpe ratio: {avg_sharpe:.2f}")
        print(f"Average win rate: {avg_win_rate:.2f}%")
        print(f"Total trades: {total_trades}")
    
    return consolidated_results

# Example parameter ranges for optimization
param_ranges_example = {
    'strength_threshold': [0.2, 0.25, 0.3, 0.35],
    'momentum_threshold': [0.1, 0.15, 0.2],
    'profit_target': [8, 10, 12],
    'stop_loss': [10, 12, 15],
    'trailing_stop': [True, False],
    'filter_volatility': [True, False]
}

# Example usage (would be used with actual data)
# wfo_results = walk_forward_optimization(combined_df, price_df, param_ranges_example)
```### 6. Backtesting Considerations for Algorithmic Strategies

#### Comprehensive Scalping Strategy Backtesting Framework

```python
def backtest_scalping_strategy(strength_df, price_df, strategy_params=None, initial_capital=10000, 
                          pairs=None, pip_value=0.0001, commission=2.0, slippage=1.0):
    """
    Comprehensive backtesting framework specifically optimized for currency strength-based scalping strategies.
    
    Parameters:
    strength_df: DataFrame with currency strength data and indicators
    price_df: DataFrame with OHLC price data for currency pairs
    strategy_params: Dictionary with strategy parameters (uses defaults if None)
    initial_capital: Starting capital in account currency
    pairs: List of pairs to trade (uses major pairs if None)
    pip_value: Value of 1 pip in account currency
    commission: Commission per trade in account currency
    slippage: Expected slippage in pips
    
    Returns:
    DataFrame with detailed backtest results and performance metrics
    """
    # Set default strategy parameters if none provided
    if strategy_params is None:
        strategy_params = {
            'strength_threshold': 0.25,       # Minimum strength change to consider
            'momentum_threshold': 0.15,       # Minimum momentum to confirm trend
            'rsi_oversold': 30,               # RSI oversold threshold
            'rsi_overbought': 70,             # RSI overbought threshold
            'profit_target': 10,              # Take profit in pips
            'stop_loss': 15,                  # Stop loss in pips
            'trailing_stop': True,            # Use trailing stop
            'trailing_distance': 5,           # Trailing stop distance in pips
            'max_trades_per_day': 5,          # Maximum trades per day
            'time_exit': 12,                  # Force exit after N periods (6 hours with 30min data)
            'filter_volatility': True,        # Filter trades based on volatility
            'volatility_min': 0.08,           # Minimum volatility to trade
            'trade_size_percent': 2.0,        # Risk per trade (% of account)
            'max_correlation': 0.7            # Maximum correlation between active trades
        }
    
    # Set default pairs if none provided
    if pairs is None:
        pairs = ['EURUSD', 'GBPUSD', 'USDJPY', 'USDCHF', 'AUDUSD', 'USDCAD']
    
    # Initialize results dataframe
    results = pd.DataFrame(index=strength_df.index)
    results['timestamp'] = strength_df['timestamp']
    results['equity'] = initial_capital
    
    # Initialize trade tracking
    open_trades = {}         # Dictionary to store open trade details
    closed_trades = []       # List to store closed trade details
    daily_trades = {}        # Dictionary to track daily trade counts
    
    # Track account statistics
    equity_curve = [initial_capital]
    available_margin = initial_capital
    
    # Process each timestamp
    for i in range(1, len(strength_df)):
        current_time = strength_df['timestamp'].iloc[i]
        prev_time = strength_df['timestamp'].iloc[i-1]
        
        # Track today's date for daily trade limits
        today = pd.to_datetime(current_time).date()
        if today not in daily_trades:
            daily_trades[today] = 0
        
        # === Update open trades ===
        trades_to_close = []
        
        for trade_id, trade in open_trades.items():
            pair = trade['pair']
            
            # Skip if price data is not available for this pair
            if pair not in price_df.columns:
                continue
            
            # Get current price data
            try:
                current_price = price_df[pair].iloc[i]
                prev_price = price_df[pair].iloc[i-1]
            except:
                # Skip if price data is missing
                continue
            
            # Calculate current P&L in pips
            if trade['direction'] == 'long':
                pip_profit = (current_price - trade['entry_price']) / pip_value
            else:  # short
                pip_profit = (trade['entry_price'] - current_price) / pip_value
            
            trade['current_profit_pips'] = pip_profit
            trade['current_profit_money'] = pip_profit * pip_value * trade['position_size']
            
            # Check stop loss
            if trade['trailing_stop_price'] is not None:
                stop_level = trade['trailing_stop_price']
            else:
                stop_level = trade['stop_loss_price']
            
            # Check if stop loss is hit
            if (trade['direction'] == 'long' and current_price <= stop_level) or \
               (trade['direction'] == 'short' and current_price >= stop_level):
                trade['exit_price'] = stop_level
                trade['exit_time'] = current_time
                trade['exit_reason'] = 'stop_loss'
                trade['profit_pips'] = -trade['stop_loss']  # Negative pips
                trade['profit_money'] = -trade['stop_loss'] * pip_value * trade['position_size']
                trades_to_close.append(trade_id)
                continue
            
            # Check take profit
            if (trade['direction'] == 'long' and current_price >= trade['take_profit_price']) or \
               (trade['direction'] == 'short' and current_price <= trade['take_profit_price']):
                trade['exit_price'] = trade['take_profit_price']
                trade['exit_time'] = current_time
                trade['exit_reason'] = 'take_profit'
                trade['profit_pips'] = trade['profit_target']
                trade['profit_money'] = trade['profit_target'] * pip_value * trade['position_size']
                trades_to_close.append(trade_id)
                continue
            
            # Check time-based exit
            periods_open = i - trade['entry_index']
            if periods_open >= strategy_params['time_exit']:
                trade['exit_price'] = current_price
                trade['exit_time'] = current_time
                trade['exit_reason'] = 'time_exit'
                trade['profit_pips'] = pip_profit
                trade['profit_money'] = pip_profit * pip_value * trade['position_size']
                trades_to_close.append(trade_id)
                continue
            
            # Update trailing stop if enabled
            if strategy_params['trailing_stop'] and pip_profit > strategy_params['trailing_distance']:
                if trade['direction'] == 'long':
                    new_stop = current_price - strategy_params['trailing_distance'] * pip_value
                    if trade['trailing_stop_price'] is None or new_stop > trade['trailing_stop_price']:
                        trade['trailing_stop_price'] = new_stop
                else:  # short
                    new_stop = current_price + strategy_params['trailing_distance'] * pip_value
                    if trade['trailing_stop_price'] is None or new_stop < trade['trailing_stop_price']:
                        trade['trailing_stop_price'] = new_stop
        
        # Close trades and update equity
        total_profit = 0
        for trade_id in trades_to_close:
            trade = open_trades.pop(trade_id)
            closed_trades.append(trade)
            total_profit += trade['profit_money']
            available_margin += trade['margin_required'] + trade['profit_money']
        
        # Update equity
        current_equity = equity_curve[-1] + total_profit
        equity_curve.append(current_equity)
        
        # === Generate new trade signals ===
        
        # Skip if maximum daily trades reached
        if daily_trades[today] >= strategy_params['max_trades_per_day']:
            results.loc[results.index[i], 'equity'] = current_equity
            continue
        
        # Check for new trade opportunities
        for pair in pairs:
            # Skip pairs we're already trading
            if any(t['pair'] == pair for t in open_trades.values()):
                continue
            
            # Get price data
            if pair not in price_df.columns:
                continue
            
            # Parse pair into base and quote currencies
            if pair in ['USDJPY', 'USDCHF', 'USDCAD']:  # USD is base
                base, quote = 'USD', pair[3:]
            else:  # USD is quote
                base, quote = pair[:3], 'USD'
            
            # Check if we have strength data for these currencies
            if f'{base}_Change' not in strength_df.columns or f'{quote}_Change' not in strength_df.columns:
                continue
            
            # Calculate strength differential
            strength_diff = strength_df[f'{base}_Change'].iloc[i] - strength_df[f'{quote}_Change'].iloc[i]
            
            # Calculate momentum if available
            momentum_diff = 0
            if f'{base}_STMomentum' in strength_df.columns and f'{quote}_STMomentum' in strength_df.columns:
                momentum_diff = strength_df[f'{base}_STMomentum'].iloc[i] - strength_df[f'{quote}_STMomentum'].iloc[i]
            
            # Check RSI if available
            base_rsi = strength_df.get(f'{base}_RSI_9', pd.Series(50, index=strength_df.index)).iloc[i]
            quote_rsi = strength_df.get(f'{quote}_RSI_9', pd.Series(50, index=strength_df.index)).iloc[i]
            
            # Check volatility if filtering enabled
            if strategy_params['filter_volatility']:
                volatility = strength_df.get(f'{pair}_Volatility', 
                                             pd.Series(strategy_params['volatility_min'] + 0.01, 
                                                      index=strength_df.index)).iloc[i]
                if volatility < strategy_params['volatility_min']:
                    continue
            
            # Generate trading signals
            long_signal = False
            short_signal = False
            
            # For pairs where USD is the quote currency (e.g., EUR/USD)
            if pair not in ['USDJPY', 'USDCHF', 'USDCAD']:
                # Long signal: Base strengthening vs Quote
                long_signal = (
                    strength_diff > strategy_params['strength_threshold'] and
                    momentum_diff > strategy_params['momentum_threshold'] and
                    base_rsi < strategy_params['rsi_overbought']
                )
                
                # Short signal: Quote strengthening vs Base
                short_signal = (
                    strength_diff < -strategy_params['strength_threshold'] and
                    momentum_diff < -strategy_params['momentum_threshold'] and
                    base_rsi > strategy_params['rsi_oversold']
                )
            # For pairs where USD is the base currency (e.g., USD/JPY)
            else:
                # Long signal: Base strengthening vs Quote
                long_signal = (
                    strength_diff > strategy_params['strength_threshold'] and
                    momentum_diff > strategy_params['momentum_threshold'] and
                    base_rsi < strategy_params['rsi_overbought']
                )
                
                # Short signal: Quote strengthening vs Base
                short_signal = (
                    strength_diff < -strategy_params['strength_threshold'] and
                    momentum_diff < -strategy_params['momentum_threshold'] and
                    base_rsi > strategy_params['rsi_oversold']
                )
            
            # Check correlation with existing trades if needed
            if open_trades and strategy_params['max_correlation'] < 1.0:
                # Get recent price data for correlation calculation
                recent_window = 12  # 6 hours with 30min data
                
                for existing_trade in open_trades.values():
                    existing_pair = existing_trade['pair']
                    
                    if existing_pair in price_df.columns and pair in price_df.columns:
                        # Calculate correlation between pairs
                        start_idx = max(0, i - recent_window)
                        pair1_prices = price_df[existing_pair].iloc[start_idx:i]
                        pair2_prices = price_df[pair].iloc[start_idx:i]
                        
                        if len(pair1_prices) > 3 and len(pair2_prices) > 3:
                            correlation = pair1_prices.corr(pair2_prices)
                            
                            # Skip this pair if correlation is too high
                            if abs(correlation) > strategy_params['max_correlation']:
                                long_signal = False
                                short_signal = False
                                break
            
            # Execute trades if signals are triggered
            if long_signal or short_signal:
                # Get current price
                current_price = price_df[pair].iloc[i]
                
                # Determine trade direction
                direction = 'long' if long_signal else 'short'
                
                # Calculate position size based on risk percentage
                risk_amount = current_equity * (strategy_params['trade_size_percent'] / 100)
                stop_loss_amount = strategy_params['stop_loss'] * pip_value
                position_size = risk_amount / stop_loss_amount
                
                # Calculate margin required (simplified)
                leverage = 100  # Assume 100:1 leverage
                margin_required = (current_price * position_size) / leverage
                
                # Check if we have enough margin
                if margin_required > available_margin:
                    # Adjust position size based on available margin
                    position_size = (available_margin * leverage) / current_price
                    
                    # Skip if position would be too small
                    if position_size < 0.01:
                        continue
                
                # Calculate entry, stop loss, and take profit prices
                if direction == 'long':
                    entry_price = current_price
                    stop_loss_price = entry_price - strategy_params['stop_loss'] * pip_value
                    take_profit_price = entry_price + strategy_params['profit_target'] * pip_value
                else:  # short
                    entry_price = current_price
                    stop_loss_price = entry_price + strategy_params['stop_loss'] * pip_value
                    take_profit_price = entry_price - strategy_params['profit_target'] * pip_value
                
                # Create new trade
                trade_id = f"{pair}_{i}_{direction}"
                new_trade = {
                    'trade_id': trade_id,
                    'pair': pair,
                    'direction': direction,
                    'entry_price': entry_price,
                    'entry_time': current_time,
                    'entry_index': i,
                    'stop_loss_price': stop_loss_price,
                    'take_profit_price': take_profit_price,
                    'trailing_stop_price': None,
                    'position_size': position_size,
                    'stop_loss': strategy_params['stop_loss'],
                    'profit_target': strategy_params['profit_target'],
                    'margin_required': margin_required,
                    'exit_price': None,
                    'exit_time': None,
                    'exit_reason': None,
                    'profit_pips': None,
                    'profit_money': None,
                    'current_profit_pips': 0,
                    'current_profit_money': 0
                }
                
                # Add trade to open trades
                open_trades[trade_id] = new_trade
                
                # Update available margin
                available_margin -= margin_required
                
                # Increment daily trade counter
                daily_trades[today] += 1
        
        # Update equity in results
        results.loc[results.index[i], 'equity'] = current_equity
    
    # Close any remaining open trades at the last price
    final_timestamp = strength_df['timestamp'].iloc[-1]
    
    for trade_id, trade in open_trades.items():
        pair = trade['pair']
        
        if pair in price_df.columns:
            final_price = price_df[pair].iloc[-1]
            
            if trade['direction'] == 'long':
                pip_profit = (final_price - trade['entry_price']) / pip_value
            else:  # short
                pip_profit = (trade['entry_price'] - final_price) / pip_value
            
            trade['exit_price'] = final_price
            trade['exit_time'] = final_timestamp
            trade['exit_reason'] = 'backtest_end'
            trade['profit_pips'] = pip_profit
            trade['profit_money'] = pip_profit * pip_value * trade['position_size']
            
            closed_trades.append(trade)
    
    # Combine all trades into a single DataFrame
    all_trades = pd.DataFrame(closed_trades)
    
    # Calculate performance metrics
    if not all_trades.empty:
        total_trades = len(all_trades)
        winning_trades = len(all_trades[all_trades['profit_money'] > 0])
        losing_trades = len(all_trades[all_trades['profit_money'] <= 0])
        win_rate = winning_trades / total_trades * 100 if total_trades > 0 else 0
        
        avg_profit = all_trades[all_trades['profit_money'] > 0]['profit_money'].mean() if winning_trades > 0 else 0
        avg_loss = all_trades[all_trades['profit_money'] <= 0]['profit_money'].mean() if losing_trades > 0 else 0
        
        profit_factor = abs(all_trades[all_trades['profit_money'] > 0]['profit_money'].sum() / 
                            all_trades[all_trades['profit_money'] <= 0]['profit_money'].sum()) if losing_trades > 0 else float('inf')
        
        total_return = (results['equity'].iloc[-1] / initial_capital - 1) * 100
        
        # Calculate daily returns for Sharpe ratio
        results['daily_returns'] = results['equity'].pct_change()
        daily_sharpe = results['daily_returns'].mean() / results['daily_returns'].std() * np.sqrt(252) if results['daily_returns'].std() > 0 else 0
        
        # Calculate drawdown
        results['drawdown'] = results['equity'] / results['equity'].cummax() - 1
        max_drawdown = results['drawdown'].min() * 100
        
        print(f"===== Backtest Results =====")
        print(f"Total Return: {total_return:.2f}%")
        print(f"Total Trades: {total_trades}")
        print(f"Win Rate: {win_rate:.2f}%")
        print(f"Profit Factor: {profit_factor:.2f}")
        print(f"Average Profit: {avg_profit:.2f}")
        print(f"Average Loss: {avg_loss:.2f}")
        print(f"Sharpe Ratio: {daily_sharpe:.2f}")
        print(f"Maximum Drawdown: {max_drawdown:.2f}%")
    
    return results, all_trades

# Example strategy parameters
scalping_params = {
    'strength_threshold': 0.3,
    'momentum_threshold': 0.15,
    'rsi_oversold': 30,
    'rsi_overbought': 70,
    'profit_target': 8,
    'stop_loss': 12,
    'trailing_stop': True,
    'trailing_distance': 4,
    'max_trades_per_day': 5,
    'time_exit': 8,
    'filter_volatility': True,
    'volatility_min': 0.1,
    'trade_size_percent': 1.5,
    'max_correlation': 0.6
}

# Example usage (would be used with actual data)
# backtest_results, trade_data = backtest_scalping_strategy(combined_df, price_df, scalping_params)
```# Currency Strength as Price Data - Indicator Development
## Focus: Scalping & Intraday Trading Strategies

## Introduction

This report explores the innovative approach of using currency strength data from 28 major currency pairs as the foundation for technical indicator development. We focus specifically on applications for scalping, intraday trading, and algorithmic statistical strategies, with an emphasis on improving entry/exit timing and market direction indication.

## Data Transformation Process

### Percentage Change Calculation

We start by calculating the percentage change of each currency's strength value relative to its previous 30-minute value. This forms our base dataset:

```python
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# Assuming we have a DataFrame with currency strength data
# Example structure:
# df = pd.DataFrame({
#     'timestamp': pd.date_range(start='2023-10-27 10:00:00', periods=48, freq='30min'),
#     'USD': [value1, value2, ...],
#     'EUR': [value1, value2, ...],
#     ... other currencies
# })

def calculate_percentage_change(df):
    """Calculate percentage change for each currency's strength."""
    # Create a new DataFrame for storing percentage changes
    pct_change_df = pd.DataFrame({'timestamp': df['timestamp']})
    
    # Calculate percentage change for each currency
    for currency in df.columns:
        if currency != 'timestamp':
            pct_change_df[f'{currency}_Change'] = df[currency].pct_change() * 100
    
    # Drop the first row which contains NaN values
    pct_change_df = pct_change_df.dropna()
    
    return pct_change_df

# Apply the function
pct_change_df = calculate_percentage_change(df)

# Display sample of the transformed data
print(pct_change_df.head())
```

### Rate of Change (ROC) Calculation

Next, we calculate the Rate of Change (ROC) over different time periods to capture momentum:

```python
def calculate_roc(df, windows=[2, 8, 24]):  # 1hr, 4hr, 12hr (assuming 30min intervals)
    """Calculate Rate of Change for different window lengths."""
    roc_df = df.copy()
    
    for currency in df.columns:
        if '_Change' in currency:
            for window in windows:
                roc_df[f'{currency}_ROC_{window}'] = df[currency].pct_change(periods=window) * 100
    
    # Drop rows with NaN values
    roc_df = roc_df.dropna()
    
    return roc_df

# Apply the function
roc_df = calculate_roc(pct_change_df)
```

## Indicator Development for Scalping & Intraday Trading

### 1. Adapting Traditional Price Indicators for Short Timeframes

#### Fast Moving Averages for Quick Signals

```python
def calculate_fast_moving_averages(df, short_window=3, medium_window=7, long_window=14):
    """Calculate fast moving averages optimized for short timeframes."""
    ma_df = df.copy()
    
    for currency in df.columns:
        if '_Change' in currency:
            # Short-term MA (1.5 hours with 30min data)
            ma_df[f'{currency}_SMA_{short_window}'] = df[currency].rolling(window=short_window).mean()
            
            # Medium-term MA (3.5 hours with 30min data)
            ma_df[f'{currency}_SMA_{medium_window}'] = df[currency].rolling(window=medium_window).mean()
            
            # Long-term MA (7 hours with 30min data)
            ma_df[f'{currency}_SMA_{long_window}'] = df[currency].rolling(window=long_window).mean()
            
            # Exponential MAs for more responsive signals
            ma_df[f'{currency}_EMA_{short_window}'] = df[currency].ewm(span=short_window, adjust=False).mean()
            ma_df[f'{currency}_EMA_{medium_window}'] = df[currency].ewm(span=medium_window, adjust=False).mean()
    
    return ma_df

# Apply the function
ma_df = calculate_fast_moving_averages(pct_change_df)
```

#### Scalping-Optimized RSI with Short Lookback Period

```python
def calculate_fast_rsi(df, window=9):  # 4.5 hours with 30min data
    """Calculate RSI with shorter window for scalping opportunities."""
    rsi_df = df.copy()
    
    for currency in df.columns:
        if '_Change' in currency:
            # Calculate diff
            delta = df[currency].diff()
            
            # Calculate gain and loss
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            
            # Calculate average gain and loss with smaller window
            avg_gain = gain.rolling(window=window).mean()
            avg_loss = loss.rolling(window=window).mean()
            
            # Calculate RS and RSI
            rs = avg_gain / avg_loss
            rsi_df[f'{currency}_RSI_{window}'] = 100 - (100 / (1 + rs))
            
            # Calculate extreme overbought/oversold levels (specific for currency strength)
            rsi_df[f'{currency}_Overbought'] = rsi_df[f'{currency}_RSI_{window}'] > 75
            rsi_df[f'{currency}_Oversold'] = rsi_df[f'{currency}_RSI_{window}'] < 25
    
    return rsi_df

# Apply the function
rsi_df = calculate_fast_rsi(pct_change_df)
```

#### Intraday Bollinger Bands (Narrower for Quick Signals)

```python
def calculate_scalping_bollinger_bands(df, window=10, num_std=1.5):
    """Calculate Bollinger Bands optimized for scalping with narrower bands."""
    bb_df = df.copy()
    
    for currency in df.columns:
        if '_Change' in currency:
            # Calculate rolling mean and standard deviation
            bb_df[f'{currency}_BB_MA'] = df[currency].rolling(window=window).mean()
            rolling_std = df[currency].rolling(window=window).std()
            
            # Calculate upper and lower bands with tighter standard deviation multiplier
            bb_df[f'{currency}_BB_Upper'] = bb_df[f'{currency}_BB_MA'] + (rolling_std * num_std)
            bb_df[f'{currency}_BB_Lower'] = bb_df[f'{currency}_BB_MA'] - (rolling_std * num_std)
            
            # Calculate bandwidth for volatility assessment
            bb_df[f'{currency}_BB_Width'] = (bb_df[f'{currency}_BB_Upper'] - bb_df[f'{currency}_BB_Lower']) / bb_df[f'{currency}_BB_MA']
            
            # Identify potential breakouts
            bb_df[f'{currency}_BB_Breakout_Up'] = df[currency] > bb_df[f'{currency}_BB_Upper']
            bb_df[f'{currency}_BB_Breakout_Down'] = df[currency] < bb_df[f'{currency}_BB_Lower']
    
    return bb_df

# Apply the function
bb_df = calculate_scalping_bollinger_bands(pct_change_df)
```

### 2. Momentum and Volatility Analysis for Rapid Decision Making

#### Ultra-Short-Term Momentum Indicator (5-15 Minutes)

```python
def calculate_ultra_short_momentum(df, short_window=1, medium_window=2):  # 5-15 mins with 5min resampled data
    """Calculate ultra-short-term momentum for quick scalping decisions."""
    # First resample the data to 5-minute intervals if possible
    # For this example, we'll assume we're working with the original 30min data
    
    momentum_df = df.copy()
    
    for currency in df.columns:
        if '_Change' in currency:
            # Ultra-short momentum (look at immediate change)
            momentum_df[f'{currency}_Momentum_1'] = df[currency].diff(short_window)
            
            # Short momentum (look at very recent trend)
            momentum_df[f'{currency}_Momentum_2'] = df[currency].diff(medium_window)
            
            # Rate of acceleration (change in momentum)
            momentum_df[f'{currency}_Acceleration'] = momentum_df[f'{currency}_Momentum_1'].diff()
            
            # Momentum strength classification
            momentum_df[f'{currency}_Strong_Up'] = (momentum_df[f'{currency}_Momentum_1'] > 0.2) & (momentum_df[f'{currency}_Momentum_2'] > 0.3)
            momentum_df[f'{currency}_Strong_Down'] = (momentum_df[f'{currency}_Momentum_1'] < -0.2) & (momentum_df[f'{currency}_Momentum_2'] < -0.3)
    
    return momentum_df

# Apply the function
momentum_df = calculate_ultra_short_momentum(pct_change_df)
```

#### Currency Volatility Index

```python
def calculate_currency_volatility_index(df, window=6):  # 3 hours with 30min data
    """Create a volatility index based on average change across all currencies."""
    volatility_df = df.copy()
    
    # Extract only the currency change columns
    change_columns = [col for col in df.columns if '_Change' in col]
    
    # Calculate absolute changes for each currency
    abs_changes = df[change_columns].abs()
    
    # Calculate the average absolute change across all currencies (Volatility Index)
    volatility_df['Volatility_Index'] = abs_changes.mean(axis=1)
    
    # Calculate rolling volatility
    volatility_df['Rolling_Volatility'] = volatility_df['Volatility_Index'].rolling(window=window).mean()
    
    # Identify high volatility periods (useful for scalping)
    volatility_df['High_Volatility'] = volatility_df['Volatility_Index'] > volatility_df['Rolling_Volatility'] * 1.5
    
    # Identify low volatility periods (useful for ranging markets)
    volatility_df['Low_Volatility'] = volatility_df['Volatility_Index'] < volatility_df['Rolling_Volatility'] * 0.5
    
    return volatility_df

# Apply the function
volatility_df = calculate_currency_volatility_index(pct_change_df)
```

### 3. Cross-Currency Correlation Analysis for Rapid Pair Selection

#### Dynamic Correlation Matrix (5-Minute Updates)

```python
def calculate_dynamic_correlation(df, window=12):  # 6 hours with 30min data
    """Calculate dynamic correlation between currencies that updates frequently."""
    # In a real-time trading system, this would be updated every 5 minutes
    
    # Extract only the currency change columns
    change_columns = [col for col in df.columns if '_Change' in col]
    
    # Initialize dictionary to store correlation matrices for each timestamp
    correlation_matrices = {}
    
    # Calculate rolling correlation for each timestamp
    for i in range(window, len(df)):
        # Get the window of data
        window_data = df[change_columns].iloc[i-window:i]
        
        # Calculate correlation matrix
        corr_matrix = window_data.corr()
        
        # Store in dictionary with timestamp as key
        correlation_matrices[df['timestamp'].iloc[i]] = corr_matrix
    
    # Example: Find the strongest positive and negative correlations at the most recent timestamp
    latest_timestamp = df['timestamp'].iloc[-1]
    if latest_timestamp in correlation_matrices:
        latest_corr = correlation_matrices[latest_timestamp]
        
        # Find strongest positive correlations
        np.fill_diagonal(latest_corr.values, np.nan)
        strongest_positive = latest_corr.stack().nlargest(5)
        print("Strongest positive correlations:")
        print(strongest_positive)
        
        # Find strongest negative correlations
        strongest_negative = latest_corr.stack().nsmallest(5)
        print("Strongest negative correlations:")
        print(strongest_negative)
    
    return correlation_matrices

# Apply the function
correlation_matrices = calculate_dynamic_correlation(pct_change_df)
```

#### Correlation-Based Pair Selection for Scalping

```python
def identify_trading_opportunities(correlation_matrices, df, timestamp):
    """Identify trading opportunities based on recent correlation patterns."""
    if timestamp not in correlation_matrices:
        return None
    
    corr_matrix = correlation_matrices[timestamp]
    
    # Extract currency pairs with strong inverse correlation (potential pair trades)
    np.fill_diagonal(corr_matrix.values, np.nan)
    
    # Find pairs with strong negative correlation (good for pair trading)
    negative_corr = corr_matrix.stack().nsmallest(10)
    
    opportunities = []
    for pair, corr_value in negative_corr.items():
        currency1, currency2 = pair
        
        # Get recent strength changes
        currency1_change = df.loc[df['timestamp'] == timestamp, f'{currency1}'].values[0]
        currency2_change = df.loc[df['timestamp'] == timestamp, f'{currency2}'].values[0]
        
        # If currencies are moving in opposite directions with strong momentum
        if (currency1_change > 0.3 and currency2_change < -0.3) or (currency1_change < -0.3 and currency2_change > 0.3):
            opportunities.append({
                'pair': f"{currency1}/{currency2}",
                'correlation': corr_value,
                'currency1_change': currency1_change,
                'currency2_change': currency2_change,
                'trade_idea': "Long" if currency1_change > currency2_change else "Short"
            })
    
    return opportunities

# Example: Identify opportunities at a specific timestamp
sample_timestamp = pct_change_df['timestamp'].iloc[-1]
opportunities = identify_trading_opportunities(correlation_matrices, pct_change_df, sample_timestamp)
print("Trading opportunities:", opportunities)
```

### 4. Custom Indicator Development for Algorithmic Trading

#### Multi-Currency Strength Momentum Alert System

```python
def create_momentum_alert_system(df, threshold=0.5):
    """Create an alert system based on significant momentum across multiple currencies."""
    alert_df = df.copy()
    
    # Extract only the currency change columns
    change_columns = [col for col in df.columns if '_Change' in col]
    
    # Calculate significant positive and negative movements for each currency
    for currency in change_columns:
        alert_df[f'{currency}_Significant_Up'] = df[currency] > threshold
        alert_df[f'{currency}_Significant_Down'] = df[currency] < -threshold
    
    # Count how many currencies are showing significant movement at each timestamp
    alert_df['Num_Significant_Up'] = alert_df[[col for col in alert_df.columns if 'Significant_Up' in col]].sum(axis=1)
    alert_df['Num_Significant_Down'] = alert_df[[col for col in alert_df.columns if 'Significant_Down' in col]].sum(axis=1)
    
    # Create market momentum indicator (positive means more currencies strengthening, negative means more weakening)
    alert_df['Market_Momentum'] = alert_df['Num_Significant_Up'] - alert_df['Num_Significant_Down']
    
    # Generate alerts when market momentum exceeds thresholds
    alert_df['Strong_Bullish_Alert'] = alert_df['Market_Momentum'] >= 3
    alert_df['Strong_Bearish_Alert'] = alert_df['Market_Momentum'] <= -3
    
    return alert_df

# Apply the function
alert_df = create_momentum_alert_system(pct_change_df)
```

#### Scalping Opportunity Detector (SOD)

```python
def create_scalping_opportunity_detector(df, lookback=3, momentum_threshold=0.15, 
                                        strength_threshold=0.25, volatility_min=0.1):
    """
    Create a custom indicator that identifies high-probability scalping opportunities
    by analyzing rapid currency strength changes across multiple pairs.
    
    Parameters:
    df: DataFrame with currency strength data
    lookback: Number of periods to look back for change acceleration
    momentum_threshold: Minimum momentum value to consider
    strength_threshold: Minimum strength change to consider
    volatility_min: Minimum market volatility to trade (filters ranging markets)
    """
    sod_df = df.copy()
    
    # Get base currencies (without the '_Change' suffix)
    change_columns = [col for col in df.columns if '_Change' in col]
    currencies = [col.replace('_Change', '') for col in change_columns]
    
    # Calculate the key components for each currency
    for currency in currencies:
        col = f'{currency}_Change'
        
        # 1. Short-term momentum (rate of change)
        sod_df[f'{currency}_STMomentum'] = df[col].diff(lookback)
        
        # 2. Acceleration (change in momentum)
        sod_df[f'{currency}_Acceleration'] = sod_df[f'{currency}_STMomentum'].diff()
        
        # 3. Volatility (using Bollinger Band width concept)
        bb_width = df[col].rolling(window=lookback*2).std() * 2
        sod_df[f'{currency}_Volatility'] = bb_width / df[col].rolling(window=lookback*2).mean().abs()
        
        # 4. Identify potential reversals (momentum direction change)
        sod_df[f'{currency}_Reversal'] = (
            (sod_df[f'{currency}_STMomentum'] > 0) & 
            (sod_df[f'{currency}_STMomentum'].shift(1) < 0)
        ) | (
            (sod_df[f'{currency}_STMomentum'] < 0) & 
            (sod_df[f'{currency}_STMomentum'].shift(1) > 0)
        )
    
    # === Generate Scalping Signals for Currency Pairs ===
    
    # Define major pairs to track
    major_pairs = [
        ('EUR', 'USD'), ('GBP', 'USD'), ('USD', 'JPY'), 
        ('USD', 'CHF'), ('AUD', 'USD'), ('USD', 'CAD')
    ]
    
    # Calculate the SOD Score for each pair
    for base, quote in major_pairs:
        pair_name = f'{base}{quote}'
        
        # Calculate strength differential (positive means base is stronger than quote)
        if pair_name in ['USDJPY', 'USDCHF', 'USDCAD']:  # USD is base
            strength_diff = sod_df[f'{base}_Change'] - sod_df[f'{quote}_Change']
        else:  # USD is quote
            strength_diff = sod_df[f'{base}_Change'] - sod_df[f'{quote}_Change']
        
        sod_df[f'{pair_name}_StrengthDiff'] = strength_diff
        
        # Calculate momentum differential
        if f'{base}_STMomentum' in sod_df.columns and f'{quote}_STMomentum' in sod_df.columns:
            if pair_name in ['USDJPY', 'USDCHF', 'USDCAD']:  # USD is base
                momentum_diff = sod_df[f'{base}_STMomentum'] - sod_df[f'{quote}_STMomentum']
            else:  # USD is quote
                momentum_diff = sod_df[f'{base}_STMomentum'] - sod_df[f'{quote}_STMomentum']
                
            sod_df[f'{pair_name}_MomentumDiff'] = momentum_diff
        
        # Calculate volatility (average of both currencies)
        if f'{base}_Volatility' in sod_df.columns and f'{quote}_Volatility' in sod_df.columns:
            sod_df[f'{pair_name}_Volatility'] = (
                sod_df[f'{base}_Volatility'] + sod_df[f'{quote}_Volatility']
            ) / 2
        
        # === Calculate SOD Score (Scalping Opportunity Detector) ===
        # Higher absolute value means stronger signal
        # Positive value suggests long, negative suggests short
        
        sod_df[f'{pair_name}_SOD_Score'] = (
            # Strength component
            sod_df[f'{pair_name}_StrengthDiff'] +
            # Momentum component (weighted higher for scalping)
            sod_df.get(f'{pair_name}_MomentumDiff', pd.Series(0, index=sod_df.index)) * 1.5
        )
        
        # Generate trading signals
        # For uptrend entry
        sod_df[f'{pair_name}_Long_Signal'] = (
            # Strong positive SOD score
            (sod_df[f'{pair_name}_SOD_Score'] > strength_threshold) &
            # Rising momentum
            (sod_df.get(f'{pair_name}_MomentumDiff', pd.Series(0, index=sod_df.index)) > momentum_threshold) &
            # Sufficient volatility to trade
            (sod_df.get(f'{pair_name}_Volatility', pd.Series(1, index=sod_df.index)) > volatility_min)
        )
        
        # For downtrend entry
        sod_df[f'{pair_name}_Short_Signal'] = (
            # Strong negative SOD score
            (sod_df[f'{pair_name}_SOD_Score'] < -strength_threshold) &
            # Falling momentum
            (sod_df.get(f'{pair_name}_MomentumDiff', pd.Series(0, index=sod_df.index)) < -momentum_threshold) &
            # Sufficient volatility to trade
            (sod_df.get(f'{pair_name}_Volatility', pd.Series(1, index=sod_df.index)) > volatility_min)
        )
        
        # Calculate signal strength (1-10 scale)
        signal_strength = abs(sod_df[f'{pair_name}_SOD_Score'] * 10).clip(upper=10)
        
        # Assign signal strength to long and short signals
        sod_df[f'{pair_name}_Long_Strength'] = np.where(
            sod_df[f'{pair_name}_Long_Signal'], signal_strength, 0
        )
        
        sod_df[f'{pair_name}_Short_Strength'] = np.where(
            sod_df[f'{pair_name}_Short_Signal'], signal_strength, 0
        )
    
    # === Create Summary Columns ===
    
    # Count total signals at each timestamp
    sod_df['Total_Long_Signals'] = sod_df[[col for col in sod_df.columns if '_Long_Signal' in col]].sum(axis=1)
    sod_df['Total_Short_Signals'] = sod_df[[col for col in sod_df.columns if '_Short_Signal' in col]].sum(axis=1)
    
    # Create overall market bias indicator
    sod_df['Market_Bias'] = sod_df['Total_Long_Signals'] - sod_df['Total_Short_Signals']
    
    # Find strongest long and short signals at each timestamp
    for i in range(len(sod_df)):
        # Find strongest long signal
        long_strengths = {pair: sod_df[f'{pair}_Long_Strength'].iloc[i] 
                          for base, quote in major_pairs 
                          for pair in [f'{base}{quote}'] 
                          if f'{pair}_Long_Strength' in sod_df.columns}
        
        if long_strengths and max(long_strengths.values()) > 0:
            sod_df.loc[sod_df.index[i], 'Best_Long'] = max(long_strengths, key=long_strengths.get)
            sod_df.loc[sod_df.index[i], 'Best_Long_Strength'] = long_strengths[sod_df.loc[sod_df.index[i], 'Best_Long']]
        else:
            sod_df.loc[sod_df.index[i], 'Best_Long'] = None
            sod_df.loc[sod_df.index[i], 'Best_Long_Strength'] = 0
        
        # Find strongest short signal
        short_strengths = {pair: sod_df[f'{pair}_Short_Strength'].iloc[i] 
                           for base, quote in major_pairs 
                           for pair in

#### Statistical Divergence Indicator for High-Probability Setups

```python
def detect_divergence(currency_strength_df, price_df, window=12, corr_threshold=-0.5):
    """
    Detect divergences between currency strength and price action for high-probability setups.
    
    Parameters:
    currency_strength_df: DataFrame with currency strength data
    price_df: DataFrame with actual price data for currency pairs
    window: Lookback period for identifying divergence
    corr_threshold: Correlation threshold to identify significant divergence
    
    Returns:
    DataFrame with divergence and reversal signals for various currency pairs
    """
    divergence_df = pd.DataFrame(index=currency_strength_df.index)
    divergence_df['timestamp'] = currency_strength_df['timestamp']
    
    # Define major pairs to analyze
    major_pairs = [
        ('EUR', 'USD'), ('GBP', 'USD'), ('AUD', 'USD'), ('NZD', 'USD'),
        ('USD', 'JPY'), ('USD', 'CHF'), ('USD', 'CAD'), ('EUR', 'JPY')
    ]
    
    # Iterate through all pairs
    for base, quote in major_pairs:
        pair_name = f'{base}{quote}'
        
        # Calculate strength differential
        strength_diff = currency_strength_df[f'{base}_Change'] - currency_strength_df[f'{quote}_Change']
        
        # Get price data for this pair (assuming it exists in price_df)
        if pair_name in price_df.columns:
            pair_price = price_df[pair_name]
            
            # Calculate Z-scores to normalize both series
            strength_diff_z = (strength_diff - strength_diff.rolling(window=window).mean()) / strength_diff.rolling(window=window).std()
            price_z = (pair_price - pair_price.rolling(window=window).mean()) / pair_price.rolling(window=window).std()
            
            # Calculate correlation within rolling window
            correlations = []
            for i in range(window, len(currency_strength_df)):
                if i < window:
                    correlations.append(np.nan)
                    continue
                    
                # Get windows of data
                strength_window = strength_diff_z.iloc[i-window:i].dropna()
                price_window = price_z.iloc[i-window:i].dropna()
                
                # Skip if either window is empty
                if len(strength_window) < 3 or len(price_window) < 3:
                    correlations.append(np.nan)
                    continue
                
                # Calculate correlation
                correlation = strength_window.corr(price_window)
                correlations.append(correlation)
            
            # Add any missing values to match length
            while len(correlations) < len(divergence_df):
                correlations.insert(0, np.nan)
                
            # Add correlation to dataframe
            divergence_df[f'{pair_name}_Correlation'] = correlations
            
            # Identify divergences (when correlation goes below threshold)
            divergence_df[f'{pair_name}_Divergence'] = divergence_df[f'{pair_name}_Correlation'] < corr_threshold
            
            # Calculate strength of divergence (0-10 scale, with 10 being strongest)
            # Convert correlation from [-1,1] to [0,10] scale, but only for values below threshold
            divergence_df[f'{pair_name}_Divergence_Strength'] = np.where(
                divergence_df[f'{pair_name}_Correlation'] < corr_threshold,
                ((divergence_df[f'{pair_name}_Correlation'] * -1) - corr_threshold) * (10 / (1 - corr_threshold)),
                0
            )
            
            # Identify potential reversal points (new divergence)
            divergence_df[f'{pair_name}_Reversal_Signal'] = (
                (divergence_df[f'{pair_name}_Divergence']) & 
                (divergence_df[f'{pair_name}_Divergence'].shift(1) == False)
            )
            
            # Determine direction of potential reversal
            # If strength > price, expect price to rise (bullish)
            # If strength < price, expect price to fall (bearish)
            divergence_df[f'{pair_name}_Reversal_Direction'] = np.where(
                divergence_df[f'{pair_name}_Reversal_Signal'],
                np.sign(strength_diff_z - price_z),
                0
            )
            
            # Create clear bullish/bearish signals
            divergence_df[f'{pair_name}_Bullish_Reversal'] = (
                divergence_df[f'{pair_name}_Reversal_Signal'] & 
                (divergence_df[f'{pair_name}_Reversal_Direction'] > 0)
            )
            
            divergence_df[f'{pair_name}_Bearish_Reversal'] = (
                divergence_df[f'{pair_name}_Reversal_Signal'] & 
                (divergence_df[f'{pair_name}_Reversal_Direction'] < 0)
            )
    
    # Create summary columns
    bullish_cols = [col for col in divergence_df.columns if 'Bullish_Reversal' in col]
    bearish_cols = [col for col in divergence_df.columns if 'Bearish_Reversal' in col]
    
    if bullish_cols:
        divergence_df['Total_Bullish_Reversals'] = divergence_df[bullish_cols].sum(axis=1)
    
    if bearish_cols:
        divergence_df['Total_Bearish_Reversals'] = divergence_df[bearish_cols].sum(axis=1)
    
    return divergence_df

# Example usage with actual price data
# divergence_df = detect_divergence(pct_change_df, price_df)
```

#### Visualizing Statistical Divergences

```python
def plot_divergence_dashboard(divergence_df, price_df, currency_strength_df, lookback=24):
    """
    Create a dashboard visualizing statistical divergences between currency strength and price action.
    
    Parameters:
    divergence_df: DataFrame with divergence signals
    price_df: DataFrame with price data
    currency_strength_df: DataFrame with currency strength data
    lookback: Number of periods to look back
    """
    # Use only recent data
    recent_div_df = divergence_df.iloc[-lookback:]
    recent_price_df = price_df.iloc[-lookback:]
    recent_strength_df = currency_strength_df.iloc[-lookback:]
    
    # Find which pairs have divergence data
    divergence_pairs = [col.split('_')[0] for col in divergence_df.columns 
                       if '_Divergence' in col]
    
    # Create a figure
    fig = plt.figure(figsize=(14, 4 * min(3, len(divergence_pairs))))
    
    # Determine how many pairs to show (max 3 for clarity)
    pairs_to_show = min(3, len(divergence_pairs))
    
    # Loop through pairs with divergence data
    for i, pair in enumerate(divergence_pairs[:pairs_to_show]):
        # Create subplot
        ax = fig.add_subplot(pairs_to_show, 1, i+1)
        
        # Set up twin axes for price and strength
        ax2 = ax.twinx()
        
        # Plot price data
        if pair in recent_price_df.columns:
            # Normalize price for comparison
            norm_price = (recent_price_df[pair] - recent_price_df[pair].min()) / (recent_price_df[pair].max() - recent_price_df[pair].min())
            price_line, = ax.plot(recent_div_df['timestamp'], norm_price, 
                                 color='blue', linewidth=2, label=f'{pair} Price')
        
        # Plot strength differential
        base, quote = pair[:3], pair[3:] if len(pair) > 3 else pair[3:]
        if f'{base}_Change' in recent_strength_df.columns and f'{quote}_Change' in recent_strength_df.columns:
            strength_diff = recent_strength_df[f'{base}_Change'] - recent_strength_df[f'{quote}_Change']
            
            # Normalize strength diff for comparison
            if not strength_diff.empty and strength_diff.max() != strength_diff.min():
                norm_strength = (strength_diff - strength_diff.min()) / (strength_diff.max() - strength_diff.min())
                strength_line, = ax.plot(recent_div_df['timestamp'], norm_strength, 
                                        color='green', linewidth=2, linestyle='--', 
                                        label='Strength Differential')
        
        # Plot correlation
        if f'{pair}_Correlation' in recent_div_df.columns:
            # Scale correlation to [0,1] for visual comparison
            scaled_corr = (recent_div_df[f'{pair}_Correlation'] + 1) / 2
            corr_line, = ax2.plot(recent_div_df['timestamp'], recent_div_df[f'{pair}_Correlation'], 
                                 color='red', linewidth=1.5, label='Correlation')
            
            # Add correlation threshold line
            ax2.axhline(y=-0.5, color='red', linestyle=':', alpha=0.7, label='Divergence Threshold')
        
        # Mark divergence points
        if f'{pair}_Bullish_Reversal' in recent_div_df.columns:
            bullish_points = recent_div_df[recent_div_df[f'{pair}_Bullish_Reversal']]['timestamp']
            if not bullish_points.empty:
                # Find corresponding y-values for the markers (use price data)
                if pair in recent_price_df.columns:
                    bullish_y = norm_price.loc[bullish_points.index]
                    ax.scatter(bullish_points, bullish_y, color='green', s=120, marker='^', 
                              label='Bullish Reversal Signal', zorder=5)
        
        if f'{pair}_Bearish_Reversal' in recent_div_df.columns:
            bearish_points = recent_div_df[recent_div_df[f'{pair}_Bearish_Reversal']]['timestamp']
            if not bearish_points.empty:
                # Find corresponding y-values for the markers (use price data)
                if pair in recent_price_df.columns:
                    bearish_y = norm_price.loc[bearish_points.index]
                    ax.scatter(bearish_points, bearish_y, color='red', s=120, marker='v', 
                              label='Bearish Reversal Signal', zorder=5)
        
        # Set up axes labels and title
        ax.set_ylabel('Normalized Value', fontsize=12)
        ax2.set_ylabel('Correlation [-1,1]', fontsize=12)
        ax2.set_ylim(-1.1, 1.1)
        
        ax.set_title(f'{pair} Divergence Analysis', fontsize=14)
        
        # Combine legends from both axes
        lines1, labels1 = ax.get_legend_handles_labels()
        lines2, labels2 = ax2.get_legend_handles_labels()
        ax.legend(lines1 + lines2, labels1 + labels2, loc='upper right')
        
        ax.grid(True, alpha=0.3)
    
    plt.tight_layout()
    plt.show()
    
    return fig

# Example usage
# divergence_dashboard = plot_divergence_dashboard(divergence_df, price_df, pct_change_df)
```

### 5. Visualization and Interpretation for Quick Decision-Making

#### Real-Time Heatmap for Currency Strength

```python
def create_strength_heatmap(df, timestamp=None):
    """Create a heatmap visualizing currency strength changes across multiple pairs."""
    if timestamp is None:
        # Use the last timestamp if none specified
        timestamp = df['timestamp'].iloc[-1]
    
    # Filter data for the specified timestamp
    data = df[df['timestamp'] == timestamp]
    
    # Extract only the currency change columns
    change_columns = [col for col in df.columns if '_Change' in col]
    
    # Get the base currencies without the '_Change' suffix
    currencies = [col.replace('_Change', '') for col in change_columns]
    
    # Create matrix to show currency strength relationships
    num_currencies = len(currencies)
    strength_matrix = np.zeros((num_currencies, num_currencies))
    
    # Populate the matrix with relative strength values
    for i, base in enumerate(currencies):
        base_strength = data[f'{base}_Change'].values[0]
        
        for j, quote in enumerate(currencies):
            if i != j:  # Avoid diagonal (same currency)
                quote_strength = data[f'{quote}_Change'].values[0]
                # Calculate relative strength (positive means base is stronger than quote)
                strength_matrix[i, j] = base_strength - quote_strength
    
    # Set up the heatmap with clear labels
    plt.figure(figsize=(12, 10))
    sns.heatmap(strength_matrix, annot=True, cmap='RdYlGn', center=0,
                xticklabels=currencies, yticklabels=currencies,
                fmt='.2f', linewidths=0.5)
    
    # Add informative title and labels
    plt.title(f'Currency Relative Strength Heatmap at {timestamp}')
    plt.xlabel('Quote Currency')
    plt.ylabel('Base Currency')
    
    # Add visual guide
    plt.figtext(0.5, 0.01, 
                'Green: Base currency stronger than Quote | Red: Quote currency stronger than Base', 
                ha='center', fontsize=10, bbox={'facecolor':'white', 'alpha':0.8, 'pad':5})
    
    plt.tight_layout()
    plt.show()

# Example visualization for latest timestamp
# create_strength_heatmap(pct_change_df)
```

#### Multi-Currency Dashboard for Scalpers

```python
def create_scalping_dashboard(df, lookback_periods=24, currencies=['USD', 'EUR', 'JPY', 'GBP']):
    """
    Create a comprehensive dashboard with key scalping indicators for multiple currencies.
    
    Parameters:
    df: DataFrame with currency strength and indicator data
    lookback_periods: Number of recent periods to display (24 periods = 12 hours with 30min data)
    currencies: List of currencies to include in the dashboard
    """
    # Use only the most recent data based on lookback_periods
    recent_df = df.iloc[-lookback_periods:]
    
    # Create a figure with gridspec for flexible layout
    fig = plt.figure(figsize=(20, 5*len(currencies)))
    gs = fig.add_gridspec(len(currencies), 6)
    
    # Add timestamp to title
    latest_time = recent_df['timestamp'].iloc[-1]
    fig.suptitle(f'Currency Strength Scalping Dashboard - Last Updated: {latest_time}', 
                 fontsize=16, y=0.995)
    
    for i, currency in enumerate(currencies):
        # Get relevant columns for this currency
        strength_col = f'{currency}_Change'
        rsi_col = f'{currency}_RSI_9' if f'{currency}_RSI_9' in recent_df.columns else None
        momentum_col = f'{currency}_Momentum_1' if f'{currency}_Momentum_1' in recent_df.columns else None
        
        # === Plot 1: Currency strength trend (larger panel) ===
        ax1 = fig.add_subplot(gs[i, 0:2])
        strength_line = ax1.plot(recent_df['timestamp'], recent_df[strength_col], 
                                 linewidth=2, color='blue', label='Strength')
        
        # Add zero line for reference
        ax1.axhline(y=0, color='black', linestyle='-', alpha=0.3)
        
        # Add SMA lines if available
        sma_short_col = f'{currency}_Change_SMA_3'
        sma_med_col = f'{currency}_Change_SMA_7'
        
        if sma_short_col in recent_df.columns:
            ax1.plot(recent_df['timestamp'], recent_df[sma_short_col], 
                    linewidth=1.5, color='orange', label='1.5hr SMA')
            
        if sma_med_col in recent_df.columns:
            ax1.plot(recent_df['timestamp'], recent_df[sma_med_col], 
                    linewidth=1.5, color='red', label='3.5hr SMA')
        
        # Highlight the latest value
        latest_val = recent_df[strength_col].iloc[-1]
        color = 'green' if latest_val > 0 else 'red'
        ax1.scatter(recent_df['timestamp'].iloc[-1], latest_val, 
                   color=color, s=100, zorder=5)
        
        # Add key strength value as text
        ax1.text(0.02, 0.95, f"Current: {latest_val:.2f}%", 
                transform=ax1.transAxes, fontsize=12,
                bbox=dict(facecolor=color, alpha=0.2))
        
        ax1.set_title(f'{currency} Strength Trend', fontsize=14)
        ax1.set_ylabel('% Change', fontsize=12)
        ax1.legend(loc='lower left')
        ax1.grid(True, alpha=0.3)
        
        # === Plot 2: RSI indicator ===
        ax2 = fig.add_subplot(gs[i, 2:4])
        if rsi_col and rsi_col in recent_df.columns:
            ax2.plot(recent_df['timestamp'], recent_df[rsi_col], 
                    linewidth=2, color='purple')
            
            # Add overbought/oversold lines
            ax2.axhline(y=70, color='r', linestyle='-', alpha=0.3)
            ax2.axhline(y=30, color='g', linestyle='-', alpha=0.3)
            
            # Highlight current value
            latest_rsi = recent_df[rsi_col].iloc[-1]
            rsi_color = 'red' if latest_rsi > 70 else ('green' if latest_rsi < 30 else 'blue')
            ax2.scatter(recent_df['timestamp'].iloc[-1], latest_rsi, 
                       color=rsi_color, s=100, zorder=5)
            
            # Add RSI value and status text
            status = "OVERBOUGHT" if latest_rsi > 70 else ("OVERSOLD" if latest_rsi < 30 else "NEUTRAL")
            ax2.text(0.02, 0.95, f"RSI: {latest_rsi:.1f} - {status}", 
                    transform=ax2.transAxes, fontsize=12,
                    bbox=dict(facecolor=rsi_color, alpha=0.2))
            
            ax2.set_title(f'{currency} RSI (9)', fontsize=14)
            ax2.set_ylim(0, 100)
            ax2.grid(True, alpha=0.3)
        
        # === Plot 3: Momentum and Acceleration ===
        ax3 = fig.add_subplot(gs[i, 4:6])
        if momentum_col and momentum_col in recent_df.columns:
            # Plot momentum
            ax3.plot(recent_df['timestamp'], recent_df[momentum_col], 
                    linewidth=2, color='darkgreen', label='Momentum')
            
            # Plot acceleration if available
            accel_col = f'{currency}_Acceleration'
            if accel_col in recent_df.columns:
                ax3.plot(recent_df['timestamp'], recent_df[accel_col], 
                        linewidth=1.5, color='orange', linestyle='--', label='Acceleration')
            
            # Add zero line
            ax3.axhline(y=0, color='black', linestyle='-', alpha=0.3)
            
            # Highlight current momentum
            latest_momentum = recent_df[momentum_col].iloc[-1]
            mom_color = 'green' if latest_momentum > 0.1 else ('red' if latest_momentum < -0.1 else 'blue')
            ax3.scatter(recent_df['timestamp'].iloc[-1], latest_momentum, 
                       color=mom_color, s=100, zorder=5)
            
            # Add momentum strength text
            strength = "STRONG UP" if latest_momentum > 0.2 else \
                      ("STRONG DOWN" if latest_momentum < -0.2 else \
                       ("UP" if latest_momentum > 0 else "DOWN"))
            ax3.text(0.02, 0.95, f"Momentum: {latest_momentum:.2f} - {strength}", 
                    transform=ax3.transAxes, fontsize=12,
                    bbox=dict(facecolor=mom_color, alpha=0.2))
            
            ax3.set_title(f'{currency} Momentum & Acceleration', fontsize=14)
            ax3.legend(loc='lower left')
            ax3.grid(True, alpha=0.3)
    
    # Add trade opportunity summary at the bottom of the dashboard
    strong_currencies = []
    weak_currencies = []
    
    for currency in currencies:
        strength_col = f'{currency}_Change'
        latest_val = recent_df[strength_col].iloc[-1]
        momentum_col = f'{currency}_Momentum_1'
        
        if momentum_col in recent_df.columns:
            latest_momentum = recent_df[momentum_col].iloc[-1]
            
            if latest_val > 0.3 and latest_momentum > 0.2:
                strong_currencies.append(currency)
            elif latest_val < -0.3 and latest_momentum < -0.2:
                weak_currencies.append(currency)
    
    # Add trade opportunities text at the bottom
    if strong_currencies and weak_currencies:
        opportunities_text = f"Potential Pair Opportunities:\n"
        for strong in strong_currencies:
            for weak in weak_currencies:
                if f"{strong}/{weak}" in ["EUR/USD", "GBP/USD", "AUD/USD", "NZD/USD", 
                                         "USD/JPY", "USD/CHF", "USD/CAD", "EUR/JPY",
                                         "GBP/JPY", "EUR/GBP", "AUD/JPY", "NZD/JPY"]:
                    opportunities_text += f"• LONG {strong}/{weak}\n"
        
        if opportunities_text != "Potential Pair Opportunities:\n":
            fig.text(0.5, 0.01, opportunities_text, 
                    ha='center', fontsize=12, 
                    bbox=dict(facecolor='lightgreen', alpha=0.5, pad=10))
    
    plt.tight_layout(rect=[0, 0.03, 1, 0.97])
    plt.show()
    
    return fig

# Example dashboard visualization
# scalping_dashboard = create_scalping_dashboard(combined_df)  # combined_df would include all indicators
```

### 6. Backtesting Considerations for Algorithmic Strategies

#### Comprehensive Scalping

### 7. Strategy Development as Core Foundation

#### Conceptual Framework for Currency Strength-Based Scalping Strategy

```python
def currency_strength_scalping_strategy(df, parameters=None):
    """
    Implement a currency strength-based scalping strategy.
    
    Parameters:
    df: DataFrame with currency strength and indicator data
    parameters: Dictionary of strategy parameters (with defaults if None)
    """
    if parameters is None:
        parameters = {
            'strength_threshold': 0.3,         # Minimum strength change to consider
            'momentum_threshold': 0.2,         # Minimum momentum to confirm trend
            'rsi_overbought': 70,              # RSI overbought threshold
            'rsi_oversold': 30,                # RSI oversold threshold
            'volatility_multiplier': 1.2,      # Minimum volatility to trade
            'correlation_threshold': -0.7,     # Correlation threshold for pair trading
            'profit_target_pips': 10,          # Profit target in pips
            'stop_loss_pips': 5                # Stop loss in pips
        }
    
    # Initialize signals DataFrame
    signals = pd.DataFrame(index=df.index)
    signals['timestamp'] = df['timestamp']
    
    # Filter currencies with significant strength changes
    for currency in ['USD', 'EUR', 'JPY', 'GBP', 'AUD', 'CAD', 'CHF', 'NZD']:
        col = f'{currency}_Change'
        if col in df.columns:
            # Identify strong movements
            signals[f'{currency}_Strong_Up'] = (
                (df[col] > parameters['strength_threshold']) & 
                (df.get(f'{currency}_Momentum_1', pd.Series(0, index=df.index)) > parameters['momentum_threshold']) &
                (df.get(f'{currency}_RSI_9', pd.Series(50, index=df.index)) < parameters['rsi_overbought'])
            )
            
            signals[f'{currency}_Strong_Down'] = (
                (df[col] < -parameters['strength_threshold']) & 
                (df.get(f'{currency}_Momentum_1', pd.Series(0, index=df.index)) < -parameters['momentum_threshold']) &
                (df.get(f'{currency}_RSI_9', pd.Series(50, index=df.index)) > parameters['rsi_oversold'])
            )
    
    # Generate pair trading opportunities
    currency_pairs = []
    for base in ['EUR', 'GBP', 'AUD', 'NZD']:
        for quote in ['USD', 'JPY', 'CHF', 'CAD']:
            currency_pairs.append(f'{base}/{quote}')
    
    for pair in currency_pairs:
        base, quote = pair.split('/')
        
        # Long signal: Base currency strengthening and quote currency weakening
        signals[f'{pair}_Long'] = signals[f'{base}_Strong_Up'] & signals[f'{quote}_Strong_Down']
        
        # Short signal: Base currency weakening and quote currency strengthening
        signals[f'{pair}_Short'] = signals[f'{base}_Strong_Down'] & signals[f'{quote}_Strong_Up']
    
    return signals

# This would be applied with actual data in a live trading system
# strategy_signals = currency_strength_scalping_strategy(combined_df)
```

## Advantages and Challenges

### Advantages:
1. **Broader Market Insight** - Analyzing 28 pairs simultaneously provides a comprehensive view of market dynamics
2. **Early Signal Generation** - Currency strength often shifts before price action, potentially offering earlier entry points
3. **Reduced Noise** - Aggregating strength across multiple pairs filters out market noise
4. **Multi-Timeframe Analysis** - Allows examination of both immediate and developing trends
5. **More Trading Opportunities** - Algorithmically identifies potentially overlooked trading setups

### Challenges:
1. **Computational Intensity** - Processing 28 pairs at high frequency requires robust systems
2. **Latency Concerns** - Scalping strategies demand minimal processing delays
3. **Parameter Optimization** - Finding optimal thresholds requires extensive testing
4. **Correlation Stability** - Currency correlations can shift rapidly in volatile markets
5. **Implementation Complexity** - Integrating with existing trading platforms

## Implementation Recommendations

### For Scalping (1-15 Minute Timeframes):
1. Focus on ultra-short momentum indicators (1-3 periods)
2. Prioritize immediate strength divergences between currency pairs
3. Use tighter Bollinger Bands (1.5 standard deviations)
4. Implement strict volatility filters to avoid ranging markets
5. Set smaller profit targets (5-15 pips) with tight stop losses

### For Intraday Trading (15 Minute - 4 Hour Timeframes):
1. Incorporate medium-term currency strength trends (4-12 periods)
2. Watch for divergence between currency strength and price action
3. Monitor correlation shifts for potential reversal signals
4. Combine with support/resistance from price action
5. Aim for larger moves (20-80 pips) with scaled entries/exits

### For Algorithmic Strategies:
1. Implement real-time correlation matrix updates
2. Create dynamic strength volatility rankings
3. Design cross-pair opportunity scanners
4. Develop adaptive parameter optimization
5. Establish robust risk management frameworks

## Conclusion

Currency strength data provides a unique perspective for traders, allowing them to view the forex market from a multi-dimensional angle rather than simply following individual pairs. By transforming this data into percentage changes and developing specialized indicators, scalpers and intraday traders can identify high-probability setups with greater precision and speed.

The key to successful implementation lies in:
1. Proper data transformation and normalization
2. Optimizing indicator parameters for shorter timeframes
3. Creating efficient visualization systems for quick decision-making
4. Implementing robust backtesting with realistic assumptions
5. Developing systematic trading rules with clear risk management

When properly implemented, currency strength indicators can form the core foundation of a systematic trading approach that capitalizes on the interconnected nature of the forex market.**