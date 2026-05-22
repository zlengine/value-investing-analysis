import urllib.request
import urllib.error
import re
import time
import csv
from datetime import datetime

class EPSExtractor:
    """
    从已知的AAPL 10-K文件链接中提取EPS数据
    只使用Python标准库，无需外部依赖
    """
    
    def __init__(self):
        self.headers = {
            "User-Agent": "Your Name your.email@example.com",  # 请替换为您的姓名和邮箱
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
        }
        self.request_delay = 2  # SEC要求的请求间隔
    
    def make_request(self, url):
        """
        发送HTTP请求并返回响应内容
        """
        try:
            req = urllib.request.Request(url, headers=self.headers)
            with urllib.request.urlopen(req, timeout=20) as response:
                return response.read().decode('utf-8')
        except urllib.error.URLError as e:
            print(f"请求失败: {url}")
            print(f"错误信息: {str(e)}")
            return None
    
    def extract_eps(self, html_content):
        """
        从HTML内容中提取EPS数据
        """
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
    
    def process_10k_files(self, file_links):
        """
        处理多个10-K文件，提取EPS数据
        """
        print("=" * 70)
        print("从已知10-K文件链接提取AAPL EPS数据")
        print("=" * 70)
        
        results = []
        
        for year, url in file_links.items():
            print(f"\n处理 {year} 年的10-K文件:")
            print(f"文件链接: {url}")
            
            # 发送请求
            html_content = self.make_request(url)
            if not html_content:
                print(f"  无法获取文件内容")
                continue
            
            # 提取EPS数据
            eps = self.extract_eps(html_content)
            if eps:
                print(f"  成功提取EPS数据: ${eps}")
                results.append({
                    "year": year,
                    "url": url,
                    "eps": eps
                })
            else:
                print(f"  未找到EPS数据")
            
            # 遵守SEC的请求间隔规则
            time.sleep(self.request_delay)
        
        # 按年份排序
        results.sort(key=lambda x: int(x["year"]))
        
        # 输出结果
        print("\n" + "=" * 70)
        print("提取结果")
        print("=" * 70)
        print("年份 | EPS数据")
        print("-" * 70)
        
        for result in results:
            print(f"{result['year']}  | ${result['eps']}")
        
        print("-" * 70)
        print(f"共成功提取 {len(results)} 年的EPS数据")
        
        # 保存到CSV文件
        self.save_to_csv(results)
        
        return results
    
    def save_to_csv(self, results):
        """
        将结果保存到CSV文件
        """
        filename = "aapl_eps_from_known_links.csv"
        
        try:
            with open(filename, 'w', newline='', encoding='utf-8') as csvfile:
                fieldnames = ['year', 'url', 'eps']
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                
                writer.writeheader()
                for result in results:
                    writer.writerow(result)
            
            print(f"\n结果已保存到 {filename}")
            
        except Exception as e:
            print(f"保存CSV文件失败: {str(e)}")

def main():
    """
    主函数，定义已知的10-K文件链接并开始提取
    """
    # 用户提供的AAPL 10-K文件链接
    known_10k_links = {
        "2025": "https://www.sec.gov/Archives/edgar/data/320193/000032019325000079/aapl-20250927.htm",
        "2024": "https://www.sec.gov/Archives/edgar/data/320193/000032019324000123/aapl-20240928.htm",
        "2023": "https://www.sec.gov/Archives/edgar/data/320193/000032019323000106/aapl-20230930.htm",
        "2022": "https://www.sec.gov/Archives/edgar/data/320193/000032019322000108/aapl-20220924.htm",
        "2021": "https://www.sec.gov/Archives/edgar/data/320193/000032019321000105/aapl-20210925.htm",
        "2020": "https://www.sec.gov/Archives/edgar/data/320193/000032019320000096/aapl-20200926.htm",
        "2019": "https://www.sec.gov/Archives/edgar/data/320193/000032019319000119/a10-k20199282019.htm"
    }
    
    # 补充更多年份的10-K文件链接
    additional_links = {
        "2018": "https://www.sec.gov/Archives/edgar/data/320193/000032019318000145/a10-k201809292018.htm",
        "2017": "https://www.sec.gov/Archives/edgar/data/320193/000032019317000070/a10-k201709302017.htm",
        "2016": "https://www.sec.gov/Archives/edgar/data/320193/000032019316000105/a10-k201609242016.htm",
        "2015": "https://www.sec.gov/Archives/edgar/data/320193/000032019315000103/a10-k201509262015.htm",
        "2014": "https://www.sec.gov/Archives/edgar/data/320193/000119312514383437/d783162d10k.htm",
        "2013": "https://www.sec.gov/Archives/edgar/data/320193/000119312513416534/d590790d10k.htm",
        "2012": "https://www.sec.gov/Archives/edgar/data/320193/000119312512444068/d411355d10k.htm",
        "2011": "https://www.sec.gov/Archives/edgar/data/320193/000119312511282113/d220369d10k.htm",
        "2010": "https://www.sec.gov/Archives/edgar/data/320193/000119312510238044/d10k.htm"
    }
    
    # 合并所有链接
    all_links = {**known_10k_links, **additional_links}
    
    # 创建提取器并开始提取
    extractor = EPSExtractor()
    extractor.process_10k_files(all_links)

if __name__ == "__main__":
    print("启动AAPL EPS数据提取程序...")
    print("使用已知的10-K文件链接，绕过搜索API限制")
    print("=" * 70)
    
    main()
    
    print("\n提取程序完成!")