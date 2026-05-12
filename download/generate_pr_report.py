import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

# ━━ Fonts ━━
pdfmetrics.registerFont(TTFont('Carlito', '/usr/share/fonts/truetype/english/Carlito-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Carlito-Bold', '/usr/share/fonts/truetype/english/Carlito-Bold.ttf'))
pdfmetrics.registerFont(TTFont('LiberationSerif', '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'))
pdfmetrics.registerFont(TTFont('LiberationSerif-Bold', '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans-Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
registerFontFamily('LiberationSerif', normal='LiberationSerif', bold='LiberationSerif-Bold')
registerFontFamily('Carlito', normal='Carlito', bold='Carlito-Bold')
registerFontFamily('DejaVuSans', normal='DejaVuSans', bold='DejaVuSans-Bold')

# ━━ Cascade Palette ━━
PAGE_BG       = colors.HexColor('#f3f3f2')
TABLE_STRIPE  = colors.HexColor('#f1f0ee')
HEADER_FILL   = colors.HexColor('#685e43')
BORDER        = colors.HexColor('#d4d0c2')
ACCENT        = colors.HexColor('#562dce')
TEXT_PRIMARY   = colors.HexColor('#272623')
TEXT_MUTED     = colors.HexColor('#88857e')

# ━━ Human-readable date ━━
REPORT_DATE = "May 12, 2026"

# ━━ Styles ━━
h1 = ParagraphStyle(name='H1', fontName='LiberationSerif', fontSize=20, leading=28, textColor=TEXT_PRIMARY, spaceBefore=18, spaceAfter=10, alignment=TA_LEFT)
h2 = ParagraphStyle(name='H2', fontName='LiberationSerif', fontSize=15, leading=22, textColor=TEXT_PRIMARY, spaceBefore=14, spaceAfter=8, alignment=TA_LEFT)
body = ParagraphStyle(name='Body', fontName='LiberationSerif', fontSize=10.5, leading=17, textColor=TEXT_PRIMARY, alignment=TA_JUSTIFY, spaceAfter=6)
cap = ParagraphStyle(name='Caption', fontName='LiberationSerif', fontSize=9, leading=14, textColor=TEXT_MUTED, alignment=TA_CENTER, spaceBefore=3, spaceAfter=6)
hcs = ParagraphStyle(name='HCS', fontName='LiberationSerif', fontSize=9.5, leading=14, textColor=colors.white, alignment=TA_CENTER)
cs = ParagraphStyle(name='CS', fontName='LiberationSerif', fontSize=9, leading=13, textColor=TEXT_PRIMARY, alignment=TA_LEFT)
ccs = ParagraphStyle(name='CCS', fontName='LiberationSerif', fontSize=9, leading=13, textColor=TEXT_PRIMARY, alignment=TA_CENTER)
kick = ParagraphStyle(name='Kick', fontName='Carlito', fontSize=10, leading=14, textColor=ACCENT, spaceBefore=4, spaceAfter=4, alignment=TA_LEFT)

def make_table(data, col_widths):
    t = Table(data, colWidths=col_widths, hAlign='CENTER', repeatRows=1)
    cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), HEADER_FILL),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(data)):
        bg = colors.white if i % 2 == 1 else TABLE_STRIPE
        cmds.append(('BACKGROUND', (0, i), (-1, i), bg))
    t.setStyle(TableStyle(cmds))
    return t

output_path = '/home/z/my-project/download/pr_body.pdf'
doc = SimpleDocTemplate(output_path, pagesize=A4, leftMargin=1.0*inch, rightMargin=1.0*inch, topMargin=0.9*inch, bottomMargin=0.9*inch,
    title='GitHub Pull Request Status Report', author='euxaristia', creator='Z.ai',
    subject='Open PR overview for euxaristia and Cairn organization')
aw = A4[0] - 2*inch
story = []

# ━━ Executive Summary ━━
story.append(Paragraph('<b>Pull Request Status Report</b>', h1))
story.append(Paragraph('GitHub: euxaristia / Cairn Organization', kick))
story.append(Spacer(1, 6))
story.append(Paragraph(
    'This report provides a comprehensive overview of all open pull requests associated with the '
    'GitHub user <b>euxaristia</b> across personal repositories and upstream contributions, as well as '
    'any open pull requests within the <b>Cairn</b> organization. The data was collected on '
    '<b>%s</b> using the GitHub public API. The report is designed to help track '
    'contribution velocity, identify stale PRs that may need follow-up, and highlight key areas of '
    'active development work.' % REPORT_DATE, body))
