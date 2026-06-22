"""Fix shangpin_*.html files: add inline CSS for top-nav-bar and adjust fixed-topbar position."""
import glob

BASE_DIR = r'c:\Users\Admin\Documents\trae_projects\value'
shangpin_files = glob.glob(BASE_DIR + r'\shangpin_*.html')

INLINE_STYLE = '''<style>
.top-nav-bar { position: fixed; top: 0; left: 0; right: 0; height: 44px; background: #2c3e50; display: flex; align-items: center; justify-content: flex-end; padding: 0 20px; z-index: 9999; box-shadow: 0 2px 8px rgba(0,0,0,0.15); gap: 8px; }
.top-nav-link { color: white; padding: 6px 16px; border-radius: 16px; text-decoration: none; font-size: 13px; transition: background 0.2s; white-space: nowrap; }
.fixed-topbar { top: 44px !important; z-index: 9998 !important; }
body { padding-top: 104px !important; }
</style>
</head>'''

for filepath in shangpin_files:
    filename = filepath.split('\\')[-1]
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    if '.top-nav-bar {' in content:
        print(f'  SKIP (already has CSS): {filename}')
        continue

    # Add inline style before </head>
    if '</head>' in content:
        content = content.replace('</head>', INLINE_STYLE, 1)
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f'  UPDATED: {filename}')
    else:
        print(f'  FAILED (no </head>): {filename}')

print('\nDone!')
