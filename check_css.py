import glob
BASE_DIR = r'c:\Users\Admin\Documents\trae_projects\value'
files = glob.glob(BASE_DIR + r'\*.html')
missing = []
for f in files:
    content = open(f, encoding='utf-8').read()
    if 'class="top-nav-bar"' in content and '.top-nav-bar {' not in content and '.top-nav-bar{' not in content:
        missing.append(f.split('\\')[-1])
for m in missing:
    print(m)
print(f'\nTotal missing CSS: {len(missing)}')
