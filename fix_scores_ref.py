"""
修复所有公司页面：添加缺失的 scores_client.js 引用
- 检查每个页面是否使用了 ScoresDB 但缺少 scores_client.js 引用
- 在 ScoresDB 使用前的 <script> 标签前添加 <script src="scores_client.js"></script>
"""
import os
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

CLIENT_REF = '<script src="scores_client.js"></script>'


def process_file(filepath):
    """处理单个 HTML 文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # 如果已经有 scores_client.js 引用，跳过
    if CLIENT_REF in content:
        return False

    # 检查是否使用了 ScoresDB
    if 'ScoresDB' not in content:
        return False

    # 找到使用 ScoresDB 的 <script> 标签位置
    # 查找特征：var code=document.getElementById('topbarCode')
    marker = "var code=document.getElementById('topbarCode')"
    marker_pos = content.find(marker)
    if marker_pos == -1:
        return False

    # 向前查找最近的 <script> 标签
    script_tag = '<script>'
    script_pos = content.rfind(script_tag, 0, marker_pos)
    if script_pos == -1:
        return False

    # 在 <script> 标签前插入 scores_client.js 引用
    new_content = content[:script_pos] + CLIENT_REF + '\n    ' + content[script_pos:]

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(new_content)
    return True


def main():
    # 获取所有公司页面（排除非公司页面）
    exclude_files = {
        'index.html', 'scorer.html', 'changelog.html',
        'financial_analysis.html', 'server.py', 'scores_client.js',
        'scores_data.json', 'backup.py', 'update_topbar_scripts.py',
        'fix_scores_ref.py', 'main_analysis.html', 'buffett.html',
        'himalaya.html', 'duan.html'
    }

    html_files = glob.glob(os.path.join(BASE_DIR, '*.html'))
    html_files = [f for f in html_files if os.path.basename(f) not in exclude_files]
    html_files = [f for f in html_files if not os.path.basename(f).startswith('shangpin_')]

    updated = 0
    skipped = 0
    failed = []

    for filepath in html_files:
        try:
            if process_file(filepath):
                updated += 1
                print(f'[OK] {os.path.basename(filepath)}')
            else:
                skipped += 1
                print(f'[SKIP] {os.path.basename(filepath)}')
        except Exception as e:
            failed.append((os.path.basename(filepath), str(e)))
            print(f'[FAIL] {os.path.basename(filepath)}: {e}')

    print(f'\n=== Summary ===')
    print(f'Updated: {updated}')
    print(f'Skipped: {skipped}')
    print(f'Failed: {len(failed)}')
    if failed:
        print('Failed files:')
        for f, e in failed:
            print(f'  - {f}: {e}')


if __name__ == '__main__':
    main()
