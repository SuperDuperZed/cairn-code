import json
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable,
    Table, TableStyle, PageBreak
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

pdfmetrics.registerFont(TTFont('LS', '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'))
pdfmetrics.registerFont(TTFont('LSB', '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'))
pdfmetrics.registerFont(TTFont('LSI', '/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf'))
pdfmetrics.registerFont(TTFont('LaS', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'))
pdfmetrics.registerFont(TTFont('LaSB', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'))
registerFontFamily('LS', normal='LS', bold='LSB', italic='LSI')
registerFontFamily('LaS', normal='LaS', bold='LaSB')

ACCENT = colors.HexColor('#5d39c8')
TEXT_PRIMARY = colors.HexColor('#1f2022')
TEXT_MUTED = colors.HexColor('#73787f')

def fmt_date(iso_str):
    if not iso_str: return 'N/A'
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        return dt.strftime('%B %d, %Y')
    except: return iso_str[:10]

def ci_badge(status):
    m = {'success': ('#16a34a', 'Passed'), 'failure': ('#dc2626', 'Failed'), 'pending': ('#d97706', 'Pending')}
    c, l = m.get(status, ('#73787f', status))
    return f'<font color="{c}">{l}</font>'

def review_badge(r):
    if not r: return 'No reviews'
    state = r.split(' by ')[0] if ' by ' in r else r
    who = r.split(' by ')[1] if ' by ' in r else ''
    m = {'APPROVED': ('#16a34a', 'Approved'), 'CHANGES_REQUESTED': ('#dc2626', 'Changes Requested'), 'COMMENTED': ('#73787f', 'Commented')}
    c, l = m.get(state, ('#73787f', state))
    t = f'<font color="{c}">{l}</font>'
    if who: t += f' <font color="#73787f">by {who}</font>'
    return t

styles = {
    'cover_title': ParagraphStyle('CT', fontName='LaSB', fontSize=28, leading=34, alignment=TA_CENTER, spaceAfter=6, textColor=TEXT_PRIMARY),
    'cover_sub': ParagraphStyle('CS', fontName='LSI', fontSize=14, leading=18, alignment=TA_CENTER, textColor=TEXT_MUTED, spaceAfter=4),
    'cover_date': ParagraphStyle('CD', fontName='LaS', fontSize=12, leading=16, alignment=TA_CENTER, textColor=ACCENT),
    'h1': ParagraphStyle('H1', fontName='LaSB', fontSize=18, leading=22, spaceBefore=14, spaceAfter=8, textColor=TEXT_PRIMARY),
    'h2': ParagraphStyle('H2', fontName='LaSB', fontSize=13, leading=16, spaceBefore=10, spaceAfter=5, textColor=ACCENT),
    'body': ParagraphStyle('Body', fontName='LS', fontSize=10, leading=14, spaceAfter=4, alignment=TA_JUSTIFY),
    'meta': ParagraphStyle('Meta', fontName='LSI', fontSize=9, leading=12, textColor=TEXT_MUTED, spaceAfter=2),
    'small': ParagraphStyle('Small', fontName='LaS', fontSize=8.5, leading=11, textColor=TEXT_MUTED),
    'footer': ParagraphStyle('Footer', fontName='LaS', fontSize=8, leading=10, textColor=TEXT_MUTED, alignment=TA_CENTER),
    'th': ParagraphStyle('TH', fontName='LaSB', fontSize=8, leading=10, textColor=colors.white),
    'td': ParagraphStyle('TD', fontName='LS', fontSize=8, leading=10.5),
    'td_a': ParagraphStyle('TDA', fontName='LS', fontSize=8, leading=10.5, textColor=ACCENT),
    'td_ci': ParagraphStyle('TDCI', fontName='LaS', fontSize=8, leading=10),
}

def make_table(prs):
    avail = A4[0] - 3.0*cm
    cw = [w/17.2*avail for w in [3.0, 7.8, 2.2, 2.2, 2.0]]
    hdr = [Paragraph(f'<b>{t}</b>', styles['th']) for t in ['Repo', 'Title', 'Created', 'Updated', 'CI']]
    data = [hdr]
    for p in prs:
        short = p['repo'].split('/')[-1]
        data.append([
            Paragraph(f'<b>{short}</b>', styles['td_a']),
            Paragraph(p['title'][:60] + ('...' if len(p['title'])>60 else ''), styles['td']),
            Paragraph(fmt_date(p['created']).replace(', 2026', ', \'26'), styles['td']),
            Paragraph(fmt_date(p['updated']).replace(', 2026', ', \'26'), styles['td']),
            Paragraph(ci_badge(p['ci']), styles['td_ci']),
        ])
    t = Table(data, colWidths=cw, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), ACCENT), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
        ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4),
        ('LEFTPADDING', (0,0), (-1,-1), 4), ('RIGHTPADDING', (0,0), (-1,-1), 4),
        ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#e5e7eb')),
        ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f9fafb')]),
    ]))
    return t

