import json
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm, mm
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

# ── Font Registration ──
pdfmetrics.registerFont(TTFont('LiberationSerif', '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'))
pdfmetrics.registerFont(TTFont('LiberationSerif-Bold', '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'))
pdfmetrics.registerFont(TTFont('LiberationSerif-Italic', '/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf'))
pdfmetrics.registerFont(TTFont('LiberationSans', '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf'))
pdfmetrics.registerFont(TTFont('LiberationSans-Bold', '/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf'))
registerFontFamily('LiberationSerif', normal='LiberationSerif', bold='LiberationSerif-Bold', italic='LiberationSerif-Italic')
registerFontFamily('LiberationSans', normal='LiberationSans', bold='LiberationSans-Bold')

# ── Color Palette ──
ACCENT = colors.HexColor('#5d39c8')
TEXT_PRIMARY = colors.HexColor('#1f2022')
TEXT_MUTED = colors.HexColor('#73787f')
BG_SURFACE = colors.HexColor('#d4d8dd')
BG_PAGE = colors.HexColor('#f3f4f6')

# ── Styles ──
cover_title_style = ParagraphStyle(
    'CoverTitle', fontName='LiberationSans-Bold', fontSize=28,
    leading=34, alignment=TA_CENTER, spaceAfter=6, textColor=TEXT_PRIMARY
)
cover_sub_style = ParagraphStyle(
    'CoverSub', fontName='LiberationSerif-Italic', fontSize=14,
    leading=18, alignment=TA_CENTER, textColor=TEXT_MUTED, spaceAfter=4
)
cover_date_style = ParagraphStyle(
    'CoverDate', fontName='LiberationSans', fontSize=12,
    leading=16, alignment=TA_CENTER, textColor=ACCENT
)
h1_style = ParagraphStyle(
    'H1', fontName='LiberationSans-Bold', fontSize=18,
    leading=22, spaceBefore=14, spaceAfter=8, textColor=TEXT_PRIMARY
)
h2_style = ParagraphStyle(
    'H2', fontName='LiberationSans-Bold', fontSize=13,
    leading=16, spaceBefore=10, spaceAfter=5, textColor=ACCENT
)
body_style = ParagraphStyle(
    'Body', fontName='LiberationSerif', fontSize=10,
    leading=14, spaceAfter=4, alignment=TA_JUSTIFY
)
bullet_style = ParagraphStyle(
    'Bullet', fontName='LiberationSerif', fontSize=9.5,
    leading=13, leftIndent=14, bulletIndent=0, spaceBefore=1, spaceAfter=1
)
meta_style = ParagraphStyle(
    'Meta', fontName='LiberationSerif-Italic', fontSize=9,
    leading=12, textColor=TEXT_MUTED, spaceAfter=2
)
small_style = ParagraphStyle(
    'Small', fontName='LiberationSans', fontSize=8.5,
    leading=11, textColor=TEXT_MUTED
)
footer_style = ParagraphStyle(
    'Footer', fontName='LiberationSans', fontSize=8,
    leading=10, textColor=TEXT_MUTED, alignment=TA_CENTER
)

# ── Helpers ──
def fmt_date(iso_str):
    """ISO 8601 -> human-readable like 'May 12, 2026'"""
    if not iso_str:
        return 'N/A'
    try:
        dt = datetime.fromisoformat(iso_str.replace('Z', '+00:00'))
        return dt.strftime('%B %d, %Y')
    except:
        return iso_str[:10]

def ci_badge(status):
    """Return colored status text."""
    if status == 'success':
        return '<font color="#16a34a">Passed</font>'
    elif status == 'failure':
        return '<font color="#dc2626">Failed</font>'
    elif status == 'pending':
        return '<font color="#d97706">Pending</font>'
    return status

def review_badge(review_str):
    """Return formatted review status."""
    if not review_str:
        return 'No reviews'
    state = review_str.split(' by ')[0] if ' by ' in review_str else review_str
    who = review_str.split(' by ')[1] if ' by ' in review_str else ''
    state_map = {
        'APPROVED': ('Approved', '#16a34a'),
        'CHANGES_REQUESTED': ('Changes Requested', '#dc2626'),
        'COMMENTED': ('Commented', '#73787f'),
    }
    label, clr = state_map.get(state, (state, '#73787f'))
    txt = f'<font color="{clr}">{label}</font>'
    if who:
        txt += f' <font color="#73787f">by {who}</font>'
    return txt

