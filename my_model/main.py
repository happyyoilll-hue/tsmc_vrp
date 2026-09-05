import sys
import time

# 匯入自建的四個功能模組
from back_testing import calculate_pnl, generate_vrp_signals
from data_import import prepare_option_and_garch_data
from plots import inspect_max_drawdown_event, plot_backtest_results, print_performance_report

def main():
    start_time = time.time()
    print("==================================================")
    print("      台積電期權 VRP (Volatility Risk Premium)    ")
    print("               量化回測系統啟動                    ")
    print("==================================================\n")

    # --------------------------------------------------------------------------
    # 步驟 1: 資料載入與預處理 (Data Loading & Preprocessing)
    # --------------------------------------------------------------------------
    print("【Step 1/4】開始處理市場歷史資料與 SQL 期權配對...")
    try:
        df_garch, df_pairs = prepare_option_and_garch_data()
        print(" -> 資料載入與 GARCH 波動率計算完成！")
    except Exception as e:
        print(f" -> [錯誤] 資料載入失敗: {e}")
        sys.exit(1)

    # --------------------------------------------------------------------------
    # 步驟 2: 訊號生成 (Signal Generation)
    # --------------------------------------------------------------------------
    print("\n【Step 2/4】執行 VRP 與 Z-Score 交易訊號計算...")
    df_strategy = generate_vrp_signals(
        df_garch,
        df_pairs,
        window=60,  # Z-Score 計算滾動視窗
        upper_threshold=1.5,  # 做空 VRP (Sell Vol) 門檻
        lower_threshold=-1.5,  # 做多 VRP (Buy Vol) 門檻
        itm_delta_threshold=0.85,  # 深度價內強制平倉 Delta 門檻
    )
    print(f" -> 策略資料集整理完成，共計 {len(df_strategy)} 個交易日。")

    # --------------------------------------------------------------------------
    # 步驟 3: 對沖與損益計算 (Delta-Gamma Hedging & PnL Accounting)
    # --------------------------------------------------------------------------
    print("\n【Step 3/4】計算 Delta-Gamma 動態對沖與每日 PnL 權益曲線...")
    df_final = calculate_pnl(
        df_strategy, initial_capital=1_000_000, multiplier=2000
    )
    print(" -> PnL 結算與權益曲線計算 completed.")

    # --------------------------------------------------------------------------
    # 步驟 4: 視覺化繪圖與績效報告 (Visualization & Performance Metrics)
    # --------------------------------------------------------------------------
    print("\n【Step 4/4】產出績效報告與視覺化圖表...")
    print_performance_report(
        df_final, initial_capital=1_000_000, annual_trading_days=252
    )

    elapsed_time = time.time() - start_time
    print(f"回測執行完畢！總共耗時: {elapsed_time:.2f} 秒\n")

    # 繪製圖表 (會彈出 Matplotlib 視窗)
    plot_backtest_results(df_final)

    print("\n【Step 4/4】產出績效報告與最大回落診斷...")
    print_performance_report(df_final)

    # 執行最大回落診斷分析
    inspect_max_drawdown_event(df_final)

    # 繪製圖表
    plot_backtest_results(df_final)

if __name__ == "__main__":
    main()