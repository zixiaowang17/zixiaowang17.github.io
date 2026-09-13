from pathlib import Path
import copy, hashlib, importlib.util, json, subprocess, sys
import tempfile
SKILLS=Path(__file__).resolve().parents[2]
workspace=tempfile.TemporaryDirectory(prefix='census-skill-test-')
TEST=Path(workspace.name)
sys.path.insert(0,str(SKILLS/'statistical-paper-census/scripts'))
from census_metrics import derive_metrics, MetricsError
from canonical_dependencies import canonical_dependencies
from publication_contract import attach_inventory
from validate_census import validate as validate_census
sys.path.insert(0,str(SKILLS/'ranked-mathlib-audit/scripts'))
from validate_audit import validate as validate_audit

evidence=[dict(page=1,location='Synthetic fixture, not a paper extraction')]
papers=[dict(paper_id=p,title='Synthetic paper '+p,version='fixture',source_url='https://example.org/'+p+'.pdf',pdf_pages=2,pdf_sha256='0'*64) for p in ('p1','p2','p3')]
def claim(pid,tid,order,deps):
 return dict(paper_id=pid,claim_id=pid+tid,claim_kind='theorem',label='Theorem '+str(order),source_order=order,
  statement_original='For $x \\in \\mathbb{R}$, the following holds.\n\n\\[x^2 \\geq 0.\\]\n\nLiteral text: <script>alert(1)</script>.',depends_on=deps,evidence=evidence)
def member(pid,lid,deps):
 return dict(paper_id=pid,local_id=lid,local_label='Definition '+lid,source_kind='definition',source_heading='Definition '+lid,statement_original='Let $f(x)=x^2$.',highlight_symbols=['x^2'],relation='exact',depends_on=deps,evidence=evidence)
def use(iid,pid,cid):
 return dict(use_id=iid+cid,paper_id=pid,claim_id=cid,use_kind='statement_dependency',reason='Synthetic direct statement dependency',evidence=evidence)
def dep(iid,prereq):
 return dict(dependency_id=iid+prereq,prerequisite_interface_id=prereq,dependency_kind='definition_body',reason='Synthetic prerequisite',evidence=evidence)
def interface(iid,members,uses,deps):
 return dict(interface_id=iid,rank_group='all',name='Synthetic interface '+iid,lean_role='definition',type_shape='INTERNAL_SHAPE_SENTINEL',semantic_boundary='INTERNAL_BOUNDARY_SENTINEL',members=members,central_claim_uses=uses,dependencies=deps)
data=dict(schema_version='statistical-ranked-interfaces-v4',scope=dict(paper_count=3,theorem_scope='main_text_only',source_policy='fixture',normalization_policy='fixture',semantic_ranking_policy='direct edges',build_order_policy='dependency order'),papers=papers,claims=[claim('p1','t1',1,['a1']),claim('p1','t2',2,['a1']),claim('p1','t3',3,[]),claim('p2','t1',1,['s2'])],interfaces=[
 interface('A',[member('p1','a1',['s1'])],[use('A','p1','p1t1'),use('A','p1','p1t2')],[dep('A','S')]),
 interface('S',[member('p1','s1',[]),member('p2','s2',['z2'])],[use('S','p2','p2t1')],[dep('S','Z')]),
 interface('Z',[member('p2','z2',[])],[],[]),
])
# Reviewed inventory is an independent upstream artifact.
for p in papers:
 p.update(main_text_last_pdf_page=2, main_text_boundary=dict(location='End of synthetic main text',shared_page_with_appendix=False),
          intake_review=dict(status='complete',theorem_ids=[c['claim_id'] for c in data['claims'] if c['paper_id']==p['paper_id']],zero_theorems_confirmed=not any(c['paper_id']==p['paper_id'] for c in data['claims'])))
for x in data['interfaces']:
 m=x['members'][0];m['statement_original']+=' '+x['name']
 x['source_keywords']=[dict(paper_id=m['paper_id'],local_id=m['local_id'],source_text=x['name'],label=x['name'],kind='term')]
