"""
Batch restructure navigation on all company pages:
1. Remove the 3 nav links (财务分析/更新日志/股票打分) from topbar-left
2. Add a new top-nav-bar above fixed-topbar with the 3 nav links
3. Change fixed-topbar top from 0 to 44px, z-index from 9999 to 9998
4. Change body padding-top from 60px to 104px
5. Replace .topbar-nav-link CSS with .top-nav-bar/.top-nav-link CSS
"""
import os
import re
import glob

BASE_DIR = r'c:\Users\Admin\Documents\trae_projects\value'

SKIP_FILES = {'index.html', 'scorer.html', 'changelog.html', 'financial_analysis.html',
              'main_analysis.html', 'himalaya.html', 'duan.html', 'buffett.html', 'shangpin_index.html'}

# The 3 nav links block to remove from topbar-left (with leading whitespace variations)
NAV_LINKS_PATTERN = re.compile(
    r'\s*<a href="financial_analysis\.html" class="topbar-nav-link"[^>]*>📖 财务分析</a>\s*'
    r'<a href="changelog\.html" class="topbar-nav-link"[^>]*>📋 更新日志</a>\s*'
    r'<a href="scorer\.html" class="topbar-nav-link"[^>]*>📊 股票打分</a>',
    re.MULTILINE
)

# New top-nav-bar HTML to insert before fixed-topbar
TOP_NAV_BAR = '''    <div class="top-nav-bar">
        <a href="scorer.html" class="top-nav-link" style="background:#1a5276;" onmouseover="this.style.background='#2e86c1'" onmouseout="this.style.background='#1a5276'">📊 股票打分</a>
        <a href="financial_analysis.html" class="top-nav-link" style="background:#2e7d32;" onmouseover="this.style.background='#43a047'" onmouseout="this.style.background='#2e7d32'">📖 财务分析</a>
        <a href="changelog.html" class="top-nav-link" style="background:#856404;" onmouseover="this.style.background='#a0762a'" onmouseout="this.style.background='#856404'">📋 更新日志</a>
    </div>
'''

def process_file(filepath):
    filename = os.path.basename(filepath)
    if filename in SKIP_FILES:
        return False

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip if no fixed-topbar
    if 'fixed-topbar' not in content and 'fixedTopbar' not in content:
        print(f'  SKIP (no topbar): {filename}')
        return False

    # Skip if already has top-nav-bar (already processed)
    if 'class="top-nav-bar"' in content:
        print(f'  SKIP (already has top-nav-bar): {filename}')
        return False

    modified = False

    # Step 1: Remove the 3 nav links from topbar-left
    new_content, count = NAV_LINKS_PATTERN.subn('', content)
    if count > 0:
        content = new_content
        modified = True
        print(f'  - Removed nav links from topbar-left')
    else:
        print(f'  - No nav links found in topbar-left (may not have been added)')

    # Step 2: Replace .topbar-nav-link CSS with .top-nav-bar/.top-nav-link CSS
    old_css_pattern = re.compile(
        r'\.topbar-nav-link\s*\{[^}]*\}\s*\n\s*\.topbar-nav-link:hover\s*\{[^}]*\}\s*\n'
    )
    new_css = ('        .top-nav-bar { position: fixed; top: 0; left: 0; right: 0; height: 44px; '
               'background: #2c3e50; display: flex; align-items: center; justify-content: flex-end; '
               'padding: 0 20px; z-index: 9999; box-shadow: 0 2px 8px rgba(0,0,0,0.15); gap: 8px; }\n'
               '        .top-nav-link { color: white; padding: 6px 16px; border-radius: 16px; '
               'text-decoration: none; font-size: 13px; transition: background 0.2s; white-space: nowrap; }\n')
    new_content, count = old_css_pattern.subn(new_css, content)
    if count > 0:
        content = new_content
        modified = True
        print(f'  - Replaced topbar-nav-link CSS with top-nav-bar CSS')
    else:
        # If no topbar-nav-link CSS found, add top-nav-bar CSS before </style>
        if '.top-nav-bar' not in content:
            content = content.replace('    </style>', new_css + '    </style>', 1)
            modified = True
            print(f'  - Added top-nav-bar CSS (no old topbar-nav-link CSS found)')

    # Step 3: Change fixed-topbar top:0 to top:44px and z-index 9999 to 9998
    # Handle both "top: 0;" and "top:0;" variations
    content_new = re.sub(
        r'(\.fixed-topbar\s*\{[^}]*?top:\s*)0(\s*;)',
        r'\g<1>44px\g<2>',
        content
    )
    if content_new != content:
        content = content_new
        modified = True
        print(f'  - Changed fixed-topbar top to 44px')

    content_new = re.sub(
        r'(\.fixed-topbar\s*\{[^}]*?z-index:\s*)9999(\s*;)',
        r'\g<1>9998\g<2>',
        content
    )
    if content_new != content:
        content = content_new
        modified = True
        print(f'  - Changed fixed-topbar z-index to 9998')

    # Step 4: Change body padding-top from 60px to 104px
    content_new = re.sub(
        r'body\s*\{\s*padding-top:\s*60px\s*!important;\s*\}',
        'body { padding-top: 104px !important; }',
        content
    )
    if content_new != content:
        content = content_new
        modified = True
        print(f'  - Changed body padding-top to 104px')

    # Step 5: Insert top-nav-bar before fixed-topbar div
    # Find the <body> tag followed by fixed-topbar
    body_topbar_pattern = re.compile(
        r'(<body[^>]*>\s*\n)(\s*<div class="fixed-topbar")',
        re.MULTILINE
    )
    new_content, count = body_topbar_pattern.subn(
        lambda m: m.group(1) + TOP_NAV_BAR + m.group(2),
        content
    )
    if count > 0:
        content = new_content
        modified = True
        print(f'  - Inserted top-nav-bar before fixed-topbar')
    else:
        print(f'  - WARNING: Could not find <body> followed by fixed-topbar')

    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'  UPDATED: {filename}')
        return True
    else:
        print(f'  NO CHANGE: {filename}')
        return False

def main():
    html_files = glob.glob(os.path.join(BASE_DIR, '*.html'))
    updated = 0
    skipped = 0

    for filepath in sorted(html_files):
        filename = os.path.basename(filepath)
        if filename == 'chh.html':
            print(f'  SKIP (prototype already done): {filename}')
            skipped += 1
            continue
        if process_file(filepath):
            updated += 1
        else:
            skipped += 1

    print(f'\nDone! Updated: {updated}, Skipped: {skipped}')

if __name__ == '__main__':
    main()