def make_pr_table(prs):
    """Build a compact PR table for a group of PRs."""
    col_widths = [3.0*cm, 7.8*cm, 2.2*cm, 2.2*cm, 2.0*cm]
    available = A4[0] - 3.0*cm  # ~17cm
    col_widths = [w/sum(col_widths)*available for w in col_widths]

    header = [
        Paragraph('<b>Repo</b>', ParagraphStyle('TH', fontName='LiberationSans-Bold', fontSize=8, leading=10, textColor=colors.white)),
        Paragraph('<b>Title</b>', ParagraphStyle('TH2', fontName='LiberationSans-Bold', fontSize=8, leading=10, textColor=colors.white)),
        Paragraph('<b>Created</b>', ParagraphStyle('TH3', fontName='LiberationSans-Bold', fontSize=8, leading=10, textColor=colors.white)),
        Paragraph('<b>Updated</b>', ParagraphStyle('TH4', fontName='LiberationSans-Bold', fontSize=8, leading=10, textColor=colors.white)),
        Paragraph('<b>CI</b>', ParagraphStyle('TH5', fontName='LiberationSans-Bold', fontSize=8, leading=10, textColor=colors.white)),
    ]
    data = [header]
    td_style = ParagraphStyle('TD', fontName='LiberationSerif', fontSize=8, leading=10.5)
    td_style_accent = ParagraphStyle('TDA', fontName='LiberationSerif', fontSize=8, leading=10.5, textColor=ACCENT)

    for pr in prs:
        repo_short = pr['repo'].split('/')[-1] if '/' in pr['repo'] else pr['repo']
        data.append([
            Paragraph(f'<b>{repo_short}</b>', td_style_accent),
            Paragraph(pr['title'][:60] + ('...' if len(pr['title']) > 60 else ''), td_style),
            Paragraph(fmt_date(pr['created']).replace(', 2026', ', \'26'), td_style),
            Paragraph(fmt_date(pr['updated']).replace(', 2026', ', \'26'), td_style),
            Paragraph(ci_badge(pr['ci']), ParagraphStyle('CI', fontName='LiberationSans', fontSize=8, leading=10)),
        ])

    t = Table(data, colWidths=col_widths, repeatRows=1)
    style_cmds = [
        ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 4),
        ('RIGHTPADDING', (0, 0), (-1, -1), 4),
        ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e5e7eb')),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
    ]
    t.setStyle(TableStyle(style_cmds))
    return t

def pr_detail_block(pr):
    """Build a detail block for a single PR."""
    elements = []
    # Title line
    title_text = f'<b>{pr["title"]}</b>'
    elements.append(Paragraph(title_text, ParagraphStyle('PRT', fontName='LiberationSans-Bold', fontSize=9.5, leading=12.5, spaceAfter=1)))
    # Meta line
    meta_parts = [
        f'{pr["repo"]}',
        f'Created: {fmt_date(pr["created"])}',
        f'Updated: {fmt_date(pr["updated"])}',
    ]
    if pr.get('labels'):
        meta_parts.append('Labels: ' + ', '.join(pr['labels']))
    elements.append(Paragraph('  |  '.join(meta_parts), meta_style))
    # Stats
    stats = f'+{pr["additions"]} / -{pr["deletions"]} across {pr["changed_files"]} file(s)'
    if pr.get('draft'):
        stats += '  |  Draft'
    elements.append(Paragraph(stats, small_style))
    # Review + CI
    elements.append(Paragraph(
        f'Review: {review_badge(pr["review"])}  |  CI: {ci_badge(pr["ci"])}',
        ParagraphStyle('RevCI', fontName='LiberationSans', fontSize=8.5, leading=11, spaceAfter=2)
    ))
    # Body excerpt
    body = pr.get('body', '')[:200]
    if body:
        elements.append(Paragraph(body, ParagraphStyle('BodyEx', fontName='LiberationSerif', fontSize=9, leading=12, textColor=TEXT_MUTED, spaceAfter=1)))
    elements.append(Paragraph(f'Link: {pr["url"]}', ParagraphStyle('Link', fontName='LiberationSans', fontSize=8, leading=10, textColor=ACCENT, spaceAfter=6)))
    elements.append(Spacer(1, 4))
    return elements

