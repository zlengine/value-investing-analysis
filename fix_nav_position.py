"""Fix pages where top-nav-bar was inserted between </head> and <body>.
Move it to after <body> tag."""
import glob
import re

BASE_DIR = r'c:\Users\Admin\Documents\trae_projects\value'
files = glob.glob(BASE_DIR + r'\*.html')

fixed = 0
for filepath in files:
    filename = filepath.split('\\')[-1]
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()

    # Check if top-nav-bar is between </head> and <body>
    # Pattern: </head>\n    <div class="top-nav-bar">...</div>\n<body>
    pattern = re.compile(
        r'(</head>\s*\n)\s*<div class="top-nav-bar">.*?</div>\s*\n(<body[^>]*>)',
        re.MULTILINE | re.DOTALL
    )

    match = pattern.search(content)
    if match:
        # Extract the top-nav-bar HTML
        nav_bar_match = re.search(r'(<div class="top-nav-bar">.*?</div>)', content, re.DOTALL)
        if nav_bar_match:
            nav_bar_html = nav_bar_match.group(1)
            # Remove the top-nav-bar from between </head> and <body>
            content = pattern.sub(r'\1\2', content)
            # Insert it after <body>
            content = content.replace('<body>', '<body>\n    ' + nav_bar_html, 1) if '<body>' in content else content
            # Handle <body ...> with attributes
            content = re.sub(r'(<body[^>]*>)', r'\1\n    ' + nav_bar_html, content, count=1) if '<body>' not in content else content

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f'  FIXED: {filename}')
            fixed += 1

print(f'\nDone! Fixed: {fixed}')