def detail_block(p):
    e = []
    e.append(Paragraph(f'<b>{p["title"]}</b>', ParagraphStyle('PRT', fontName='LaSB', fontSize=9.5, leading=12.5, spaceAfter=1)))
    parts = [p['repo'], f'Created: {fmt_date(p["created"])}', f'Updated: {fmt_date(p["updated"])}']
    if p.get('labels'): parts.append('Labels: ' + ', '.join(p['labels']))
    e.append(Paragraph('  |  '.join(parts), styles['meta']))
    s = f'+{p["additions"]} / -{p["deletions"]} across {p["changed_files"]} file(s)'
    if p.get('draft'): s += '  |  Draft'
    e.append(Paragraph(s, styles['small']))
    e.append(Paragraph(f'Review: {review_badge(p["review"])}  |  CI: {ci_badge(p["ci"])}',
        ParagraphStyle('RC', fontName='LaS', fontSize=8.5, leading=11, spaceAfter=2)))
    body = p.get('body', '')[:200]
    if body: e.append(Paragraph(body, ParagraphStyle('BE', fontName='LS', fontSize=9, leading=12, textColor=TEXT_MUTED, spaceAfter=1)))
    e.append(Paragraph(f'Link: {p["url"]}', ParagraphStyle('LK', fontName='LaS', fontSize=8, leading=10, textColor=ACCENT, spaceAfter=6)))
    e.append(Spacer(1, 4))
    return e

