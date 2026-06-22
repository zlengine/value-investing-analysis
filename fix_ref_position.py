"""修复 scores_client.js 引用位置问题（被插入到 <script> 标签内部）"""
import os
import re

files = ['atmu.html','bah.html','blbd.html','chh.html','ctas.html',
         'ftdr.html','idxx.html','it.html','lii.html','rol.html']

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

for f in files:
    filepath = os.path.join(BASE_DIR, f)
    if not os.path.exists(filepath):
        continue
    with open(filepath, 'r', encoding='utf-8') as fp:
        content = fp.read()

    # 查找错误的 scores_client.js 引用位置
    # 模式：在 <script> 标签内部，前面是代码（不是 </script>）
    ref_tag = '<script src="scores_client.js"></script>'

    # 查找所有 ref_tag 的位置
    pos = 0
    fixed = False
    while True:
        ref_pos = content.find(ref_tag, pos)
        if ref_pos == -1:
            break

        # 检查前面是否有 </script>
        last_close_script = content.rfind('</script>', 0, ref_pos)
        last_open_script = content.rfind('<script>', 0, ref_pos)

        if last_open_script > last_close_script:
            # 引用在 <script> 标签内部，需要修复
            # 在 ref_tag 前添加 </script>
            content = content[:ref_pos] + '</script>\n    ' + ref_tag + content[ref_pos + len(ref_tag):]
            fixed = True
            print(f'{f}: FIXED')
            break
        pos = ref_pos + len(ref_tag)

    if fixed:
        with open(filepath, 'w', encoding='utf-8') as fp:
            fp.write(content)
    else:
        print(f'{f}: NO FIX NEEDED')
