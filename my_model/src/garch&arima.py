import warnings
import numpy as np
import pandas as pd
from arch import arch_model
from scipy.optimize import brentq
from scipy.stats import norm
from statsmodels.tools.sm_exceptions import ConvergenceWarning, ValueWarning
from statsmodels.tsa.arima.model import ARIMA
from tqdm import tqdm

# 忽略警告訊息
warnings.filterwarnings('ignore', category=ValueWarning)
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=ConvergenceWarning)


# =========================================================
# 步驟 0：基礎 BSM 評價、Delta、Gamma 與 IV 函式
# =========================================================
def bsm_call_price(S, K, T, r, sigma):
  if T <= 0 or sigma <= 0 or np.isnan(sigma):
    return 0.0
  d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
  d2 = d1 - sigma * np.sqrt(T)
  return S * norm.cdf(d1) - K * np.exp(-r * T) * norm.cdf(d2)


def bsm_call_delta(S, K, T, r, sigma):
  if T <= 0 or sigma <= 0 or np.isnan(sigma):
    return 0.0
  d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
  return norm.cdf(d1)


def bsm_call_gamma(S, K, T, r, sigma):
  if T <= 0 or sigma <= 0 or np.isnan(sigma):
    return 0.0
  d1 = (np.log(S / K) + (r + 0.5 * sigma**2) * T) / (sigma * np.sqrt(T))
  return norm.pdf(d1) / (S * sigma * np.sqrt(T))


def calculate_iv(C_market, S, K, T, r=0.00821):
  intrinsic_val = max(0.0, S - K * np.exp(-r * T))
  if C_market <= intrinsic_val or T <= 0 or np.isnan(C_market):
    return np.nan
  objective_function = (
      lambda sigma: bsm_call_price(S, K, T, r, sigma) - C_market
  )
  try:
    return brentq(objective_function, a=0.001, b=5.0)
  except (ValueError, RuntimeError):
    return np.nan


def get_settlement_date(year_month_str):
  ym_str = str(year_month_str).split('.')[0].strip()
  year, month = int(ym_str[:4]), int(ym_str[4:6])
  first_day = pd.Timestamp(year=year, month=month, day=1)
  days_to_wed = (2 - first_day.weekday()) % 7
  first_wed = first_day + pd.Timedelta(days=days_to_wed)
  return first_wed + pd.Timedelta(weeks=2)