edges=canonical_dependencies(data)
for x in data['interfaces']:x['dependencies']=edges[x['interface_id']]
inventory={k:copy.deepcopy(data[k]) for k in ('scope','papers','claims')};inventory['schema_version']='statistical-theorem-inventory-v1'
for c in inventory['claims']:c.pop('depends_on')
inv=TEST/'inventory.json';inv.write_text(json.dumps(inventory));assert not validate_census(inv)
attach_inventory(data, inv, TEST/'census.json')
# Same-paper propagation must not route p1 theorems through p2's shared-interface variant.
derive_metrics(data)
byid={x['interface_id']:x for x in data['interfaces']}
for x in data['interfaces']:
 x['theorem_explanations']={r['claim_id']:dict(paper_id=r['paper_id'],via_local_ids=r['via_local_ids'],text='The squared quantity $x^2$ is used in this synthetic source.',evidence=evidence) for r in x['related_theorems']}
assert {r['claim_id'] for r in byid['Z']['related_theorems']}=={'p2t1'}
assert len(byid['S']['related_theorems'])==3
assert [r['relation'] for r in byid['S']['related_theorems']]==['indirect','indirect','direct']
assert byid['Z']['build_order']<byid['S']['build_order']<byid['A']['build_order']
# A source-backed note must remain tied to its actual same-paper relation.
byid['S']['theorem_explanations']={record['claim_id']:dict(
 paper_id=record['paper_id'],via_local_ids=record['via_local_ids'],
 text='The symbol $f$ denotes the squared quantity; source-connection-token.',evidence=evidence)
 for record in byid['S']['related_theorems']}
byid['S']['members'][0]['highlight_symbols']=['f']
census=TEST/'census.json';census.write_text(json.dumps(data,ensure_ascii=False,indent=2))
assert not validate_census(census),validate_census(census)
# Inventory-only permits unlinked theorems and zero-theorem papers.
inventory={k:copy.deepcopy(data[k]) for k in ('scope','papers','claims')};inventory['schema_version']='statistical-theorem-inventory-v1'
for c in inventory['claims']:c.pop('depends_on')
inv=TEST/'inventory.json';inv.write_text(json.dumps(inventory));assert not validate_census(inv)
audit=copy.deepcopy(data);audit.update(schema_version='ranked-mathlib-audit-v4',source_census_sha256=hashlib.sha256(census.read_bytes()).hexdigest(),mathlib_revision='TEST_FIXTURE_ONLY',lean_version='TEST_FIXTURE_ONLY')
for x in audit['interfaces']:
 x['library_audit']=dict(status='partial_match',related_declarations=[dict(name='Synthetic.declaration',type='Synthetic type',declaration_kind='defnInfo',module='Mathlib.Synthetic',url='https://leanprover-community.github.io/mathlib4_docs/Mathlib/Synthetic.html#Synthetic.declaration',link_checked=True,provides='Synthetic fixture only; not a real mathlib audit')],searches=[dict(mechanism='synthetic fixture',query='fixture',result='fixture')],gap='Synthetic fixture only; no mathematical verdict is claimed.')
assert not validate_audit(audit,census)
for mutate in (
 lambda a:a['interfaces'][0]['library_audit'].update(unverified=True),
 lambda a:a['interfaces'][0]['library_audit'].update(status='unresolved'),
 lambda a:a['interfaces'][0]['library_audit']['related_declarations'][0].update(link_checked=False),
 lambda a:a['interfaces'][0]['library_audit']['related_declarations'][0].update(url='javascript:alert(1)'),
 lambda a:a['interfaces'][0]['library_audit']['related_declarations'][0].update(url='https://example.com/fake'),
 lambda a:a['interfaces'][0]['library_audit'].update(searches=[]),
 lambda a:a['claims'][0].update(statement_original='changed'),
 lambda a:a.update(source_census_sha256='a'*64)):
 bad=copy.deepcopy(audit);mutate(bad);assert validate_audit(bad,census)
