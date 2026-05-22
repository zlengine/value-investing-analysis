import requests
from bs4 import BeautifulSoup
import re
import time
import csv
from datetime import datetime

class EdgarEPSCrawler:
    """
    从SEC EDGAR搜索页面爬取AAPL年报中的EPS数据
    遵守SEC EDGAR的爬虫规则，使用合理的请求间隔
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
        
    def get_filing_links(self):
        """
        从搜索页面获取所有10-K文件的链接
        注意：由于EDGAR搜索页面使用JavaScript动态加载内容，
        我们需要使用不同的方法获取文件列表
        """
        print("正在从SEC EDGAR搜索页面获取10-K文件列表...")
        
        # 直接使用EDGAR REST API获取文件列表，比解析搜索页面更可靠
        # AAPL的CIK是0000320193
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
            filings = []
            
            # 找到包含文件列表的表格
            table = soup.find('table', class_='tableFile2')
            if not table:
                print("未找到文件列表表格")
                return filings
            
            rows = table.find_all('tr')[1:]  # 跳过表头
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 4:
                    continue
                
                # 提取文件类型、日期和链接
                form_type = cols[0].text.strip()
                filing_date = cols[3].text.strip()
                
                # 确保是10-K文件
                if form_type != "10-K":
                    continue
                
                # 获取 filings 详情页面链接
                filings_link = cols[1].find('a', href=True)
                if not filings_link:
                    continue
                
                filings_url = f"{self.base_url}{filings_link['href']}"
                
                filings.append({
                    "form_type": form_type,
                    "filing_date": filing_date,
                    "filings_url": filings_url
                })
            
            print(f"成功获取 {len(filings)} 份10-K文件")
            return filings
            
        except requests.RequestException as e:
            print(f"获取文件列表失败: {str(e)}")
            return []
    
    def get_10k_document_link(self, filings_url):
        """
        从 filings 详情页面获取10-K主文档的链接
        """
        try:
            time.sleep(self.request_delay)
            response = requests.get(filings_url, headers=self.headers, timeout=15)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 找到包含文档链接的表格
            table = soup.find('table', class_='tableFile', summary='Document Format Files')
            if not table:
                return None
            
            rows = table.find_all('tr')[1:]  # 跳过表头
            
            for row in rows:
                cols = row.find_all('td')
                if len(cols) < 4:
                    continue
                
                # 找到主文档（通常是第一个HTML文件）
                document_type = cols[2].text.strip()
                if document_type == "10-K":
                    document_link = cols[3].find('a', href=True)
                    if document_link:
                        return f"{self.base_url}{document_link['href']}"
            
            return None
            
        except requests.RequestException as e:
            print(f"获取文档链接失败: {str(e)}")
            return None
    
    def extract_eps_from_10k(self, document_url):
        """
        从10-K文档中提取EPS数据
        """
        try:
            time.sleep(self.request_delay)
            response = requests.get(document_url, headers=self.headers, timeout=20)
            response.raise_for_status()
            
            content = response.text
            
            # 提取EPS数据的正则表达式模式
            eps_patterns = [
                # 模式1: Earnings per share: Basic $X.XX
                r'Earnings per share:\s*Basic\s*\$?([\d\.\(\)\-]+)',
                # 模式2: Basic earnings per share $X.XX
                r'Basic earnings per share\s*\$?([\d\.\(\)\-]+)',
                # 模式3: EPS - Basic $X.XX
                r'EPS\s*\-\s*Basic\s*\$?([\d\.\(\)\-]+)',
                # 模式4: Basic EPS $X.XX
                r'Basic EPS\s*\$?([\d\.\(\)\-]+)',
                # 模式5: Earnings per common share - basic $X.XX
                r'Earnings per common share\s*\-\s*basic\s*\$?([\d\.\(\)\-]+)',
                # 模式6: Net income per share - basic $X.XX
                r'Net income per share\s*\-\s*basic\s*\$?([\d\.\(\)\-]+)'
            ]
            
            # 尝试所有模式
            for pattern in eps_patterns:
                matches = re.findall(pattern, content, re.IGNORECASE)
                if matches:
                    # 获取第一个匹配项（通常是最重要的EPS数据）
                    eps = matches[0]
                    
                    # 处理负数格式，如(0.50)表示-0.50
                    if eps.startswith('(') and eps.endswith(')'):
                        eps = '-' + eps[1:-1]
                    
                    return eps
            
            return None
            
        except requests.RequestException as e:
            print(f"获取文档内容失败: {str(e)}")
            return None
        except Exception as e:
            print(f"解析文档失败: {str(e)}")
            return None
    
    def crawl_eps_data(self):
        """
        爬取所有10-K文件的EPS数据
        """
        print("=" * 70)
        print("AAPL 2010-2025年年报EPS数据爬取")
        print("数据来源: SEC EDGAR")
        print("=" * 70)
        
        # 获取文件列表
        filings = self.get_filing_links()
        if not filings:
            print("没有找到任何10-K文件")
            return
        
        results = []
        
        for filing in filings:
            print(f"\n处理文件: {filing['form_type']} - {filing['filing_date']}")
            
            # 获取10-K文档链接
            document_url = self.get_10k_document_link(filing['filings_url'])
            if not document_url:
                print(f"  未找到10-K文档链接")
                continue
            
            print(f"  文档链接: {document_url}")
            
            # 提取EPS数据
            eps = self.extract_eps_from_10k(document_url)
            if eps:
                print(f"  EPS数据: ${eps}")
                
                # 计算财务年度
                filing_date_obj = datetime.strptime(filing['filing_date'], "%Y-%m-%d")
                # 苹果公司的财年通常截止到9月30日
                fiscal_year = filing_date_obj.year
                if filing_date_obj.month <= 9:
                    fiscal_year -= 1
                
                results.append({
                    "fiscal_year": fiscal_year,
                    "filing_date": filing['filing_date'],
                    "document_url": document_url,
                    "eps": eps
                })
            else:
                print(f"  未找到EPS数据")
        
        # 按财务年度排序
        results.sort(key=lambda x: x["fiscal_year"])
        
        # 输出结果
        print("\n" + "=" * 70)
        print("爬取结果")
        print("=" * 70)
        print("财年 | 提交日期 | EPS数据")
        print("-" * 70)
        
        for result in results:
            print(f"{result['fiscal_year']}  | {result['filing_date']} | ${result['eps']}")
        
        print("-" * 70)
        print(f"共成功爬取 {len(results)} 年的EPS数据")
        
        # 保存到CSV文件
        self.save_to_csv(results)
        
        return results
    
    def save_to_csv(self, results):
        """
        将结果保存到CSV文件
        """
        filename = "aapl_eps_2010_2025.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['fiscal_year', 'filing_date', 'document_url', 'eps']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for result in results:
                    writer.writerow(result)
            
            print(f"\n结果已保存到 {filename}")
            
        except Exception as e:
            print(f"保存CSV文件失败: {str(e)}")

if __name__ == "__main__":
    # 安装必要的依赖
    # pip install requests beautifulsoup4
    
    crawler = EdgarEPSCrawler()
    crawler.crawl_eps_data()