# ── Data ──
prs_data = [
  {
    "repo": "google-gemini/gemini-cli",
    "title": "feat(cli): show acknowledgment when user steering hint is processed",
    "url": "https://github.com/google-gemini/gemini-cli/pull/26498",
    "created": "2026-05-05T11:03:16Z",
    "updated": "2026-05-13T02:22:30Z",
    "draft": False, "mergeable": True,
    "additions": 190, "deletions": 6, "changed_files": 4,
    "review": "COMMENTED by gemini-code-assist[bot]",
    "ci": "pending",
    "labels": ["priority/p2", "area/agent", "status/pr-nudge-sent"],
    "body": "When a user submits a steering hint mid-turn, the CLI silently splices the hint into the conversation with no visible feedback. This PR adds an acknowledgment message when the hint is processed."
  },
  {
    "repo": "google-gemini/gemini-cli",
    "title": "fix(build): detect Bun runtime in build scripts to avoid hardcoded npm",
    "url": "https://github.com/google-gemini/gemini-cli/pull/26280",
    "created": "2026-04-30T19:29:27Z",
    "updated": "2026-05-08T02:21:58Z",
    "draft": False, "mergeable": True,
    "additions": 44, "deletions": 8, "changed_files": 3,
    "review": "COMMENTED by gemini-code-assist[bot]",
    "ci": "pending",
    "labels": ["priority/p2", "area/platform", "status/pr-nudge-sent"],
    "body": "Build scripts invoke npm unconditionally, breaking on Bun-only systems. This PR detects the Bun runtime and uses it instead of npm."
  },
  {
    "repo": "microsoft/node-pty",
    "title": "fix: swallow resize() errors after PTY exit on Windows and Unix",
    "url": "https://github.com/microsoft/node-pty/pull/901",
    "created": "2026-03-13T15:11:41Z",
    "updated": "2026-03-13T15:21:49Z",
    "draft": False, "mergeable": True,
    "additions": 8, "deletions": 2, "changed_files": 2,
    "review": "", "ci": "pending",
    "labels": [],
    "body": "Silently ignore resize() calls after the PTY process has already exited, catching EBADF errors on Unix and preventing crashes on Windows."
  },
  {
    "repo": "QwenLM/qwen-code",
    "title": "feat: add bun runtime support",
    "url": "https://github.com/QwenLM/qwen-code/pull/2838",
    "created": "2026-04-02T20:40:44Z",
    "updated": "2026-04-24T23:31:33Z",
    "draft": False, "mergeable": True,
    "additions": 3683, "deletions": 126, "changed_files": 9,
    "review": "CHANGES_REQUESTED by wenshao",
    "ci": "pending",
    "labels": [],
    "body": "Add support for running Qwen Code with Bun runtime for significantly improved performance. Bun provides 3-5x faster startup, lower memory usage, and native TypeScript support."
  },
  {
    "repo": "clockworklabs/SpacetimeDB",
    "title": "feat(bindings-cpp-ffi): add Rust FFI crate for WASM modules",
    "url": "https://github.com/clockworklabs/SpacetimeDB/pull/4773",
    "created": "2026-04-10T04:22:37Z",
    "updated": "2026-04-28T05:33:51Z",
    "draft": False, "mergeable": None,
    "additions": 2417, "deletions": 0, "changed_files": 6,
    "review": "COMMENTED by chatgpt-codex-connector[bot]",
    "ci": "success",
    "labels": [],
    "body": "Add a new Rust crate providing type registration and FFI dispatch for SpacetimeDB WASM modules, re-implementing the C++ bindings logic in Rust."
  },
  {
    "repo": "charmbracelet/glow",
    "title": "fix: ensure closing fence in WrapCodeBlock is on its own line",
    "url": "https://github.com/charmbracelet/glow/pull/937",
    "created": "2026-04-26T19:33:29Z",
    "updated": "2026-04-26T19:33:29Z",
    "draft": False, "mergeable": True,
    "additions": 3, "deletions": 0, "changed_files": 1,
    "review": "", "ci": "pending",
    "labels": [],
    "body": "WrapCodeBlock glued the closing fence directly onto the last line. When input didn't end with a newline, Markdown renderers never saw the closing fence on its own line."
  },
  {
    "repo": "anomalyco/opencode",
    "title": "fix(tui): bind home/end to line start/end in input",
    "url": "https://github.com/anomalyco/opencode/pull/25355",
    "created": "2026-05-01T20:10:08Z",
    "updated": "2026-05-11T01:39:11Z",
    "draft": False, "mergeable": None,
    "additions": 192, "deletions": 192, "changed_files": 20,
    "review": "", "ci": "pending",
    "labels": [],
    "body": "Closes #14899. Home/End keys are not bound in the input field. This PR adds the bindings to the keybinds source-of-truth file."
  },
  {
    "repo": "euxaristia/adapt",
    "title": "Add shell completion for zsh and bash",
    "url": "https://github.com/euxaristia/adapt/pull/1",
    "created": "2026-05-09T00:27:04Z",
    "updated": "2026-05-12T22:16:24Z",
    "draft": False, "mergeable": None,
    "additions": 239, "deletions": 0, "changed_files": 3,
    "review": "COMMENTED by gemini-code-assist[bot]",
    "ci": "pending",
    "labels": [],
    "body": "Add zsh and bash completions for adapt install and adapt remove commands, using the same data sources as apt's own completions."
  },
  {
    "repo": "euxaristia/gemini-cli",
    "title": "fix(build): detect Bun runtime in build scripts",
    "url": "https://github.com/euxaristia/gemini-cli/pull/4",
    "created": "2026-05-12T20:35:46Z",
    "updated": "2026-05-12T20:38:20Z",
    "draft": False, "mergeable": True,
    "additions": 44, "deletions": 8, "changed_files": 3,
    "review": "COMMENTED by gemini-code-assist[bot]",
    "ci": "pending",
    "labels": [],
    "body": "Build scripts invoke npm and node unconditionally, breaking on Bun-only systems. Detects Bun runtime and uses it instead."
  },
  {
    "repo": "euxaristia/gemini-cli",
    "title": "fix(core): make shell tool work under Bun",
    "url": "https://github.com/euxaristia/gemini-cli/pull/3",
    "created": "2026-05-12T20:05:43Z",
    "updated": "2026-05-12T20:05:50Z",
    "draft": False, "mergeable": True,
    "additions": 39, "deletions": 5, "changed_files": 3,
    "review": "", "ci": "pending",
    "labels": [],
    "body": "Two runtime issues prevented Bun-launched builds from running shell tool calls: ioctl EBADF crash and empty command results."
  },
  {
    "repo": "euxaristia/gitee-cli",
    "title": "feat: implicitly use current repo and branch context for pr commands",
    "url": "https://github.com/euxaristia/gitee-cli/pull/2",
    "created": "2026-05-09T06:29:41Z",
    "updated": "2026-05-09T06:31:48Z",
    "draft": False, "mergeable": True,
    "additions": 116, "deletions": 13, "changed_files": 3,
    "review": "COMMENTED by gemini-code-assist[bot]",
    "ci": "pending",
    "labels": [],
    "body": "Updates gt pr commands to implicitly infer repository context from local git remote, bringing parity with gh behavior."
  },
  {
    "repo": "euxaristia/colt",
    "title": "feat: mouse click moves cursor; drag enters Visual mode",
    "url": "https://github.com/euxaristia/colt/pull/4",
    "created": "2026-05-07T05:37:02Z",
    "updated": "2026-05-09T00:46:47Z",
    "draft": False, "mergeable": True,
    "additions": 138, "deletions": 4, "changed_files": 2,
    "review": "COMMENTED by gemini-code-assist[bot]",
    "ci": "pending",
    "labels": [],
    "body": "Switches SGR mouse mode from press-only to press/release/motion. Left-click moves cursor, drag enters Visual mode."
  },
  {
    "repo": "euxaristia/colt",
    "title": "feat(substitute): add regex support to :s/ command",
    "url": "https://github.com/euxaristia/colt/pull/1",
    "created": "2026-04-14T06:41:21Z",
    "updated": "2026-05-09T00:44:56Z",
    "draft": False, "mergeable": True,
    "additions": 407, "deletions": 11, "changed_files": 5,
    "review": "COMMENTED by gemini-code-assist[bot]",
    "ci": "pending",
    "labels": [],
    "body": "Adds a pure-Pony backtracking regex engine (~230 LOC) and wires it into :s/, :%s/, and :.,$s/ commands. Previously literal-only."
  },
  {
    "repo": "euxaristia/colt",
    "title": "fix(editor): typing/pasting ( now actually inserts the character",
    "url": "https://github.com/euxaristia/colt/pull/5",
    "created": "2026-05-09T00:01:29Z",
    "updated": "2026-05-09T00:41:56Z",
    "draft": False, "mergeable": True,
    "additions": 408, "deletions": 18, "changed_files": 7,
    "review": "COMMENTED by gemini-code-assist[bot]",
    "ci": "pending",
    "labels": [],
    "body": "Two compounding bugs made it impossible to enter an opening paren: auto-insert-pair discarded its work, and insert-mode precedence was wrong."
  },
  {
    "repo": "euxaristia/colt",
    "title": "fix: prevent status bar from wrapping when narrower than its content",
    "url": "https://github.com/euxaristia/colt/pull/3",
    "created": "2026-04-28T04:30:55Z",
    "updated": "2026-05-09T00:41:32Z",
    "draft": False, "mergeable": True,
    "additions": 27, "deletions": 7, "changed_files": 1,
    "review": "COMMENTED by gemini-code-assist[bot]",
    "ci": "pending",
    "labels": [],
    "body": "When status bar content was wider than terminal width, it wrapped onto a second row, scrolling the screen up by one line."
  },
  {
    "repo": "euxaristia/dotfiles",
    "title": "feat: add protected-branch check to git safety rules",
    "url": "https://github.com/euxaristia/dotfiles/pull/1",
    "created": "2026-04-13T21:21:51Z",
    "updated": "2026-05-08T23:59:52Z",
    "draft": False, "mergeable": True,
    "additions": 17, "deletions": 0, "changed_files": 2,
    "review": "COMMENTED by gemini-code-assist[bot]",
    "ci": "pending",
    "labels": [],
    "body": "Add a git pre-push rule to check for protected branches and open a PR instead of pushing directly."
  },
  {
    "repo": "euxaristia/VoxelPopuli",
    "title": "Parallelize chunk generation across rayon worker pool",
    "url": "https://github.com/euxaristia/VoxelPopuli/pull/4",
    "created": "2026-04-28T23:04:07Z",
    "updated": "2026-04-28T23:40:17Z",
    "draft": False, "mergeable": True,
    "additions": 127, "deletions": 117, "changed_files": 2,
    "review": "COMMENTED by gemini-code-assist[bot]",
    "ci": "pending",
    "labels": [],
    "body": "Moves Chunk::generate() from the render thread onto the existing rayon worker pool, utilizing multiple CPU cores for world generation."
  },
  {
    "repo": "euxaristia/VoxelPopuli",
    "title": "chore(deps): replace image and rayon with smaller alternatives",
    "url": "https://github.com/euxaristia/VoxelPopuli/pull/2",
    "created": "2026-04-22T04:03:20Z",
    "updated": "2026-04-22T04:05:00Z",
    "draft": False, "mergeable": None,
    "additions": 26, "deletions": 8, "changed_files": 4,
    "review": "COMMENTED by gemini-code-assist[bot]",
    "ci": "pending",
    "labels": [],
    "body": "Remove image and rayon crates, replacing with direct png decoding and std::thread::spawn to reduce dependency tree."
  },
  {
    "repo": "euxaristia/tree-sitter",
    "title": "feat(runtime): pure-Rust runtime crate; port point.c",
    "url": "https://github.com/euxaristia/tree-sitter/pull/1",
    "created": "2026-04-14T06:31:17Z",
    "updated": "2026-04-14T06:41:38Z",
    "draft": False, "mergeable": True,
    "additions": 241, "deletions": 0, "changed_files": 6,
    "review": "COMMENTED by gemini-code-assist[bot]",
    "ci": "pending",
    "labels": [],
    "body": "Introduces a pure-Rust staticlib crate to progressively replace the C runtime while preserving the tree-sitter C ABI."
  },
]

