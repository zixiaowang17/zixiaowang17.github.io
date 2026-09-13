"""Regression tests for source-preserving math layout and complete-atom highlighting."""
import re,xml.etree.ElementTree as ET
from build_report import render_statement,render_with_highlights
def highlighted(source,selector):
    return render_with_highlights(source,(selector,))
def has(source,selector):return 'class="symbol-highlight"' in highlighted(source,selector)
def annotations(source):
    return [e.text for m in re.findall(r'<math\b.*?</math>',source,re.S) for e in ET.fromstring(m).iter() if e.tag.rsplit('}',1)[-1]=='annotation']
# Exact scripts and accents are essential: a common base cannot license a match.
for source,selector in [
    (r'$x_i$',r'x'),(r'$x_i^2$',r'x_i'),(r'$\hat{x}_i$',r'\hat{x}'),
    (r'$\hat{x}_i$',r'x_i'),(r'$\bar{x}_i$',r'\hat{x}_i'),
    (r'$M_{20}$',r'M_2'),(r'$\mathbf{x}$',r'x'),(r'$\mathcal P_4$',r'\mathcal P'),
    (r'$A_{ij}$',r'i'),(r'$\sum_{i=1}^n x_i$',r'i=1')]:
    assert not has(source,selector),(source,selector)
for source,selector in [
    (r'$x_i+\hat{x}_i+x_i^2$',r'\hat{x}_i'),
    (r'$\frac{x_i}{y_j}$',r'x_i'),
    (r'$\sqrt{x_i+y_j}$',r'y_j'),
    (r'\[\sum_{i=1}^n x_i\]',r'\sum_{i=1}^n'),
    (r'$\sum_{i=1}^n x_i$',r'\sum_{i=1}^n'),
    (r'\[\max_{i\in I}n(i)\]',r'\max_{i\in I}n(i)'),
    (r'\[a+D\left(\epsilon,B,d\right)+z\]',r'D(\epsilon,B,d)'),
    (r'\[a+\operatorname{Unif}\left(-B_n,B_n\right)+z\]',r'\operatorname{Unif}(-B_n,B_n)')]:
    assert has(source,selector),(source,selector)
    assert annotations(highlighted(source,selector))==annotations(render_statement(source))
# Equation labels remain adjacent to their own formula even with no space before tag.
for source,label in [(r'\[x=y\tag{4.5}\]','4.5'),(r'$x=y\tag{4.7}$','4.7'),
                     (r'\[\begin{aligned}x&=y\\z&=w\end{aligned}\tag{9}\]','9')]:
    out=render_statement(source)
    assert '<math' in out and '('+label+')' in out and 'merror' not in out
assert 'equation-number' in render_statement(r'\[x=y\tag{4.5}\]')
for source in [r'$c_{\textup{conv}}$',r'$\mathfrak M^{\rm loc}$',r'$x\ \mbox{s.t.}\ y$']:
    assert '<math' in render_statement(source)
for source in [r'$x+\unknownCommand$',r'$\inP$',r'$\hat I_j=\begin{cases}$']:
    try:render_statement(source)
    except ValueError:pass
    else:raise AssertionError('Invalid source TeX accepted: '+source)
try:highlighted(r'$x$',r'\tag{9}')
except ValueError:pass
else:raise AssertionError('Empty mathematical selector accepted')
print('PASS: complete atoms, inline/display operators, delimiter sizing, labels and strict errors')

# Converted font/accent syntax must produce the same mathematical atom as
# explicit braces, while a different accent or font remains different.
from build_report import symbol_keys
for short,explicit in [
    (r'\widetilde\boldsymbol{\Theta}',r'\widetilde{\boldsymbol{\Theta}}'),
    (r'\widehat\boldsymbol{\Theta}_j',r'\widehat{\boldsymbol{\Theta}}_j'),
    (r'\mathop{\mathrm\mathrm{Cov}}',r'\mathop{\mathrm{Cov}}')]:
    assert symbol_keys((short,))==symbol_keys((explicit,)),(short,explicit)
