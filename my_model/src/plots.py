import matplotlib.pyplot as plt
import matplotlib.ticker as mtick
import numpy as np
import pandas as pd


def plot_backtest_results(df_strategy):
    """繪製策略權益曲線與進出場點位圖表"""
    fig, ax = plt.subplots(figsize=(15, 8))

    # 1. 繪製權益曲線
    ax.plot(
        df_strategy['交易日期'],
        df_strategy['Equity_Buy_Hold_Stock'],
        label='Buy & Hold TSMC Stock (2330.TW)',
        color='darkorange',
        linewidth=1.8,
        alpha=0.8,
    )
    ax.plot(
        df_strategy['交易日期'],
        df_strategy['Equity_Delta_Only'],
        label='VRP Strategy (Delta-Only)',
        color='darkblue',
        linestyle='--',
        linewidth=1.8,
        alpha=0.8,
    )
    ax.plot(
        df_strategy['交易日期'],
        df_strategy['Equity_Delta_Gamma'],
        label='VRP Strategy (Fixed 1:1 Ratio + Stock Delta Hedge)',
        color='crimson',
        linewidth=2.5,
    )

    # 2. 標示進出場點位
    pos_diff = df_strategy['Position_ATM'].diff().fillna(0)
    long_entry = df_strategy[
        (df_strategy['Position_ATM'] == 1) & (pos_diff == 1)
    ]
    short_entry = df_strategy[
        (df_strategy['Position_ATM'] == -1) & (pos_diff == -1)
    ]
    exit_trade = df_strategy[
        (df_strategy['Position_ATM'] == 0) & (pos_diff != 0)
    ]

    ax.scatter(
        long_entry['交易日期'],
        long_entry['Equity_Delta_Gamma'],
        color='green',
        marker='^',
        s=100,
        zorder=5,
        label='Long Entry (Buy VRP)',
    )
    ax.scatter(
        short_entry['交易日期'],
        short_entry['Equity_Delta_Gamma'],
        color='red',
        marker='v',
        s=100,
        zorder=5,
        label='Short Entry (Sell VRP)',
    )
    ax.scatter(
        exit_trade['交易日期'],
        exit_trade['Equity_Delta_Gamma'],
        color='black',
        marker='x',
        s=80,
        zorder=5,
        label='Exit / Flat Position',
    )

    # 3. 圖表樣式設定
    ax.set_title(
        'Performance Comparison with Clean Signals: Fixed 1:1 Hedge Ratio vs.'
        ' Benchmarks',
        fontsize=14,
        fontweight='bold',
    )
    ax.set_xlabel('Date', fontsize=12)
    ax.set_ylabel('Portfolio Value (TWD)', fontsize=12)
    ax.yaxis.set_major_formatter(mtick.StrMethodFormatter('{x:,.0f}'))
    ax.legend(loc='upper left', fontsize=10, framealpha=0.9)
    ax.grid(True, linestyle=':', alpha=0.6)

    plt.tight_layout()
    plt.show()


def print_performance_report(
    df_strategy, initial_capital=1_000_000, annual_trading_days=252
):
    """計算並印出三個對照組的績效比較報告"""

    def _calc_metrics(returns, equity):
        total_return = (equity.iloc[-1] / initial_capital) - 1
        num_years = len(returns) / annual_trading_days
        cagr = (
            (1 + total_return) ** (1 / num_years) - 1 if num_years > 0 else np.nan
        )

        annual_vol = returns.std() * np.sqrt(annual_trading_days)
        rf = 0.015
        sharpe_ratio = (
            (cagr - rf) / annual_vol if annual_vol > 0 else np.nan
        )

        peak = equity.cummax()
        drawdown = (equity - peak) / peak
        max_drawdown = drawdown.min()

        calmar_ratio = (
            cagr / abs(max_drawdown) if max_drawdown != 0 else np.nan
        )

        return pd.Series({
            '累積總報酬率 (Total Return)': f'{total_return * 100:.2f}%',
            '年化報酬率 (CAGR)': f'{cagr * 100:.2f}%',
            '年化波動率 (Annualized Vol)': f'{annual_vol * 100:.2f}%',
            '夏普比率 (Sharpe Ratio)': f'{sharpe_ratio:.2f}',
            '最大回撤 (Max Drawdown)': f'{max_drawdown * 100:.2f}%',
            '卡瑪比率 (Calmar Ratio)': f'{calmar_ratio:.2f}',
        })

    metrics_dg = _calc_metrics(
        df_strategy['Return_Delta_Gamma'], df_strategy['Equity_Delta_Gamma']
    )
    metrics_d = _calc_metrics(
        df_strategy['Return_Delta_Only'], df_strategy['Equity_Delta_Only']
    )
    metrics_stock = _calc_metrics(
        df_strategy['Stock_Return'], df_strategy['Equity_Buy_Hold_Stock']
    )

    comparison_df = pd.DataFrame({
        'VRP (固定 1:1 比率避險)': metrics_dg,
        'VRP (純 Delta 避險)': metrics_d,
        '持有台積電股票 (Buy & Hold)': metrics_stock,
    })

    print(
        '\n========================= 修改對沖比率後績效比較報告'
        ' ========================='
    )
    print(comparison_df)
    print(
        '=============================================================================\n'
    )
def inspect_max_drawdown_event(df_final):
    """診斷並印出 Delta-Gamma 策略最大回落當天與前後交易日的明細數據"""
    df = df_final.copy()

    # 確保交易日期為 datetime 格式
    df['交易日期'] = pd.to_datetime(df['交易日期'])

    # 針對 Delta-Gamma 策略計算歷史高點與回落幅度
    equity_col = (
        'Equity_Delta_Gamma'
        if 'Equity_Delta_Gamma' in df.columns
        else df.columns[-1]
    )
    peak = df[equity_col].cummax()
    drawdown = (df[equity_col] - peak) / peak

    # 找出最大回落發生的索引點與日期
    mdd_idx = drawdown.idxmin()
    mdd_date = df.loc[mdd_idx, '交易日期'].strftime('%Y-%m-%d')
    max_dd_val = drawdown.min()

    print('\n' + '=' * 85)
    print(f'【最大回落（Max Drawdown）事件深度診斷】')
    print(f'最大回落發生日期 : {mdd_date}')
    print(f'最大回落峰值跌幅 : {max_dd_val * 100:.2f}%')
    print('=' * 85)

    # 擷取最大回落日 前 2 天至後 2 天 的關鍵資料
    start_idx = max(0, mdd_idx - 2)
    end_idx = min(len(df), mdd_idx + 3)

    # 欲檢視的關鍵欄位列表
    target_cols = [
        '交易日期',
        'Underlying_Close',
        'Stock_Price_Change',
        'ATM_Strike',
        'Position_ATM',
        'Hedge_OTM_Pos',
        'Hedge_Stock_Shares_DG',
        'ATM_PnL_TWD',
        'OTM_PnL_TWD',
        'Stock_PnL_DG_TWD',
        'PnL_Delta_Gamma_Hedged',
        equity_col,
    ]

    # 過濾出 DataFrame 中實際存在的欄位
    valid_cols = [c for c in target_cols if c in df.columns]
    detail_df = df.loc[start_idx : end_idx - 1, valid_cols].copy()

    # 格式化日期與數字輸出
    detail_df['交易日期'] = detail_df['交易日期'].dt.strftime('%Y-%m-%d')
    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)

    print(detail_df.to_string(index=False))
    print('=' * 85 + '\n')