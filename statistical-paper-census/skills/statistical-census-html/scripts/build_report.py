#!/usr/bin/env python3
"""Generate an interface index and independent theorem reading pages from audited census data."""
from __future__ import annotations
import argparse
import hashlib
import html
import json
import os
import tempfile
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from functools import lru_cache
from collections import defaultdict
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit, urlunsplit

SKILL = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SKILL.parent / 'ranked-mathlib-audit' / 'scripts'))
from validate_audit import validate

ESC = lambda value: html.escape(str(value), quote=True)


class SafeMathHTML(HTMLParser):
    tags = set('p div span em strong b i ol ul li blockquote br sub sup code math semantics annotation mrow mi mn mo mtext mspace ms mfrac msqrt mroot mstyle merror mpadded mphantom mfenced menclose msub msup msubsup munder mover munderover mmultiscripts mprescripts none mtable mtr mtd maligngroup malignmark'.split())
    attrs = set('class xmlns display encoding mathvariant mathsize mathcolor stretchy fence separator form lspace rspace accent accentunder movablelimits largeop symmetric minsize maxsize scriptlevel displaystyle linethickness bevelled columnalign rowalign columnspacing rowspacing columnlines rowlines width height depth voffset notation rowspan columnspan'.split())
    void = {'br'}
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.parts=[]
    def allows_attribute(self, tag, name, value):
        if value is None:
            return False
        if name in self.attrs:
            return True
        # These attributes preserve source case labels and list offsets. Keep
        # them restricted to their list elements and HTML numbering values.
        if tag == 'ol' and name == 'type':
            return value in ('1', 'a', 'A', 'i', 'I')
        if (tag == 'ol' and name == 'start') or (tag == 'li' and name == 'value'):
            return re.fullmatch(r'-?[0-9]+', value) is not None
        return False
    def handle_starttag(self, tag, attrs):
        if tag in self.tags:
            safe=''.join(f' {k}="{ESC(v)}"' for k,v in attrs if self.allows_attribute(tag,k,v))
            self.parts.append(f'<{tag}{safe}>')
    def handle_endtag(self, tag):
        if tag in self.tags and tag not in self.void:
            self.parts.append(f'</{tag}>')
    def handle_startendtag(self, tag, attrs):
        self.handle_starttag(tag, attrs)
        self.handle_endtag(tag)
    def handle_data(self, data):
        self.parts.append(html.escape(data))