for mutate in (
 lambda d:d['claims'][0].pop('statement_original'),
 lambda d:d['claims'][0].update(claim_kind='lemma'),
 lambda d:d['scope'].update(theorem_scope='appendices_included'),
 lambda d:d['interfaces'][0].update(related_theorems=[])):
 bad=copy.deepcopy(data);mutate(bad);p=TEST/'bad-census.json';p.write_text(json.dumps(bad));assert validate_census(p)
for mutate in (
 lambda notes:notes.pop('p1t1'),
 lambda notes:notes['p1t1'].update(paper_id='p2'),
 lambda notes:notes['p1t1'].update(via_local_ids=['s2']),
 lambda notes:notes['p1t1'].update(evidence=[]),
 lambda notes:notes['p1t1'].update(evidence=[dict(page=3,location='Outside source')])):
 bad=copy.deepcopy(data);mutate(next(x for x in bad['interfaces'] if x['interface_id']=='S')['theorem_explanations'])
 p=TEST/'bad-explanation.json';p.write_text(json.dumps(bad));assert validate_census(p)
bad=copy.deepcopy(data);next(x for x in bad['interfaces'] if x['interface_id']=='Z')['members'][0]['depends_on']=['s2']
try: derive_metrics(bad)
except MetricsError: pass
else: raise AssertionError('local cycle accepted')
a=TEST/'audited.json';a.write_text(json.dumps(audit,ensure_ascii=False,indent=2))
builder=SKILLS/'statistical-census-html/scripts/build_report.py';out=TEST/'report.html'
command=[sys.executable,str(builder),str(a),str(out),'--census',str(census)]
subprocess.run(command,check=True);subprocess.run(command+['--check'],check=True)
allhtml='\n'.join(p.read_text() for p in TEST.rglob('*.html'))
reader_folder=next((TEST/'report-pages').iterdir())
assert 'INTERNAL_SHAPE_SENTINEL' not in allhtml and 'INTERNAL_BOUNDARY_SENTINEL' not in allhtml
assert '<math' in allhtml
assert '<script>alert(1)</script>' not in allhtml
assert 'Theorem 3' in allhtml
assert 'No Theorems occur in the main text.' in allhtml
# Real source-layout regression: do not merge a TeX command into the next variable,
# and render negative kerning, indicator fonts, and LaTeXML array/subarray output.
spec=importlib.util.spec_from_file_location('report_builder',builder)
report_builder=importlib.util.module_from_spec(spec);spec.loader.exec_module(report_builder)
layout = r'\[\int\mspace{-3mu}x\,dx + \mathbbm{1}_{A} + \sum_{\begin{subarray}{c}i<j\\j<n\end{subarray}} a_{ij}\]'
normalized=report_builder.normalize_math_layout(layout)
assert r'\intx' not in normalized
rendered=report_builder.render_statement(layout)
assert '<math' in rendered and 'merror' not in rendered
assert '<math' in report_builder.render_statement(r'\[\begin{array}[]{ll}1 & x>0\\0 & x<0\end{array}\]')
# Search views use semantic rank and deduplicated local API dependencies.
search_audit=copy.deepcopy(audit)
for x in search_audit['interfaces']:
 x['library_audit']['status']={'A':'partial_match','S':'composable','Z':'exact_reuse'}[x['interface_id']]
