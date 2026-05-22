import urllib.request
import urllib.error
import html.parser
import re
import time
import csv
from datetime import datetime

class EdgarParser(html.parser.HTMLParser):
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

class EdgarEPSCrawler:
    """
    从SEC EDGAR搜索页面爬取AAPL年报中的EPS数据
    只使用Python标准库，无需安装任何外部依赖
    遵守SEC EDGAR的爬虫规则
    """
    
    def __init__(self):
        self.base_url = "https://www.sec.gov"
        self.headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.request_delay = 2  # SEC要求的请求间隔，至少1秒
    
    def make_request(self, url):
        """
        发送HTTP请求，只使用标准库
        """
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=15) as response:
                return response.read().decode('utf-8')
        except urllib.error.URLError as e:
            print(f"请求失败: {str(e)}")
            return None
    
    def get_filing_links(self):
        """
        从SEC EDGAR API获取AAPL的10-K文件列表
        """
        print("正在从SEC EDGAR获取10-K文件列表...")
        
        # 使用EDGAR的browse-edgar接口
        cik = "0000320193"
        api_url = f"{self.base_url}/cgi-bin/browse-edgar?action=getcompany&CIK={cik}&type=10-K&dateb=20251116&datea=20101101&count=100"
        
        html_content = self.make_request(api_url)
        if not html_content:
            return []
        
        # 使用自定义解析器解析HTML
        parser = EdgarParser()
        parser.feed(html_content)
        
        filings = []
        
        # 提取表格数据
        for row in parser.table_rows:
            if len(row) < 4:
                continue
            
            form_type = row[0]
            filing_date = row[3]
            
            if form_type == "10-K":
                # 查找该文件的链接
                for link_text, href in parser.links:
                    if link_text == "Documents" and href.startswith("/Archives/edgar/data/"):
                        filings_url = f"{self.base_url}{href}"
                        filings.append({
                            "form_type": form_type,
                            "filing_date": filing_date,
                            "filings_url": filings_url
                        })
                        break
        
        print(f"成功获取 {len(filings)} 份10-K文件")
        return filings
    
    def get_10k_document_link(self, filings_url):
        """
        从filings页面获取10-K主文档链接
        """
        time.sleep(self.request_delay)  # 遵守SEC请求间隔规则
        
        html_content = self.make_request(filings_url)
        if not html_content:
            return None
        
        # 使用正则表达式提取10-K文档链接
        # 查找类似: <a href="/Archives/edgar/data/320193/000032019323000074/aapl-20230930.htm">
        pattern = r'<a href="(/Archives/edgar/data/\d+/[\d\w-]+/[\d\w-]+\.htm)".*?10-K'
        match = re.search(pattern, html_content, re.IGNORECASE)
        
        if match:
            return f"{self.base_url}{match.group(1)}"
        
        # 如果正则表达式失败，尝试使用解析器
        parser = EdgarParser()
        parser.feed(html_content)
        
        for link_text, href in parser.links:
            if href.endswith(".htm") or href.endswith(".html"):
                return f"{self.base_url}{href}"
        
        return None
    
    def extract_eps_from_10k(self, document_url):
        """
        从10-K文档中提取EPS数据
        """
        time.sleep(self.request_delay)  # 遵守SEC请求间隔规则
        
        html_content = self.make_request(document_url)
        if not html_content:
            return None
        
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
            matches = re.findall(pattern, html_content, re.IGNORECASE)
            if matches:
                # 获取第一个匹配项
                eps = matches[0]
                
                # 处理负数格式，如(0.50)表示-0.50
                if eps.startswith('(') and eps.endswith(')'):
                    eps = '-' + eps[1:-1]
                
                return eps
        
        return None
    
    def crawl_eps_data(self):
        """
        爬取所有10-K文件的EPS数据
        """
        print("=" * 70)
        print("AAPL 2010-2025年年报EPS数据爬取")
        print("数据来源: SEC EDGAR")
        print("使用Python标准库，无需外部依赖")
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
        filename = "aapl_eps_2010_2025_standard.csv"
        
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
    print("启动AAPL EPS数据爬取程序...")
    print("此程序只使用Python标准库，无需安装任何外部依赖")
    print("程序将遵守SEC EDGAR的爬虫规则，使用合理的请求间隔")
    print("=" * 70)
    
    crawler = EdgarEPSCrawler()
    crawler.crawl_eps_data()
    
    print("\n爬取程序完成!")