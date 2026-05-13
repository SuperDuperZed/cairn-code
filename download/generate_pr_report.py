import json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, PageBreak, KeepTogether
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

pdfmetrics.registerFont(TTFont('LS', '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'))
pdfmetrics.registerFont(TTFont('LSB', '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'))
pdfmetrics.registerFont(TTFont('LSI', '/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf'))
pdfmetrics.registerFont(TTFont('LAS', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'))
pdfmetrics.registerFont(TTFont('LASB', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'))
registerFontFamily('LS', normal='LS', bold='LSB', italic='LSI')
registerFontFamily('LAS', normal='LAS', bold='LASB')

ACCENT = colors.HexColor('#5d39c8')
TP = colors.HexColor('#1f2022')
TM = colors.HexColor('#73787f')

ct = ParagraphStyle('ct', fontName='LASB', fontSize=28, leading=34, alignment=TA_CENTER, spaceAfter=6, textColor=TP)
cs = ParagraphStyle('cs', fontName='LSI', fontSize=14, leading=18, alignment=TA_CENTER, textColor=TM)
cd = ParagraphStyle('cd', fontName='LAS', fontSize=12, leading=16, alignment=TA_CENTER, textColor=ACCENT)
h1 = ParagraphStyle('h1', fontName='LASB', fontSize=18, leading=22, spaceBefore=14, spaceAfter=8, textColor=TP)
h2 = ParagraphStyle('h2', fontName='LASB', fontSize=13, leading=16, spaceBefore=10, spaceAfter=5, textColor=ACCENT)
bd = ParagraphStyle('bd', fontName='LS', fontSize=10, leading=14, spaceAfter=4, alignment=TA_JUSTIFY)
mt = ParagraphStyle('mt', fontName='LSI', fontSize=9, leading=12, textColor=TM, spaceAfter=2)
sm = ParagraphStyle('sm', fontName='LAS', fontSize=8.5, leading=11, textColor=TM)
ft = ParagraphStyle('ft', fontName='LAS', fontSize=8, leading=10, textColor=TM, alignment=TA_CENTER)

def fd(iso):
    if not iso: return 'N/A'
    try:
        dt = datetime.fromisoformat(iso.replace('Z','+00:00'))
        return dt.strftime('%B %d, %Y')
    except: return iso[:10]

def ci_b(s):
    if s == 'success': return '<font color="#16a34a">Passed</font>'
    elif s == 'failure': return '<font color="#dc2626">Failed</font>'
    return '<font color="#d97706">Pending</font>'

def rv_b(r):
    if not r: return 'No reviews'
    st = r.split(' by ')[0] if ' by ' in r else r
    wh = r.split(' by ')[1] if ' by ' in r else ''
    m = {'APPROVED':('Approved','#16a34a'),'CHANGES_REQUESTED':('Changes Requested','#dc2626'),'COMMENTED':('Commented','#73787f')}
    lb,cl = m.get(st,(st,'#73787f'))
    t = f'<font color="{cl}">{lb}</font>'
    if wh: t += f' <font color="#73787f">by {wh}</font>'
    return t

prs = [
  {"repo":"google-gemini/gemini-cli","title":"feat(cli): show acknowledgment when user steering hint is processed","url":"https://github.com/google-gemini/gemini-cli/pull/26498","created":"2026-05-05T11:03:16Z","updated":"2026-05-13T02:22:30Z","draft":False,"additions":190,"deletions":6,"changed_files":4,"review":"COMMENTED by gemini-code-assist[bot]","ci":"pending","labels":["priority/p2","area/agent","status/pr-nudge-sent"],"body":"When a user submits a steering hint mid-turn, the CLI silently splices the hint into the conversation with no visible feedback. This PR adds an acknowledgment message."},
  {"repo":"google-gemini/gemini-cli","title":"fix(build): detect Bun runtime in build scripts to avoid hardcoded npm","url":"https://github.com/google-gemini/gemini-cli/pull/26280","created":"2026-04-30T19:29:27Z","updated":"2026-05-08T02:21:58Z","draft":False,"additions":44,"deletions":8,"changed_files":3,"review":"COMMENTED by gemini-code-assist[bot]","ci":"pending","labels":["priority/p2","area/platform","status/pr-nudge-sent"],"body":"Build scripts invoke npm unconditionally, breaking on Bun-only systems. Detects Bun runtime and uses it instead."},
  {"repo":"microsoft/node-pty","title":"fix: swallow resize() errors after PTY exit on Windows and Unix","url":"https://github.com/microsoft/node-pty/pull/901","created":"2026-03-13T15:11:41Z","updated":"2026-03-13T15:21:49Z","draft":False,"additions":8,"deletions":2,"changed_files":2,"review":"","ci":"pending","labels":[],"body":"Silently ignore resize() calls after PTY process exits, catching EBADF errors on Unix and preventing crashes on Windows."},
  {"repo":"QwenLM/qwen-code","title":"feat: add bun runtime support","url":"https://github.com/QwenLM/qwen-code/pull/2838","created":"2026-04-02T20:40:44Z","updated":"2026-04-24T23:31:33Z","draft":False,"additions":3683,"deletions":126,"changed_files":9,"review":"CHANGES_REQUESTED by wenshao","ci":"pending","labels":[],"body":"Add Bun runtime support for 3-5x faster startup, lower memory usage, and native TypeScript support."},
  {"repo":"clockworklabs/SpacetimeDB","title":"feat(bindings-cpp-ffi): add Rust FFI crate for WASM modules","url":"https://github.com/clockworklabs/SpacetimeDB/pull/4773","created":"2026-04-10T04:22:37Z","updated":"2026-04-28T05:33:51Z","draft":False,"additions":2417,"deletions":0,"changed_files":6,"review":"COMMENTED by chatgpt-codex-connector[bot]","ci":"success","labels":[],"body":"New Rust crate for type registration and FFI dispatch for SpacetimeDB WASM modules, re-implementing C++ bindings logic."},
  {"repo":"charmbracelet/glow","title":"fix: ensure closing fence in WrapCodeBlock is on its own line","url":"https://github.com/charmbracelet/glow/pull/937","created":"2026-04-26T19:33:29Z","updated":"2026-04-26T19:33:29Z","draft":False,"additions":3,"deletions":0,"changed_files":1,"review":"","ci":"pending","labels":[],"body":"WrapCodeBlock glued the closing fence onto the last line. When input lacked a trailing newline, Markdown renderers never saw the closing fence."},
  {"repo":"anomalyco/opencode","title":"fix(tui): bind home/end to line start/end in input","url":"https://github.com/anomalyco/opencode/pull/25355","created":"2026-05-01T20:10:08Z","updated":"2026-05-11T01:39:11Z","draft":False,"additions":192,"deletions":192,"changed_files":20,"review":"","ci":"pending","labels":[],"body":"Closes #14899. Home/End keys not bound in input field. Adds bindings to the keybinds source-of-truth file."},
  {"repo":"euxaristia/adapt","title":"Add shell completion for zsh and bash","url":"https://github.com/euxaristia/adapt/pull/1","created":"2026-05-09T00:27:04Z","updated":"2026-05-12T22:16:24Z","draft":False,"additions":239,"deletions":0,"changed_files":3,"review":"COMMENTED by gemini-code-assist[bot]","ci":"pending","labels":[],"body":"Add zsh and bash completions for adapt install and adapt remove commands."},
  {"repo":"euxaristia/gemini-cli","title":"fix(build): detect Bun runtime in build scripts","url":"https://github.com/euxaristia/gemini-cli/pull/4","created":"2026-05-12T20:35:46Z","updated":"2026-05-12T20:38:20Z","draft":False,"additions":44,"deletions":8,"changed_files":3,"review":"COMMENTED by gemini-code-assist[bot]","ci":"pending","labels":[],"body":"Detects Bun runtime and uses it instead of npm/node in build scripts."},
  {"repo":"euxaristia/gemini-cli","title":"fix(core): make shell tool work under Bun","url":"https://github.com/euxaristia/gemini-cli/pull/3","created":"2026-05-12T20:05:43Z","updated":"2026-05-12T20:05:50Z","draft":False,"additions":39,"deletions":5,"changed_files":3,"review":"","ci":"pending","labels":[],"body":"Fixes ioctl EBADF crash and empty command results when running shell tool under Bun."},
  {"repo":"euxaristia/gitee-cli","title":"feat: implicitly use current repo and branch context for pr commands","url":"https://github.com/euxaristia/gitee-cli/pull/2","created":"2026-05-09T06:29:41Z","updated":"2026-05-09T06:31:48Z","draft":False,"additions":116,"deletions":13,"changed_files":3,"review":"COMMENTED by gemini-code-assist[bot]","ci":"pending","labels":[],"body":"Infers repo context from local git remote, bringing parity with gh behavior."},
  {"repo":"euxaristia/colt","title":"feat: mouse click moves cursor; drag enters Visual mode","url":"https://github.com/euxaristia/colt/pull/4","created":"2026-05-07T05:37:02Z","updated":"2026-05-09T00:46:47Z","draft":False,"additions":138,"deletions":4,"changed_files":2,"review":"COMMENTED by gemini-code-assist[bot]","ci":"pending","labels":[],"body":"Switches SGR mouse mode to press/release/motion. Left-click moves cursor, drag enters Visual mode."},
  {"repo":"euxaristia/colt","title":"feat(substitute): add regex support to :s/ command","url":"https://github.com/euxaristia/colt/pull/1","created":"2026-04-14T06:41:21Z","updated":"2026-05-09T00:44:56Z","draft":False,"additions":407,"deletions":11,"changed_files":5,"review":"COMMENTED by gemini-code-assist[bot]","ci":"pending","labels":[],"body":"Pure-Pony backtracking regex engine (~230 LOC) wired into :s/, :%s/, and :.,$s/ commands."},
  {"repo":"euxaristia/colt","title":"fix(editor): typing/pasting ( now actually inserts the character","url":"https://github.com/euxaristia/colt/pull/5","created":"2026-05-09T00:01:29Z","updated":"2026-05-09T00:41:56Z","draft":False,"additions":408,"deletions":18,"changed_files":7,"review":"COMMENTED by gemini-code-assist[bot]","ci":"pending","labels":[],"body":"Two compounding bugs made it impossible to enter an opening paren: auto-insert-pair discarded work and insert-mode precedence was wrong."},
  {"repo":"euxaristia/colt","title":"fix: prevent status bar from wrapping when narrower than its content","url":"https://github.com/euxaristia/colt/pull/3","created":"2026-04-28T04:30:55Z","updated":"2026-05-09T00:41:32Z","draft":False,"additions":27,"deletions":7,"changed_files":1,"review":"COMMENTED by gemini-code-assist[bot]","ci":"pending","labels":[],"body":"Status bar content wider than terminal caused it to wrap, scrolling the screen up by one line."},
  {"repo":"euxaristia/dotfiles","title":"feat: add protected-branch check to git safety rules","url":"https://github.com/euxaristia/dotfiles/pull/1","created":"2026-04-13T21:21:51Z","updated":"2026-05-08T23:59:52Z","draft":False,"additions":17,"deletions":0,"changed_files":2,"review":"COMMENTED by gemini-code-assist[bot]","ci":"pending","labels":[],"body":"Git pre-push rule to check for protected branches and open a PR instead of pushing directly."},
  {"repo":"euxaristia/VoxelPopuli","title":"Parallelize chunk generation across rayon worker pool","url":"https://github.com/euxaristia/VoxelPopuli/pull/4","created":"2026-04-28T23:04:07Z","updated":"2026-04-28T23:40:17Z","draft":False,"additions":127,"deletions":117,"changed_files":2,"review":"COMMENTED by gemini-code-assist[bot]","ci":"pending","labels":[],"body":"Moves Chunk::generate() from render thread onto rayon worker pool for multi-core world generation."},
  {"repo":"euxaristia/VoxelPopuli","title":"chore(deps): replace image and rayon with smaller alternatives","url":"https://github.com/euxaristia/VoxelPopuli/pull/2","created":"2026-04-22T04:03:20Z","updated":"2026-04-22T04:05:00Z","draft":False,"additions":26,"deletions":8,"changed_files":4,"review":"COMMENTED by gemini-code-assist[bot]","ci":"pending","labels":[],"body":"Replace image and rayon crates with direct png decoding and std::thread::spawn to reduce dependency tree."},
  {"repo":"euxaristia/tree-sitter","title":"feat(runtime): pure-Rust runtime crate; port point.c","url":"https://github.com/euxaristia/tree-sitter/pull/1","created":"2026-04-14T06:31:17Z","updated":"2026-04-14T06:41:38Z","draft":False,"additions":241,"deletions":0,"changed_files":6,"review":"COMMENTED by gemini-code-assist[bot]","ci":"pending","labels":[],"body":"Pure-Rust staticlib crate to progressively replace the C runtime while preserving the tree-sitter C ABI."},
]

upstream = [p for p in prs if not p['repo'].startswith('euxaristia/')]
personal = [p for p in prs if p['repo'].startswith('euxaristia/')]
upstream.sort(key=lambda x: x['updated'], reverse=True)
personal.sort(key=lambda x: x['updated'], reverse=True)

av = A4[0] - 3.0*cm
ths = ParagraphStyle('ths', fontName='LASB', fontSize=8, leading=10, textColor=colors.white)
tds = ParagraphStyle('tds', fontName='LS', fontSize=8, leading=10.5)
tda = ParagraphStyle('tda', fontName='LS', fontSize=8, leading=10.5, textColor=ACCENT)

def make_tbl(prs):
    cw = [2.8*cm, 7.5*cm, 2.2*cm, 2.0*cm, 1.8*cm]
    cw = [w/sum(cw)*av for w in cw]
    hdr = [Paragraph('<b>Repo</b>',ths),Paragraph('<b>Title</b>',ths),Paragraph('<b>Created</b>',ths),Paragraph('<b>Updated</b>',ths),Paragraph('<b>CI</b>',ths)]
    rows = [hdr]
    for p in prs:
        rn = p['repo'].split('/')[-1]
        short_d = fd(p['created']).replace(', 2026',', \'26')
        short_u = fd(p['updated']).replace(', 2026',', \'26')
        rows.append([
            Paragraph(f'<b>{rn}</b>',tda),
            Paragraph(p['title'][:55]+('...' if len(p['title'])>55 else ''),tds),
            Paragraph(short_d,tds),
            Paragraph(short_u,tds),
            Paragraph(ci_b(p['ci']),ParagraphStyle('c',fontName='LAS',fontSize=8,leading=10)),
        ])
    t = Table(rows, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',(0,0),(-1,0),ACCENT),('TEXTCOLOR',(0,0),(-1,0),colors.white),
        ('FONTSIZE',(0,0),(-1,-1),8),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),
        ('LEFTPADDING',(0,0),(-1,-1),4),('RIGHTPADDING',(0,0),(-1,-1),4),
        ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#e5e7eb')),('VALIGN',(0,0),(-1,-1),'TOP'),
        ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f9fafb')]),
    ]))
    return t

def pr_block(p):
    els = []
    els.append(Paragraph(f'<b>{p["title"]}</b>',ParagraphStyle('pt',fontName='LASB',fontSize=9.5,leading=12.5,spaceAfter=1)))
    mp = [p['repo'],f'Created: {fd(p["created"])}',f'Updated: {fd(p["updated"])}']
    if p.get('labels'): mp.append('Labels: '+', '.join(p['labels']))
    els.append(Paragraph('  |  '.join(mp), mt))
    s = f'+{p["additions"]} / -{p["deletions"]} across {p["changed_files"]} file(s)'
    if p.get('draft'): s += '  |  Draft'
    els.append(Paragraph(s, sm))
    els.append(Paragraph(f'Review: {rv_b(p["review"])}  |  CI: {ci_b(p["ci"])}',ParagraphStyle('rc',fontName='LAS',fontSize=8.5,leading=11,spaceAfter=2)))
    b = p.get('body','')[:200]
    if b: els.append(Paragraph(b,ParagraphStyle('be',fontName='LS',fontSize=9,leading=12,textColor=TM,spaceAfter=1)))
    els.append(Paragraph(f'Link: {p["url"]}',ParagraphStyle('lnk',fontName='LAS',fontSize=8,leading=10,textColor=ACCENT,spaceAfter=6)))
    els.append(Spacer(1,4))
    return els

output = '/home/z/my-project/download/GitHub_PR_Report_euxaristia_2026-05-14.pdf'
doc = SimpleDocTemplate(output, pagesize=A4, leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm,
    title='GitHub PR Report - euxaristia', author='euxaristia', creator='Z.ai')

story = []
# Cover
story.append(Spacer(1,4*cm))
story.append(Paragraph('<b>GitHub PR Report</b>',ct))
story.append(Spacer(1,12))
story.append(Paragraph('euxaristia',cs))
story.append(Spacer(1,6))
story.append(Paragraph('May 14, 2026',cd))
story.append(Spacer(1,2*cm))
ss = ParagraphStyle('ss',fontName='LS',fontSize=11,leading=16,alignment=TA_CENTER,textColor=TP)
story.append(Paragraph(f'{len(prs)} open pull requests across {len(set(p["repo"] for p in prs))} repositories',ss))
story.append(Spacer(1,8))
story.append(Paragraph(f'{len(upstream)} upstream contributions  |  {len(personal)} personal repositories',ParagraphStyle('sd',fontName='LAS',fontSize=10,leading=14,alignment=TA_CENTER,textColor=TM)))
story.append(PageBreak())

# Summary
story.append(Paragraph('<b>Executive Summary</b>',h1))
story.append(HRFlowable(width='100%',thickness=0.8,color=ACCENT,spaceBefore=0,spaceAfter=8))
ta = sum(p['additions'] for p in prs)
td = sum(p['deletions'] for p in prs)
tf = sum(p['changed_files'] for p in prs)
cp = sum(1 for p in prs if p['ci']=='success')
cf = sum(1 for p in prs if p['ci']=='failure')
cpe = sum(1 for p in prs if p['ci']=='pending')
cr = sum(1 for p in prs if 'CHANGES_REQUESTED' in p['review'])
ap = sum(1 for p in prs if 'APPROVED' in p['review'])
nr = sum(1 for p in prs if not p['review'])
story.append(Paragraph(f'This report covers all <b>{len(prs)}</b> open pull requests authored by <b>euxaristia</b> across <b>{len(set(p["repo"] for p in prs))}</b> repositories. The PRs touch <b>{ta:,}</b> lines added and <b>{td:,}</b> lines deleted across <b>{tf}</b> files. Of these, <b>{len(upstream)}</b> are upstream contributions and <b>{len(personal)}</b> are within personal repositories.',bd))

ths2 = ParagraphStyle('ths2',fontName='LASB',fontSize=9,leading=12,textColor=colors.white)
tds2 = ParagraphStyle('tds2',fontName='LS',fontSize=9,leading=12)

story.append(Spacer(1,6))
story.append(Paragraph('<b>CI Status</b>',h2))
ci_d = [[Paragraph('<b>Status</b>',ths2),Paragraph('<b>Count</b>',ths2)],
    [Paragraph('<font color="#16a34a">Passed</font>',tds2),str(cp)],
    [Paragraph('<font color="#d97706">Pending</font>',tds2),str(cpe)],
    [Paragraph('<font color="#dc2626">Failed</font>',tds2),str(cf)]]
ct2 = Table(ci_d,colWidths=[4*cm,3*cm])
ct2.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),ACCENT),('TEXTCOLOR',(0,0),(-1,0),colors.white),
    ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#e5e7eb')),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('LEFTPADDING',(0,0),(-1,-1),6),
    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f9fafb')])]))
