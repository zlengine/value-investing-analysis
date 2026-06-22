"""
美股价值投资分析网站 - 打分数据服务器
提供 SQLite 数据库存储 + JSON 文件同步（供 GitHub Pages 读取）
每次打分自动备份到 backups/ 目录

启动方式：python server.py
访问：http://localhost:8000
"""
import http.server
import json
import os
import sqlite3
import shutil
from datetime import datetime
from urllib.parse import parse_qs

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'scores.db')
JSON_PATH = os.path.join(BASE_DIR, 'scores_data.json')
BACKUP_DIR = os.path.join(BASE_DIR, 'backups', 'scores')

os.makedirs(BACKUP_DIR, exist_ok=True)


def init_db():
    """初始化数据库"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS scores (
        code TEXT PRIMARY KEY,
        fundamental INTEGER DEFAULT 0,
        price INTEGER DEFAULT 0,
        updated TEXT
    )''')
    conn.commit()
    conn.close()


def get_all_scores():
    """从数据库获取所有打分"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('SELECT code, fundamental, price, updated FROM scores')
    rows = c.fetchall()
    conn.close()
    scores = {}
    for code, f, p, updated in rows:
        scores[code] = {
            'fundamental': f or 0,
            'price': p or 0,
            'updated': updated or ''
        }
    return scores


def save_score(code, fundamental, price):
    """保存单个打分到数据库"""
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    updated = datetime.now().isoformat()
    c.execute('''INSERT OR REPLACE INTO scores (code, fundamental, price, updated)
                 VALUES (?, ?, ?, ?)''', (code, fundamental, price, updated))
    conn.commit()
    conn.close()
    return updated


def export_to_json():
    """将数据库打分导出到 JSON 文件（供 GitHub Pages 读取）"""
    scores = get_all_scores()
    data = {
        'scores': scores,
        'updated': datetime.now().isoformat(),
        'count': len(scores)
    }
    with open(JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    return data


def backup_scores():
    """备份打分数据"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = os.path.join(BACKUP_DIR, f'scores_{timestamp}.json')
    scores = get_all_scores()
    with open(backup_file, 'w', encoding='utf-8') as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)
    # 保留最近 50 个备份
    backups = sorted([f for f in os.listdir(BACKUP_DIR) if f.startswith('scores_')])
    while len(backups) > 50:
        old = os.path.join(BACKUP_DIR, backups.pop(0))
        try:
            os.remove(old)
        except:
            pass


class ScoreHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP 请求处理器"""

    def __init__(self, *args, **kwargs):
        # 设置网站根目录
        super().__init__(*args, directory=BASE_DIR, **kwargs)

    def do_GET(self):
        """处理 GET 请求"""
        if self.path.startswith('/api/scores'):
            self.handle_get_scores()
        else:
            super().do_GET()

    def do_POST(self):
        """处理 POST 请求"""
        if self.path == '/api/scores':
            self.handle_save_score()
        else:
            self.send_error(404, 'Not Found')

    def handle_get_scores(self):
        """返回所有打分数据"""
        scores = get_all_scores()
        data = {
            'scores': scores,
            'updated': datetime.now().isoformat(),
            'count': len(scores),
            'source': 'database'
        }
        self.send_json(data)

    def handle_save_score(self):
        """保存打分数据"""
        content_length = int(self.headers.get('Content-Length', 0))
        body = self.rfile.read(content_length).decode('utf-8')
        try:
            data = json.loads(body)
            code = data.get('code', '').upper().strip()
            fundamental = int(data.get('fundamental', 0))
            price = int(data.get('price', 0))

            if not code or len(code) > 10:
                self.send_error(400, 'Invalid stock code')
                return

            updated = save_score(code, fundamental, price)
            export_to_json()  # 同步到 JSON 文件
            backup_scores()   # 自动备份

            self.send_json({
                'success': True,
                'code': code,
                'fundamental': fundamental,
                'price': price,
                'updated': updated
            })
        except Exception as e:
            self.send_json({'success': False, 'error': str(e)}, status=500)

    def send_json(self, data, status=200):
        """发送 JSON 响应"""
        body = json.dumps(data, ensure_ascii=False).encode('utf-8')
        self.send_response(status)
        self.send_header('Content-Type', 'application/json; charset=utf-8')
        self.send_header('Content-Length', len(body))
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
        self.wfile.write(body)

    def do_OPTIONS(self):
        """处理 CORS 预检请求"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def log_message(self, format, *args):
        """简化日志输出"""
        msg = format % args
        if '/api/' in msg or 'GET /' == msg[:5]:
            print(f'[{datetime.now().strftime("%H:%M:%S")}] {msg}')


def main():
    init_db()

    # 启动时导出一次 JSON
    export_to_json()

    port = 8000
    print('=' * 60)
    print('  美股价值投资分析网站 - 打分数据服务器')
    print('=' * 60)
    print(f'  数据库: {DB_PATH}')
    print(f'  JSON 文件: {JSON_PATH}')
    print(f'  备份目录: {BACKUP_DIR}')
    print(f'  访问地址: http://localhost:{port}')
    print(f'  打分数据条数: {len(get_all_scores())}')
    print('=' * 60)
    print('  按 Ctrl+C 停止服务器')
    print('=' * 60)

    server = http.server.HTTPServer(('127.0.0.1', port), ScoreHandler)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n服务器已停止')
        server.server_close()


if __name__ == '__main__':
    main()
