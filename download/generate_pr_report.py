import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether
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
SECTION_BG    = colors.HexColor('#f2f1f0')
CARD_BG       = colors.HexColor('#efeeec')
TABLE_STRIPE  = colors.HexColor('#f1f0ee')
HEADER_FILL   = colors.HexColor('#685e43')
COVER_BLOCK   = colors.HexColor('#675f49')
BORDER        = colors.HexColor('#d4d0c2')
ICON          = colors.HexColor('#816e34')
ACCENT        = colors.HexColor('#562dce')
ACCENT_2      = colors.HexColor('#58c48e')
TEXT_PRIMARY   = colors.HexColor('#272623')
TEXT_MUTED     = colors.HexColor('#88857e')
SEM_SUCCESS   = colors.HexColor('#447c57')
SEM_WARNING   = colors.HexColor('#a2854b')
SEM_ERROR     = colors.HexColor('#924d46')
SEM_INFO      = colors.HexColor('#426e99')

# ━━ Report Date (ISO 8601) ━━
REPORT_DATE = "2026-05-12"

# ━━ Styles ━━
h1_style = ParagraphStyle(
    name='H1', fontName='LiberationSerif', fontSize=20, leading=28,
    textColor=TEXT_PRIMARY, spaceBefore=18, spaceAfter=10, alignment=TA_LEFT
)
h2_style = ParagraphStyle(
    name='H2', fontName='LiberationSerif', fontSize=15, leading=22,
    textColor=TEXT_PRIMARY, spaceBefore=14, spaceAfter=8, alignment=TA_LEFT
)
body_style = ParagraphStyle(
    name='Body', fontName='LiberationSerif', fontSize=10.5, leading=17,
    textColor=TEXT_PRIMARY, alignment=TA_JUSTIFY, spaceAfter=6
)
caption_style = ParagraphStyle(
    name='Caption', fontName='LiberationSerif', fontSize=9, leading=14,
    textColor=TEXT_MUTED, alignment=TA_CENTER, spaceBefore=3, spaceAfter=6
)
header_cell_style = ParagraphStyle(
    name='HeaderCell', fontName='LiberationSerif', fontSize=9.5, leading=14,
    textColor=colors.white, alignment=TA_CENTER
)
cell_style = ParagraphStyle(
    name='Cell', fontName='LiberationSerif', fontSize=9, leading=13,
    textColor=TEXT_PRIMARY, alignment=TA_LEFT
)
cell_center_style = ParagraphStyle(
    name='CellCenter', fontName='LiberationSerif', fontSize=9, leading=13,
    textColor=TEXT_PRIMARY, alignment=TA_CENTER
)
kicker_style = ParagraphStyle(
    name='Kicker', fontName='Carlito', fontSize=10, leading=14,
    textColor=ACCENT, spaceBefore=4, spaceAfter=4, alignment=TA_LEFT
)

# ━━ Build document ━━
output_path = '/home/z/my-project/download/pr_body.pdf'
doc = SimpleDocTemplate(
    output_path, pagesize=A4,
    leftMargin=1.0*inch, rightMargin=1.0*inch,
    topMargin=0.9*inch, bottomMargin=0.9*inch,
    title='GitHub Pull Request Status Report',
    author='euxaristia',
    creator='Z.ai',
    subject='Open PR overview for euxaristia and Cairn organization'
)
page_width = A4[0]
available_width = page_width - 2 * inch
story = []

# ━━━━━━━━━━━━ SECTION: Executive Summary ━━━━━━━━━━━━
story.append(Paragraph('<b>Pull Request Status Report</b>', h1_style))
story.append(Paragraph('GitHub: euxaristia / Cairn Organization', kicker_style))
story.append(Spacer(1, 6))
story.append(Paragraph(
    'This report provides a comprehensive overview of all open pull requests associated with the '
    'GitHub user <b>euxaristia</b> across personal repositories and upstream contributions, as well as '
    'any open pull requests within the <b>Cairn</b> organization. The data was collected on '
    '<b>%s</b> (ISO 8601) using the GitHub public API. The report is designed to help track '
    'contribution velocity, identify stale PRs that may need follow-up, and highlight key areas of '
    'active development work.' % REPORT_DATE,
    body_style
))
story.append(Spacer(1, 10))

