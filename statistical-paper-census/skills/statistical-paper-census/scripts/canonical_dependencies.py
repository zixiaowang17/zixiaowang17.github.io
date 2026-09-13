"""Derive canonical prerequisites exclusively from same-paper local edges."""
import hashlib


def canonical_dependencies(data):
    local = {(m['paper_id'], m['local_id']): (x, m) for x in data['interfaces'] for m in x['members']}
    result = {}
    for x in data['interfaces']:
        edges = {}
        for m in x['members']:
            for dep in m['depends_on']:
                target = local.get((m['paper_id'], dep))
                if target is None:
                    raise ValueError(f"{m['paper_id']}/{m['local_id']}: unknown prerequisite {dep}")
                prerequisite, _ = target; iid = prerequisite['interface_id']
                # Local dependencies between members of one keyword group remain local.
                if iid == x['interface_id']: continue
                if prerequisite['rank_group'] != x['rank_group']:
                    raise ValueError('Local dependency crosses rank groups; resolve the grouping explicitly')
                edge = edges.setdefault(iid, dict(
                    dependency_id='dependency-' + hashlib.sha256((x['interface_id']+'\0'+iid).encode()).hexdigest()[:16],
                    prerequisite_interface_id=iid,
                    dependency_kind='theorem_statement' if x['lean_role'] == 'theorem' else 'definition_body',
                    reason='Derived from the recorded same-paper source dependencies.',
                    local_edges=[], evidence=[]))
                edge['local_edges'].append(dict(paper_id=m['paper_id'], from_local_id=m['local_id'], to_local_id=dep))
                for e in m['evidence']:
                    record=dict(e, paper_id=m['paper_id'])
                    if record not in edge['evidence']: edge['evidence'].append(record)
        for edge in edges.values():
            edge['local_edges'].sort(key=lambda e:(e['paper_id'],e['from_local_id'],e['to_local_id']))
            edge['evidence'].sort(key=lambda e:(e['paper_id'],e['page'],e['location']))
        result[x['interface_id']] = [edges[k] for k in sorted(edges)]
    return result