search_index=report_builder.build_search_index(search_audit,'report-pages')
assert [x['route'] for x in search_index['interfaces']]==['interface:A','interface:S','interface:Z']
assert [x['semantic_rank'] for x in sorted(search_audit['interfaces'],key=lambda x:x['build_order'])]!=[1,2,3]
assert 'source-connection-token' in next(x for x in search_index['interfaces'] if x['route']=='interface:S')['search']
shared=(reader_folder/report_builder.filename('interface','S')).read_text()
assert shared.count('class="connection"')==3
assert 'href="#'+report_builder.variant_anchor(byid['S']['members'][0])+'"' in shared
assert 'id="'+report_builder.variant_anchor(byid['S']['members'][1])+'"' in shared
assert 'This theorem directly uses the API.' not in shared
assert '<h2>Variants</h2>' not in shared
assert shared.index('id="'+report_builder.variant_anchor(byid['S']['members'][0])+'"') < shared.index('id="'+report_builder.theorem_anchor('p1t1')+'"')
assert shared.index('id="'+report_builder.variant_anchor(byid['S']['members'][1])+'"') < shared.index('id="'+report_builder.theorem_anchor('p2t1')+'"')
first_paper, second_paper = shared.split('data-paper-id="p2"')
assert 'class="symbol-highlight"' in first_paper
assert '<mi class="symbol-highlight">f</mi>' not in second_paper
# Exact MathML matching highlights moment symbols, not similarly named constants/sieves.
source=r'Outside math M_2. $M_2(x)+M_{\mu,\nu}+\mathcal{P}_4+\mathscr{P}_n+M_{20}$'
plain=report_builder.render_statement(source)
highlighted=report_builder.render_with_highlights(source,(r'M_{2}',r'\mathcal{P}_{4}'))
assert highlighted.count('class="symbol-highlight"')==2
assert 'Outside math M_2.' in highlighted
# Removing presentation attributes recovers the same rendered mathematical structure.
import re, xml.etree.ElementTree as ET
before=[ET.fromstring(m) for m in re.findall(r'<math\b.*?</math>',plain,re.S)]
after=[ET.fromstring(m) for m in re.findall(r'<math\b.*?</math>',highlighted,re.S)]
assert [report_builder.math_key(m) for m in before]==[report_builder.math_key(m) for m in after]
assert report_builder.render_with_highlights(r'$M_{20}$',(r'M_{2}',))==report_builder.render_statement(r'$M_{20}$')
# Prose and multi-node mathematical highlights are reusable, safe and precise.
prose=report_builder.render_with_highlights('Assumption 4.1; Assumption 4.10. <script>alert(1)</script>.',(),('Assumption 4.1',))
assert prose.count('<mark class="symbol-highlight">')==1
assert '<script>alert(1)</script>' not in prose
sequence=report_builder.render_with_highlights(r'$a+ D(\epsilon, B, d)+D+\rightarrow 0$',(r'D(\epsilon, B, d)',r'\rightarrow 0'))
assert sequence.count('class="symbol-highlight"')==2
assert '<mi>D</mi>' in sequence  # Scalar D is not itself a selector.
# Universal coverage: no renderer path silently emits an API with missing or ineffective annotations.
for selector in ([],[r'\mathbb{R}']):
 bad=copy.deepcopy(audit)
 member=next(x for x in bad['interfaces'] if x['interface_id']=='S')['members'][0]
 member['highlight_symbols']=selector
 try:report_builder.generate(bad,TEST/'missing-highlights.html')
 except ValueError as error:assert 'highlight' in str(error)
 else:raise AssertionError('Missing definition highlight accepted')
bad=copy.deepcopy(data)
next(x for x in bad['interfaces'] if x['interface_id']=='S')['members'][0]['highlight_symbols']=['not in the source']
bad_path=TEST/'bad-highlights.json';bad_path.write_text(json.dumps(bad));assert validate_census(bad_path)
# Source identity is independent of an implementation's proposed Lean role.
typed=copy.deepcopy(audit)
typed_member=next(x for x in typed['interfaces'] if x['interface_id']=='A')['members'][0]
typed_member.update(source_kind='assumption',source_heading='Assumption 4.1',local_label='Assumption 4.1')
rendered_source=report_builder.generate(typed,TEST/'typed.html')
page=next(v for k,v in rendered_source.items() if k.endswith('/'+report_builder.filename('interface','A')))
assert '<h3>Assumption 4.1<' in page and '<h3>Definition<' not in page
for changes in ({'source_kind':'assumption','source_heading':'Definition'},
                {'source_kind':'definition','source_heading':'Definition','local_label':'Assumption 4.1'},
                {'source_kind':'unresolved'}):
 bad=copy.deepcopy(data);bad['interfaces'][0]['members'][0].update(changes)
 p=TEST/'bad-source-kind.json';p.write_text(json.dumps(bad));assert validate_census(p)
