"""检查模式3处理的页面是否有 scores_client.js 引用位置问题"""
import os

files = ['atmu.html','bah.html','blbd.html','chh.html','ctas.html',
         'ftdr.html','idxx.html','it.html','lii.html','rol.html','zts.html']

for f in files:
    filepath = os.path.join(os.path.dirname(os.path.abspath(__file__)), f)
    if not os.path.exists(filepath):
        continue
    with open(filepath, 'r', encoding='utf-8') as fp:
        content = fp.read()

    # 查找 scores_client.js 引用
    ref_pos = content.find('<script src="scores_client.js"></script>')
    if ref_pos == -1:
        print(f'{f}: NO REF')
        continue

    # 检查引用前后的上下文
    before = content[max(0, ref_pos-50):ref_pos]
    after = content[ref_pos:ref_pos+80]

    # 检查是否在 <script> 标签内部（前面没有 </script>）
    last_close_script = content.rfind('</script>', 0, ref_pos)
    last_open_script = content.rfind('<script>', 0, ref_pos)

    if last_open_script > last_close_script:
        print(f'{f}: PROBLEM - ref is inside <script> tag')
        print(f'  before: ...{before[-30:]}')
        print(f'  after: {after[:50]}...')
    else:
        print(f'{f}: OK')