def normalize_math_layout(source):
    """Expand presentational macros only; archived source text stays untouched."""
    source = re.sub(r'\\mspace\{[+-]?[\d.]+mu\}', ' ', source)
    source = re.sub(r'\\mathbbm\b', lambda _: r'\mathbb', source)
    source = source.replace(r'\begin{array}[]', r'\begin{array}')
    source = re.sub(r'\\begin\{subarray\}\{[clr]\}(.*?)\\end\{subarray\}',
                    lambda m: r'\substack{' + m.group(1) + '}', source, flags=re.S)
    # Authors use repeated spacing to place a continuation on a printed page.
    source = re.sub(r'(?:\\qquad\s*){2,}', lambda _: r'\qquad ', source)
    # Upright text/font declarations are presentational, not paper-specific macros.
    source = re.sub(r'\\textup\b|\\mbox\b', lambda _: r'\text', source)
    # Font size inside a text annotation is layout only. Retain every text
    # character, including its grouping, rather than dropping the annotation.
    source = re.sub(r'\\text\{\\(?:tiny|scriptsize|footnotesize|small)\{([^{}]*)\}\}',
                    lambda m: r'\text{' + m.group(1) + '}', source)
    source = re.sub(r'\{\\rm\s+([^{}]*)\}', lambda m: r'\mathrm{' + m.group(1) + '}', source)
    # Brace an accent's font-macro operand. This is the same mathematical
    # atom as the explicit braced form, not a repaired symbol or new macro.
    source = re.sub(r'\\(hat|widehat|tilde|widetilde|bar|overline|vec|dot|ddot)\s*(\\(?:boldsymbol|mathbf|mathcal|mathbb|mathrm)\{[^{}]*\})',
                    lambda m: '\\' + m.group(1) + '{' + m.group(2) + '}', source)
    # Repeated identical font wrappers occur in converted source macros.
    source = re.sub(r'\\(mathrm|mathbf|mathcal|mathbb)\s*\\\1(?=\{)',
                    lambda m: '\\' + m.group(1), source)
    # Pandoc's TeX reader cannot consistently consume a trailing equation tag.
    # Move a single terminal tag beside its own math span, preserving its label.
    # Leave internal/multiple row tags to the strict renderer rather than misplacing them.
    math_spans = re.compile(r'(?<!\\)\\\[(.*?)\\\]|(?<!\\)\$\$(.*?)\$\$|(?<!\\)\$(?!\$)(.*?)(?<!\\)\$', re.S)
    def equation_tag(match):
        body = next(v for v in match.groups() if v is not None)
        # A blank source line is not a paragraph break inside mathematics.
        # Pandoc otherwise silently emits raw formula text instead of MathML.
        body = re.sub(r'\n[ \t]*\n', '\n', body)
        original = (r'\[' + body + r'\]' if match.group(1) is not None else
                    '$$' + body + '$$' if match.group(2) is not None else '$' + body + '$')
        tag = re.search(r'\\tag\{([A-Za-z0-9]+(?:[.\-][A-Za-z0-9]+)*)\}\s*([.,]?)\s*$', body)
        if not tag or len(re.findall(r'\\tag\b', body)) != 1:
            return original
        # A standalone tag is not a mathematical selector.
        if not body[:tag.start()].strip():
            return match.group()
        formula = body[:tag.start()] + tag.group(2)
        if match.group(1) is not None:
            return r'\[' + formula + r'\] (' + tag.group(1) + ')'
        if match.group(2) is not None:
            return '$$' + formula + '$$ (' + tag.group(1) + ')'
        return '$' + formula + '$ (' + tag.group(1) + ')'
    return math_spans.sub(equation_tag, source)


@lru_cache(maxsize=None)
def render_statement(source):
    source = normalize_math_layout(source)
    result=subprocess.run(['pandoc','--from=markdown-raw_html-raw_tex+tex_math_dollars+tex_math_single_backslash',
                           '--to=html5','--mathml','--wrap=none'],input=source,text=True,capture_output=True)
    if result.returncode or 'Could not convert TeX math' in result.stderr:
        raise ValueError('Statement math could not be rendered: '+result.stderr.strip())
    cleaner=SafeMathHTML();cleaner.feed(result.stdout);cleaner.close()
    rendered = ''.join(cleaner.parts)
    # Keep printed equation labels beside their own display without touching the formula.
    return re.sub(r'<p>(<math display="block"(?:(?!</math>).)*</math>)\s*\(([0-9]+(?:\.[0-9]+)*)\)</p>',
                  lambda m: '<div class="equation">' + m.group(1) + '<span class="equation-number">(' + m.group(2) + ')</span></div>',
                  rendered, flags=re.S)


def math_sequence(keys):
    """Flatten redundant row grouping only; scripted atoms remain indivisible."""
    flattened = []
    for key in keys:
        if key[0] == 'mspace' or (key[0] == 'mo' and key[2] == '\u2061'):
            continue
        if key[0] == 'mrow' and not key[1] and not key[2]:
            flattened.extend(math_sequence(key[3]))
        else:
            flattened.append(key)
    return tuple(flattened)


