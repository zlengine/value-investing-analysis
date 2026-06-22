"""
批量更新所有公司页面的 topbar 打分脚本
- 替换 localStorage 为 ScoresDB（数据库同步）
- 添加 scores_client.js 引用
"""
import os
import re
import glob

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# 新的 topbar 打分脚本（使用 ScoresDB）
NEW_TOPBAR_SCRIPT = '''<script src="scores_client.js"></script>
    <script>
    (function(){
        var code=document.getElementById('topbarCode').textContent.trim();
        function starsHTML(val){var h='';for(var i=1;i<=5;i++){h+='<span class="'+(i<=val?'on':'off')+'">\u2605</span>';}return h;}
        function valClass(v){return v>=5?'s5':v>=4?'s4':v>=3?'s3':v>=2?'s2':'s1';}
        function renderDisplay(f,p){
            document.getElementById('topbarFVal').textContent=f>0?f:'-';
            document.getElementById('topbarFVal').className='topbar-score-val'+(f>0?' '+valClass(f):'');
            document.getElementById('topbarFStars').innerHTML=starsHTML(f);
            document.getElementById('topbarPVal').textContent=p>0?p:'-';
            document.getElementById('topbarPVal').className='topbar-score-val'+(p>0?' '+valClass(p):'');
            document.getElementById('topbarPStars').innerHTML=starsHTML(p);
        }
        function renderFromDB(){
            ScoresDB.getAll(function(scores){
                var sc=scores[code]||{};
                renderDisplay(sc.fundamental||0, sc.price||0);
            });
        }
        window.topbarEdit=function(){
            ScoresDB.getAll(function(scores){
                var sc=scores[code]||{};
                document.getElementById('topbarFSel').value=sc.fundamental||0;
                document.getElementById('topbarPSel').value=sc.price||0;
                document.getElementById('topbarFSel').style.display='';
                document.getElementById('topbarPSel').style.display='';
                document.getElementById('topbarEditBtn').style.display='none';
                document.getElementById('topbarSaveBtn').style.display='';
                document.getElementById('topbarCancelBtn').style.display='';
                document.getElementById('topbarFVal').style.display='none';
                document.getElementById('topbarPVal').style.display='none';
                document.getElementById('topbarFStars').style.display='none';
                document.getElementById('topbarPStars').style.display='none';
            });
        };
        window.topbarSave=function(){
            var f=parseInt(document.getElementById('topbarFSel').value);
            var p=parseInt(document.getElementById('topbarPSel').value);
            ScoresDB.save(code, f, p, function(result){
                if(result.success){
                    topbarCancel();
                    renderFromDB();
                } else {
                    alert('保存失败：'+result.error+'\n\n请确保已启动本地服务器：python server.py');
                    topbarCancel();
                }
            });
        };
        window.topbarCancel=function(){
            document.getElementById('topbarFSel').style.display='none';
            document.getElementById('topbarPSel').style.display='none';
            document.getElementById('topbarEditBtn').style.display='';
            document.getElementById('topbarSaveBtn').style.display='none';
            document.getElementById('topbarCancelBtn').style.display='none';
            document.getElementById('topbarFVal').style.display='';
            document.getElementById('topbarPVal').style.display='';
            document.getElementById('topbarFStars').style.display='';
            document.getElementById('topbarPStars').style.display='';
        };
        // 初始加载
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', renderFromDB);
        } else {
            renderFromDB();
        }
        // 定期刷新（同步其他页面的修改）
        setInterval(renderFromDB, 5000);
    })();
    </script>'''

# 匹配旧的 topbar 打分脚本（从 <script> 开始到 </script> 结束）
# 旧脚本特征：包含 SCORE_KEY='stock_scores_v1'（兼容不同缩进）
OLD_SCRIPT_PATTERN = re.compile(
    r'<script>\s*\(function\(\)\{\s*var SCORE_KEY=\'stock_scores_v1\';.*?\}\)\(\);\s*</script>',
    re.DOTALL | re.IGNORECASE
)

# 备用：匹配以更多空格开头的版本
OLD_SCRIPT_PATTERN2 = re.compile(
    r'<script>\s+\(function\(\)\{\s+var SCORE_KEY=\'stock_scores_v1\';.*?\}\)\(\);\s+</script>',
    re.DOTALL
)

# 检查是否已有 scores_client.js 引用
HAS_CLIENT_REF = re.compile(r'<script src="scores_client\.js"></script>')


def process_file(filepath):
    """处理单个 HTML 文件"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    original = content
    changed = False

    # 如果已经有 scores_client.js 引用，先移除（避免重复）
    if HAS_CLIENT_REF.search(content):
        content = HAS_CLIENT_REF.sub('', content)
        changed = True

    # 替换旧的 topbar 脚本（主模式 - 独立 script 标签）
    new_content, n = OLD_SCRIPT_PATTERN.subn(NEW_TOPBAR_SCRIPT, content)
    if n > 0:
        content = new_content
        changed = True
    else:
        # 备用模式（多空格缩进）
        new_content, n = OLD_SCRIPT_PATTERN2.subn(NEW_TOPBAR_SCRIPT, content)
        if n > 0:
            content = new_content
            changed = True

    # 模式3：嵌入式 topbar 脚本（在已有 script 块内，无独立 <script> 标签）
    if not changed:
        embedded_pattern = re.compile(
            r'\s*//\s*Topbar scoring logic.*?\(function\(\)\{.*?var SCORE_KEY=\'stock_scores_v1\';.*?\}\)\(\);',
            re.DOTALL
        )
        new_content, n = embedded_pattern.subn('\n\n    ' + NEW_TOPBAR_SCRIPT, content)
        if n > 0:
            content = new_content
            changed = True

    if changed:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False


def main():
    # 获取所有公司页面（排除 index.html, scorer.html 等）
    exclude_files = {
        'index.html', 'scorer.html', 'changelog.html',
        'financial_analysis.html', 'server.py', 'scores_client.js',
        'scores_data.json', 'backup.py'
    }

    html_files = glob.glob(os.path.join(BASE_DIR, '*.html'))
    html_files = [f for f in html_files if os.path.basename(f) not in exclude_files]

    # 排除 shangpin_*.html
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
                print(f'[SKIP] {os.path.basename(filepath)} (no old script found)')
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