assert symbol_keys((r'\widehat\boldsymbol{\Theta}',))!=symbol_keys((r'\widetilde\boldsymbol{\Theta}',))
assert symbol_keys((r'\widehat\boldsymbol{\Theta}',))!=symbol_keys((r'\widehat{\Theta}',))
print('PASS: converted font/accent notation preserves symbol identity')

# Aligned cells have implicit rows: match within one cell, never across cells.
for source,selector in [
    (r'\[\begin{aligned}R_0(g)&=0\\R_1(g)&=1\end{aligned}\]',r'R_0(g)'),
    (r'\[\begin{aligned}a&=d^\star(s,a)\\b&=0\end{aligned}\]',r'd^\star(s,a)'),
    (r'$D(\epsilon,\,B,\,d)$',r'D(\epsilon,B,d)')]:
    assert has(source,selector),(source,selector)
    assert annotations(highlighted(source,selector))==annotations(render_statement(source))
for source,selector in [
    (r'\[\begin{aligned}x&y\end{aligned}\]',r'xy'),
    (r'$\frac{x}{y}$',r'xy'),
    (r'$x_i^j$',r'ij')]:
    assert not has(source,selector),(source,selector)
# TeX blank lines within a display must not silently degrade to prose.
for source in ['\\[x+\n\ny\\]','$$x+\n\ny$$']:
    result=render_statement(source)
    assert '<math' in result and has(source,'x+y')
assert symbol_keys((r'\overset{\text{\tiny{i.i.d.}}}{\sim}',))==symbol_keys((r'\overset{\text{i.i.d.}}{\sim}',))
print('PASS: aligned-cell sequences, math spacing, blank display lines and text sizing')

# Pandoc inserts an invisible apply-function token depending on the preceding
# operator. Its absence does not change the spelled operator or its arguments.
assert has(r'\[\bigotimes_{j=1}^n\operatorname{Unif}(-a_j,b_j)\]',r'\operatorname{Unif}(-a_j,b_j)')
assert not has(r'$\operatorname{Uniform}(a,b)$',r'\operatorname{Unif}(a,b)')
print('PASS: operator application layout retains exact names and arguments')

# Natural-language phrases inside visible math text remain eligible, with no
# TeX-annotation-only matches and no expansion to surrounding words.
source=r'$h\text{ is symmetric, positive, bounded and decreasing on }[0,\infty)$'
result=render_with_highlights(source,(),('symmetric, positive, bounded and decreasing',))
assert 'class="symbol-highlight"' in result
assert annotations(result)==annotations(render_statement(source))
roots=[ET.fromstring(m) for m in re.findall(r'<math\b.*?</math>',result,re.S)]
marked=[e.text for root in roots for e in root.iter() if e.get('class')=='symbol-highlight']
assert marked==['symmetric, positive, bounded and decreasing']
assert 'class="symbol-highlight"' not in render_with_highlights(r'$\operatorname{LAMN}$',(),('operatorname',))
assert 'class="symbol-highlight"' not in render_with_highlights(r'$\mathcal{LAMN}$',(),('LAMN',))
print('PASS: exact prose phrases in visible math text; annotations and symbols unchanged')
source=r'$h\text{ is symmetric and positive on }I$'
out=render_with_highlights(source,(),('symmetric and positive',))
root=ET.fromstring(re.search(r'<math\b.*?</math>',out,re.S).group())
parts=[e.text or '' for e in root.iter() if e.tag.rsplit('}',1)[-1]=='mtext']
assert ''.join(parts).replace('\u00a0',' ')==' is symmetric and positive on '
assert parts[0].endswith('\u00a0') and parts[-1].startswith('\u00a0')
print('PASS: splitting formula prose preserves spaces at highlight boundaries')
