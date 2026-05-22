import requests
from bs4 import BeautifulSoup
import re
import time
import csv
from datetime import datetime

class AAPLEPSExtractor:
    """
    从SEC EDGAR搜索页面提取AAPL 10-K文件中的Basic和Diluted EPS数据
    只使用网络获取数据，不使用本地CSV文件
    """
    
    def __init__(self):
        self.base_url = "https://www.sec.gov"
        self.search_url = "https://www.sec.gov/edgar/search/?r=el#/dateRange=custom&category=form-cat0&ciks=0000320193&entityName=Apple%2520Inc.%2520(AAPL)%2520(CIK%25200000320193)&startdt=2010-11-01&enddt=2025-11-16&filter_forms=10-K"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        self.request_delay = 2  # SEC要求的请求间隔，至少1秒
    
    def get_10k_links(self):
        """
        从SEC EDGAR搜索结果获取AAPL 2010-2025年的10-K文件链接
        使用browse-edgar API而非JavaScript动态页面
        """
        print("正在获取AAPL 2010-2025年的10-K文件链接...")
        
        # 使用EDGAR的browse-edgar接口获取文件列表
        cik = "0000320193"
        api_url = f"{self.base_url}/cgi-bin/browse-edgar"
        
        params = {
            "action": "getcompany",
            "CIK": cik,
            "type": "10-K",
            "dateb": "20251116",
            "datea": "20101101",
            "count": "100"
        }
        
        try:
            response = requests.get(api_url, headers=self.headers, params=params, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 找到包含文件列表的表格
            table = soup.find('table', class_='tableFile2')
            if not table:
                print("未找到文件列表表格")
                return []
            
            # 提取表格中的文件链接
            ten_k_links = []
            rows = table.find_all('tr')[1:]  # 跳过表头
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 4:
                    continue
                
                form_type = cols[0].text.strip()
                filing_date = cols[3].text.strip()
                
                # 只处理10-K文件
                if form_type != "10-K":
                    continue
                
                # 获取filings详情页面链接
                filings_link = cols[1].find('a', href=True)
                if filings_link:
                    filings_url = f"{self.base_url}{filings_link['href']}"
                    
                    # 添加到结果列表
                    ten_k_links.append({
                        "filing_date": filing_date,
                        "filings_url": filings_url
                    })
            
            print(f"成功获取 {len(ten_k_links)} 份10-K文件链接")
            return ten_k_links
            
        except requests.RequestException as e:
            print(f"获取10-K链接失败: {str(e)}")
            return []
    
    def get_10k_document_url(self, filings_url):
        """
        从filings详情页面获取10-K主文档的URL
        """
        time.sleep(self.request_delay)  # 遵守SEC请求间隔规则
        
        try:
            response = requests.get(filings_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 找到包含文档链接的表格
            table = soup.find('table', class_='tableFile', summary='Document Format Files')
            if not table:
                print(f"未找到文档链接表格: {filings_url}")
                return None
            
            rows = table.find_all('tr')[1:]  # 跳过表头
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 4:
                    continue
                
                document_type = cols[2].text.strip()
                if document_type == "10-K":
                    document_link = cols[3].find('a', href=True)
                    if document_link:
                        return f"{self.base_url}{document_link['href']}"
            
            print(f"未找到10-K文档链接: {filings_url}")
            return None
            
        except requests.RequestException as e:
            print(f"获取10-K文档URL失败: {str(e)}")
            return None
    
    def extract_eps_data(self, document_url):
        """
        从10-K文档中提取Basic和Diluted EPS数据
        """
        time.sleep(self.request_delay)  # 遵守SEC请求间隔规则
        
        try:
            response = requests.get(document_url, headers=self.headers, timeout=20)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 获取文档文本，用于正则表达式匹配
            document_text = soup.get_text()
            
            # 定义提取EPS的正则表达式模式
            eps_patterns = {
                "basic": [
                    r'Earnings per share.*?Basic.*?([\d\.\(\)\-]+)',
                    r'Basic.*?Earnings per share.*?([\d\.\(\)\-]+)',
                    r'BASIC\s*EPS\s*([\d\.\(\)\-]+)',
                    r'EPS.*?BASIC\s*([\d\.\(\)\-]+)'
                ],
                "diluted": [
                    r'Earnings per share.*?Diluted.*?([\d\.\(\)\-]+)',
                    r'Diluted.*?Earnings per share.*?([\d\.\(\)\-]+)',
                    r'DILUTED\s*EPS\s*([\d\.\(\)\-]+)',
                    r'EPS.*?DILUTED\s*([\d\.\(\)\-]+)'
                ]
            }
            
            eps_data = {
                "basic": None,
                "diluted": None
            }
            
            # 提取Basic EPS
            for pattern in eps_patterns["basic"]:
                matches = re.findall(pattern, document_text, re.IGNORECASE | re.DOTALL)
                if matches:
                    # 处理匹配结果
                    eps_value = matches[0].strip()
                    # 处理负数格式 (1.23) -> -1.23
                    if eps_value.startswith('(') and eps_value.endswith(')'):
                        eps_value = '-' + eps_value[1:-1]
                    eps_data["basic"] = eps_value
                    break
            
            # 提取Diluted EPS
            for pattern in eps_patterns["diluted"]:
                matches = re.findall(pattern, document_text, re.IGNORECASE | re.DOTALL)
                if matches:
                    # 处理匹配结果
                    eps_value = matches[0].strip()
                    # 处理负数格式 (1.23) -> -1.23
                    if eps_value.startswith('(') and eps_value.endswith(')'):
                        eps_value = '-' + eps_value[1:-1]
                    eps_data["diluted"] = eps_value
                    break
            
            return eps_data
            
        except requests.RequestException as e:
            print(f"提取EPS数据失败: {str(e)}")
            return None
    
    def extract_all_eps(self):
        """
        提取所有10-K文件中的EPS数据
        """
        print("=" * 70)
        print("AAPL 10-K文件EPS数据提取")
        print("=" * 70)
        
        # 获取10-K链接
        ten_k_links = self.get_10k_links()
        if not ten_k_links:
            print("没有找到任何10-K文件链接")
            return []
        
        results = []
        
        for ten_k in ten_k_links:
            print(f"\n处理文件: {ten_k['filing_date']}")
            print(f"Filings URL: {ten_k['filings_url']}")
            
            # 获取10-K文档URL
            document_url = self.get_10k_document_url(ten_k['filings_url'])
            if not document_url:
                print(f"跳过文件: {ten_k['filing_date']}")
                continue
            
            print(f"Document URL: {document_url}")
            
            # 提取EPS数据
            eps_data = self.extract_eps_data(document_url)
            if not eps_data:
                print(f"未提取到EPS数据: {ten_k['filing_date']}")
                continue
            
            # 计算财务年度
            filing_date_obj = datetime.strptime(ten_k['filing_date'], "%Y-%m-%d")
            # 苹果公司的财年通常截止到9月30日
            fiscal_year = filing_date_obj.year
            if filing_date_obj.month <= 9:
                fiscal_year -= 1
            
            # 添加到结果列表
            results.append({
                "fiscal_year": fiscal_year,
                "filing_date": ten_k['filing_date'],
                "document_url": document_url,
                "basic_eps": eps_data["basic"],
                "diluted_eps": eps_data["diluted"]
            })
            
            print(f"成功提取 {fiscal_year} 年EPS数据:")
            print(f"  Basic EPS: ${eps_data['basic']}")
            print(f"  Diluted EPS: ${eps_data['diluted']}")
        
        # 按财务年度排序
        results.sort(key=lambda x: x["fiscal_year"])
        
        # 保存到CSV文件
        self.save_to_csv(results)
        
        return results
    
    def save_to_csv(self, results):
        """
        将提取的EPS数据保存到CSV文件
        """
        filename = "aapl_eps_basic_diluted.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['fiscal_year', 'filing_date', 'document_url', 'basic_eps', 'diluted_eps']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for result in results:
                    writer.writerow(result)
            
            print(f"\n结果已保存到 {filename}")
            
        except Exception as e:
            print(f"保存CSV文件失败: {str(e)}")

if __name__ == "__main__":
    print("启动AAPL EPS数据提取程序")
    print("从SEC EDGAR获取10-K文件并提取Basic和Diluted EPS")
    print("=" * 70)
    
    # 提示用户安装必要的依赖
    print("请确保已安装必要的依赖:")
    print("pip install requests beautifulsoup4")
    print("=" * 70)
    
    extractor = AAPLEPSExtractor()
    results = extractor.extract_all_eps()
    
    print("\n" + "=" * 70)
    print("提取完成!")
    print("=" * 70)
    
    if results:
        print(f"共成功提取 {len(results)} 年的EPS数据")
    else:
        print("未提取到任何EPS数据")