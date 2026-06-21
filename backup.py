#!/usr/bin/env python3
"""
网站备份与恢复工具
用法：
  python backup.py backup          -- 创建备份快照
  python backup.py list            -- 列出所有备份
  python backup.py restore <id>    -- 恢复指定备份
  python backup.py verify          -- 验证index.html中所有链接都有对应文件
  python backup.py diff <id>       -- 对比当前文件与备份的差异
"""

import os
import sys
import shutil
import json
import glob
from datetime import datetime

PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKUP_DIR = os.path.join(PROJECT_DIR, 'backups')
MANIFEST_FILE = os.path.join(BACKUP_DIR, 'manifest.json')

# 需要备份的文件扩展名
BACKUP_EXTENSIONS = {'.html', '.css', '.js', '.json'}
# 需要排除的文件
EXCLUDE_FILES = {'changelog.html'}  # changelog本身不需要备份，它是记录


def ensure_backup_dir():
    os.makedirs(BACKUP_DIR, exist_ok=True)


def get_html_files():
    """获取项目中所有html文件"""
    files = []
    for f in os.listdir(PROJECT_DIR):
        if f.endswith('.html') and f not in EXCLUDE_FILES:
            files.append(f)
    return sorted(files)


def get_all_backup_files():
    """获取所有需要备份的文件"""
    files = []
    for f in os.listdir(PROJECT_DIR):
        ext = os.path.splitext(f)[1].lower()
        if ext in BACKUP_EXTENSIONS and f not in EXCLUDE_FILES:
            files.append(f)
    return sorted(files)


