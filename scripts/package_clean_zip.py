import os
import zipfile

source_dir = r"c:\Users\91866\Desktop\automated_interview_analyzer"
dest_zip_desktop = r"c:\Users\91866\Desktop\automated_interview_analyzer_final_all_fixes.zip"
dest_zip_downloads = r"c:\Users\91866\Downloads\automated_interview_analyzer_final_all_fixes.zip"

EXCLUDE_DIRS = {'.git', '__pycache__', '.pytest_cache', 'venv', '.venv', 'env', '.idea', '.vscode'}
EXCLUDE_FILES = {'secrets.toml', '.DS_Store', 'interview_history.json'}
EXCLUDE_EXTS = {'.pyc', '.pyo'}

def make_zip(out_path):
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    count = 0
    with zipfile.ZipFile(out_path, 'w', zipfile.ZIP_DEFLATED) as zf:
        for root, dirs, files in os.walk(source_dir):
            dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS and not d.startswith('.')]
            for f in files:
                if f in EXCLUDE_FILES or any(f.endswith(ext) for ext in EXCLUDE_EXTS):
                    continue
                # Also exclude any generated zip files themselves if inside root
                if f.endswith('.zip'):
                    continue
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, source_dir)
                if 'secrets.toml' in rel_path.lower():
                    continue
                zf.write(full_path, rel_path)
                count += 1
    print(f"Wrote {count} files to {out_path} ({os.path.getsize(out_path)/1024:.1f} KB)")

if __name__ == "__main__":
    make_zip(dest_zip_desktop)
    make_zip(dest_zip_downloads)