def math_key(element):
    """Retain notation identity while ignoring spacing and delimiter sizing."""
    tag = element.tag.rsplit('}', 1)[-1]
    # These change placement/size, not the mathematical token or its scripts.
    layout = {'class', 'stretchy', 'form', 'lspace', 'rspace', 'minsize', 'maxsize',
              'symmetric', 'displaystyle', 'scriptlevel'}
    attrs = tuple(sorted((k, v) for k, v in element.attrib.items() if k not in layout))
    children = tuple(math_key(c) for c in element)
    if tag == 'mrow' or (tag == 'mstyle' and not attrs):
        children = math_sequence(children)
        if len(children) == 1 and not attrs:
            return children[0]
        tag = 'mrow'
    return (tag, attrs, (element.text or '').strip(), children)


@lru_cache(maxsize=None)
def symbol_keys(symbols):
    keys = set()
    for symbol in symbols:
        # Operators put limits below/above in display math and beside in inline
        # math. Both are exact renderings of the same stored selector.
        for source in ('$' + symbol + '$', r'\[' + symbol + r'\]'):
            rendered = render_statement(source)
            match = re.search(r'<math\b.*?</math>', rendered, re.S)
            if not match:
                raise ValueError('Highlight symbol must render as mathematics')
            root = ET.fromstring(match.group())
            semantics = next(e for e in root if e.tag.rsplit('}', 1)[-1] == 'semantics')
            key = math_key(semantics[0])
            if key == ('mrow', (), '', ()):
                raise ValueError('Highlight symbol has no visible mathematical content: ' + symbol)
            keys.add(key)
    return keys


class PhraseHighlighter(SafeMathHTML):
    """Highlight exact phrases in prose, keeping MathML and TeX annotations intact."""
    def __init__(self, phrases):
        super().__init__()
        self.math_depth = 0
        self.pattern = re.compile(r'(?<!\w)(?:' + '|'.join(re.escape(p) for p in sorted(set(phrases), key=len, reverse=True)) + r')(?!\w)')
    def handle_starttag(self, tag, attrs):
        if tag == 'math':
            self.math_depth += 1
        super().handle_starttag(tag, attrs)
    def handle_endtag(self, tag):
        super().handle_endtag(tag)
        if tag == 'math':
            self.math_depth -= 1
    def handle_data(self, data):
        if self.math_depth:
            super().handle_data(data)
            return
        last = 0
        for match in self.pattern.finditer(data):
            self.parts.append(ESC(data[last:match.start()]))
            self.parts.append('<mark class="symbol-highlight">' + ESC(match.group()) + '</mark>')
            last = match.end()
        self.parts.append(ESC(data[last:]))


def highlight_prose(rendered, phrases):
    if not phrases:
        return rendered
    parser = PhraseHighlighter(phrases)
    parser.feed(rendered)
    parser.close()
    rendered = ''.join(parser.parts)
    # Words in a TeX text annotation are visible prose too. Split only mtext
    # nodes into exact phrase spans; never touch TeX source annotations or mi.
    def math_text(match):
        root = ET.fromstring(match.group())
        changed = False
        for parent in list(root.iter()):
            for element in list(parent):
                if element.tag.rsplit('}', 1)[-1] != 'mtext' or len(element):
                    continue
                text = element.text or ''
                matches = list(parser.pattern.finditer(text))
                if not matches:
                    continue
                ns = element.tag.rsplit('}', 1)[0] + '}' if '}' in element.tag else ''
                row = ET.Element(ns + 'mrow')
                end = 0
                for found in matches:
                    if found.start() > end:
                        plain = ET.SubElement(row, element.tag, dict(element.attrib))
                        plain.text = text[end:found.start()]
                    marked = ET.SubElement(row, element.tag, dict(element.attrib))
                    marked.set('class', 'symbol-highlight')
                    marked.text = found.group()
                    end = found.end()
                if end < len(text):
                    plain = ET.SubElement(row, element.tag, dict(element.attrib))
                    plain.text = text[end:]
                # MathML trims edge spaces on each mtext. Preserve word
                # separation when the original text is split for highlighting.
                for part in row:
                    part.text = re.sub(r'^ +| +$', lambda m: '\u00a0' * len(m.group()), part.text or '')
                row.tail = element.tail
                position = list(parent).index(element)
                parent.remove(element)
                parent.insert(position, row)
                changed = True
        if not changed:
            return match.group()
        ET.register_namespace('', 'http://www.w3.org/1998/Math/MathML')
        return ET.tostring(root, encoding='unicode', short_empty_elements=False)
    return re.sub(r'<math\b.*?</math>', math_text, rendered, flags=re.S)