def create_backup(description=""):
    """创建备份快照"""
    ensure_backup_dir()
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_path = os.path.join(BACKUP_DIR, timestamp)

    os.makedirs(backup_path, exist_ok=True)

    files = get_all_backup_files()
    file_info = {}

    for f in files:
        src = os.path.join(PROJECT_DIR, f)
        dst = os.path.join(backup_path, f)
        shutil.copy2(src, dst)
        size = os.path.getsize(src)
        file_info[f] = {'size': size}

    # 保存备份元数据
    metadata = {
        'timestamp': timestamp,
        'created_at': datetime.now().isoformat(),
        'description': description,
        'file_count': len(files),
        'files': file_info
    }

    with open(os.path.join(backup_path, '_metadata.json'), 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    # 更新manifest
    update_manifest(timestamp, metadata)

    print(f"[OK] 备份创建成功: {timestamp}")
    print(f"     文件数: {len(files)}")
    print(f"     路径: {backup_path}")
    return timestamp


def update_manifest(timestamp, metadata):
    """更新备份清单"""
    ensure_backup_dir()
    manifest = load_manifest()
    manifest['backups'].insert(0, {
        'timestamp': timestamp,
        'created_at': metadata['created_at'],
        'description': metadata['description'],
        'file_count': metadata['file_count']
    })
    # 最多保留50个备份记录
    manifest['backups'] = manifest['backups'][:50]

    with open(MANIFEST_FILE, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)


def load_manifest():
    """加载备份清单"""
    if os.path.exists(MANIFEST_FILE):
        with open(MANIFEST_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {'backups': []}


def list_backups():
    """列出所有备份"""
    manifest = load_manifest()
    if not manifest['backups']:
        print("[INFO] 没有找到备份记录")
        return

    print(f"{'序号':<4} {'备份ID':<20} {'时间':<22} {'文件数':<8} {'描述'}")
    print("-" * 80)
    for i, b in enumerate(manifest['backups'], 1):
        desc = b.get('description', '')
        print(f"{i:<4} {b['timestamp']:<20} {b['created_at']:<22} {b['file_count']:<8} {desc}")


def restore_backup(backup_id):
    """恢复指定备份"""
    backup_path = os.path.join(BACKUP_DIR, backup_id)
    if not os.path.exists(backup_path):
        print(f"[ERROR] 备份不存在: {backup_id}")
        return False

    # 先创建当前状态的备份
    print("[INFO] 恢复前先备份当前状态...")
    pre_restore_id = create_backup(f"恢复前自动备份 (即将恢复 {backup_id})")

    # 恢复文件
    metadata_path = os.path.join(backup_path, '_metadata.json')
    restored_count = 0

    for f in os.listdir(backup_path):
        if f.startswith('_'):
            continue
        src = os.path.join(backup_path, f)
        dst = os.path.join(PROJECT_DIR, f)
        shutil.copy2(src, dst)
        restored_count += 1
        print(f"  恢复: {f}")

    print(f"\n[OK] 恢复完成! 恢复了 {restored_count} 个文件")
    print(f"     恢复前备份ID: {pre_restore_id}")
    return True


def verify_links():
    """验证index.html中所有链接都有对应文件"""
    index_path = os.path.join(PROJECT_DIR, 'index.html')
    if not os.path.exists(index_path):
        print("[ERROR] index.html 不存在")
        return

    with open(index_path, 'r', encoding='utf-8') as f:
        content = f.read()

    import re
    links = re.findall(r'href="([a-z][a-z0-9]*\.html)"', content)
    links = sorted(set(links))

    missing = []
    existing = []
    for link in links:
        filepath = os.path.join(PROJECT_DIR, link)
        if os.path.exists(filepath):
            existing.append(link)
        else:
            missing.append(link)

    print(f"[验证结果] index.html中共 {len(links)} 个链接")
    print(f"  存在对应文件: {len(existing)} 个")
    print(f"  缺失文件: {len(missing)} 个")

    if missing:
        print("\n[缺失文件列表]:")
        for m in missing:
            print(f"  [X] {m}")
        return False
    else:
        print("\n[OK] 所有链接都有对应文件!")
        return True


def diff_backup(backup_id):
    """对比当前文件与备份的差异"""
    backup_path = os.path.join(BACKUP_DIR, backup_id)
    if not os.path.exists(backup_path):
        print(f"[ERROR] 备份不存在: {backup_id}")
        return

    # 获取备份中的文件列表
    backup_files = set()
    for f in os.listdir(backup_path):
        if not f.startswith('_'):
            backup_files.add(f)

    # 获取当前文件列表
    current_files = set(get_all_backup_files())

    added = current_files - backup_files
    deleted = backup_files - current_files
    common = current_files & backup_files

    modified = []
    for f in common:
        src = os.path.join(PROJECT_DIR, f)
        dst = os.path.join(backup_path, f)
        if os.path.getsize(src) != os.path.getsize(dst):
            modified.append(f)

    print(f"对比备份: {backup_id}")
    print(f"  新增文件 ({len(added)}):")
    for f in sorted(added):
        print(f"    + {f}")
    print(f"  删除文件 ({len(deleted)}):")
    for f in sorted(deleted):
        print(f"    - {f}")
    print(f"  修改文件 ({len(modified)}):")
    for f in sorted(modified):
        print(f"    ~ {f}")
    print(f"  未变化: {len(common) - len(modified)}")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == 'backup':
        desc = ' '.join(sys.argv[2:]) if len(sys.argv) > 2 else ''
        create_backup(desc)
    elif command == 'list':
        list_backups()
    elif command == 'restore':
        if len(sys.argv) < 3:
            print("[ERROR] 请指定备份ID，例如: python backup.py restore 20260621_100000")
            sys.exit(1)
        restore_backup(sys.argv[2])
    elif command == 'verify':
        verify_links()
    elif command == 'diff':
        if len(sys.argv) < 3:
            print("[ERROR] 请指定备份ID，例如: python backup.py diff 20260621_100000")
            sys.exit(1)
        diff_backup(sys.argv[2])
    else:
        print(f"[ERROR] 未知命令: {command}")
        print(__doc__)