story.append(Spacer(1, 10))

# ━━ Metrics ━━
md = [[Paragraph('<b>Metric</b>', hcs), Paragraph('<b>Count</b>', hcs)],
    [Paragraph('Open PRs authored by euxaristia', cs), Paragraph('<b>19</b>', ccs)],
    [Paragraph('Open PRs in Cairn organization', cs), Paragraph('<b>0</b>', ccs)],
    [Paragraph('PRs involving euxaristia (non-author)', cs), Paragraph('<b>2</b>', ccs)],
    [Paragraph('Total personal repositories', cs), Paragraph('<b>59</b>', ccs)],
    [Paragraph('Cairn organization repositories', cs), Paragraph('<b>1</b>', ccs)]]
story.append(Spacer(1, 12))
story.append(make_table(md, [aw*0.70, aw*0.30]))
story.append(Paragraph('Table 1: Summary of pull request metrics for euxaristia and Cairn', cap))
story.append(Spacer(1, 18))

# ━━ Open PRs ━━
story.append(Paragraph('<b>Open Pull Requests Detail</b>', h1))
story.append(Paragraph(
    'The following table lists all 19 open pull requests authored by euxaristia, sorted by creation date '
    'in descending order. These span personal repositories, forks, and upstream contributions to major '
    'open-source projects. All repository names use the full owner/repo format.', body))
story.append(Spacer(1, 12))

prs = [
    ('euxaristia/gemini-cli', '#4', 'fix(build): detect Bun runtime in build scripts', 'May 12, 2026'),
    ('euxaristia/gemini-cli', '#3', 'fix(core): make shell tool work under Bun', 'May 12, 2026'),
    ('euxaristia/gitee-cli', '#2', 'feat: implicitly use current repo and branch context for pr commands', 'May 9, 2026'),
    ('euxaristia/colt', '#5', 'fix(editor): typing/pasting "(" now actually inserts the character', 'May 9, 2026'),
    ('euxaristia/colt', '#4', 'feat: mouse click moves cursor; drag enters Visual mode', 'May 7, 2026'),
    ('google-gemini/gemini-cli', '#26498', 'feat(cli): show acknowledgment when user steering hint is processed', 'May 5, 2026'),
    ('anomalyco/opencode', '#25355', 'fix(tui): bind home/end to line start/end in input', 'May 1, 2026'),
    ('google-gemini/gemini-cli', '#26280', 'fix(build): detect Bun runtime in build scripts', 'Apr 30, 2026'),
    ('euxaristia/VoxelPopuli', '#4', 'Parallelize chunk generation across rayon worker pool', 'Apr 28, 2026'),
    ('euxaristia/colt', '#3', 'fix: prevent status bar from wrapping when narrower than its content', 'Apr 28, 2026'),
    ('charmbracelet/glow', '#937', 'fix: ensure closing fence in WrapCodeBlock is on its own line', 'Apr 26, 2026'),
    ('euxaristia/VoxelPopuli', '#2', 'chore(deps): replace image and rayon with smaller alternatives', 'Apr 22, 2026'),
    ('euxaristia/colt', '#1', 'feat(substitute): add regex support to ":s/" command', 'Apr 14, 2026'),
    ('euxaristia/tree-sitter', '#1', 'feat(runtime): pure-Rust runtime crate; port point.c', 'Apr 14, 2026'),
    ('euxaristia/dotfiles', '#1', 'feat: add protected-branch check to git safety rules', 'Apr 13, 2026'),
    ('clockworklabs/SpacetimeDB', '#4773', 'feat(bindings-cpp-ffi): add Rust FFI crate for WASM modules', 'Apr 10, 2026'),
    ('QwenLM/qwen-code', '#2838', 'feat: add bun runtime support', 'Apr 2, 2026'),
    ('google-gemini/gemini-cli', '#22618', 'fix(cli): respect ui.loadingPhrases "off" setting', 'Mar 16, 2026'),
    ('microsoft/node-pty', '#901', 'fix: swallow resize() errors after PTY exit on Windows and Unix', 'Mar 13, 2026'),
]

ptd = [[Paragraph('<b>Repository</b>', hcs), Paragraph('<b>PR</b>', hcs), Paragraph('<b>Title</b>', hcs), Paragraph('<b>Created</b>', hcs)]]
for repo, num, title, date in prs:
    ptd.append([Paragraph(repo, cs), Paragraph(num, ccs), Paragraph(title, cs), Paragraph(date, ccs)])