# ── Group PRs ──
upstream = [p for p in prs_data if '/' in p['repo'] and not p['repo'].startswith('euxaristia/')]
personal = [p for p in prs_data if p['repo'].startswith('euxaristia/')]

upstream.sort(key=lambda x: x['updated'], reverse=True)
personal.sort(key=lambda x: x['updated'], reverse=True)

# ── Build PDF ──
output_path = '/home/z/my-project/download/GitHub_PR_Report_euxaristia_2026-05-13.pdf'
doc = SimpleDocTemplate(
    output_path, pagesize=A4,
    leftMargin=1.5*cm, rightMargin=1.5*cm,
    topMargin=1.5*cm, bottomMargin=1.5*cm,
    title='GitHub PR Report - euxaristia',
    author='euxaristia', creator='Z.ai'
)

story = []

# ── Cover ──
story.append(Spacer(1, 4*cm))
story.append(Paragraph('<b>GitHub PR Report</b>', cover_title_style))
story.append(Spacer(1, 12))
story.append(Paragraph('euxaristia', cover_sub_style))
story.append(Spacer(1, 6))
story.append(Paragraph('May 13, 2026', cover_date_style))
story.append(Spacer(1, 2*cm))

# Summary box
summary_style = ParagraphStyle('SummaryBox', fontName='LiberationSerif', fontSize=11, leading=16, alignment=TA_CENTER, textColor=TEXT_PRIMARY)
story.append(Paragraph(
    f'{len(prs_data)} open pull requests across {len(set(p["repo"] for p in prs_data))} repositories',
    summary_style
))
story.append(Spacer(1, 8))
story.append(Paragraph(
    f'{len(upstream)} upstream contributions  |  {len(personal)} personal repositories',
    ParagraphStyle('SummaryDetail', fontName='LiberationSans', fontSize=10, leading=14, alignment=TA_CENTER, textColor=TEXT_MUTED)
))
story.append(PageBreak())

