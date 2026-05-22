import urllib.request
import urllib.error
import html.parser
import re
import time
import csv
from datetime import datetime

class EDGARParser(html.parser.HTMLParser):
    """
    简单的HTML解析器，用于提取SEC EDGAR页面中的链接和数据
    只使用Python标准库
    """
    def __init__(self):
        super().__init__()
        self.table_rows = []
        self.current_row = []
        self.in_table = False
        self.in_table_row = False
        self.in_table_cell = False
        self.links = []
        self.current_link = None
    
    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            # 检查是否是文件列表表格
            for attr in attrs:
                if attr[0] == 'class' and 'tableFile2' in attr[1]:
                    self.in_table = True
                    break
                if attr[0] == 'summary' and 'Document Format Files' in attr[1]:
                    self.in_table = True
                    break
        elif tag == 'tr' and self.in_table:
            self.in_table_row = True
            self.current_row = []
        elif tag == 'td' and self.in_table_row:
            self.in_table_cell = True
        elif tag == 'a' and attrs:
            href = None
            for attr in attrs:
                if attr[0] == 'href':
                    href = attr[1]
                    break
            if href:
                self.current_link = href
    
    def handle_endtag(self, tag):
        if tag == 'table':
            self.in_table = False
        elif tag == 'tr' and self.in_table:
            self.in_table_row = False
            if self.current_row:
                self.table_rows.append(self.current_row)
        elif tag == 'td' and self.in_table_row:
            self.in_table_cell = False
    
    def handle_data(self, data):
        if self.in_table_cell:
            self.current_row.append(data.strip())
        if self.current_link and data.strip():
            self.links.append((data.strip(), self.current_link))
            self.current_link = None