assert 'href="https://example.org/p1.pdf"' in page
assert '#page=' not in page
assert report_builder.source_pdf_url(papers[0])=='https://example.org/p1.pdf'
for url in ('','javascript:alert(1)','https://user:password@example.org/paper.pdf'):
 bad_paper=dict(papers[0],source_url=url)
 try:report_builder.source_pdf_url(bad_paper)
 except ValueError:pass
 else:raise AssertionError('Missing/unsafe original-source URL accepted')
indexed_papers={p['route']:p for p in search_index['papers']}
assert indexed_papers['paper:p1']['api_count']==2  # A and S count once each, even across multiple theorems.
assert indexed_papers['paper:p2']['api_count']==2
assert {a['route'] for t in indexed_papers['paper:p1']['theorems'] for a in t['requirements']}=={'interface:A','interface:S'}
assert report_builder.build_search_index(audit,'report-pages')==search_index  # Internal statuses do not affect presentation.
assert indexed_papers['paper:p3']['theorem_count']==0
assert not indexed_papers['paper:p1']['theorems'][2]['requirements']
assert indexed_papers['paper:p1']['theorems'][0]['url'].split('#')[1].startswith('theorem-')
assert 'data-route="interface:A"' in allhtml
assert 'API gap' not in allhtml and 'Assembly needed' not in allhtml
assert 'coverage_label' not in allhtml and 'assembly_count' not in allhtml
assert 'id="coverage"' not in allhtml
# Work decisions are explicit audit data, never guessed from the legacy categories.
work_audit=copy.deepcopy(audit)
work_audit['work_status_policy']={'id':'mathematical-work-v2'}
for x in work_audit['interfaces']:
 x['library_audit'].update(work_status={'Z':'use_mathlib','S':'small_adaptation','A':'new_infrastructure'}[x['interface_id']],work_status_reason='Synthetic reviewed action reason.',work_status_review={k:'Synthetic evidence for '+k for k in ('basis','available','remaining','comparison_evidence','scope')})
assert not validate_audit(work_audit,census)
for mutate in (lambda x:x.update(work_status='unknown'),lambda x:x.pop('work_status'),lambda x:x.update(work_status_reason=''),lambda x:x.pop('work_status_review'),lambda x:x['work_status_review'].update(remaining='')):
 invalid=copy.deepcopy(work_audit);mutate(invalid['interfaces'][0]['library_audit']);assert validate_audit(invalid,census)
work_files=report_builder.generate(work_audit,TEST/'work-status.html')
work_index=report_builder.build_search_index(work_audit,'pages')
assert {x['route']:x['work_status'] for x in work_index['interfaces']}=={'interface:A':'new_infrastructure','interface:S':'small_adaptation','interface:Z':'use_mathlib'}
assert all(set(r)=={'route','relation'} for p in work_index['papers'] for t in p['theorems'] for r in t['requirements'])
for x in work_audit['interfaces']:
 content=next(v for k,v in work_files.items() if k.endswith('/'+report_builder.filename('interface',x['interface_id'])))
 assert f'data-work-status="{x["library_audit"]["work_status"]}"' in content
 assert 'Synthetic reviewed action reason.' in content
paper_content=next(v for k,v in work_files.items() if k.endswith('/'+report_builder.filename('paper','p2')))
assert 'data-work-status="small_adaptation"' in paper_content and 'data-work-status="use_mathlib"' in paper_content
print('PASS: explicit three-tier work statuses, reasons, strict validation, reader/requirement labels and shared-index preservation')
numbered = report_builder.render_statement(r'\[x^2\]'+'\n(3.5)')
assert 'class="equation-number">(3.5)' in numbered
try: report_builder.render_statement(r'\[\unsupportedCensusMacro{x}\]')
except ValueError: pass
else: raise AssertionError('Unknown TeX must fail, not silently degrade')
print('PASS: same-paper links, full inventory, ranks, strict audit handoff, MathML, escaping, reproducible generation and negative cases')

