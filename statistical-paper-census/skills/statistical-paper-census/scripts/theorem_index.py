"""Derive same-paper theorem relationships; never propagate between paper variants."""
from collections import deque


def derive_related(data):
    interfaces = data.get('interfaces', [])
    local = {}
    by_id = {x['interface_id']: x for x in interfaces}
    for item in interfaces:
        for member in item.get('members', []):
            key = (member.get('paper_id'), member.get('local_id'))
            if not all(isinstance(x, str) and x for x in key) or key in local:
                raise ValueError(f'invalid or duplicate local interface {key}')
            if not isinstance(member.get('depends_on'), list):
                raise ValueError(f'{key}: depends_on must be a list')
            local[key] = (item['interface_id'], member)
    visiting, visited = set(), set()
    def visit(key):
        if key in visiting:
            raise ValueError(f'local dependency cycle at {key}')
        if key in visited:
            return
        visiting.add(key)
        for dependency in local[key][1]['depends_on']:
            target = (key[0], dependency)
            if target not in local:
                raise ValueError(f'{key}: unknown local dependency {dependency!r}')
            visit(target)
        visiting.remove(key)
        visited.add(key)
    for key in local:
        visit(key)
    related = {x: {} for x in by_id}
    claims = {x['claim_id']: x for x in data.get('claims', [])}
    for claim in claims.values():
        cid, pid = claim['claim_id'], claim['paper_id']
        if not isinstance(claim.get('depends_on'), list):
            raise ValueError(f'{cid}: depends_on must be a list')
        queue = deque([[x] for x in claim['depends_on']])
        seen = set()
        while queue:
            path = queue.popleft()
            key = (pid, path[-1])
            if key not in local:
                raise ValueError(f'{cid}: unknown local interface {key}')
            if key in seen:
                continue
            seen.add(key)
            interface_id, member = local[key]
            relation = 'direct' if len(path) == 1 else 'indirect'
            if cid not in related[interface_id]:
                related[interface_id][cid] = dict(paper_id=pid, claim_id=cid,
                                                  relation=relation, via_local_ids=path)
            queue.extend(path + [x] for x in member['depends_on'])
    for item in interfaces:
        iid = item['interface_id']
        seen_uses = set()
        for use in item.get('central_claim_uses', []):
            cid = use.get('claim_id')
            if cid not in claims or claims[cid]['paper_id'] != use.get('paper_id'):
                raise ValueError(f'{iid}: unknown or wrong-paper theorem use {cid}')
            if cid in seen_uses:
                raise ValueError(f'{iid}: duplicate direct use for theorem {cid}')
            seen_uses.add(cid)
            if use.get('use_kind') == 'claim_target' and item.get('lean_role') == 'theorem':
                related[iid][cid] = dict(paper_id=use['paper_id'], claim_id=cid,
                                        relation='target', via_local_ids=[])
            elif related[iid].get(cid, {}).get('relation') != 'direct':
                raise ValueError(f'{iid}: recorded direct use {cid} is not a direct local dependency')
        expected_direct = {cid for cid, r in related[iid].items() if r['relation'] in ('direct','target')}
        if seen_uses != expected_direct:
            raise ValueError(f'{iid}: direct use list does not match the theorem statements')
    paper_order = {p['paper_id']: n for n,p in enumerate(data.get('papers', []))}
    return {iid: sorted(entries.values(), key=lambda r: (
        paper_order.get(r['paper_id'], 0), claims[r['claim_id']].get('source_order', 0), r['claim_id']))
        for iid, entries in related.items()}