story.append(ct2)

story.append(Spacer(1,8))
story.append(Paragraph('<b>Review Status</b>',h2))
rv_d = [[Paragraph('<b>Status</b>',ths2),Paragraph('<b>Count</b>',ths2)],
    [Paragraph('<font color="#16a34a">Approved</font>',tds2),str(ap)],
    [Paragraph('<font color="#dc2626">Changes Requested</font>',tds2),str(cr)],
    [Paragraph('<font color="#73787f">Commented (Bot)</font>',tds2),str(len(prs)-ap-cr-nr)],
    [Paragraph('No Reviews',tds2),str(nr)]]
rt2 = Table(rv_d,colWidths=[4*cm,3*cm])
rt2.setStyle(TableStyle([('BACKGROUND',(0,0),(-1,0),ACCENT),('TEXTCOLOR',(0,0),(-1,0),colors.white),
    ('GRID',(0,0),(-1,-1),0.4,colors.HexColor('#e5e7eb')),('TOPPADDING',(0,0),(-1,-1),4),('BOTTOMPADDING',(0,0),(-1,-1),4),('LEFTPADDING',(0,0),(-1,-1),6),
    ('ROWBACKGROUNDS',(0,1),(-1,-1),[colors.white,colors.HexColor('#f9fafb')])]))