# ── Executive Summary ──
story.append(Paragraph('<b>Executive Summary</b>', h1_style))
story.append(HRFlowable(width='100%', thickness=0.8, color=ACCENT, spaceBefore=0, spaceAfter=8))

# Stats
total_add = sum(p['additions'] for p in prs_data)
total_del = sum(p['deletions'] for p in prs_data)
total_files = sum(p['changed_files'] for p in prs_data)
ci_pass = sum(1 for p in prs_data if p['ci'] == 'success')
ci_fail = sum(1 for p in prs_data if p['ci'] == 'failure')
ci_pend = sum(1 for p in prs_data if p['ci'] == 'pending')
changes_req = sum(1 for p in prs_data if 'CHANGES_REQUESTED' in p['review'])
approved = sum(1 for p in prs_data if 'APPROVED' in p['review'])
no_review = sum(1 for p in prs_data if not p['review'])

story.append(Paragraph(
    f'This report covers all <b>{len(prs_data)}</b> open pull requests authored by <b>euxaristia</b> across '
    f'<b>{len(set(p["repo"] for p in prs_data))}</b> repositories. The PRs touch <b>{total_add:,}</b> lines added and '
    f'<b>{total_del:,}</b> lines deleted across <b>{total_files}</b> files. '
    f'Of these, <b>{len(upstream)}</b> are contributions to upstream (third-party) repositories and '
    f'<b>{len(personal)}</b> are within personal repositories.',
    body_style
))

