import urllib.request
import urllib.error
import json
import re
import sys

def get_aapl_eps_simple(start_year=2010, end_year=2025):
    """
    使用Python标准库从SEC EDGAR获取苹果公司(AAPL)的EPS数据
    只使用urllib和re等标准库，无需额外安装依赖
    """
    print("正在使用Python标准库获取AAPL的EPS数据...")
    print(f"年份范围: {start_year}-{end_year}")
    print("=" * 50)
    print("年份 | 基本EPS")
    print("-" * 50)
    
    # 苹果公司的CIK号码
    aapl_cik = "0000320193"
    
    for year in range(start_year, end_year + 1):
        try:
            # 构建SEC EDGAR搜索URL
            # 注意：这是一个简化的URL，实际SEC EDGAR API需要更复杂的请求
            # 这里使用一个示例的10-K文件URL模式
            # 实际使用时可能需要先搜索文件列表
            
            # 示例：获取2023年的10-K文件
            # 实际文件URL需要通过搜索API获取，这里使用简化的方式
            print(f"正在尝试获取 {year} 年的数据...")
            
            # 使用Financial Modeling Prep的免费API（无需安装依赖）
            # 这是一个公开的免费API，有访问限制
            url = f"https://financialmodelingprep.com/api/v3/income-statement/AAPL?period=annual&limit=20&apikey=demo"
            
            # 使用urllib请求数据
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=10) as response:
                data = json.loads(response.read().decode())
                
                # 查找对应年份的数据
                for item in data:
                    if item['calendarYear'] == year:
                        eps = item.get('epsBasic', 'N/A')
                        print(f"{year}  | ${eps}")
                        break
                else:
                    print(f"{year}  | 未找到数据")
                    
        except urllib.error.URLError as e:
            print(f"{year}  | 网络错误: {str(e)}")
        except json.JSONDecodeError as e:
            print(f"{year}  | 数据解析错误: {str(e)}")
        except Exception as e:
            print(f"{year}  | 错误: {str(e)}")
    
    print("=" * 50)
    print("数据获取完成")
    print("\n注意：")
    print("1. 此数据来自Financial Modeling Prep的免费API")
    print("2. 免费API有访问限制，可能需要间隔一段时间再使用")
    print("3. 如需更准确的数据，建议使用SEC EDGAR的官方搜索工具")

def get_eps_from_edgar_direct(start_year=2010, end_year=2025):
    """
    尝试直接从SEC EDGAR搜索页面解析数据（实验性）
    """
    print("\n尝试直接从SEC EDGAR搜索页面获取数据...")
    print("这是一个实验性功能，可能不稳定...")
    
    aapl_cik = "0000320193"
    
    try:
        # SEC EDGAR搜索URL
        search_url = f"https://www.sec.gov/edgar/search/?r=el#/dateRange=custom&category=form-cat0&ciks={aapl_cik}&entityName=Apple%2520Inc.%2520(AAPL)%2520(CIK%2520{aapl_cik})&startdt={start_year}-01-01&enddt={end_year}-12-31&filter_forms=10-K"
        
        req = urllib.request.Request(search_url, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=15) as response:
            content = response.read().decode()
            
            # 尝试找到 filings列表
            print("已获取搜索页面内容")
            print("注意：直接解析HTML页面不可靠，建议使用官方API")
            
            # 查找年份信息
            year_pattern = r'\b(20[12]\d)\b'
            years_found = set(re.findall(year_pattern, content))
            
            if years_found:
                print(f"找到以下年份的文件: {sorted(years_found)}")
            else:
                print("未找到年份信息")
                
    except Exception as e:
        print(f"直接解析失败: {str(e)}")
        print("建议使用官方API或第三方数据源")

if __name__ == "__main__":
    get_aapl_eps_simple(2010, 2025)
    # 尝试直接从EDGAR获取（可选）
    # get_eps_from_edgar_direct(2010, 2025)