story.append(rt2)

# Upstream
story.append(Spacer(1,12))
story.append(Paragraph(f'<b>Upstream Contributions ({len(upstream)})</b>',h1))
story.append(HRFlowable(width='100%',thickness=0.8,color=ACCENT,spaceBefore=0,spaceAfter=8))
story.append(Paragraph('PRs open against third-party repositories maintained by other organizations.',bd))
story.append(Spacer(1,6))
story.append(make_tbl(upstream))
story.append(Spacer(1,10))
for p in upstream:
    story.extend(pr_block(p))

# Personal
story.append(Paragraph(f'<b>Personal Repositories ({len(personal)})</b>',h1))
story.append(HRFlowable(width='100%',thickness=0.8,color=ACCENT,spaceBefore=0,spaceAfter=8))
story.append(Paragraph('PRs open within personal repositories under the euxaristia account.',bd))
story.append(Spacer(1,6))
story.append(make_tbl(personal))
story.append(Spacer(1,10))
for p in personal:
    story.extend(pr_block(p))

story.append(Spacer(1,12))
story.append(HRFlowable(width='100%',thickness=0.4,color=TM,spaceBefore=4,spaceAfter=4))
story.append(Paragraph('Generated May 14, 2026  |  github.com/euxaristia',ft))

doc.build(story)
print(f'Report saved to {output}')