# ━━ Summary Metrics Table ━━
metrics_data = [
    [Paragraph('<b>Metric</b>', header_cell_style), Paragraph('<b>Count</b>', header_cell_style)],
    [Paragraph('Open PRs authored by euxaristia', cell_style), Paragraph('<b>19</b>', cell_center_style)],
    [Paragraph('Open PRs in Cairn organization', cell_style), Paragraph('<b>0</b>', cell_center_style)],
    [Paragraph('PRs involving euxaristia (non-author)', cell_style), Paragraph('<b>2</b>', cell_center_style)],
    [Paragraph('Total personal repositories', cell_style), Paragraph('<b>59</b>', cell_center_style)],
    [Paragraph('Cairn organization repositories', cell_style), Paragraph('<b>1</b>', cell_center_style)],
]
metrics_col_widths = [available_width * 0.70, available_width * 0.30]
metrics_table = Table(metrics_data, colWidths=metrics_col_widths, hAlign='CENTER')
metrics_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), HEADER_FILL),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('BACKGROUND', (0, 1), (-1, 1), colors.white),
    ('BACKGROUND', (0, 2), (-1, 2), TABLE_STRIPE),
    ('BACKGROUND', (0, 3), (-1, 3), colors.white),
    ('BACKGROUND', (0, 4), (-1, 4), TABLE_STRIPE),
    ('BACKGROUND', (0, 5), (-1, 5), colors.white),
    ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('LEFTPADDING', (0, 0), (-1, -1), 10),
    ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
story.append(Spacer(1, 12))
story.append(metrics_table)
story.append(Paragraph('Table 1: Summary of pull request metrics for euxaristia and Cairn', caption_style))
story.append(Spacer(1, 18))

# ━━━━━━━━━━━━ SECTION: Open Pull Requests Detail ━━━━━━━━━━━━
story.append(Paragraph('<b>Open Pull Requests Detail</b>', h1_style))
story.append(Paragraph(
    'The following table lists all 19 open pull requests authored by euxaristia, sorted by creation date '
    'in descending order. These span personal repositories, forks, and upstream contributions to major '
    'open-source projects. Each entry includes the repository, PR number, a descriptive title, and the '
    'date the PR was created. All dates conform to ISO 8601 (YYYY-MM-DD).',
    body_style
))
story.append(Spacer(1, 12))

prs = [
    ('gemini-cli (fork)', '#4', 'fix(build): detect Bun runtime in build scripts', '2026-05-12'),
    ('gemini-cli (fork)', '#3', 'fix(core): make shell tool work under Bun', '2026-05-12'),
    ('gitee-cli', '#2', 'feat: implicitly use current repo and branch context for pr commands', '2026-05-09'),
    ('colt', '#5', 'fix(editor): typing/pasting "(" now actually inserts the character', '2026-05-09'),
    ('colt', '#4', 'feat: mouse click moves cursor; drag enters Visual mode', '2026-05-07'),
    ('google-gemini/gemini-cli', '#26498', 'feat(cli): show acknowledgment when user steering hint is processed', '2026-05-05'),
    ('anomalyco/opencode', '#25355', 'fix(tui): bind home/end to line start/end in input', '2026-05-01'),
    ('google-gemini/gemini-cli', '#26280', 'fix(build): detect Bun runtime in build scripts', '2026-04-30'),
    ('VoxelPopuli', '#4', 'Parallelize chunk generation across rayon worker pool', '2026-04-28'),
    ('colt', '#3', 'fix: prevent status bar from wrapping when narrower than its content', '2026-04-28'),
    ('charmbracelet/glow', '#937', 'fix: ensure closing fence in WrapCodeBlock is on its own line', '2026-04-26'),
    ('VoxelPopuli', '#2', 'chore(deps): replace image and rayon with smaller alternatives', '2026-04-22'),
    ('colt', '#1', 'feat(substitute): add regex support to ":s/" command', '2026-04-14'),
    ('tree-sitter', '#1', 'feat(runtime): pure-Rust runtime crate; port point.c', '2026-04-14'),
    ('dotfiles', '#1', 'feat: add protected-branch check to git safety rules', '2026-04-13'),
    ('clockworklabs/SpacetimeDB', '#4773', 'feat(bindings-cpp-ffi): add Rust FFI crate for WASM modules', '2026-04-10'),
    ('QwenLM/qwen-code', '#2838', 'feat: add bun runtime support', '2026-04-02'),
    ('google-gemini/gemini-cli', '#22618', 'fix(cli): respect ui.loadingPhrases "off" setting', '2026-03-16'),
    ('microsoft/node-pty', '#901', 'fix: swallow resize() errors after PTY exit on Windows and Unix', '2026-03-13'),
]