def render_with_highlights(source, symbols=(), phrases=()):
    rendered = render_statement(source)
    if not symbols:
        return highlight_prose(rendered, phrases)
    keys = symbol_keys(tuple(symbols))
    sequences = sorted((key[3] for key in keys if key[0] == 'mrow' and len(key[3]) > 1), key=len, reverse=True)
    max_sequence_length = max((len(seq) for seq in sequences), default=0)
    def highlight(match):
        root = ET.fromstring(match.group())
        changed = False
        def visit(element):
            nonlocal changed
            tag = element.tag.rsplit('}', 1)[-1]
            if tag == 'annotation':
                return
            if tag not in ('math', 'semantics') and math_key(element) in keys:
                element.set('class', 'symbol-highlight')
                changed = True
                return
            # Never match x inside x_i, x_i inside x_i^2, or a base
            # beneath a different accent. Selectors must identify the full atom.
            if tag in {'msub', 'msup', 'msubsup', 'munder', 'mover',
                       'munderover', 'mmultiscripts'}:
                return
            children = list(element)
            i = 0
            while i < len(children):
                span_length = 0
                # A table cell is an implicit mathematical row. Never join
                # tokens across cells, rows, fraction slots or script slots.
                if tag in {'mrow', 'mtd'}:
                    for stop in range(i + 1, len(children) + 1):
                        candidate = math_sequence(tuple(math_key(c) for c in children[i:stop]))
                        if candidate in sequences:
                            span_length = stop - i
                        if len(candidate) >= max_sequence_length:
                            break
                if span_length:
                    matched = children[i:i+span_length]
                    namespace = element.tag.rsplit('}', 1)[0] + '}' if '}' in element.tag else ''
                    group = ET.Element(namespace + 'mrow', {'class': 'symbol-highlight'})
                    position = list(element).index(matched[0])
                    group.tail = matched[-1].tail
                    matched[-1].tail = None
                    for child in matched:
                        element.remove(child)
                        group.append(child)
                    element.insert(position, group)
                    changed = True
                    i += span_length
                else:
                    visit(children[i])
                    i += 1
        visit(root)
        if not changed:
            return match.group()
        ET.register_namespace('', 'http://www.w3.org/1998/Math/MathML')
        return ET.tostring(root, encoding='unicode', short_empty_elements=False)
    return highlight_prose(re.sub(r'<math\b.*?</math>', highlight, rendered, flags=re.S), phrases)


def verify_highlights(data):
    """Every source definition must visibly highlight; every selector must actually match."""
    claims = {c['claim_id']: c for c in data['claims']}
    for interface in data['interfaces']:
        for member in interface['members']:
            where = f"{interface['interface_id']}/{member['paper_id']}/{member['local_id']}"
            symbols = tuple(member.get('highlight_symbols', []))
            phrases = tuple(member.get('highlight_phrases', []))
            if not symbols and not phrases:
                raise ValueError(where + ': source highlight annotations required')
            definition = render_with_highlights(member['statement_original'], symbols, phrases)
            label = highlight_prose(ESC(member['local_label']), phrases)
            if 'class="symbol-highlight"' not in definition + label:
                raise ValueError(where + ': no visible highlight matches the original definition or its source label')
            sources = [member['statement_original']] + [claims[rec['claim_id']]['statement_original']
                       for rec in interface['related_theorems'] if rec['paper_id'] == member['paper_id']]
            for symbol in symbols:
                if not any('class="symbol-highlight"' in render_with_highlights(text, (symbol,)) for text in sources):
                    raise ValueError(where + ': mathematical highlight did not match: ' + symbol)
            for phrase in phrases:
                if not any('class="symbol-highlight"' in render_with_highlights(text, (), (phrase,)) for text in sources) and 'class="symbol-highlight"' not in highlight_prose(ESC(member['local_label']), (phrase,)):
                    raise ValueError(where + ': prose highlight did not match: ' + phrase)