# Publication gates reject loss of source coverage, provenance, and invalid evidence.
for mutate in (
 lambda d:d['papers'][0]['intake_review'].update(status='pending'),
 lambda d:d['papers'][0]['intake_review'].update(theorem_ids=[]),
 lambda d:d['papers'][0].update(main_text_last_pdf_page=999),
 lambda d:d['claims'][0]['evidence'][0].update(page=999),
 lambda d:d['interfaces'][0]['members'][0]['evidence'][0].update(page=999),
 lambda d:d['interfaces'][0].pop('source_keywords'),
 lambda d:d['interfaces'][0].pop('theorem_explanations'),
 lambda d:d['source_inventory'].update(sha256='a'*64),
 lambda d:d['interfaces'][0]['source_keywords'][0].update(label='Invented title')):
 bad=copy.deepcopy(data);mutate(bad);p=TEST/'bad-publication.json';p.write_text(json.dumps(bad));assert validate_census(p)
# Matching counts cannot conceal a changed or omitted source theorem.
bad=copy.deepcopy(data);bad['claims'][0]['statement_original']='A substituted theorem.'
p=TEST/'changed-source.json';p.write_text(json.dumps(bad));assert any('source records differ' in e for e in validate_census(p))
bad=copy.deepcopy(data);bad['claims']=[c for c in bad['claims'] if c['claim_id']!='p1t3'];bad['papers'][0]['intake_review']['theorem_ids'].remove('p1t3')
p.write_text(json.dumps(bad));assert any('source records differ' in e for e in validate_census(p))
# Even inventory-only evidence respects the boundary and completed-zero distinction.
bad=copy.deepcopy(inventory);bad['claims']=[];p.write_text(json.dumps(bad));assert validate_census(p)
bad=copy.deepcopy(inventory);bad['papers'][0]['main_text_last_pdf_page']=1;bad['claims'][0]['evidence'][0]['page']=2
p.write_text(json.dumps(bad));assert validate_census(p)
bad=copy.deepcopy(inventory);bad['papers'][0]['main_text_last_pdf_page']=1;bad['papers'][0]['main_text_boundary']['shared_page_with_appendix']=True
p.write_text(json.dumps(bad));assert validate_census(p)
for c in bad['claims']:
 if c['paper_id']=='p1':c['evidence']=[dict(page=1,location='Main text above appendix heading',before_main_text_end=True)]
p.write_text(json.dumps(bad));assert not validate_census(p),validate_census(p)
# Missing or invented global prerequisite edges cannot silently change build order.
bad=copy.deepcopy(data)
for x in bad['interfaces']:x['dependencies']=[]
try:derive_metrics(bad)
except MetricsError:pass
else:raise AssertionError('Canonical edges not reconciled with local edges')
# Failed finalization preserves the previous artifact; a good run pins its inventory.
finalizer=SKILLS/'statistical-paper-census/scripts/finalize_census.py'
bad=copy.deepcopy(data);bad['claims'][0]['statement_original']=''
inp=TEST/'finalize-input.json';dest=TEST/'last-good.json';inp.write_text(json.dumps(bad));dest.write_text('LAST GOOD')
cmd=[sys.executable,str(finalizer),str(inp),str(dest),'--inventory',str(inv)]
assert subprocess.run(cmd,capture_output=True).returncode!=0
assert dest.read_text()=='LAST GOOD'
inp.write_text(json.dumps(data));assert subprocess.run(cmd,capture_output=True).returncode==0
assert not validate_census(dest),validate_census(dest)
# A shared interface is stored once even when its source text grows across papers.
def search_fixture(n):
 ps=[dict(paper_id=f'p{i}',title=f'Paper {i}') for i in range(n)]
 cs=[dict(claim_id=f't{i}',paper_id=f'p{i}',label='Theorem 1',source_order=1,statement_original='A synthetic theorem.') for i in range(n)]
 ms=[dict(paper_id=f'p{i}',local_label='Definition',statement_original='A source statement about a shared mathematical interface. '*10) for i in range(n)]
 rs=[dict(paper_id=f'p{i}',claim_id=f't{i}',relation='direct') for i in range(n)]
 api=dict(interface_id='shared',name='Shared interface',lean_role='definition',rank_group='all',semantic_rank=1,central_claim_paper_count=n,central_claim_use_count=n,library_audit={'gap':'Synthetic fixture.'},members=ms,related_theorems=rs)
 idx=report_builder.build_search_index(dict(papers=ps,claims=cs,interfaces=[api]),'pages');idx.pop('theorems')
 assert all(set(a)=={'route','relation'} for p in idx['papers'] for t in p['theorems'] for a in t['requirements'])
 return len(json.dumps(idx,separators=(',',':')).encode())