# CI Summary
story.append(Spacer(1, 6))
story.append(Paragraph('<b>CI Status Overview</b>', h2_style))
ci_data = [
    [Paragraph('<b>Status</b>', ParagraphStyle('THead', fontName='LiberationSans-Bold', fontSize=9, leading=12, textColor=colors.white)),
     Paragraph('<b>Count</b>', ParagraphStyle('THead2', fontName='LiberationSans-Bold', fontSize=9, leading=12, textColor=colors.white))],
    [Paragraph('<font color="#16a34a">Passed</font>', ParagraphStyle('TD', fontName='LiberationSerif', fontSize=9, leading=12)), str(ci_pass)],
    [Paragraph('<font color="#d97706">Pending</font>', ParagraphStyle('TD2', fontName='LiberationSerif', fontSize=9, leading=12)), str(ci_pend)],
    [Paragraph('<font color="#dc2626">Failed</font>', ParagraphStyle('TD3', fontName='LiberationSerif', fontSize=9, leading=12)), str(ci_fail)],
]
ci_table = Table(ci_data, colWidths=[4*cm, 3*cm])
ci_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e5e7eb')),
    ('TOPPADDING', (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
]))
story.append(ci_table)

# Review Summary
story.append(Spacer(1, 8))
story.append(Paragraph('<b>Review Status Overview</b>', h2_style))
rev_data = [
    [Paragraph('<b>Status</b>', ParagraphStyle('THead', fontName='LiberationSans-Bold', fontSize=9, leading=12, textColor=colors.white)),
     Paragraph('<b>Count</b>', ParagraphStyle('THead2', fontName='LiberationSans-Bold', fontSize=9, leading=12, textColor=colors.white))],
    [Paragraph('<font color="#16a34a">Approved</font>', ParagraphStyle('TD', fontName='LiberationSerif', fontSize=9, leading=12)), str(approved)],
    [Paragraph('<font color="#dc2626">Changes Requested</font>', ParagraphStyle('TD2', fontName='LiberationSerif', fontSize=9, leading=12)), str(changes_req)],
    [Paragraph('<font color="#73787f">Commented (Bot)</font>', ParagraphStyle('TD3', fontName='LiberationSerif', fontSize=9, leading=12)), str(len(prs_data) - approved - changes_req - no_review)],
    [Paragraph('No Reviews', ParagraphStyle('TD4', fontName='LiberationSerif', fontSize=9, leading=12)), str(no_review)],
]
rev_table = Table(rev_data, colWidths=[4*cm, 3*cm])
rev_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), ACCENT),
    ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e5e7eb')),
    ('TOPPADDING', (0, 0), (-1, -1), 4),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f9fafb')]),
]))
story.append(rev_table)

