#!/usr/bin/env python3
"""Check release contents, research hashes and local HTML links without printing secrets."""
import hashlib
import json
import re
import subprocess
import sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT=Path(__file__).resolve().parents[1]
PATTERNS={
    'personal filesystem path':re.compile(r'/(?:Users|home)/[^\s/"\']+|/private/(?:tmp|var)/|/var[/]folders/|[A-Za-z]:\\Users\\'),
    'temporary filesystem path':re.compile(r'(?<![A-Za-z])/tmp/[A-Za-z0-9_-]+'),
    'GitHub credential':re.compile(r'\b(?:gh[pousr]_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,})\b'),
    'API credential':re.compile(r'\bsk-(?:proj-)?[A-Za-z0-9_-]{32,}\b'),
    'private key':re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----'),
    'AWS access key':re.compile(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b'),
    'credential-bearing URL':re.compile(r'https?://[^\s/<>"\']+:[^\s/<>"\']+@'),
}
ALLOWED_SUFFIXES={'.py','.md','.json','.html','.css','.js','.yaml','.yml','.txt'}
ALLOWED_NAMES={'LICENSE','NOTICE','.gitignore','.gitattributes','.nojekyll'}
EXCLUDED_DIRS={'.git','__pycache__','.venv','venv','node_modules'}
DYNAMIC={'release-manifest.json','release-check.json'}

class Links(HTMLParser):
    def __init__(self):
        super().__init__();self.ids=set();self.links=[]
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if 'id' in a:self.ids.add(a['id'])
        for key in ('href','src'):
            if a.get(key):self.links.append(a[key])

def files():
    return sorted(p for p in ROOT.rglob('*') if p.is_file() and not any(part in EXCLUDED_DIRS for part in p.relative_to(ROOT).parts))

def main():
    errors=[];entries={};pages={};total_bytes=0
    for p in files():
        name=p.relative_to(ROOT).as_posix();raw=p.read_bytes();total_bytes+=len(raw)
        if p.is_symlink():errors.append({'file':name,'issue':'symlink'});continue
        if p.suffix.lower()=='.pdf' or raw[:16].lstrip().startswith(b'%PDF-'):
            errors.append({'file':name,'issue':'PDF document'})
        if p.name.startswith('.env') or p.suffix.lower() in {'.pem','.key'}:
            errors.append({'file':name,'issue':'sensitive file type'})
        if p.suffix not in ALLOWED_SUFFIXES and p.name not in ALLOWED_NAMES:
            errors.append({'file':name,'issue':'unexpected file type'})
        try:text=raw.decode('utf-8')
        except UnicodeDecodeError:
            errors.append({'file':name,'issue':'non-text file'});continue
        for label,pattern in PATTERNS.items():
            checked=text
            if name in {'skills/statistical-census-html/scripts/test_workflow.py','scripts/check_release.py'}:
                # Deliberately invalid URL used to test rejection; not a real credential.
                checked=checked.replace('https://user:password@example.org/paper.pdf','SYNTHETIC_INVALID_URL')
            if pattern.search(checked):errors.append({'file':name,'issue':label})
        if p.suffix=='.html':
            parsed=Links();parsed.feed(text);pages[p.resolve()]=parsed
        if name not in DYNAMIC:entries[name]={'sha256':hashlib.sha256(raw).hexdigest(),'bytes':len(raw)}
    checked_links=0
    for p,parsed in pages.items():
        for href in parsed.links:
            u=urlsplit(href)
            if u.scheme or u.netloc:
                if u.scheme not in {'http','https'}:errors.append({'file':p.relative_to(ROOT).as_posix(),'issue':'unexpected link scheme'})
                continue
            target=(p.parent/unquote(u.path)).resolve() if u.path else p
            if ROOT not in target.parents and target!=ROOT:
                errors.append({'file':p.relative_to(ROOT).as_posix(),'issue':'link escapes repository'});continue
            if not target.exists():errors.append({'file':p.relative_to(ROOT).as_posix(),'issue':'missing local link target'})
            elif u.fragment and target in pages and unquote(u.fragment) not in pages[target].ids:
                errors.append({'file':p.relative_to(ROOT).as_posix(),'issue':'missing HTML fragment'})
            checked_links+=1
    exp=ROOT/'experiments/aos-2024'
    provenance=json.loads((exp/'export-provenance.json').read_text())
    for item in provenance['preserved_artifacts']:
        digest=hashlib.sha256((ROOT/item['path']).read_bytes()).hexdigest()
        if digest!=item['source_sha256'] or digest!=item['export_sha256']:
            errors.append({'file':item['path'],'issue':'preserved research hash changed'})
    census=json.loads((exp/'ranked-interfaces.json').read_text());audit=json.loads((exp/'audited.json').read_text())
    counts={'papers':len(census['papers']),'theorems':len(census['claims']),'interfaces':len(census['interfaces'])}
    if counts!={'papers':113,'theorems':637,'interfaces':2486}:errors.append({'file':'experiment','issue':'inventory count changed'})
    command=[sys.executable,'skills/ranked-mathlib-audit/scripts/validate_audit.py','experiments/aos-2024/audited.json','--census','experiments/aos-2024/ranked-interfaces.json']
    result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True)
    if result.returncode:errors.append({'file':'experiment','issue':'audit/census validation failed'})
    manifest={'files':entries,'scope':'Current release files; Git metadata, bytecode, environments and these two generated check files are excluded.'}
    report={'status':'passed' if not errors else 'failed','files_checked':len(entries),'bytes_checked':total_bytes,'local_html_links_checked':checked_links,'counts':counts,'findings':errors,'limits':'Pattern-based file scan and consistency checks, not a guarantee that every possible secret or mathematical error has been detected. No Git history is scanned.'}
    (ROOT/'release-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
    (ROOT/'release-check.json').write_text(json.dumps(report,indent=2)+'\n')
    print(json.dumps(report,indent=2));return bool(errors)
if __name__=='__main__':raise SystemExit(main())