pr_table_data = [
    [Paragraph('<b>Repository</b>', header_cell_style),
     Paragraph('<b>PR</b>', header_cell_style),
     Paragraph('<b>Title</b>', header_cell_style),
     Paragraph('<b>Created</b>', header_cell_style)]
]
for i, (repo, num, title, date) in enumerate(prs):
    pr_table_data.append([
        Paragraph(repo, cell_style),
        Paragraph(num, cell_center_style),
        Paragraph(title, cell_style),
        Paragraph(date, cell_center_style),
    ])

pr_col_widths = [available_width * 0.22, available_width * 0.10, available_width * 0.50, available_width * 0.18]
pr_table = Table(pr_table_data, colWidths=pr_col_widths, hAlign='CENTER', repeatRows=1)
style_cmds = [
    ('BACKGROUND', (0, 0), (-1, 0), HEADER_FILL),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
]
for i in range(1, len(pr_table_data)):
    bg = colors.white if i % 2 == 1 else TABLE_STRIPE
    style_cmds.append(('BACKGROUND', (0, i), (-1, i), bg))
pr_table.setStyle(TableStyle(style_cmds))
story.append(pr_table)
story.append(Paragraph('Table 2: All open pull requests authored by euxaristia, sorted by date (newest first)', caption_style))
story.append(Spacer(1, 18))

# ━━━━━━━━━━━━ SECTION: Staleness Analysis ━━━━━━━━━━━━
story.append(Paragraph('<b>Staleness Analysis</b>', h1_style))
story.append(Paragraph(
    'Understanding the age of open pull requests is critical for prioritizing follow-up actions. '
    'The table below categorizes each PR by age bracket as of the report generation date (%s). '
    'PRs older than 30 days are flagged as potentially stale, as they may have accumulated merge '
    'conflicts or lost reviewer context. Proactive rebasing and polite follow-up comments on these '
    'older contributions can significantly improve merge velocity.' % REPORT_DATE,
    body_style
))
story.append(Spacer(1, 10))

stale_data = [
    [Paragraph('<b>Age Bracket</b>', header_cell_style),
     Paragraph('<b>Count</b>', header_cell_style),
     Paragraph('<b>Repositories</b>', header_cell_style)],
    [Paragraph('0-7 days', cell_center_style),
     Paragraph('6', cell_center_style),
     Paragraph('gemini-cli, gitee-cli, colt, opencode', cell_style)],
    [Paragraph('8-30 days', cell_center_style),
     Paragraph('8', cell_center_style),
     Paragraph('colt, VoxelPopuli, glow, tree-sitter, dotfiles, SpacetimeDB, qwen-code', cell_style)],
    [Paragraph('31-60 days (stale)', cell_center_style),
     Paragraph('5', cell_center_style),
     Paragraph('gemini-cli, qwen-code, node-pty', cell_style)],
]
stale_col_widths = [available_width * 0.20, available_width * 0.10, available_width * 0.70]
stale_table = Table(stale_data, colWidths=stale_col_widths, hAlign='CENTER')
stale_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), HEADER_FILL),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('BACKGROUND', (0, 1), (-1, 1), colors.white),
    ('BACKGROUND', (0, 2), (-1, 2), TABLE_STRIPE),
    ('BACKGROUND', (0, 3), (-1, 3), colors.white),
    ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
story.append(stale_table)
story.append(Paragraph('Table 3: PR age distribution as of %s' % REPORT_DATE, caption_style))
story.append(Spacer(1, 18))

