import requests
import re
from sec_api import QueryApi
import sys

def get_aapl_eps_from_edgar(start_year=2010, end_year=2025):
    """
    从SEC EDGAR获取苹果公司(AAPL)指定年份范围内的年报中的EPS数据
    """
    try:
        # 初始化sec_api客户端
        print("正在初始化SEC EDGAR API客户端...")
        queryApi = QueryApi(api_key="demo")  # 使用demo密钥，实际使用时需要替换为自己的API密钥
        
        # 构建查询，获取AAPL的10-K文件
        query = {
            "query": { "query_string": { "query": "ticker:AAPL AND formType:\"10-K\"" } },
            "from": "0",
            "size": "20",
            "sort": [{ "filedAt": { "order": "desc" } }]
        }
        
        print("正在查询AAPL的10-K文件...")
        filings = queryApi.get_filings(query)
        
        if not filings or "filings" not in filings:
            print("未找到任何10-K文件")
            return
        
        print(f"共找到 {len(filings['filings'])} 份10-K文件")
        print("\n苹果公司(AAPL) 2010-2025年基本每股收益(EPS)数据：")
        print("=" * 50)
        print("年份 | 基本EPS")
        print("-" * 50)
        
        # 遍历所有 filings
        for filing in filings['filings']:
            try:
                filing_url = filing.get("linkToFilingDetails", "")
                filing_date = filing.get("filedAt", "")
                
                if not filing_url or not filing_date:
                    continue
                
                # 提取年份
                year = int(filing_date[:4])
                if not (start_year <= year <= end_year):
                    continue
                
                print(f"正在处理 {year} 年的10-K文件...")
                
                # 下载10-K文件内容
                response = requests.get(filing_url)
                if response.status_code != 200:
                    print(f"  无法下载文件: HTTP {response.status_code}")
                    continue
                
                content = response.text
                
                # 使用正则表达式查找EPS数据
                # 查找模式如: "Earnings per share: Basic" 或 "Basic earnings per share"
                patterns = [
                    r'Earnings per share:\s*Basic\s*([\d\.\(\)\-]+)',
                    r'Basic earnings per share\s*([\d\.\(\)\-]+)',
                    r'EPS\s*Basic\s*([\d\.\(\)\-]+)'
                ]
                
                eps_found = False
                for pattern in patterns:
                    matches = re.findall(pattern, content, re.IGNORECASE)
                    if matches:
                        # 取第一个匹配的EPS值
                        eps = matches[0]
                        # 处理负数格式，如(0.50)表示-0.50
                        if eps.startswith('(') and eps.endswith(')'):
                            eps = '-' + eps[1:-1]
                        
                        print(f"{year}  | ${eps}")
                        eps_found = True
                        break
                
                if not eps_found:
                    print(f"{year}  | 未找到EPS数据")
                    
            except Exception as e:
                print(f"{year}  | 处理错误: {str(e)}")
                continue
        
        print("=" * 50)
        print("数据获取完成")
        
    except ImportError:
        print("错误: 未找到sec_api库。请先安装: pip install sec-api")
        print("\n备选方案：使用SEC EDGAR直接API")
        use_alternative_method(start_year, end_year)
    except Exception as e:
        print(f"发生错误: {str(e)}")
        print("\n备选方案：使用SEC EDGAR直接API")
        use_alternative_method(start_year, end_year)

def use_alternative_method(start_year=2010, end_year=2025):
    """
    备选方法：使用requests直接调用SEC EDGAR API获取EPS数据
    """
    try:
        print("\n正在使用备选方法获取数据...")
        
        # 使用Financial Modeling Prep的免费API（有访问限制）
        url = f"https://financialmodelingprep.com/api/v3/income-statement/AAPL?period=annual&limit=20&apikey=demo"
        
        response = requests.get(url)
        if response.status_code == 200:
            data = response.json()
            
            print("\n苹果公司(AAPL) 2010-2025年基本每股收益(EPS)数据：")
            print("=" * 50)
            print("年份 | 基本EPS")
            print("-" * 50)
            
            # 按年份排序
            sorted_data = sorted(data, key=lambda x: x['calendarYear'])
            
            for item in sorted_data:
                year = item['calendarYear']
                if start_year <= year <= end_year:
                    eps = item.get('epsBasic', 'N/A')
                    print(f"{year}  | ${eps}")
            
            print("=" * 50)
            print("数据获取完成")
            print("\n注意：此数据来自Financial Modeling Prep，可能与SEC EDGAR原始数据有所不同")
        else:
            print(f"无法获取数据: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"备选方法也失败了: {str(e)}")
        print("请检查网络连接或尝试其他数据源")

if __name__ == "__main__":
    get_aapl_eps_from_edgar(2010, 2025)