story.append(make_table(ptd, [aw*0.25, aw*0.09, aw*0.48, aw*0.18]))
story.append(Paragraph('Table 2: All open pull requests authored by euxaristia, sorted by date (newest first)', cap))
story.append(Spacer(1, 18))

# ━━ Staleness ━━
story.append(Paragraph('<b>Staleness Analysis</b>', h1))
story.append(Paragraph(
    'Understanding the age of open pull requests is critical for prioritizing follow-up actions. '
    'The table below categorizes each PR by age bracket as of the report date (%s). '
    'PRs older than 30 days are flagged as potentially stale, as they may have accumulated merge '
    'conflicts or lost reviewer context.' % REPORT_DATE, body))
story.append(Spacer(1, 10))

sd = [[Paragraph('<b>Age Bracket</b>', hcs), Paragraph('<b>Count</b>', hcs), Paragraph('<b>Repositories</b>', hcs)],
    [Paragraph('0-7 days', ccs), Paragraph('6', ccs), Paragraph('euxaristia/gemini-cli, euxaristia/gitee-cli, euxaristia/colt, anomalyco/opencode', cs)],
    [Paragraph('8-30 days', ccs), Paragraph('8', ccs), Paragraph('euxaristia/colt, euxaristia/VoxelPopuli, charmbracelet/glow, euxaristia/tree-sitter, euxaristia/dotfiles, clockworklabs/SpacetimeDB, QwenLM/qwen-code', cs)],
    [Paragraph('31-60 days (stale)', ccs), Paragraph('5', ccs), Paragraph('google-gemini/gemini-cli, QwenLM/qwen-code, microsoft/node-pty', cs)]]
story.append(make_table(sd, [aw*0.18, aw*0.08, aw*0.74]))
story.append(Paragraph('Table 3: PR age distribution as of %s' % REPORT_DATE, cap))
story.append(Spacer(1, 18))

# ━━ Non-author PRs ━━
story.append(Paragraph('<b>PRs Involving euxaristia (Non-Author)</b>', h1))
story.append(Paragraph(
    'In addition to the 19 PRs directly authored by euxaristia, two additional pull requests involve '
    'euxaristia as a commenter, reviewer, or referenced contributor. These may represent collaborative '
    'work, review requests, or issues where euxaristia provided input that shaped the contribution.', body))
story.append(Spacer(1, 10))

nd = [[Paragraph('<b>Repository</b>', hcs), Paragraph('<b>PR</b>', hcs), Paragraph('<b>Title</b>', hcs)],
    [Paragraph('BingqingLyu/qwen-code', cs), Paragraph('#73', ccs), Paragraph('feat: add bun runtime support', cs)],
    [Paragraph('this-is-dev/InnerDemons', cs), Paragraph('#9', ccs), Paragraph('y cant i merge?', cs)]]
story.append(make_table(nd, [aw*0.30, aw*0.10, aw*0.60]))
story.append(Paragraph('Table 4: PRs involving euxaristia as a non-author contributor', cap))
story.append(Spacer(1, 18))

# ━━ Cairn ━━
story.append(Paragraph('<b>Cairn Organization Status</b>', h1))
story.append(Paragraph(
    'The Cairn organization currently maintains a single repository: <b>Cairn/floriography</b>, a TypeScript '
    'project described as providing a random flower, its Latin name, and a verse from a real English poem. '
    'As of <b>%s</b>, there are no open pull requests across the Cairn organization. All previous '
    'contributions have likely been merged or closed, or the project is in a stable state with no pending '
    'changes requiring review.' % REPORT_DATE, body))
story.append(Spacer(1, 18))

# ━━ Key Themes ━━
story.append(Paragraph('<b>Key Themes and Analysis</b>', h1))
story.append(Paragraph(
    'Examining the distribution of open pull requests reveals several clear patterns in the types of work '
    'euxaristia is actively pursuing. These themes highlight both technical interests and the breadth of the '
    'open-source communities in which euxaristia participates.', body))
story.append(Spacer(1, 8))

