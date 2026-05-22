import yfinance as yf
import pandas as pd

# 获取苹果公司的股票数据
aapl = yf.Ticker("AAPL")

# 获取年度财务报表数据
income_stmt = aapl.financials.T  # 利润表
balance_sheet = aapl.balance_sheet.T  # 资产负债表
cash_flow = aapl.cash_flow.T  # 现金流量表

# 打印可用的财务指标
print("利润表中可用的指标:")
print(list(income_stmt.columns))

# 尝试获取基本每股收益(EPS)
print("\n=== 苹果公司(AAPL)基本每股收益数据 ===")

# 方法1: 从财务报表中获取
eps_data = {}
if 'Basic EPS' in income_stmt.columns:
    eps_data['从财务报表'] = income_stmt['Basic EPS']
    print("从财务报表获取的基本每股收益:")
    print(income_stmt['Basic EPS'])
else:
    print("财务报表中没有直接的基本每股收益数据")

# 方法2: 使用earnings数据
if hasattr(aapl, 'earnings'):
    earnings = aapl.earnings
    print("\n年度盈利数据:")
    print(earnings)
    
    # 如果有股票数量数据，可以计算EPS
    if hasattr(aapl, 'shares'):
        shares = aapl.shares
        if shares is not None and not shares.empty:
            print("\n股票数量数据:")
            print(shares)

# 方法3: 获取历史EPS数据
print("\n=== 尝试获取历史EPS数据 ===")
try:
    # 使用yahoo finance的API获取历史财务数据
    import requests
    import json
    
    # 使用financialmodelingprep API获取EPS数据
    # 注意：这里使用免费API，可能有访问限制
    url = "https://financialmodelingprep.com/api/v3/income-statement/AAPL?period=annual&limit=20&apikey=demo"
    response = requests.get(url)
    
    if response.status_code == 200:
        data = response.json()
        print("\n从Financial Modeling Prep获取的EPS数据:")
        for item in data:
            if 2010 <= item['calendarYear'] <= 2025:
                print(f"年份: {item['calendarYear']}, 基本EPS: {item['epsBasic']}, 稀释EPS: {item['epsDiluted']}")
    else:
        print(f"API请求失败，状态码: {response.status_code}")
except Exception as e:
    print(f"获取历史EPS数据时出错: {e}")

# 方法4: 显示所有可用的财务数据
print("\n=== 所有可用的年度财务数据 ===")
print("利润表:")
print(income_stmt)
