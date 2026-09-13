"""Checked inventory handoff and main-text evidence bounds for completed artifacts."""
from pathlib import Path
import hashlib
import json
from urllib.parse import urlsplit


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def claim_source(claim):
    return {k: v for k, v in claim.items() if k != 'depends_on'}


def attach_inventory(data, inventory, destination):
    import os
    inventory = Path(inventory).resolve()
    data['source_inventory'] = {'path': os.path.relpath(inventory, Path(destination).resolve().parent),
                                'sha256': digest(inventory)}


def publication_errors(data, path, inventory_only=False):
    errors = []
    papers = {p.get('paper_id'): p for p in data.get('papers', []) if isinstance(p, dict)}
    claims = data.get('claims', [])
    for pid, p in papers.items():
        try:
            url = urlsplit(p.get('source_url', ''))
            if url.scheme not in ('https', 'http') or not url.hostname or url.username or url.password: raise ValueError()
        except (TypeError, ValueError):
            errors.append(f'{pid}: original source_url must be a valid HTTP(S) paper link')
        end = p.get('main_text_last_pdf_page')
        total = p.get('pdf_pages')
        if type(end) is not int or type(total) is not int or not 1 <= end <= total:
            errors.append(f'{pid}: main_text_last_pdf_page must be within the PDF')
        boundary = p.get('main_text_boundary', {})
        if not isinstance(boundary, dict) or not isinstance(boundary.get('location'), str) or not boundary['location'].strip() or type(boundary.get('shared_page_with_appendix')) is not bool:
            errors.append(f'{pid}: inspected main_text_boundary location and shared-page flag required')
        review = p.get('intake_review', {})
        expected = [c.get('claim_id') for c in sorted((c for c in claims if isinstance(c, dict) and c.get('paper_id') == pid), key=lambda c: c.get('source_order', 0))]
        if not isinstance(review, dict) or review.get('status') != 'complete':
            errors.append(f'{pid}: intake must be complete; pending/failed papers belong in the work queue')
        elif review.get('theorem_ids') != expected or type(review.get('zero_theorems_confirmed')) is not bool or review['zero_theorems_confirmed'] != (not expected):
            errors.append(f'{pid}: claims differ from the reviewed theorem inventory (including explicit zero-theorem confirmation)')

    def evidence(records, pid, where):
        if not isinstance(records, list):
            return  # Shape diagnostics are supplied by the primary validator.
        for e in records:
            if not isinstance(e, dict):
                continue
            owner = e.get('paper_id', pid)
            if owner not in papers or (pid is not None and owner != pid):
                errors.append(f'{where}: evidence must identify its own source paper')
                continue
            p = papers[owner]; page = e.get('page'); end = p.get('main_text_last_pdf_page')
            if type(page) is not int or type(end) is not int or not 1 <= page <= end:
                errors.append(f'{where}: evidence outside the main text')
            elif page == end and isinstance(p.get('main_text_boundary'), dict) and p['main_text_boundary'].get('shared_page_with_appendix') and e.get('before_main_text_end') is not True:
                errors.append(f'{where}: evidence on a shared boundary page must be inspected before the main-text endpoint')

    for c in claims:
        if isinstance(c, dict): evidence(c.get('evidence'), c.get('paper_id'), c.get('claim_id', 'claim'))
    for x in data.get('interfaces', []) if isinstance(data.get('interfaces', []), list) else []:
        if not isinstance(x, dict): continue
        iid = x.get('interface_id', '?')
        for field in ('members', 'central_claim_uses', 'dependencies', 'source_keywords'):
            for r in x.get(field, []) if isinstance(x.get(field, []), list) else []:
                if isinstance(r, dict) and 'evidence' in r: evidence(r['evidence'], r.get('paper_id'), f'{iid}/{field}')
        for m in x.get('members', []) if isinstance(x.get('members', []), list) else []:
            if isinstance(m, dict):
                for context in m.get('naming_context', []) if isinstance(m.get('naming_context', []), list) else []:
                    if isinstance(context, dict): evidence(context.get('evidence'), m.get('paper_id'), f'{iid}/naming_context')
        notes = x.get('theorem_explanations', {})
        for r in notes.values() if isinstance(notes, dict) else []:
            if isinstance(r, dict): evidence(r.get('evidence'), r.get('paper_id'), f'{iid}/explanation')
    if inventory_only:
        return errors
    ref = data.get('source_inventory')
    if not isinstance(ref, dict) or not isinstance(ref.get('path'), str) or not ref['path']:
        return errors + ['source_inventory.path and sha256 required for completed census']
    source_path = Path(path).resolve().parent / ref['path']
    if source_path.resolve() == Path(path).resolve():
        return errors + ['source inventory cannot refer to the census itself']
    try:
        content = source_path.read_bytes()
        if hashlib.sha256(content).hexdigest() != ref.get('sha256'):
            errors.append('source_inventory.sha256 mismatch')
        source = json.loads(content)
        if not isinstance(source, dict) or source.get('schema_version') != 'statistical-theorem-inventory-v1':
            return errors + ['source_inventory must identify an independent theorem inventory']
        # Inventory validation cannot recurse into a census handoff.
        from validate_census import validate
        errors.extend('Source inventory: ' + e for e in validate(source_path))
        if source.get('papers') != data.get('papers'):
            errors.append('papers differ from the inspected inventory')
        left = sorted((claim_source(c) for c in source.get('claims', [])), key=lambda c: c['claim_id'])
        right = sorted((claim_source(c) for c in claims), key=lambda c: c['claim_id'])
        if left != right:
            errors.append('theorem IDs or original source records differ from the inspected inventory')
    except (OSError, ValueError, KeyError, TypeError) as e:
        errors.append('Invalid source inventory: ' + str(e))
    return errors
