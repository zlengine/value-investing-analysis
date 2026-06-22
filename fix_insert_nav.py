"""
Fix script: Insert top-nav-bar before fixed-topbar div for pages that failed.
Handles various structures:
1. <body>\n    <div class="fixed-topbar" - standard (already handled)
2. <body>    <div class="fixed-topbar" - same line
3. <div style="...">    <div class="fixed-topbar" - wrapped
4. Any other case where fixed-topbar exists but top-nav-bar doesn't
"""
import os
import re
import glob

BASE_DIR = r'c:\Users\Admin\Documents\trae_projects\value'

SKIP_FILES = {'index.html', 'scorer.html', 'changelog.html', 'financial_analysis.html',
              'main_analysis.html', 'himalaya.html', 'duan.html', 'buffett.html', 'shangpin_index.html'}

TOP_NAV_BAR = '    <div class="top-nav-bar">\n        <a href="scorer.html" class="top-nav-link" style="background:#1a5276;" onmouseover="this.style.background=\'#2e86c1\'" onmouseout="this.style.background=\'#1a5276\'">📊 股票打分</a>\n        <a href="financial_analysis.html" class="top-nav-link" style="background:#2e7d32;" onmouseover="this.style.background=\'#43a047\'" onmouseout="this.style.background=\'#2e7d32\'">📖 财务分析</a>\n        <a href="changelog.html" class="top-nav-link" style="background:#856404;" onmouseover="this.style.background=\'#a0762a\'" onmouseout="this.style.background=\'#856404\'">📋 更新日志</a>\n    </div>\n'

def process_file(filepath):
    filename = os.path.basename(filepath)
    if filename in SKIP_FILES:
        return False

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip if already has top-nav-bar
    if 'class="top-nav-bar"' in content:
        print(f'  SKIP (already has top-nav-bar): {filename}')
        return False

    # Skip if no fixed-topbar div
    if 'class="fixed-topbar"' not in content:
        print(f'  SKIP (no fixed-topbar div): {filename}')
        return False

    # Strategy: find the line containing <div class="fixed-topbar" and insert top-nav-bar before it
    lines = content.split('\n')
    new_lines = []
    inserted = False

    for i, line in enumerate(lines):
        if '<div class="fixed-topbar"' in line and not inserted:
            # Check if this line has other content before the fixed-topbar div
            idx = line.index('<div class="fixed-topbar"')
            prefix = line[:idx]

            # If there's non-whitespace content before fixed-topbar on the same line,
            # we need to handle it carefully
            if prefix.strip():
                # There's content before (like <body> or <div style="...">)
                # Insert top-nav-bar on a new line before this line
                new_lines.append(TOP_NAV_BAR.rstrip('\n'))
                new_lines.append(line)
            else:
                # The line starts with whitespace then fixed-topbar
                # Insert top-nav-bar before this line
                new_lines.append(TOP_NAV_BAR.rstrip('\n'))
                new_lines.append(line)
            inserted = True
        else:
            new_lines.append(line)

    if inserted:
        content = '\n'.join(new_lines)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'  UPDATED: {filename}')
        return True
    else:
        print(f'  FAILED to insert: {filename}')
        return False

def main():
    html_files = glob.glob(os.path.join(BASE_DIR, '*.html'))
    updated = 0
    skipped = 0

    for filepath in sorted(html_files):
        if process_file(filepath):
            updated += 1
        else:
            skipped += 1

    print(f'\nDone! Updated: {updated}, Skipped: {skipped}')

if __name__ == '__main__':
    main()
