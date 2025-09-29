#!/usr/bin/env python3
import argparse
import hashlib
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

import requests
import yaml

# ---------------------------
# Utilities
# ---------------------------

def sh(cmd: List[str], check: bool = True, capture: bool = True) -> subprocess.CompletedProcess:
    return subprocess.run(
        cmd,
        check=check,
        stdout=(subprocess.PIPE if capture else None),
        stderr=(subprocess.PIPE if capture else None),
        text=True,
    )

def sh_bytes(cmd: List[str], check: bool = True) -> bytes:
    proc = subprocess.run(cmd, check=check, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    return proc.stdout

def supports_branch(remote: str, branch: str) -> bool:
    try:
        sh(['git', 'ls-remote', '--exit-code', remote, f'refs/heads/{branch}'])
        return True
    except subprocess.CalledProcessError:
        return False

def git_fetch():
    sh(['git', 'fetch', '--all', '--tags', '--prune'], check=True, capture=False)

def current_branch() -> str:
    try:
        return sh(['git', 'rev-parse', '--abbrev-ref', 'HEAD']).stdout.strip()
    except subprocess.CalledProcessError:
        return 'HEAD'

def parse_name_status_z(blob: bytes) -> List[Tuple[str, str]]:
    """
    Parse output of: git diff --name-status -z ...
    Returns list of (status, path) where status in {A,M,R,C,...}.
    For R/C, returns the NEW path (second path).
    """
    items = blob.split(b'\x00')
    # strip trailing empty tokens
    items = items[:-1] if items and items[-1] == b'' else items

    out: List[Tuple[str, str]] = []
    i = 0
    while i < len(items):
        status = items[i].decode('utf-8', errors='replace')
        i += 1
        if status.startswith('R') or status.startswith('C'):
            # two paths: old, new
            if i + 1 >= len(items):
                break
            old_path = items[i].decode('utf-8', errors='replace'); i += 1
            new_path = items[i].decode('utf-8', errors='replace'); i += 1
            out.append((status[0], new_path))
        else:
            if i >= len(items):
                break
            path = items[i].decode('utf-8', errors='replace'); i += 1
            out.append((status, path))
    return out

def is_yaml(path: str) -> bool:
    p = path.lower()
    return p.endswith('.yml') or p.endswith('.yaml')

def safe_json_filename(yaml_path: str, out_dir: Path) -> Path:
    # Encode full path to avoid collisions
    h = hashlib.sha1(yaml_path.encode('utf-8', errors='ignore')).hexdigest()[:10]
    base = Path(yaml_path).name
    stem = base.rsplit('.', 1)[0]
    safe = stem.replace(os.sep, '_')
    return out_dir / f"{safe}__{h}.json"

def load_yaml_any(yaml_file_path: Path) -> Any:
    with yaml_file_path.open('r', encoding='utf-8') as f:
        docs = list(yaml.safe_load_all(f))
    if len(docs) == 0:
        return None
    if len(docs) == 1:
        return docs[0]
    return docs  # multi-doc -> list

def json_dump(obj: Any, dest: Path):
    # Handle datetimes or unknown types gracefully
    with dest.open('w', encoding='utf-8') as jf:
        json.dump(obj, jf, indent=2, ensure_ascii=False, default=str)

# ---------------------------
# Core functions
# ---------------------------

def get_changed_yaml_files(
    base_branch: str,
    compare_strategy: str = 'triple-dot',  # 'triple-dot' or 'two-dot'
    include_path: Optional[str] = None,
) -> List[str]:
    """
    Detect YAML files changed relative to base_branch.
    triple-dot: origin/base...HEAD (changes since branch divergence)
    two-dot: origin/base..HEAD (changes on HEAD not in base)
    """
    git_fetch()
    # Build range
    range_arg = f"origin/{base_branch}...HEAD" if compare_strategy == 'triple-dot' else f"origin/{base_branch}..HEAD"

    # Note: use pathspecs after '--' to let git filter, not the shell
    cmd = ['git', 'diff', '--name-status', '-z', range_arg, '--']
    if include_path:
        cmd.append(include_path)
    # Filter YAML at the git layer to avoid extra parsing
    cmd += ['*.yml', '*.yaml']

    try:
        out = sh_bytes(cmd, check=True)
    except subprocess.CalledProcessError as e:
        print(f"❌ Git diff failed: {e}", file=sys.stderr)
        return []

    entries = parse_name_status_z(out)
    changed: List[str] = []
    for status, path in entries:
        if status in ('A', 'M', 'R', 'C') and is_yaml(path):
            changed.append(path)
    return changed

def convert_yaml_to_json(yaml_file_path: str, json_file_path: Path) -> None:
    data = load_yaml_any(Path(yaml_file_path))
    json_dump(data, json_file_path)
    print(f"✅ Converted '{yaml_file_path}' → '{json_file_path}'")

def post_with_retries(
    url: str,
    json_payload_path: Path,
    verify: Optional[str | bool] = True,
    timeout: float = 15.0,
    retries: int = 3,
    backoff: float = 1.5,
    headers: Optional[Dict[str, str]] = None,
) -> Tuple[int, str]:
    headers = headers or {}
    attempt = 0
    last_status = 0
    last_text = ""
    while attempt < retries:
        attempt += 1
        try:
            with json_payload_path.open('r', encoding='utf-8') as f:
                payload = json.load(f)
            print(f"🚀 [Attempt {attempt}/{retries}] POST {url} ({json_payload_path.name})")
            resp = requests.post(url, json=payload, timeout=timeout, verify=verify, headers=headers)
            last_status = resp.status_code
            last_text = resp.text
            if 200 <= resp.status_code < 300:
                print(f"✅ {resp.status_code} {resp.reason}")
                return resp.status_code, resp.text
            else:
                print(f"⚠️  Received {resp.status_code}. Will retry..." if attempt < retries else f"❌ Failed with {resp.status_code}.")
        except requests.exceptions.RequestException as e:
            last_text = str(e)
            print(f"⚠️ Network error: {e}. Retrying..." if attempt < retries else f"❌ Network error: {e}")
        time.sleep(backoff ** attempt)
    return last_status, last_text

def maybe_rebase_onto(base: str) -> bool:
    """
    Optional and **not recommended** in the same step as network ops.
    Returns True if rebase succeeded.
    """
    try:
        git_fetch()
        # Try main, then master if base isn't found
        remote_base = base
        if not supports_branch('origin', base):
            fallback = 'master' if base == 'main' else 'main'
            if supports_branch('origin', fallback):
                print(f"ℹ️  Base branch 'origin/{base}' not found. Falling back to 'origin/{fallback}'.")
                remote_base = fallback

        # Auto-stash to avoid index issues; non-interactive
        sh(['git', '-c', 'rebase.autoStash=true', 'rebase', f'origin/{remote_base}'], check=True, capture=False)
        print("✅ Rebased successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Rebase failed: {e}", file=sys.stderr)
        # Optional: git rebase --abort
        try:
            sh(['git', 'rebase', '--abort'], check=False, capture=False)
        except Exception:
            pass
        return False

# ---------------------------
# CLI & main
# ---------------------------

def main():
    parser = argparse.ArgumentParser(description="Detect changed YAML files, convert to JSON, and POST to an API.")
    parser.add_argument('--api-url', default="https://sapient-duality-469110-d9.el.r.appspot.com/data", help="Destination API URL")
    parser.add_argument('--base-branch', default="dev", help="Base branch to diff against (e.g., dev, main)")
    parser.add_argument('--compare', choices=['triple-dot', 'two-dot'], default='triple-dot', help="Diff strategy")
    parser.add_argument('--include-path', default=None, help="Limit scanning to a subdirectory (e.g., configs/)")
    parser.add_argument('--output-dir', default=None, help="Directory to place generated JSON files (default: temp dir)")
    parser.add_argument('--timeout', type=float, default=15.0, help="HTTP timeout (seconds)")
    parser.add_argument('--retries', type=int, default=3, help="Retry attempts for POST")
    parser.add_argument('--verify', default='true', help="TLS verification: true|false|/path/to/ca-bundle.pem")
    parser.add_argument('--rebase-after', action='store_true', help="Rebase current branch onto origin/<base-branch> after posting (use with caution)")
    parser.add_argument('--dry-run', action='store_true', help="Do not POST; just show what would happen")
    args = parser.parse_args()

    # Resolve verify option
    verify_opt: bool | str
    v = args.verify.strip().lower()
    if v in ('true', '1', 'yes'):
        verify_opt = True
    elif v in ('false', '0', 'no'):
        verify_opt = False
        print("⚠️  TLS verification disabled (verify=False). Use only in trusted networks.", file=sys.stderr)
    else:
        # treat as path
        verify_opt = args.verify
        if not Path(verify_opt).exists():
            print(f"❌ CA bundle not found: {verify_opt}", file=sys.stderr)
            sys.exit(2)

    # Prepare output directory
    out_dir = Path(args.output_dir) if args.output_dir else Path(tempfile.mkdtemp(prefix='yaml2json_'))
    out_dir.mkdir(parents=True, exist_ok=True)

    print(f"📦 Branch: {current_branch()} | Base: origin/{args.base_branch} | Compare: {args.compare}")
    changed_yaml_files = get_changed_yaml_files(args.base_branch, args.compare, args.include_path)

    if not changed_yaml_files:
        print("✅ No new or modified YAML files found.")
        return

    print(f"🧭 Found {len(changed_yaml_files)} YAML file(s) to process.")
    results = []
    failures = 0

    for yaml_file in changed_yaml_files:
        yf = Path(yaml_file)
        if not yf.exists():
            print(f"⚠️  Skipping missing file (maybe deleted/renamed?): {yaml_file}")
            continue
        json_path = safe_json_filename(yaml_file, out_dir)
        try:
            convert_yaml_to_json(yaml_file, json_path)
            if args.dry_run:
                print(f"🔎 Dry-run: would POST {json_path} → {args.api_url}")
                results.append((yaml_file, 0, 'dry-run'))
            else:
                status, body = post_with_retries(
                    args.api_url,
                    json_path,
                    verify=verify_opt,
                    timeout=args.timeout,
                    retries=args.retries,
                    headers={'User-Agent': 'yaml-changes-bot/1.0'}
                )
                ok = 200 <= status < 300
                failures += 0 if ok else 1
                # Print only summary; avoid dumping secrets
                print(f"➡️  HTTP {status} for {yaml_file}")
                results.append((yaml_file, status, '(body hidden)'))
        except (yaml.YAMLError, json.JSONDecodeError) as e:
            print(f"❌ Parse/serialization error for {yaml_file}: {e}", file=sys.stderr)
            failures += 1
        except FileNotFoundError as e:
            print(f"❌ File not found: {e}", file=sys.stderr)
            failures += 1
        except requests.exceptions.RequestException as e:
            print(f"❌ Network error for {yaml_file}: {e}", file=sys.stderr)
            failures += 1
        except Exception as e:
            print(f"❌ Unexpected error for {yaml_file}: {e}", file=sys.stderr)
            failures += 1

    # Optional rebase
    if not args.dry_run and args.rebase-after:
        print("🔁 Rebase requested...")
        ok = maybe_rebase_onto(args.base_branch)
        if not ok:
            failures += 1

    # Summary
    print("\n===== Summary =====")
    for yf, status, note in results:
        status_str = f"HTTP {status}" if status else note
        print(f"- {yf}: {status_str}")
    print("===================\n")

    if failures:
        print(f"❌ Completed with {failures} failure(s).", file=sys.stderr)
        sys.exit(1)
    else:
        print("✅ All done successfully.")

if __name__ == "__main__":
    main()
