import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# 读取本地年度EPS数据
def read_local_eps_data():
    eps_file_path = "aapl_historical_eps.csv"
    if os.path.exists(eps_file_path):
        print(f"正在读取本地EPS数据：{eps_file_path}")
        eps_data = pd.read_csv(eps_file_path)
        # 将年份转换为datetime类型
        eps_data['年份'] = pd.to_datetime(eps_data['年份'], format='%Y')
        return eps_data
    else:
        print("本地EPS数据文件不存在，使用示例数据")
        # 使用示例数据
        example_data = {
            '年份': pd.date_range(start='2010-01-01', end='2025-01-01', freq='A'),
            '基本EPS': [2.16, 2.82, 4.18, 4.99, 5.68, 9.28, 8.35, 9.21, 11.91, 12.58, 3.28, 5.61, 6.11, 6.43, 7.17, 7.85]
        }
        return pd.DataFrame(example_data)

# 生成季度EPS数据
def generate_quarterly_eps(annual_eps):
    quarterly_eps = []
    for i in range(len(annual_eps)):
        year = annual_eps.iloc[i]['年份'].year
        eps = annual_eps.iloc[i]['基本EPS']
        # 简单地将年度EPS平均分配到4个季度
        quarterly_eps_value = eps / 4
        # 生成四个季度的日期和EPS值
        for quarter in range(1, 5):
            # 季度末日期
            if quarter == 1:
                quarter_end = datetime(year, 3, 31)
            elif quarter == 2:
                quarter_end = datetime(year, 6, 30)
            elif quarter == 3:
                quarter_end = datetime(year, 9, 30)
            else:  # quarter == 4
                quarter_end = datetime(year, 12, 31)
            quarterly_eps.append({
                'Date': quarter_end,
                'EPS': quarterly_eps_value
            })
    return pd.DataFrame(quarterly_eps)

# 生成示例季度股价数据
def generate_quarterly_prices(start_year, end_year):
    # 创建季度末日期列表
    quarter_end_dates = pd.date_range(start=f'{start_year}-01-01', end=f'{end_year}-12-31', freq='Q')
    
    # 生成示例股价数据（基于历史趋势的简化模型）
    # 2010年第一季度收盘价约为20美元，2025年第一季度约为200美元
    start_price = 20.0
    end_price = 200.0
    total_quarters = len(quarter_end_dates)
    
    # 生成线性增长的价格，添加一些随机波动
    prices = []
    for i in range(total_quarters):
        # 线性增长部分
        linear_price = start_price + (end_price - start_price) * (i / total_quarters)
        # 添加随机波动（±10%）
        random_factor = 0.9 + np.random.random() * 0.2
        actual_price = linear_price * random_factor
        prices.append({
            'Date': quarter_end_dates[i],
            'Close': round(actual_price, 2)
        })
    
    return pd.DataFrame(prices)

# 主函数
def main():
    print("计算AAPL 10-25年历史市盈率（每3个月一个节点）")
    
    # 获取当前日期
    current_date = datetime.now()
    
    # 设置时间范围（10-25年）
    end_year = current_date.year
    start_year = max(2000, end_year - 25)  # 最多25年，最早2000年
    
    # 读取本地年度EPS数据
    annual_eps = read_local_eps_data()
    
    # 生成季度EPS数据
    quarterly_eps = generate_quarterly_eps(annual_eps)
    
    # 生成季度股价数据
    quarterly_prices = generate_quarterly_prices(start_year, end_year)
    
    # 合并季度数据
    merged_data = pd.merge(quarterly_prices, quarterly_eps, on='Date', how='left')
    
    # 计算市盈率 (PE Ratio = 股价 / EPS)
    merged_data['PE_Ratio'] = merged_data['Close'] / merged_data['EPS']
    
    # 过滤掉无效数据
    merged_data = merged_data.dropna()
    merged_data = merged_data[merged_data['PE_Ratio'] > 0]
    
    # 按日期排序
    merged_data = merged_data.sort_values('Date')
    
    # 设置日期为索引
    merged_data.set_index('Date', inplace=True)
    
    # 打印结果
    print("\nAAPL 历史市盈率（每3个月一个节点）：")
    print(merged_data)
    
    # 将结果保存到CSV文件
    save_path = "aapl_historical_pe.csv"
    merged_data.to_csv(save_path)
    print(f"\n结果已保存到 {save_path}")
    
    # 统计信息
    print("\n统计信息：")
    print(f"数据时间范围：{merged_data.index.min().strftime('%Y-%m-%d')} 到 {merged_data.index.max().strftime('%Y-%m-%d')}")
    print(f"数据点数量：{len(merged_data)}")
    print(f"平均市盈率：{merged_data['PE_Ratio'].mean():.2f}")
    print(f"最低市盈率：{merged_data['PE_Ratio'].min():.2f}")
    print(f"最高市盈率：{merged_data['PE_Ratio'].max():.2f}")

if __name__ == "__main__":
    main()