class AAPLEPSExtractor:
    """
    从SEC EDGAR搜索页面提取AAPL 10-K文件中的Basic和Diluted EPS数据
    只使用Python标准库，不使用任何外部依赖
    只使用网络获取数据，不使用本地CSV文件
    """
    
    def __init__(self):
        self.base_url = "https://www.sec.gov"
        self.headers = {
            "User-Agent": "Your Name your.email@example.com",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        }
        self.request_delay = 2  # SEC要求的请求间隔，至少1秒
    
    def make_request(self, url):
        """
        发送HTTP请求并返回响应内容
        """
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                return response.read().decode('utf-8', errors='ignore')
        except urllib.error.URLError as e:
            print(f"请求失败: {url}")
            print(f"错误信息: {str(e)}")
            return None
    
    def get_10k_links(self):
        """
        从SEC EDGAR搜索结果获取AAPL 2010-2025年的10-K文件链接
        """
        print("正在获取AAPL 2010-2025年的10-K文件链接...")
        
        # 使用EDGAR的browse-edgar接口获取文件列表
        cik = "0000320193"
        api_url = f"{self.base_url}/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-K&dateb=20251116&datea=20101101&count=100"
        
        html_content = self.make_request(api_url)
        if not html_content:
            return []
        
        # 直接从HTML中提取所有符合条件的链接
        # 使用更简单的正则表达式匹配
        # 查找所有以 /Archives/edgar/data/ 开头的链接
        all_links = re.findall(r'<a href="(/Archives/edgar/data/\d+/[^"]+)"', html_content)
        
        # 过滤出 index.htm 链接
        filings_links = []
        for link in all_links:
            if link.endswith('-index.htm') or link.endswith('-index.html'):
                filings_links.append(link)
        
        # 去重
        filings_links = list(set(filings_links))
        
        # 提取所有日期
        all_dates = re.findall(r'\b(\d{4}-\d{2}-\d{2})\b', html_content)
        
        # 构建10-K链接列表，只包含最近的16年数据
        ten_k_links = []
        for i, link in enumerate(filings_links[:16]):  # 只取最近的16个文件
            # 为每个链接分配一个日期，使用提取到的日期列表
            filing_date = all_dates[i] if i < len(all_dates) else f"20{25-i}-10-31"
            filings_url = f"{self.base_url}{link}"
            ten_k_links.append({
                "filing_date": filing_date,
                "filings_url": filings_url
            })
        
        # 如果通过链接提取没有找到足够的文件，使用硬编码的10-K链接
        if len(ten_k_links) < 7:  # 至少需要7个文件（2019-2025）
            print("使用硬编码的10-K链接列表")
            # 硬编码的10-K链接，覆盖2019-2025年
            hardcoded_links = [
                {"filing_date": "2025-10-31", "filings_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/0000320193-25-000079-index.htm"},
                {"filing_date": "2024-10-30", "filings_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/0000320193-24-000123-index.htm"},
                {"filing_date": "2023-10-31", "filings_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/0000320193-23-000106-index.htm"},
                {"filing_date": "2022-10-28", "filings_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019322000108/0000320193-22-000108-index.htm"},
                {"filing_date": "2021-10-29", "filings_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019321000105/0000320193-21-000105-index.htm"},
                {"filing_date": "2020-10-30", "filings_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019320000096/0000320193-20-000096-index.htm"},
                {"filing_date": "2019-10-31", "filings_url": "https://www.sec.gov/Archives/edgar/data/320193/000032019319000119/0000320193-19-000119-index.htm"}
            ]
            ten_k_links = hardcoded_links
        
        print(f"成功获取 {len(ten_k_links)} 份10-K文件链接")
        return ten_k_links
    
    def get_10k_document_url(self, filings_url):
        """
        从filings详情页面获取10-K主文档的URL
        """
        time.sleep(self.request_delay)  # 遵守SEC请求间隔规则
        
        html_content = self.make_request(filings_url)
        if not html_content:
            return None
        
        # 使用自定义解析器解析HTML
        parser = EDGARParser()
        parser.feed(html_content)
        
        # 查找10-K文档链接
        for link_text, href in parser.links:
            if href.endswith(".htm") or href.endswith(".html"):
                # 检查是否是10-K文档
                if "10-k" in href.lower() or "annual" in href.lower():
                    return f"{self.base_url}{href}"
        
        # 如果没有找到明确的10-K链接，返回第一个HTML链接
        for link_text, href in parser.links:
            if href.endswith(".htm") or href.endswith(".html"):
                return f"{self.base_url}{href}"
        
        print(f"未找到10-K文档链接: {filings_url}")
        return None
    
    def extract_eps_data(self, document_url):
        """
        从10-K文档中提取Basic和Diluted EPS数据
        """
        time.sleep(self.request_delay)  # 遵守SEC请求间隔规则
        
        html_content = self.make_request(document_url)
        if not html_content:
            return None
        
        # 转换为大写以便不区分大小写匹配
        document_text = html_content.upper()
        
        # 定义提取EPS的正则表达式模式
        eps_patterns = {
            "basic": [
                r'EARNINGS PER SHARE.*?BASIC.*?([\d\.\(\)\-]+)',
                r'BASIC.*?EARNINGS PER SHARE.*?([\d\.\(\)\-]+)',
                r'BASIC\s*EPS\s*([\d\.\(\)\-]+)',
                r'EPS.*?BASIC\s*([\d\.\(\)\-]+)'
            ],
            "diluted": [
                r'EARNINGS PER SHARE.*?DILUTED.*?([\d\.\(\)\-]+)',
                r'DILUTED.*?EARNINGS PER SHARE.*?([\d\.\(\)\-]+)',
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
            matches = re.findall(pattern, document_text, re.DOTALL)
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
            matches = re.findall(pattern, document_text, re.DOTALL)
            if matches:
                # 处理匹配结果
                eps_value = matches[0].strip()
                # 处理负数格式 (1.23) -> -1.23
                if eps_value.startswith('(') and eps_value.endswith(')'):
                    eps_value = '-' + eps_value[1:-1]
                eps_data["diluted"] = eps_value
                break
        
        return eps_data
    
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
    print("只使用Python标准库，无需安装外部依赖")
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