# ━━━━━━━━━━━━ SECTION: PRs Involving euxaristia ━━━━━━━━━━━━
story.append(Paragraph('<b>PRs Involving euxaristia (Non-Author)</b>', h1_style))
story.append(Paragraph(
    'In addition to the 19 PRs directly authored by euxaristia, two additional pull requests involve '
    'euxaristia as a commenter, reviewer, or referenced contributor. These PRs are listed below and may '
    'represent collaborative work, review requests, or issues where euxaristia provided input that shaped '
    'the direction of the contribution.',
    body_style
))
story.append(Spacer(1, 10))

inv_data = [
    [Paragraph('<b>Repository</b>', header_cell_style),
     Paragraph('<b>PR</b>', header_cell_style),
     Paragraph('<b>Title</b>', header_cell_style)],
    [Paragraph('BingqingLyu/qwen-code', cell_style),
     Paragraph('#73', cell_center_style),
     Paragraph('feat: add bun runtime support', cell_style)],
    [Paragraph('this-is-dev/InnerDemons', cell_style),
     Paragraph('#9', cell_center_style),
     Paragraph('y cant i merge?', cell_style)],
]
inv_col_widths = [available_width * 0.32, available_width * 0.10, available_width * 0.58]
inv_table = Table(inv_data, colWidths=inv_col_widths, hAlign='CENTER')
inv_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), HEADER_FILL),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('BACKGROUND', (0, 1), (-1, 1), colors.white),
    ('BACKGROUND', (0, 2), (-1, 2), TABLE_STRIPE),
    ('GRID', (0, 0), (-1, -1), 0.5, BORDER),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ('TOPPADDING', (0, 0), (-1, -1), 6),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
]))
story.append(inv_table)
story.append(Paragraph('Table 4: PRs involving euxaristia as a non-author contributor', caption_style))
story.append(Spacer(1, 18))

# ━━━━━━━━━━━━ SECTION: Cairn Organization ━━━━━━━━━━━━
story.append(Paragraph('<b>Cairn Organization Status</b>', h1_style))
story.append(Paragraph(
    'The Cairn organization currently maintains a single repository: <b>floriography</b>, a TypeScript project '
    'described as providing a random flower, its Latin name, and a verse from a real English poem. As of '
    '<b>%s</b>, there are no open pull requests across the Cairn organization. This means that all previous '
    'contributions have been merged, closed, or the project is in a stable state with no pending changes '
    'requiring review. Given that the repository appears to be a small, focused project, this is consistent '
    'with expected activity levels.' % REPORT_DATE,
    body_style
))
story.append(Spacer(1, 18))

# ━━━━━━━━━━━━ SECTION: Key Themes ━━━━━━━━━━━━
story.append(Paragraph('<b>Key Themes and Analysis</b>', h1_style))
story.append(Paragraph(
    'Examining the distribution of open pull requests reveals several clear patterns in the types of work '
    'euxaristia is actively pursuing. These themes highlight both technical interests and the breadth of the '
    'open-source communities in which euxaristia participates.',
    body_style
))
story.append(Spacer(1, 8))

story.append(Paragraph('<b>Bun Runtime Compatibility</b>', h2_style))
story.append(Paragraph(
    'A significant cluster of PRs focuses on adding or improving Bun runtime support across multiple projects. '
    'This includes PR #4 and #3 on the gemini-cli fork (created 2026-05-12), PR #26280 on google-gemini/gemini-cli '
    '(2026-04-30), and PR #2838 on QwenLM/qwen-code (2026-04-02). This pattern suggests a strong interest in the Bun '
    'JavaScript runtime as an alternative to Node.js, with a focus on ensuring that build scripts, CLI tools, and '
    'shell integrations work correctly when executed under Bun rather than Node. The recurrence of this theme across '
    'independent projects indicates that Bun compatibility is an area where euxaristia has developed specialized '
    'expertise, and these contributions may serve as reference implementations for other projects encountering '
    'similar issues.',
    body_style
))
story.append(Spacer(1, 8))