# ── Upstream Contributions ──
story.append(Spacer(1, 12))
story.append(Paragraph(f'<b>Upstream Contributions ({len(upstream)})</b>', h1_style))
story.append(HRFlowable(width='100%', thickness=0.8, color=ACCENT, spaceBefore=0, spaceAfter=8))
story.append(Paragraph(
    'The following PRs are open against third-party repositories maintained by other organizations. '
    'These represent contributions to external open-source projects.',
    body_style
))
story.append(Spacer(1, 6))

# Overview table for upstream
story.append(make_pr_table(upstream))
story.append(Spacer(1, 10))

# Detailed blocks for upstream
for pr in upstream:
    story.extend(pr_detail_block(pr))

# ── Personal Repos ──
story.append(Paragraph(f'<b>Personal Repositories ({len(personal)})</b>', h1_style))
story.append(HRFlowable(width='100%', thickness=0.8, color=ACCENT, spaceBefore=0, spaceAfter=8))
story.append(Paragraph(
    'The following PRs are open within personal repositories under the euxaristia organization.',
    body_style
))
story.append(Spacer(1, 6))

story.append(make_pr_table(personal))
story.append(Spacer(1, 10))

for pr in personal:
    story.extend(pr_detail_block(pr))

# ── Footer ──
story.append(Spacer(1, 12))
story.append(HRFlowable(width='100%', thickness=0.4, color=TEXT_MUTED, spaceBefore=4, spaceAfter=4))
story.append(Paragraph('Generated May 13, 2026  |  github.com/euxaristia', footer_style))

doc.build(story)
print(f'Report saved to {output_path}')
