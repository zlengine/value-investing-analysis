"""
Batch add universal navigation links to all company pages' topbar-left section.
Adds: 财务分析, 更新日志, 股票打分 links after the stock code span.
Also adds the .topbar-nav-link CSS class if not present.
"""
import os
import re
import glob

# Directory
BASE_DIR = r'c:\Users\Admin\Documents\trae_projects\value'

# Navigation links HTML to insert after topbarCode span
NAV_LINKS = '''            <a href="financial_analysis.html" class="topbar-nav-link" style="background:#2e7d32;" onmouseover="this.style.background='#43a047'" onmouseout="this.style.background='#2e7d32'">📖 财务分析</a>
            <a href="changelog.html" class="topbar-nav-link" style="background:#856404;" onmouseover="this.style.background='#a0762a'" onmouseout="this.style.background='#856404'">📋 更新日志</a>
            <a href="scorer.html" class="topbar-nav-link" style="background:#1a5276;" onmouseover="this.style.background='#2e86c1'" onmouseout="this.style.background='#1a5276'">📊 股票打分</a>'''

# CSS to add
NAV_CSS = '        .topbar-nav-link { color: white; padding: 4px 12px; border-radius: 14px; text-decoration: none; font-size: 12px; transition: background 0.2s; white-space: nowrap; }\n        .topbar-nav-link:hover { text-decoration: none; }\n'

# Skip non-company pages
SKIP_FILES = {'index.html', 'scorer.html', 'changelog.html', 'financial_analysis.html',
              'main_analysis.html', 'himalaya.html', 'duan.html', 'buffett.html', 'shangpin_index.html'}

def process_file(filepath):
    filename = os.path.basename(filepath)
    if filename in SKIP_FILES:
        return False

    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Skip if already has nav links
    if 'topbar-nav-link' in content:
        print(f'  SKIP (already has nav links): {filename}')
        return False

    # Skip if no fixed-topbar
    if 'fixed-topbar' not in content and 'fixedTopbar' not in content:
        print(f'  SKIP (no topbar): {filename}')
        return False

    modified = False

    # Pattern 1: topbarCode span followed by closing div (standard structure)
    # Match: <span ... id="topbarCode">XXX</span>\n        </div>
    pattern1 = r'(<span\s+style="font-size:14px;font-weight:700;"\s+id="topbarCode">[^<]+</span>)\s*\n(\s*</div>\s*<!--\s*topbar-left\s*-->)?'
    # Simpler: find the topbarCode span line and add nav links after it
    lines = content.split('\n')
    new_lines = []
    found_topbar_code = False

    for i, line in enumerate(lines):
        new_lines.append(line)
        if 'id="topbarCode"' in line and 'topbar-left' in '\n'.join(lines[max(0,i-5):i]):
            # Found the topbarCode line within topbar-left
            found_topbar_code = True
            # Add nav links after this line
            new_lines.append(NAV_LINKS)
            modified = True

    if not found_topbar_code:
        print(f'  SKIP (topbarCode not found in topbar-left): {filename}')
        return False

    content = '\n'.join(new_lines)

    # Add CSS if not already present
    if '.topbar-nav-link' not in content:
        # Find </style> and insert before it
        content = content.replace('    </style>', NAV_CSS + '    </style>', 1)
        modified = True

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
        if process_file(filepath):
            updated += 1
        else:
            skipped += 1

    print(f'\nDone! Updated: {updated}, Skipped: {skipped}')

if __name__ == '__main__':
    main()