small,large=search_fixture(100),search_fixture(200)
assert large < small*2.1,(small,large)
# Interrupted publication cannot replace the old index or its referenced readers.
from unittest.mock import patch
old_index=out.read_bytes();old_readers={p:p.read_bytes() for p in reader_folder.iterdir()}
changed=copy.deepcopy(audit);changed['interfaces'][0]['library_audit']['gap']='A revised synthetic gap.'
a.write_text(json.dumps(changed));original_replace=report_builder.os.replace
original_argv=sys.argv[:]
def fail_index(source,destination):
 if Path(destination)==out:raise OSError('Simulated interruption before publishing the index')
 return original_replace(source,destination)
try:
 sys.argv=[str(builder),str(a),str(out),'--census',str(census)]
 with patch.object(report_builder.os,'replace',side_effect=fail_index):assert report_builder.main()==1
finally:sys.argv=original_argv
a.write_text(json.dumps(audit))
assert out.read_bytes()==old_index
assert all(p.read_bytes()==value for p,value in old_readers.items())
print(f'PASS: inventory pinning, main-text bounds, required provenance, atomic failure recovery, canonical edges; shared-API payload 100/200 papers: {small}/{large} bytes')

# Source subcase labels survive both sanitizing passes, including highlighting.
from html.parser import HTMLParser
class ListAttributes(HTMLParser):
 def __init__(self, html):
  super().__init__();self.records=[];self.feed(html)
 def handle_starttag(self, tag, attrs):
  if tag in {'ol','li','p'}:self.records.append((tag,dict(attrs)))

for marker,attrs,reference in (
 ('(i)',{'type':'i'},'(ii)'),
 ('(a)',{'type':'a'},'(b)'),
 ('3.',{'start':'3','type':'1'},'4'),
):
 second={'(i)':'(ii)','(a)':'(b)','3.':'4.'}[marker]
 source=f'{marker} The quantity $x^2$ is nonnegative.\n{second} The squared quantity is finite.\n\nUse conclusion {reference}.'
 for rendered in (report_builder.render_statement(source),
                  report_builder.render_with_highlights(source,('x^2',),('squared quantity',))):
  lists=[a for tag,a in ListAttributes(rendered).records if tag=='ol']
  assert lists==[attrs],(marker,lists)
  assert f'Use conclusion {reference}.' in rendered
 assert 'class="symbol-highlight"' in rendered and '<mark class="symbol-highlight">' in rendered
raw='<ol type="A" start="-2" onclick="bad()"><li value="3">First<ol type="I"><li value="-2">Nested</li></ol></li></ol><ol type="roman" start="1.5"><li value="no" style="color:red">Invalid</li></ol><p type="a" start="3" value="4">Wrong tag</p>'
expected=[('ol',{'type':'A','start':'-2'}),('li',{'value':'3'}),('ol',{'type':'I'}),('li',{'value':'-2'}),('ol',{}),('li',{}),('p',{})]
sanitizer=report_builder.SafeMathHTML();sanitizer.feed(raw)
safe=''.join(sanitizer.parts)
assert ListAttributes(safe).records==expected
assert 'onclick' not in safe and 'style=' not in safe

