import yfinance as yf
import pandas as pd

# 获取苹果公司的股票数据
aapl = yf.Ticker("AAPL")

# 获取年度财务数据
financials = aapl.financials.T

# 获取基本每股收益(EPS)
# 注意：yfinance中的EPS字段可能在income statement中，或者需要从其他地方获取
eps_data = {}

# 尝试从财务指标中获取EPS
if hasattr(aapl, 'earnings'):
    earnings = aapl.earnings
    print("年度盈利数据:")
    print(earnings)

# 尝试获取每股收益历史数据
historical_eps = aapl.get_earnings_history()
if historical_eps:
    print("\n历史EPS数据:")
    for item in historical_eps:
        print(f"年份: {item['year']}, 季度: {item['quarter']}, EPS: {item['eps']}")

# 获取过去10年的年度EPS数据
# 使用yahoo finance的历史数据API获取年度EPS
historical_data = aapl.history(period="10y", interval="1y")

# 或者从财务报表中提取
print("\n苹果公司(AAPL)财务报表数据:")
print("利润表中的关键指标:")
if 'Net Income' in financials.columns:
    print(financials['Net Income'])

# 获取股票拆分信息以调整EPS
splits = aapl.splits
print("\n股票拆分历史:")
print(splits)

# 获取基本每股收益 - 从income statement中提取
if 'Basic EPS' in financials.columns:
    eps_annual = financials['Basic EPS']
    print("\n年度基本每股收益:")
    print(eps_annual)
else:
    # 如果没有直接的EPS字段，尝试计算
    if 'Net Income' in financials.columns and hasattr(aapl, 'shares'):
        shares = aapl.shares
        if shares is not None and not shares.empty:
            print("\n尝试计算EPS:")
            print(f"净利润:")
            print(financials['Net Income'])
            print(f"\n股票数量:")
            print(shares)