story.append(Paragraph('<b>Bun Runtime Compatibility</b>', h2))
story.append(Paragraph(
    'A significant cluster of PRs focuses on adding or improving Bun runtime support across multiple projects. '
    'This includes PR #4 and #3 on euxaristia/gemini-cli (May 12, 2026), PR #26280 on google-gemini/gemini-cli '
    '(Apr 30, 2026), and PR #2838 on QwenLM/qwen-code (Apr 2, 2026). This pattern suggests a strong interest in '
    'the Bun JavaScript runtime as an alternative to Node.js, with a focus on ensuring that build scripts, CLI '
    'tools, and shell integrations work correctly when executed under Bun rather than Node. The recurrence of this '
    'theme across independent projects indicates specialized expertise that serves as reference implementations '
    'for other projects encountering similar issues.', body))
story.append(Spacer(1, 8))

story.append(Paragraph('<b>colt Editor Development</b>', h2))
story.append(Paragraph(
    'The <b>euxaristia/colt</b> repository, a vi-style editor written in the Pony programming language, has four '
    'open PRs (#1 through #5) representing active feature development. The work spans regex substitution support '
    'in the ":s/" command (PR #1, Apr 14, 2026), visual mode improvements with mouse click and drag support '
    '(PR #4, May 7, 2026), character input fixes for parentheses insertion (PR #5, May 9, 2026), and status bar '
    'layout corrections (PR #3, Apr 28, 2026). This concentration signals that colt is the primary personal '
    'project receiving active development attention.', body))
story.append(Spacer(1, 8))

story.append(Paragraph('<b>Upstream Open-Source Contributions</b>', h2))
story.append(Paragraph(
    'Several PRs target well-known upstream repositories, including google-gemini/gemini-cli, microsoft/node-pty, '
    'charmbracelet/glow, anomalyco/opencode, clockworklabs/SpacetimeDB, and QwenLM/qwen-code. These contributions '
    'demonstrate engagement with the broader open-source ecosystem. Notably, the PRs to microsoft/node-pty '
    '(#901, Mar 13, 2026, PTY resize error handling) and charmbracelet/glow (#937, Apr 26, 2026, markdown '
    'rendering fix) address fundamental cross-platform issues that benefit a wide user base. The diversity of '
    'target projects reflects broad technical fluency.', body))
story.append(Spacer(1, 8))

story.append(Paragraph('<b>Systems-Level Rust Development</b>', h2))
story.append(Paragraph(
    'Three PRs involve Rust-focused systems work: the euxaristia/tree-sitter pure-Rust runtime (PR #1, Apr 14, '
    '2026), euxaristia/VoxelPopuli chunk parallelization with rayon (PR #2, Apr 22 and PR #4, Apr 28, 2026), '
    'and clockworklabs/SpacetimeDB FFI bindings for WASM modules (PR #4773, Apr 10, 2026). These target '
    'low-level, performance-critical domains including parser runtimes, voxel engine optimization, and WebAssembly '
    'module interop. The tree-sitter contribution is particularly ambitious, involving a complete rewrite of the '
    'runtime in pure Rust to eliminate the C dependency.', body))
story.append(Spacer(1, 18))

# ━━ Recommendations ━━
story.append(Paragraph('<b>Recommendations</b>', h1))
story.append(Paragraph(
    'Based on the current state of open pull requests, the following actions may help improve contribution '
    'effectiveness and ensure that ongoing work receives timely attention from maintainers.', body))
story.append(Spacer(1, 8))
story.append(Paragraph(
    '<b>1. Prioritize stale PRs:</b> The oldest open PR (microsoft/node-pty #901, Mar 13, 2026) has '
    'been open for approximately 60 days. Consider following up with maintainers through a polite comment or by '
    'rebasing the branch onto the latest main to resolve any merge conflicts. PRs on google-gemini/gemini-cli '
    '(#22618, Mar 16, 2026) and QwenLM/qwen-code (#2838, Apr 2, 2026) are also in the stale bracket.', body))
story.append(Spacer(1, 6))
story.append(Paragraph(
    '<b>2. Consolidate gemini-cli contributions:</b> Three separate PRs target google-gemini/gemini-cli. '
    'If these changes are related (e.g., the Bun build detection fix appears in both PR #4 on the fork and '
    'PR #26280 upstream), consider consolidating them into a single, well-organized PR to reduce reviewer '
    'overhead and improve the chances of timely merge.', body))
story.append(Spacer(1, 6))
story.append(Paragraph(
    '<b>3. Continue colt editor momentum:</b> The euxaristia/colt editor has the most active development '
    'pipeline with four open PRs. Maintaining a regular merge cadence will prevent the PR stack from growing '
    'unmanageably and will allow incremental user feedback on each new capability.', body))

doc.build(story)
print("Body PDF generated:", output_path)