def source_pdf_url(paper):
    url = paper.get('source_url', '')
    try:
        parsed = urlsplit(url)
        if parsed.scheme not in ('https', 'http') or not parsed.hostname or parsed.username or parsed.password:
            raise ValueError('invalid source URL')
    except (ValueError, TypeError):
        raise ValueError(paper.get('paper_id', '?') + ': original PDF source_url required; use the inspected version, not a guessed URL') from None
    return urlunsplit(parsed)


def filename(kind, identifier):
    return f'{kind}-{hashlib.sha256(identifier.encode()).hexdigest()[:16]}.html'


def theorem_anchor(claim_id):
    return 'theorem-' + hashlib.sha256(claim_id.encode()).hexdigest()[:16]


def variant_anchor(member):
    key = member['paper_id'] + ':' + member['local_id']
    return 'variant-' + hashlib.sha256(key.encode()).hexdigest()[:16]


WORK_STATUS_LABELS = {'use_mathlib': 'Use mathlib', 'small_adaptation': 'Small adaptation', 'new_infrastructure': 'New infrastructure', 'needs_work': 'Needs more work'}


def work_status_html(audit):
    status = audit.get('work_status')
    if status is None:
        return ''
    return f'<span class="work-status" data-work-status="{ESC(status)}">{WORK_STATUS_LABELS[status]}</span>'


def build_search_index(data, folder):
    """Expose existing ranks and reverse the audited, paper-local theorem index."""
    papers = {p['paper_id']: p for p in data['papers']}
    claims = {c['claim_id']: c for c in data['claims']}
    claims_by_paper = defaultdict(list)
    for c in data['claims']: claims_by_paper[c['paper_id']].append(c)
    requirements = {cid: [] for cid in claims}
    interfaces = []
    for x in sorted(data['interfaces'], key=lambda x: (x['rank_group'], x['semantic_rank'])):
        records = x['related_theorems']
        item = dict(route='interface:' + x['interface_id'], name=x['name'], kind=x['lean_role'],
                    rank=x['semantic_rank'], rank_group=x['rank_group'], gap=x['library_audit']['gap'],
                    direct_paper_count=x['central_claim_paper_count'], direct_theorem_count=x['central_claim_use_count'],
                    theorem_count=len(records), paper_count=len({r['paper_id'] for r in records}),
                    url=f'{folder}/{filename("interface", x["interface_id"])}',
                    search=' '.join([x['name'], *(m['local_label'] for m in x['members']),
                                     *(m['statement_original'] for m in x['members']),
                                     *(n['text'] for n in x.get('theorem_explanations', {}).values()),
                                     *(claims[r['claim_id']]['label'] for r in records),
                                     *(papers[r['paper_id']]['title'] for r in records)]))
        if 'work_status' in x['library_audit']:
            item['work_status'] = x['library_audit']['work_status']
        interfaces.append(item)
        for relation in records:
            if relation['relation'] != 'target':
                requirements[relation['claim_id']].append(dict(route=item['route'], relation=relation['relation']))
    by_route = {a["route"]: a for a in interfaces}
    def totals(apis):
        return {'api_count': len({a['route'] for a in apis})}
    result = dict(interfaces=interfaces, papers=[], theorems=[])
    for p in data['papers']:
        records = sorted(claims_by_paper[p['paper_id']], key=lambda c: c['source_order'])
        url = f'{folder}/{filename("paper", p["paper_id"])}'
        theorems = []
        for c in records:
            apis = requirements[c['claim_id']]
            t = dict(route='theorem:' + c['claim_id'], name=c['label'], paper_route='paper:' + p['paper_id'],
                     url=url + '#' + theorem_anchor(c['claim_id']), requirements=apis,
                     search=' '.join([c['label'], c['statement_original'], *(by_route[a['route']]['name'] for a in apis)]), **totals(apis))
            theorems.append(t)
        result['theorems'].extend(theorems)
        result['papers'].append(dict(route='paper:' + p['paper_id'], name=p['title'], url=url,
                                    theorem_count=len(records), theorems=theorems,
                                    search=p['title'] + ' ' + p['paper_id'],
                                    **totals(a for t in theorems for a in t['requirements'])))
    return result


