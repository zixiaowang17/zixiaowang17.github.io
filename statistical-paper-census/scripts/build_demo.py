#!/usr/bin/env python3
"""Build an explicitly synthetic example; no paper or mathlib search is performed."""
import copy
import hashlib
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILLS = ROOT / 'skills'
sys.path.insert(0, str(SKILLS / 'statistical-paper-census/scripts'))
from canonical_dependencies import canonical_dependencies
from census_metrics import derive_metrics
from publication_contract import attach_inventory


def main():
    out = ROOT / 'examples/synthetic'
    out.mkdir(parents=True, exist_ok=True)
    evidence = [{'page': 1, 'location': 'Invented example; no source PDF exists.'}]
    papers = []
    for pid in ('demo-a', 'demo-b'):
        papers.append(dict(paper_id=pid, title='Synthetic paper ' + pid[-1].upper(),
                           version='SYNTHETIC_DEMO', source_url='https://example.org/' + pid + '.pdf',
                           pdf_pages=1, pdf_sha256='0'*64, main_text_last_pdf_page=1,
                           main_text_boundary=dict(location='End of invented example', shared_page_with_appendix=False)))
    claims = []
    interfaces = []
    for i, (iid, symbol) in enumerate([('square', 'f'), ('shift', 'g'), ('score', 'h')], 1):
        pid='demo-a';cid=pid+':t'+str(i)
        claims.append(dict(paper_id=pid,claim_id=cid,claim_kind='theorem',label='Theorem '+str(i),source_order=i,
                           statement_original=f'For $x\\in\\mathbb{{R}}$, ${symbol}(x)\\geq 0$.',depends_on=[iid],evidence=evidence))
        m=dict(paper_id=pid,local_id=iid,local_label='Synthetic definition '+str(i),source_kind='definition',
               source_heading='Synthetic definition '+str(i),statement_original=f'Let ${symbol}(x)=x^2$. This is the Synthetic {iid}.',
               highlight_symbols=[symbol],relation='exact',depends_on=[],evidence=evidence)
        interfaces.append(dict(interface_id=iid,rank_group='all',name='Synthetic '+iid,lean_role='definition',
                               type_shape='Real to Real',semantic_boundary='Artificial UI example, not a library verdict.',members=[m],
                               central_claim_uses=[dict(use_id=iid+':use',paper_id=pid,claim_id=cid,use_kind='statement_dependency',reason=f'The invented theorem uses {symbol}.',evidence=evidence)],dependencies=[],
                               source_keywords=[dict(paper_id=pid,local_id=iid,source_text='Synthetic '+iid,label='Synthetic '+iid,kind='term')]))
    # Reuse one interface in another paper to demonstrate distinct-paper counts.
    shared=interfaces[0];member=copy.deepcopy(shared['members'][0]);member.update(paper_id='demo-b',local_id='square-b');shared['members'].append(member)
    claims.append(dict(paper_id='demo-b',claim_id='demo-b:t1',claim_kind='theorem',label='Theorem 1',source_order=1,
                       statement_original=r'For $x\in\mathbb{R}$, $f(x)\geq 0$.',depends_on=['square-b'],evidence=evidence))
    shared['central_claim_uses'].append(dict(use_id='square:use-b',paper_id='demo-b',claim_id='demo-b:t1',use_kind='statement_dependency',reason='The second invented paper also uses f.',evidence=evidence))
    for p in papers:
        p['intake_review']=dict(status='complete',theorem_ids=[c['claim_id'] for c in claims if c['paper_id']==p['paper_id']],zero_theorems_confirmed=False)
    data=dict(schema_version='statistical-ranked-interfaces-v4',scope=dict(paper_count=2,theorem_scope='main_text_only',source_policy='synthetic_demo',normalization_policy='Invented expressions',semantic_ranking_policy='Direct use counts',build_order_policy='Dependency order'),papers=papers,claims=claims,interfaces=interfaces)
    edges=canonical_dependencies(data)
    for x in interfaces:x['dependencies']=edges[x['interface_id']]
    inventory={k:copy.deepcopy(data[k]) for k in ('scope','papers','claims')};inventory['schema_version']='statistical-theorem-inventory-v1'
    for c in inventory['claims']:c.pop('depends_on')
    def write(name,value):
        (out/name).write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n')
    write('theorem-inventory.json',inventory);attach_inventory(data,out/'theorem-inventory.json',out/'ranked-interfaces.json');derive_metrics(data)
    for x in interfaces:
        x['theorem_explanations']={r['claim_id']:dict(paper_id=r['paper_id'],via_local_ids=r['via_local_ids'],text='The invented theorem uses the function named in this synthetic definition.',evidence=evidence) for r in x['related_theorems']}
    write('ranked-interfaces.json',data)
    audit=copy.deepcopy(data);audit.update(schema_version='ranked-mathlib-audit-v4',source_census_sha256=hashlib.sha256((out/'ranked-interfaces.json').read_bytes()).hexdigest(),mathlib_revision='SYNTHETIC_DEMO_NO_SEARCH',lean_version='SYNTHETIC_DEMO_NO_LEAN_CHECK',work_status_policy={'id':'mathematical-work-v2','method':'Artificial assignments to demonstrate all three buttons; not mathematical assessments.'})
    for x,status in zip(audit['interfaces'],('use_mathlib','small_adaptation','new_infrastructure')):
        note='Synthetic display example only. This color is illustrative; no mathlib search or mathematical assessment was performed.'
        x['library_audit']=dict(status='no_verified_match',related_declarations=[],no_related_reason=note,searches=[dict(mechanism='Synthetic fixture only',query='No search performed',result='Artificial record for the demo schema')],gap=note,work_status=status,work_status_reason=note,work_status_review={key:note for key in ('basis','available','remaining','comparison_evidence','scope')})
    write('audited.json',audit)
    command=[sys.executable,str(SKILLS/'statistical-census-html/scripts/build_report.py'),str(out/'audited.json'),str(out/'report.html'),'--census',str(out/'ranked-interfaces.json')]
    subprocess.run(command,check=True);subprocess.run(command+['--check'],check=True)
    print('Synthetic demo ready: examples/synthetic/report.html')

if __name__=='__main__':main()
