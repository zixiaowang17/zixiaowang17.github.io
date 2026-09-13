#!/usr/bin/env python3
"""Validate a completed mathlib audit against its unchanged source census."""
from __future__ import annotations
import argparse
import copy
import hashlib
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

PRODUCER = Path(__file__).resolve().parents[2] / 'statistical-paper-census' / 'scripts'
sys.path.insert(0, str(PRODUCER))
from validate_census import validate as validate_census

SCHEMA = 'ranked-mathlib-audit-v4'
STATUSES = {'exact_reuse', 'composable', 'partial_match', 'no_verified_match'}


def text(value):
    return isinstance(value, str) and bool(value.strip())


def declaration_url(value):
    if not text(value):
        return False
    u = urlparse(value)
    if u.scheme != 'https' or u.username or u.password or u.port:
        return False
    if u.hostname == 'leanprover-community.github.io':
        return u.path.startswith('/mathlib4_docs/Mathlib/') and u.path.endswith('.html') and bool(u.fragment)
    if u.hostname == 'github.com':
        return u.path.startswith('/leanprover-community/mathlib4/blob/') and '/Mathlib/' in u.path and u.path.endswith('.lean') and u.fragment.startswith('L')
    return False


def validate(data, census_path):
    errors = validate_census(census_path)
    if errors:
        return ['Source census: ' + e for e in errors]
    if not isinstance(data, dict) or data.get('schema_version') != SCHEMA:
        return [f'schema_version must be {SCHEMA}']
    source_bytes = census_path.read_bytes()
    source = json.loads(source_bytes)
    if source.get('schema_version') != 'statistical-ranked-interfaces-v4':
        return ['A completed interface census is required']
    if data.get('source_census_sha256') != hashlib.sha256(source_bytes).hexdigest():
        errors.append('source_census_sha256 does not match the supplied census')
    for field in ('mathlib_revision', 'lean_version'):
        if not text(data.get(field)) or data[field] in ('main','master','latest'):
            errors.append(f'{field} must identify the inspected environment')
    for key, value in source.items():
        if key not in ('schema_version','interfaces') and data.get(key) != value:
            errors.append(f'census field {key} was changed')
    interfaces = data.get('interfaces')
    if not isinstance(interfaces, list):
        return errors + ['interfaces must be a list']
    stripped = copy.deepcopy(interfaces)
    for item in stripped:
        if isinstance(item, dict):
            item.pop('library_audit', None)
    if stripped != source['interfaces']:
        errors.append('interfaces differ from the original census beyond library_audit')
    for item in interfaces:
        if not isinstance(item, dict):
            errors.append('invalid interface record')
            continue
        where = item.get('interface_id', '?')
        audit = item.get('library_audit')
        if not isinstance(audit, dict):
            errors.append(f'{where}: library_audit required')
            continue
        if audit.get('status') not in STATUSES or 'unverified' in audit:
            errors.append(f'{where}: incomplete/unverified audit cannot be published')
        if data.get('work_status_policy') or 'work_status' in audit:
            policy = data.get('work_status_policy', {})
            three_tiers = policy.get('id') == 'mathematical-work-v2'
            allowed = {'use_mathlib', 'small_adaptation', 'new_infrastructure'} if three_tiers else {'use_mathlib', 'needs_work'}
            if audit.get('work_status') not in allowed:
                errors.append(f'{where}: valid work_status required')
            if three_tiers:
                review = audit.get('work_status_review')
                if not isinstance(review, dict) or any(not text(review.get(f)) for f in
                    ('basis', 'available', 'remaining', 'comparison_evidence', 'scope')):
                    errors.append(f'{where}: evidence-backed work_status_review required')
            if not text(audit.get('work_status_reason')):
                errors.append(f'{where}: work_status_reason required')
        if not text(audit.get('gap')):
            errors.append(f'{where}: gap sentence required')
        searches = audit.get('searches')
        if not isinstance(searches,list) or not searches or any(
            not isinstance(s,dict) or any(not text(s.get(f)) for f in ('mechanism','query','result'))
            for s in searches):
            errors.append(f'{where}: actual search records required')
        declarations = audit.get('related_declarations')
        if not isinstance(declarations,list):
            errors.append(f'{where}: related_declarations must be a list')
            continue
        if not declarations and (audit.get('status') != 'no_verified_match' or not text(audit.get('no_related_reason'))):
            errors.append(f'{where}: related links or a completed no-related-result explanation required')
        for declaration in declarations:
            if not isinstance(declaration,dict):
                errors.append(f'{where}: invalid related declaration')
                continue
            for field in ('name','type','declaration_kind','module','provides'):
                if not text(declaration.get(field)):
                    errors.append(f'{where}: related declaration {field} required')
            try:
                valid = declaration_url(declaration.get('url'))
            except ValueError:
                valid = False
            if not valid:
                errors.append(f'{where}: official declaration link with an anchor required')
            if declaration.get('link_checked') is not True:
                errors.append(f'{where}: declaration link must have been opened and checked')
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input', type=Path)
    parser.add_argument('--census', type=Path, required=True)
    args = parser.parse_args()
    try:
        errors = validate(json.loads(args.input.read_text()), args.census)
    except (OSError,ValueError) as error:
        errors = [str(error)]
    for error in errors:
        print('ERROR:',error)
    if not errors:
        print(f'{args.input}: passed')
    return bool(errors)

if __name__ == '__main__':
    raise SystemExit(main())