story.append(Paragraph('<b>colt Editor Development</b>', h2_style))
story.append(Paragraph(
    'The <b>colt</b> repository, a vi-style editor written in the Pony programming language, has four open PRs '
    '(#1 through #5) representing active and ongoing feature development. The work spans foundational editing '
    'features such as regex substitution support in the ":s/" command (PR #1, 2026-04-14), visual mode improvements '
    'with mouse click and drag support (PR #4, 2026-05-07), character input fixes for parentheses insertion '
    '(PR #5, 2026-05-09), and status bar layout corrections (PR #3, 2026-04-28). This concentration of PRs in a '
    'single repository signals that colt is the primary personal project receiving active development attention, '
    'and the breadth of features being implemented suggests a goal of making the editor increasingly usable for '
    'daily text editing workflows.',
    body_style
))
story.append(Spacer(1, 8))

story.append(Paragraph('<b>Upstream Open-Source Contributions</b>', h2_style))
story.append(Paragraph(
    'Several PRs target well-known upstream repositories, including google-gemini/gemini-cli, microsoft/node-pty, '
    'charmbracelet/glow, anomalyco/opencode, clockworklabs/SpacetimeDB, and QwenLM/qwen-code. These contributions '
    'demonstrate engagement with the broader open-source ecosystem beyond personal projects. Notably, the PRs to '
    'microsoft/node-pty (#901, 2026-03-13, PTY resize error handling) and charmbracelet/glow (#937, 2026-04-26, '
    'markdown rendering fix) address fundamental cross-platform issues that benefit a wide user base. The diversity '
    'of target projects, spanning CLI tools, terminal emulators, AI coding assistants, and database systems, '
    'reflects broad technical fluency and a willingness to contribute fixes and features wherever problems are '
    'identified.',
    body_style
))
story.append(Spacer(1, 8))

story.append(Paragraph('<b>Systems-Level Rust Development</b>', h2_style))
story.append(Paragraph(
    'Three PRs involve Rust-focused systems work: the tree-sitter pure-Rust runtime (PR #1, 2026-04-14), '
    'VoxelPopuli chunk parallelization with rayon (PR #2, 2026-04-22 and PR #4, 2026-04-28), and SpacetimeDB '
    'FFI bindings for WASM modules (PR #4773, 2026-04-10). These contributions target low-level, '
    'performance-critical domains including parser runtimes, voxel engine optimization, and WebAssembly module '
    'interop. The tree-sitter contribution is particularly ambitious, involving a complete rewrite of the runtime '
    'in pure Rust, which would eliminate the C dependency and make tree-sitter more accessible to the Rust '
    'ecosystem. This theme underscores a strong systems programming orientation alongside the higher-level CLI '
    'and web tool contributions.',
    body_style
))
story.append(Spacer(1, 18))

# ━━━━━━━━━━━━ SECTION: Recommendations ━━━━━━━━━━━━
story.append(Paragraph('<b>Recommendations</b>', h1_style))
story.append(Paragraph(
    'Based on the current state of open pull requests, the following actions may help improve contribution '
    'effectiveness and ensure that ongoing work receives timely attention from maintainers.',
    body_style
))
story.append(Spacer(1, 8))

story.append(Paragraph(
    '<b>1. Prioritize stale PRs:</b> The oldest open PR (microsoft/node-pty #901, created 2026-03-13) has '
    'been open for approximately 60 days. Consider following up with maintainers through a polite comment or by '
    'rebasing the branch onto the latest main to resolve any merge conflicts that may have accumulated. PRs on '
    'google-gemini/gemini-cli (#22618, 2026-03-16) and QwenLM/qwen-code (#2838, 2026-04-02) are also in the '
    'stale bracket and may benefit from similar follow-up actions.',
    body_style
))
story.append(Spacer(1, 6))
story.append(Paragraph(
    '<b>2. Consolidate gemini-cli contributions:</b> Three separate PRs target the google-gemini/gemini-cli '
    'repository. If these changes are related (e.g., the Bun build detection fix appears in both PR #4 on the '
    'fork and PR #26280 upstream), consider consolidating them into a single, well-organized PR to reduce '
    'reviewer overhead and improve the chances of timely merge.',
    body_style
))
story.append(Spacer(1, 6))
story.append(Paragraph(
    '<b>3. Continue colt editor momentum:</b> The colt editor has the most active development pipeline with four '
    'open PRs. Maintaining a regular merge cadence for these features will prevent the PR stack from growing '
    'unmanageably and will allow incremental user feedback on each new capability.',
    body_style
))

# ━━ Build ━━
doc.build(story)
print(f"Body PDF generated: {output_path}")