# Data
prs = json.loads('''[
  {"repo": "google-gemini/gemini-cli", "title": "feat(cli): show acknowledgment when user steering hint is processed", "url": "https://github.com/google-gemini/gemini-cli/pull/26498", "created": "2026-05-05T11:03:16Z", "updated": "2026-05-13T02:22:30Z", "draft": false, "additions": 190, "deletions": 6, "changed_files": 4, "review": "COMMENTED by gemini-code-assist[bot]", "ci": "pending", "labels": ["priority/p2", "area/agent", "status/pr-nudge-sent"], "body": "When a user submits a steering hint mid-turn, the CLI silently splices the hint into the conversation with no visible feedback. This PR adds an acknowledgment message when the hint is processed."},
  {"repo": "google-gemini/gemini-cli", "title": "fix(build): detect Bun runtime in build scripts to avoid hardcoded npm", "url": "https://github.com/google-gemini/gemini-cli/pull/26280", "created": "2026-04-30T19:29:27Z", "updated": "2026-05-08T02:21:58Z", "draft": false, "additions": 44, "deletions": 8, "changed_files": 3, "review": "COMMENTED by gemini-code-assist[bot]", "ci": "pending", "labels": ["priority/p2", "area/platform", "status/pr-nudge-sent"], "body": "Build scripts invoke npm unconditionally, breaking on Bun-only systems. Detects Bun runtime and uses it instead."},
  {"repo": "microsoft/node-pty", "title": "fix: swallow resize() errors after PTY exit on Windows and Unix", "url": "https://github.com/microsoft/node-pty/pull/901", "created": "2026-03-13T15:11:41Z", "updated": "2026-03-13T15:21:49Z", "draft": false, "additions": 8, "deletions": 2, "changed_files": 2, "review": "", "ci": "pending", "labels": [], "body": "Silently ignore resize() calls after PTY process has exited, catching EBADF errors on Unix and preventing crashes on Windows."},
  {"repo": "QwenLM/qwen-code", "title": "feat: add bun runtime support", "url": "https://github.com/QwenLM/qwen-code/pull/2838", "created": "2026-04-02T20:40:44Z", "updated": "2026-04-24T23:31:33Z", "draft": false, "additions": 3683, "deletions": 126, "changed_files": 9, "review": "CHANGES_REQUESTED by wenshao", "ci": "pending", "labels": [], "body": "Add Bun runtime support for significantly improved performance: 3-5x faster startup, lower memory usage, native TypeScript support."},
  {"repo": "clockworklabs/SpacetimeDB", "title": "feat(bindings-cpp-ffi): add Rust FFI crate for WASM modules", "url": "https://github.com/clockworklabs/SpacetimeDB/pull/4773", "created": "2026-04-10T04:22:37Z", "updated": "2026-04-28T05:33:51Z", "draft": false, "additions": 2417, "deletions": 0, "changed_files": 6, "review": "COMMENTED by chatgpt-codex-connector[bot]", "ci": "success", "labels": [], "body": "Add a new Rust crate providing type registration and FFI dispatch for SpacetimeDB WASM modules, re-implementing C++ bindings in Rust."},
  {"repo": "charmbracelet/glow", "title": "fix: ensure closing fence in WrapCodeBlock is on its own line", "url": "https://github.com/charmbracelet/glow/pull/937", "created": "2026-04-26T19:33:29Z", "updated": "2026-04-26T19:33:29Z", "draft": false, "additions": 3, "deletions": 0, "changed_files": 1, "review": "", "ci": "pending", "labels": [], "body": "WrapCodeBlock glued the closing fence onto the last line of content. When input lacked a trailing newline, Markdown renderers never saw the closing fence."},
  {"repo": "anomalyco/opencode", "title": "fix(tui): bind home/end to line start/end in input", "url": "https://github.com/anomalyco/opencode/pull/25355", "created": "2026-05-01T20:10:08Z", "updated": "2026-05-11T01:39:11Z", "draft": false, "additions": 192, "deletions": 192, "changed_files": 20, "review": "", "ci": "pending", "labels": [], "body": "Closes #14899. Home/End keys not bound in input field. Adds bindings to keybinds source-of-truth file."},
  {"repo": "euxaristia/adapt", "title": "Add shell completion for zsh and bash", "url": "https://github.com/euxaristia/adapt/pull/1", "created": "2026-05-09T00:27:04Z", "updated": "2026-05-12T22:16:24Z", "draft": false, "additions": 239, "deletions": 0, "changed_files": 3, "review": "COMMENTED by gemini-code-assist[bot]", "ci": "pending", "labels": [], "body": "Add zsh and bash completions for adapt install/remove commands, using the same data sources as apt's own completions."},
  {"repo": "euxaristia/gemini-cli", "title": "fix(build): detect Bun runtime in build scripts", "url": "https://github.com/euxaristia/gemini-cli/pull/4", "created": "2026-05-12T20:35:46Z", "updated": "2026-05-12T20:38:20Z", "draft": false, "additions": 44, "deletions": 8, "changed_files": 3, "review": "COMMENTED by gemini-code-assist[bot]", "ci": "pending", "labels": [], "body": "Build scripts invoke npm/node unconditionally, breaking on Bun-only systems. Detects Bun and uses it instead."},
  {"repo": "euxaristia/gemini-cli", "title": "fix(core): make shell tool work under Bun", "url": "https://github.com/euxaristia/gemini-cli/pull/3", "created": "2026-05-12T20:05:43Z", "updated": "2026-05-12T20:05:50Z", "draft": false, "additions": 39, "deletions": 5, "changed_files": 3, "review": "", "ci": "pending", "labels": [], "body": "Two runtime issues prevented Bun-launched builds from running shell tool calls: ioctl EBADF crash and empty command results."},
  {"repo": "euxaristia/gitee-cli", "title": "feat: implicitly use current repo and branch context for pr commands", "url": "https://github.com/euxaristia/gitee-cli/pull/2", "created": "2026-05-09T06:29:41Z", "updated": "2026-05-09T06:31:48Z", "draft": false, "additions": 116, "deletions": 13, "changed_files": 3, "review": "COMMENTED by gemini-code-assist[bot]", "ci": "pending", "labels": [], "body": "Updates gt pr commands to infer repo context from local git remote, bringing parity with gh behavior."},
  {"repo": "euxaristia/colt", "title": "feat: mouse click moves cursor; drag enters Visual mode", "url": "https://github.com/euxaristia/colt/pull/4", "created": "2026-05-07T05:37:02Z", "updated": "2026-05-09T00:46:47Z", "draft": false, "additions": 138, "deletions": 4, "changed_files": 2, "review": "COMMENTED by gemini-code-assist[bot]", "ci": "pending", "labels": [], "body": "Switches SGR mouse mode from press-only to press/release/motion. Left-click moves cursor, drag enters Visual mode."},
  {"repo": "euxaristia/colt", "title": "feat(substitute): add regex support to :s/ command", "url": "https://github.com/euxaristia/colt/pull/1", "created": "2026-04-14T06:41:21Z", "updated": "2026-05-09T00:44:56Z", "draft": false, "additions": 407, "deletions": 11, "changed_files": 5, "review": "COMMENTED by gemini-code-assist[bot]", "ci": "pending", "labels": [], "body": "Adds a pure-Pony backtracking regex engine (~230 LOC) and wires it into :s/, :%s/, and :.,$s/ commands."},
  {"repo": "euxaristia/colt", "title": "fix(editor): typing/pasting ( now actually inserts the character", "url": "https://github.com/euxaristia/colt/pull/5", "created": "2026-05-09T00:01:29Z", "updated": "2026-05-09T00:41:56Z", "draft": false, "additions": 408, "deletions": 18, "changed_files": 7, "review": "COMMENTED by gemini-code-assist[bot]", "ci": "pending", "labels": [], "body": "Two compounding bugs made it impossible to enter an opening paren: auto-insert-pair discarded its work and insert-mode precedence was wrong."},
  {"repo": "euxaristia/colt", "title": "fix: prevent status bar from wrapping when narrower than its content", "url": "https://github.com/euxaristia/colt/pull/3", "created": "2026-04-28T04:30:55Z", "updated": "2026-05-09T00:41:32Z", "draft": false, "additions": 27, "deletions": 7, "changed_files": 1, "review": "COMMENTED by gemini-code-assist[bot]", "ci": "pending", "labels": [], "body": "Status bar content wider than terminal width wrapped onto a second row, scrolling the screen up by one line."},
  {"repo": "euxaristia/dotfiles", "title": "feat: add protected-branch check to git safety rules", "url": "https://github.com/euxaristia/dotfiles/pull/1", "created": "2026-04-13T21:21:51Z", "updated": "2026-05-08T23:59:52Z", "draft": false, "additions": 17, "deletions": 0, "changed_files": 2, "review": "COMMENTED by gemini-code-assist[bot]", "ci": "pending", "labels": [], "body": "Add a git pre-push rule to check for protected branches and open a PR instead of pushing directly."},
  {"repo": "euxaristia/VoxelPopuli", "title": "Parallelize chunk generation across rayon worker pool", "url": "https://github.com/euxaristia/VoxelPopuli/pull/4", "created": "2026-04-28T23:04:07Z", "updated": "2026-04-28T23:40:17Z", "draft": false, "additions": 127, "deletions": 117, "changed_files": 2, "review": "COMMENTED by gemini-code-assist[bot]", "ci": "pending", "labels": [], "body": "Moves Chunk::generate() from render thread onto rayon worker pool for multi-core world generation."},
  {"repo": "euxaristia/VoxelPopuli", "title": "chore(deps): replace image and rayon with smaller alternatives", "url": "https://github.com/euxaristia/VoxelPopuli/pull/2", "created": "2026-04-22T04:03:20Z", "updated": "2026-04-22T04:05:00Z", "draft": false, "additions": 26, "deletions": 8, "changed_files": 4, "review": "COMMENTED by gemini-code-assist[bot]", "ci": "pending", "labels": [], "body": "Remove image/rayon crates, replacing with direct png decoding and std::thread::spawn."},
  {"repo": "euxaristia/tree-sitter", "title": "feat(runtime): pure-Rust runtime crate; port point.c", "url": "https://github.com/euxaristia/tree-sitter/pull/1", "created": "2026-04-14T06:31:17Z", "updated": "2026-04-14T06:41:38Z", "draft": false, "additions": 241, "deletions": 0, "changed_files": 6, "review": "COMMENTED by gemini-code-assist[bot]", "ci": "pending", "labels": [], "body": "Introduces a pure-Rust staticlib crate to replace the C runtime while preserving the tree-sitter C ABI."}
]''')