# Invalid explanation containers fail at intake, including when there are no related theorems.
for invalid in (None,[],False,''):
 bad=copy.deepcopy(data);next(x for x in bad['interfaces'] if x['interface_id']=='A')['theorem_explanations']=invalid
 p=TEST/'bad-notes-type.json';p.write_text(json.dumps(bad))
 errors=validate_census(p)
 assert any('(A): theorem_explanations must be an object' in e for e in errors),errors
zero=copy.deepcopy(data)
for c in zero['claims']:c['depends_on']=[]
for x in zero['interfaces']:x.update(central_claim_uses=[],theorem_explanations={})
derive_metrics(zero)
p=TEST/'zero-related.json';p.write_text(json.dumps(zero));assert not validate_census(p),validate_census(p)
zero['interfaces'][0]['theorem_explanations']=None;p.write_text(json.dumps(zero));assert validate_census(p)

# Reject retired captions without rejecting actual source-specific prose using similar words.
captions=('This theorem directly uses the API.',
          '  THIS theorem  directly uses the API!  ',
          'This theorem uses the API through another definition.',
          'This theorem is linked through another definition or assumption.',
          'The theorem represented by this API.',
          'Direct use', 'Indirect use', 'Through another definition',
          'This theorem directly uses the API. The source contains $x^2$.')
for caption in captions:
 bad=copy.deepcopy(data);next(x for x in bad['interfaces'] if x['interface_id']=='A')['theorem_explanations']['p1t1']['text']=caption
 p=TEST/'bad-caption.json';p.write_text(json.dumps(bad))
 assert any('A/p1t1: retired generic relationship caption' in e for e in validate_census(p)),caption
good=copy.deepcopy(data)
next(x for x in good['interfaces'] if x['interface_id']=='A')['theorem_explanations']['p1t1']['text']='The statement makes direct use of the squared quantity $x^2$.'
p=TEST/'specific-explanation.json';p.write_text(json.dumps(good));assert not validate_census(p),validate_census(p)

# Reproduce the former late crash and boilerplate leak through the complete audit/HTML CLI.
for name,mutate,diagnostic in (
 ('null',lambda x:x.update(theorem_explanations=None),'(A): theorem_explanations must be an object'),
 ('caption',lambda x:x['theorem_explanations']['p1t1'].update(text=captions[0]),'A/p1t1: retired generic relationship caption'),
):
 bad=copy.deepcopy(data);mutate(next(x for x in bad['interfaces'] if x['interface_id']=='A'))
 bad_census=TEST/f'{name}-census.json';bad_census.write_text(json.dumps(bad))
 bad_audit=copy.deepcopy(bad)
 bad_audit.update(schema_version=audit['schema_version'],mathlib_revision=audit['mathlib_revision'],lean_version=audit['lean_version'],source_census_sha256=hashlib.sha256(bad_census.read_bytes()).hexdigest())
 for x,original in zip(bad_audit['interfaces'],audit['interfaces']):x['library_audit']=copy.deepcopy(original['library_audit'])
 assert any(diagnostic in e for e in validate_audit(bad_audit,bad_census))
 bad_input=TEST/f'{name}-audit.json';bad_input.write_text(json.dumps(bad_audit))
 protected=TEST/f'{name}-report.html';protected.write_text('LAST GOOD REPORT')
 result=subprocess.run([sys.executable,str(builder),str(bad_input),str(protected),'--census',str(bad_census)],capture_output=True,text=True)
 assert result.returncode!=0
 assert diagnostic in result.stdout+result.stderr and 'Traceback' not in result.stdout+result.stderr
 assert protected.read_text()=='LAST GOOD REPORT'
print('PASS: original list numbering, highlight preservation, explanation types, retired-caption rejection and failed-publication protection')

workspace.cleanup()

# Shared parser/highlighter regressions must run with the publication workflow.
subprocess.run([sys.executable, str(builder.with_name('test_math_rendering.py'))], check=True)