def generate(data, output, title='Search the census'):
    if not shutil.which('pandoc'):
        raise ValueError('Pandoc is required for local MathML rendering; install it before generation.')
    for paper in data['papers']:
        source_pdf_url(paper)
    verify_highlights(data)
    assets=SKILL/'assets'
    css=(assets/'report.css').read_text()
    page_template=(assets/'reading-page.html').read_text()
    fingerprint = hashlib.sha256(json.dumps(data, ensure_ascii=False, sort_keys=True).encode() + Path(__file__).read_bytes() + b''.join(p.read_bytes() for p in sorted(assets.iterdir()) if p.is_file())).hexdigest()[:20]
    folder=output.stem+'-pages/'+fingerprint
    papers={p['paper_id']:p for p in data['papers']}
    paper_order={p['paper_id']:i for i,p in enumerate(data['papers'])}
    claims={c['claim_id']:c for c in data['claims']}
    claims_by_paper=defaultdict(list)
    for c in data['claims']: claims_by_paper[c['paper_id']].append(c)
    index=build_search_index(data,folder)
    theorem_index={t['route']:t for t in index['theorems']}
    api_index={a['route']:a for a in index['interfaces']}
    files={}
    def reading_page(name,content):
        return page_template.replace('__CSS__',css).replace('__TITLE__',ESC(name)).replace('__CONTENT__',content)
    def needs(record):
        return f'{record["api_count"]} required {"API" if record["api_count"]==1 else "APIs"}'
    def requirement_list(c):
        t=theorem_index['theorem:'+c['claim_id']]
        if not t['requirements']:
            return '<p class="dependency-note">No API dependencies have been recorded for this theorem.</p>'
        rows=[]
        for ref in sorted(t['requirements'],key=lambda a:(api_index[a['route']]['rank_group'],api_index[a['route']]['rank'])):
            a = dict(api_index[ref['route']], relation=ref['relation'])
            name=Path(a['url']).name
            rows.append(f'<li><div class="requirement-heading"><a href="{ESC(name)}" data-route="{ESC(a["route"])}">{ESC(a["name"])}</a>{work_status_html(a)}</div><p>{ESC(a["gap"])}</p></li>')
        return f'<details class="requirements" id="requirements-{theorem_anchor(c["claim_id"])}"><summary>APIs required by {ESC(c["label"])} <span>{needs(t)}</span></summary><ul>{"".join(rows)}</ul></details>'
    def theorem(c, show_requirements=False, connection=None, member=None, symbols=(), phrases=(), heading_level=3):
        explanation=''
        if connection:
            link=f'<a href="#{variant_anchor(member)}">{ESC(member["source_heading"])}</a>' if member else ''
            explanation=f'<div class="connection">{render_with_highlights(connection["text"],symbols,phrases)}{link}</div>'
        t=theorem_index['theorem:'+c['claim_id']]
        if show_requirements and t['requirements']:
            explanation+=f'<p class="theorem-needs"><a href="#requirements-{theorem_anchor(c["claim_id"])}">{needs(t)}</a></p>'
        extra=requirement_list(c) if show_requirements else ''
        return f'<article class="theorem" id="{theorem_anchor(c["claim_id"])}"><h{heading_level}>{ESC(c["label"])}</h{heading_level}>{explanation}<div class="statement">{render_with_highlights(c["statement_original"],symbols,phrases)}</div>{extra}</article>'
    def grouped(records, interface):
        result=[]
        for pid in sorted({m['paper_id'] for m in interface['members']} | {r['paper_id'] for r in records}, key=paper_order.get):
            members=[m for m in interface['members'] if m['paper_id']==pid]
            symbols=tuple(dict.fromkeys(symbol for m in members for symbol in m.get('highlight_symbols', [])))
            phrases=tuple(dict.fromkeys(phrase for m in members for phrase in m.get('highlight_phrases', [])))
            result.append(f'<section class="paper-group" data-paper-id="{ESC(pid)}"><h2 class="paper-title"><a href="{ESC(source_pdf_url(papers[pid]))}" target="_blank" rel="noopener">{ESC(papers[pid]["title"])}</a></h2>')
            for member in members:
                heading=highlight_prose(ESC(member['source_heading']),member.get('highlight_phrases',[]))
                source_label='' if member['source_heading']==member['local_label'] else f'<p class="definition-source">{highlight_prose(ESC(member["local_label"]),member.get("highlight_phrases",[]))}</p>'
                result.append(f'<section class="original-definition" data-source-kind="{ESC(member["source_kind"])}" id="{variant_anchor(member)}"><h3>{heading}</h3>{source_label}<div class="statement">{render_with_highlights(member["statement_original"],tuple(member.get("highlight_symbols",[])),tuple(member.get("highlight_phrases",[])))}</div>')
                if member.get('variant_note'):
                    result.append(f'<p class="definition-note">{ESC(member["variant_note"])}</p>')
                result.append('</section>')
            local_records=sorted((r for r in records if r['paper_id']==pid),key=lambda r:claims[r['claim_id']]['source_order'])
            if local_records:
                result.append('<section class="theorem-group"><h3 class="theorems-heading">Theorems</h3>')
            for record in local_records:
                c=claims[record['claim_id']]
                connection=interface['theorem_explanations'][c['claim_id']]
                member=next((m for m in members if record['via_local_ids'] and m['local_id']==record['via_local_ids'][-1]),None)
                result.append(theorem(c,connection=connection,member=member,symbols=symbols,phrases=phrases,heading_level=4))
            if local_records:
                result.append('</section>')
            if not local_records:
                result.append('<p class="empty">No related theorems are recorded for this source statement.</p>')
            result.append('</section>')
        return ''.join(result)
    for x in data['interfaces']:
        records=x['related_theorems'];audit=x['library_audit']
        content=f'<h1>{ESC(x["name"])}</h1><p class="summary">{len(records)} related theorem {"statement" if len(records)==1 else "statements"}</p>'
        if audit.get('work_status'):
            content+=f'<div class="work-audit">{work_status_html(audit)}<p>{ESC(audit["work_status_reason"])}</p></div>'
        content+=grouped(records,x)
        content+='<section class="secondary"><h2>Related mathlib</h2><ul class="library-links">'
        for declaration in audit['related_declarations']:
            content+=f'<li><a href="{ESC(declaration["url"])}" target="_blank" rel="noopener">{ESC(declaration["name"])}</a><small>{ESC(declaration["provides"])}</small></li>'
        content+='</ul>'
        if not audit['related_declarations']:
            content+=f'<p>{ESC(audit["no_related_reason"])}</p>'
        content+=f'<p class="gap">{ESC(audit["gap"])}</p></section>'
        name=filename('interface',x['interface_id']);files[f'{folder}/{name}']=reading_page(x['name'],content)
    for p in data['papers']:
        records=sorted(claims_by_paper[p['paper_id']],key=lambda c:c['source_order'])
        content=f'<h1><a href="{ESC(source_pdf_url(p))}" target="_blank" rel="noopener">{ESC(p["title"])}</a></h1><p class="summary">{len(records)} Theorems in the main text; appendices excluded</p>'
        if records:
            content+='<nav class="theorem-index" aria-label="Theorems in this paper">'
            for c in records:
                t=theorem_index['theorem:'+c['claim_id']]
                label=needs(t) if t['requirements'] else 'No linked APIs'
                content+=f'<a href="#{theorem_anchor(c["claim_id"])}"><span>{ESC(c["label"])}</span><small>{label}</small></a>'
            content+='</nav>'
        content+=''.join(theorem(c,show_requirements=True) for c in records) or '<p>No Theorems occur in the main text.</p>'
        name=filename('paper',p['paper_id']);files[f'{folder}/{name}']=reading_page(p['title'],content)
    scope=f'{len(data["papers"])} papers. {len(data["claims"])} Theorems from the main text; appendices excluded.'
    # Theorems are nested under papers; avoid duplicating their text in the embedded search payload.
    index.pop('theorems')
    payload=json.dumps(index,ensure_ascii=False,separators=(',',':')).replace('<','\\u003c')
    files[output.name]=(assets/'report.html').read_text().replace('__TITLE__',ESC(title)).replace('__CSS__',css).replace('__SCOPE__',ESC(scope)).replace('__DATA__',payload).replace('__SCRIPT__',(assets/'report.js').read_text())
    files[f'{folder}/manifest.json']=json.dumps({'pages':sorted(Path(n).name for n in files if n.startswith(folder+'/'))},indent=2)+'\n'
    return files


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('input',type=Path);parser.add_argument('output',type=Path)
    parser.add_argument('--census',type=Path,required=True);parser.add_argument('--check',action='store_true')
    parser.add_argument('--title',default='Search the census',help='Report heading and browser-tab title.')
    args=parser.parse_args()
    try:
        data=json.loads(args.input.read_text());errors=validate(data,args.census)
        if errors:
            raise ValueError('\n'.join(errors))
        files=generate(data,args.output,args.title)
        if args.check:
            return int(any(not (args.output.parent/n).is_file() or (args.output.parent/n).read_text()!=s for n,s in files.items()))
        args.output.parent.mkdir(parents=True,exist_ok=True)
        folder = next(n.rsplit('/', 1)[0] for n in files if n.endswith('/manifest.json'))
        target_dir = args.output.parent/folder
        target_dir.parent.mkdir(parents=True, exist_ok=True)
        # Readers are immutable. The index is the single atomic publication point.
        staging = Path(tempfile.mkdtemp(prefix='.generation-', dir=target_dir.parent))
        temporary = None
        try:
            for name, content in files.items():
                if name.startswith(folder+'/'):
                    with (staging/Path(name).name).open('w') as stream:
                        stream.write(content); stream.flush(); os.fsync(stream.fileno())
            if target_dir.exists():
                if any((target_dir/p.name).read_bytes() != p.read_bytes() for p in staging.iterdir()):
                    raise ValueError('Existing immutable report generation differs')
            else:
                os.replace(staging, target_dir)
            fd, name = tempfile.mkstemp(prefix='.'+args.output.name+'-', dir=args.output.parent)
            temporary = Path(name)
            with os.fdopen(fd, 'w') as stream:
                stream.write(files[args.output.name]); stream.flush(); os.fsync(stream.fileno())
            os.replace(temporary, args.output)
        finally:
            if staging.exists(): shutil.rmtree(staging)
            if temporary is not None: temporary.unlink(missing_ok=True)
        current=json.loads(files[folder+'/manifest.json'])['pages']
        print(f'Wrote {args.output} and {len(current)} reading pages')
        return 0
    except (OSError,ValueError) as error:
        print('ERROR:',error,file=sys.stderr)
        return 1

if __name__=='__main__':
    raise SystemExit(main())