upstream = sorted([p for p in prs if not p['repo'].startswith('euxaristia/')], key=lambda x: x['updated'], reverse=True)
personal = sorted([p for p in prs if p['repo'].startswith('euxaristia/')], key=lambda x: x['updated'], reverse=True)

output_path = '/home/z/my-project/download/GitHub_PR_Report_euxaristia_2026-05-14.pdf'
doc = SimpleDocTemplate(output_path, pagesize=A4, leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm,
    title='GitHub PR Report - euxaristia', author='euxaristia', creator='Z.ai')

story = []

# Cover
story.append(Spacer(1, 4*cm))
story.append(Paragraph('<b>GitHub PR Report</b>', styles['cover_title']))
story.append(Spacer(1, 12))
story.append(Paragraph('euxaristia', styles['cover_sub']))
story.append(Spacer(1, 6))
story.append(Paragraph('May 14, 2026', styles['cover_date']))
story.append(Spacer(1, 2*cm))

summary_style = ParagraphStyle('SB', fontName='LS', fontSize=11, leading=16, alignment=TA_CENTER, textColor=TEXT_PRIMARY)
story.append(Paragraph(f'{len(prs)} open pull requests across {len(set(p["repo"] for p in prs))} repositories', summary_style))
story.append(Spacer(1, 8))
story.append(Paragraph(f'{len(upstream)} upstream contributions  |  {len(personal)} personal repositories',
    ParagraphStyle('SD', fontName='LaS', fontSize=10, leading=14, alignment=TA_CENTER, textColor=TEXT_MUTED)))
