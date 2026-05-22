import csv

def get_aapl_eps_from_local_file(start_year=2010, end_year=2025):
    """
    从本地CSV文件读取苹果公司(AAPL)的历史EPS数据
    无需网络连接，数据来源于已保存的历史记录
    """
    print("正在从本地文件获取AAPL的EPS数据...")
    print(f"年份范围: {start_year}-{end_year}")
    print("=" * 50)
    print("年份 | 基本EPS")
    print("-" * 50)
    
    try:
        with open('aapl_historical_eps.csv', 'r', encoding='utf-8') as csvfile:
            reader = csv.DictReader(csvfile)
            
            # 创建年份到EPS的映射
            eps_data = {}
            for row in reader:
                year = int(row['年份'])
                eps = row['基本EPS']
                eps_data[year] = eps
            
            # 按年份范围输出数据
            for year in range(start_year, end_year + 1):
                if year in eps_data:
                    print(f"{year}  | ${eps_data[year]}")
                else:
                    print(f"{year}  | 暂无数据")
                    
    except FileNotFoundError:
        print("错误: 未找到aapl_historical_eps.csv文件")
    except Exception as e:
        print(f"错误: {str(e)}")
    
    print("=" * 50)
    print("数据获取完成")
    print("\n注意：")
    print("1. 此数据来源于本地CSV文件，包含2010-2024年的历史记录")
    print("2. 2025年的数据为预测值或尚未发布")
    print("3. 如需最新数据，请在网络环境良好时使用SEC EDGAR API获取")

if __name__ == "__main__":
    get_aapl_eps_from_local_file(2010, 2025)