story.append(PageBreak())

# Executive Summary
story.append(Paragraph('<b>Executive Summary</b>', styles['h1']))
story.append(HRFlowable(width='100%', thickness=0.8, color=ACCENT, spaceBefore=0, spaceAfter=8))

ta = sum(p['additions'] for p in prs)
td = sum(p['deletions'] for p in prs)
tf = sum(p['changed_files'] for p in prs)
cp = sum(1 for p in prs if p['ci']=='success')
cf = sum(1 for p in prs if p['ci']=='failure')
cpe = sum(1 for p in prs if p['ci']=='pending')
cr = sum(1 for p in prs if 'CHANGES_REQUESTED' in p['review'])
ap = sum(1 for p in prs if 'APPROVED' in p['review'])

story.append(Paragraph(
    f'This report covers all <b>{len(prs)}</b> open pull requests authored by <b>euxaristia</b> across '
    f'<b>{len(set(p["repo"] for p in prs))}</b> repositories. The PRs touch <b>{ta:,}</b> lines added and '
    f'<b>{td:,}</b> lines deleted across <b>{tf}</b> files. '
    f'Of these, <b>{len(upstream)}</b> are upstream contributions and <b>{len(personal)}</b> are within personal repositories.',
    styles['body']))

# CI table
story.append(Spacer(1, 6))
story.append(Paragraph('<b>CI Status Overview</b>', styles['h2']))
th_s = ParagraphStyle('THS', fontName='LaSB', fontSize=9, leading=12, textColor=colors.white)
td_s = ParagraphStyle('TDS', fontName='LS', fontSize=9, leading=12)
ci_data = [
    [Paragraph('<b>Status</b>', th_s), Paragraph('<b>Count</b>', th_s)],
    [Paragraph('<font color="#16a34a">Passed</font>', td_s), str(cp)],
    [Paragraph('<font color="#d97706">Pending</font>', td_s), str(cpe)],
    [Paragraph('<font color="#dc2626">Failed</font>', td_s), str(cf)],
]
ci_t = Table(ci_data, colWidths=[4*cm, 3*cm])
ci_t.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), ACCENT), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#e5e7eb')),
    ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4), ('LEFTPADDING', (0,0), (-1,-1), 6),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f9fafb')]),
]))
story.append(ci_t)

# Review table
story.append(Spacer(1, 8))
story.append(Paragraph('<b>Review Status Overview</b>', styles['h2']))
rev_data = [
    [Paragraph('<b>Status</b>', th_s), Paragraph('<b>Count</b>', th_s)],
    [Paragraph('<font color="#16a34a">Approved</font>', td_s), str(ap)],
    [Paragraph('<font color="#dc2626">Changes Requested</font>', td_s), str(cr)],
    [Paragraph('Commented (Bot)', td_s), str(sum(1 for p in prs if p['review'] and 'COMMENTED' in p['review']))],
    [Paragraph('No Reviews', td_s), str(sum(1 for p in prs if not p['review']))],
]
rev_t = Table(rev_data, colWidths=[4*cm, 3*cm])
rev_t.setStyle(TableStyle([
    ('BACKGROUND', (0,0), (-1,0), ACCENT), ('TEXTCOLOR', (0,0), (-1,0), colors.white),
    ('GRID', (0,0), (-1,-1), 0.4, colors.HexColor('#e5e7eb')),
    ('TOPPADDING', (0,0), (-1,-1), 4), ('BOTTOMPADDING', (0,0), (-1,-1), 4), ('LEFTPADDING', (0,0), (-1,-1), 6),
    ('ROWBACKGROUNDS', (0,1), (-1,-1), [colors.white, colors.HexColor('#f9fafb')]),
]))
story.append(rev_t)

# Upstream
story.append(Spacer(1, 12))
story.append(Paragraph(f'<b>Upstream Contributions ({len(upstream)})</b>', styles['h1']))
story.append(HRFlowable(width='100%', thickness=0.8, color=ACCENT, spaceBefore=0, spaceAfter=8))
story.append(Paragraph('Open PRs against third-party repositories maintained by other organizations.', styles['body']))
story.append(Spacer(1, 6))
story.append(make_table(upstream))
story.append(Spacer(1, 10))
for p in upstream:
    story.extend(detail_block(p))

# Personal
story.append(Paragraph(f'<b>Personal Repositories ({len(personal)})</b>', styles['h1']))
story.append(HRFlowable(width='100%', thickness=0.8, color=ACCENT, spaceBefore=0, spaceAfter=8))
story.append(Paragraph('Open PRs within personal repositories under the euxaristia organization.', styles['body']))
story.append(Spacer(1, 6))
story.append(make_table(personal))
story.append(Spacer(1, 10))
for p in personal:
    story.extend(detail_block(p))

# Footer
story.append(Spacer(1, 12))
story.append(HRFlowable(width='100%', thickness=0.4, color=TEXT_MUTED, spaceBefore=4, spaceAfter=4))
story.append(Paragraph('Generated May 14, 2026  |  github.com/euxaristia', styles['footer']))

doc.build(story)
print(f'Report saved to {output_path}')
