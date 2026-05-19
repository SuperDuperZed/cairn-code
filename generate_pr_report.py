#!/usr/bin/env python3
"""Generate PR report PDF for euxaristia."""
import json, os, sys
from datetime import datetime, timezone

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

# ━━ Fonts ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
pdfmetrics.registerFont(TTFont('Times New Roman', '/usr/share/fonts/truetype/dejavu/DejaVuSerif.ttf'))
pdfmetrics.registerFont(TTFont('Times New Roman Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSerif-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Calibri', '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf'))
pdfmetrics.registerFont(TTFont('Calibri Bold', '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf'))
pdfmetrics.registerFont(TTFont('DejaVuSans', '/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf'))
registerFontFamily('Times New Roman', normal='Times New Roman', bold='Times New Roman Bold')
registerFontFamily('Calibri', normal='Calibri', bold='Calibri Bold')
registerFontFamily('DejaVuSans', normal='DejaVuSans', bold='DejaVuSans')

# ━━ Palette ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
ACCENT       = colors.HexColor('#522cc5')
TEXT_PRIMARY  = colors.HexColor('#232220')
TEXT_MUTED    = colors.HexColor('#87827a')
BG_SURFACE   = colors.HexColor('#e2ded8')
BG_PAGE      = colors.HexColor('#f2f1ef')
TABLE_HEADER_COLOR = ACCENT
TABLE_HEADER_TEXT  = colors.white
TABLE_ROW_EVEN     = colors.white
TABLE_ROW_ODD      = BG_SURFACE

# ━━ Styles ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
title_style = ParagraphStyle('Title', fontName='Times New Roman', fontSize=28, leading=34, textColor=TEXT_PRIMARY, spaceAfter=6)
subtitle_style = ParagraphStyle('Subtitle', fontName='Calibri', fontSize=12, leading=16, textColor=TEXT_MUTED, spaceAfter=18)
h1_style = ParagraphStyle('H1', fontName='Times New Roman', fontSize=18, leading=22, textColor=ACCENT, spaceBefore=18, spaceAfter=10)
h2_style = ParagraphStyle('H2', fontName='Times New Roman', fontSize=14, leading=18, textColor=TEXT_PRIMARY, spaceBefore=14, spaceAfter=8)
body_style = ParagraphStyle('Body', fontName='Times New Roman', fontSize=10.5, leading=16, textColor=TEXT_PRIMARY, alignment=TA_JUSTIFY, spaceAfter=6)
small_style = ParagraphStyle('Small', fontName='Calibri', fontSize=9, leading=13, textColor=TEXT_MUTED)
meta_style = ParagraphStyle('Meta', fontName='Calibri', fontSize=10, leading=14, textColor=TEXT_MUTED, alignment=TA_CENTER)

header_cell = ParagraphStyle('HeaderCell', fontName='Times New Roman', fontSize=9.5, leading=13, textColor=colors.white, alignment=TA_CENTER)
cell_style = ParagraphStyle('Cell', fontName='Times New Roman', fontSize=9, leading=13, textColor=TEXT_PRIMARY, alignment=TA_LEFT)
cell_center = ParagraphStyle('CellCenter', fontName='Times New Roman', fontSize=9, leading=13, textColor=TEXT_PRIMARY, alignment=TA_CENTER)
cell_bold = ParagraphStyle('CellBold', fontName='Times New Roman', fontSize=9, leading=13, textColor=TEXT_PRIMARY)
status_style = ParagraphStyle('Status', fontName='Times New Roman', fontSize=9, leading=13, textColor=TEXT_PRIMARY, alignment=TA_CENTER)

# ━━ Load data ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
with open('/home/z/my-project/pr_data.json') as f:
    prs = json.load(f)

with open('/home/z/my-project/pr_report_data.json') as f:
    prev_prs = json.load(f)

prev_keys = {p['key'] for p in prev_prs}
curr_keys = {p['key'] for p in prs}
merged_closed = prev_keys - curr_keys
new_prs = curr_keys - prev_keys

def fmt_date(iso):
    if not iso:
        return '--'
    try:
        dt = datetime.fromisoformat(iso.replace('Z', '+00:00'))
        return dt.strftime('%b %d, %Y')
    except:
        return iso[:10]

def assess_pr(pr):
    """Determine the actionable status of a PR."""
    reviews = pr.get('reviews', [])
    review_states = [r['state'] for r in reviews]
    issue_comments = pr.get('issue_comments', [])
    commits = pr.get('commits', [])
    rev_comments = pr.get('review_comments', [])
    labels = pr.get('labels', [])

    has_changes_requested = 'CHANGES_REQUESTED' in review_states
    has_approved = 'APPROVED' in review_states

    if not reviews and not issue_comments:
        return 'Awaiting Review', 'No reviewer engagement yet'
    if has_approved:
        return 'Approved', 'Ready to merge'
    if has_changes_requested:
        # Check if author pushed after the review
        latest_review_date = max((r['submitted_at'] for r in reviews if r['state'] == 'CHANGES_REQUESTED'), default='')
        if latest_review_date and commits:
            author_commits_after = [c for c in commits if c.get('date', '') > latest_review_date and c.get('author', '') == pr.get('author', '')]
            if author_commits_after:
                return 'In Review Cycle', 'Author addressed feedback, awaiting re-review'
        return 'Changes Requested', 'Feedback not yet addressed'
    if issue_comments and not reviews:
        last_comment_date = max((c['created_at'] for c in issue_comments), default='')
        # Check if a maintainer commented
        maintainer_comments = [c for c in issue_comments if c.get('user', '') != pr.get('author', '')]
        if maintainer_comments:
            return 'Has Feedback', 'Maintainer commented, check conversation'
    if reviews and not has_changes_requested:
        return 'Under Review', 'Reviewer engaged, no changes requested yet'
    if not reviews and len(issue_comments) >= 2:
        return 'Stalled', 'Multiple comments but no formal review'
    return 'Active', 'Open and in progress'

def get_status_color(status):
    colors_map = {
        'Approved': colors.HexColor('#16a34a'),
        'In Review Cycle': colors.HexColor('#2563eb'),
        'Under Review': colors.HexColor('#2563eb'),
        'Has Feedback': colors.HexColor('#d97706'),
        'Changes Requested': colors.HexColor('#dc2626'),
        'Stalled': colors.HexColor('#dc2626'),
        'Awaiting Review': colors.HexColor('#87827a'),
        'Active': colors.HexColor('#16a34a'),
    }
    return colors_map.get(status, TEXT_MUTED)

# ━━ Build PDF ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
output_path = f'/home/z/my-project/download/GitHub_PR_Report_euxaristia_{datetime.now().strftime("%Y-%m-%d")}.pdf'
doc = SimpleDocTemplate(
    output_path, pagesize=A4,
    leftMargin=0.8*inch, rightMargin=0.8*inch,
    topMargin=0.7*inch, bottomMargin=0.7*inch,
)

page_width = A4[0] - 1.6*inch
story = []

# ── Title ──
story.append(Paragraph('<b>GitHub Pull Request Report</b>', title_style))
story.append(Paragraph('euxaristia -- Open PRs and Review Status', subtitle_style))
story.append(Paragraph(f'Generated: {datetime.now(timezone.utc).strftime("%B %d, %Y")} UTC', meta_style))
story.append(Spacer(1, 12))

# ── Summary stats ──
story.append(Paragraph('<b>Summary</b>', h1_style))

total_open = len(prs)
total_add = sum(p['additions'] for p in prs)
total_del = sum(p['deletions'] for p in prs)
total_files = sum(p['changed_files'] for p in prs)
need_action = sum(1 for p in prs if assess_pr(p)[0] in ('Changes Requested', 'Stalled'))

summary_data = [
    [Paragraph('<b>Metric</b>', header_cell), Paragraph('<b>Value</b>', header_cell)],
    [Paragraph('Open PRs', cell_style), Paragraph(str(total_open), cell_center)],
    [Paragraph('New since last report', cell_style), Paragraph(str(len(new_prs)), cell_center)],
    [Paragraph('Merged/Closed since last report', cell_style), Paragraph(str(len(merged_closed)), cell_center)],
    [Paragraph('Total additions', cell_style), Paragraph(f'+{total_add:,}', cell_center)],
    [Paragraph('Total deletions', cell_style), Paragraph(f'-{total_del:,}', cell_center)],
    [Paragraph('Total changed files', cell_style), Paragraph(str(total_files), cell_center)],
    [Paragraph('PRs needing action', cell_style), Paragraph(str(need_action), cell_center)],
]
avail = page_width
col_w = [avail*0.6, avail*0.4]
summary_table = Table(summary_data, colWidths=col_w, hAlign='CENTER')
ts = []
for i in range(1, len(summary_data)):
    bg = TABLE_ROW_ODD if i % 2 == 0 else TABLE_ROW_EVEN
    ts.append(('BACKGROUND', (0, i), (-1, i), bg))
summary_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_COLOR),
    ('TEXTCOLOR', (0, 0), (-1, 0), TABLE_HEADER_TEXT),
    ('GRID', (0, 0), (-1, -1), 0.5, TEXT_MUTED),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('LEFTPADDING', (0, 0), (-1, -1), 8),
    ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
] + ts))
story.append(summary_table)
story.append(Spacer(1, 18))

# ── Changes since last report ──
if merged_closed:
    story.append(Paragraph('<b>PRs Merged or Closed Since Last Report</b>', h1_style))
    closed_items = [[
        Paragraph('<b>PR</b>', header_cell),
        Paragraph('<b>State</b>', header_cell),
    ]]
    for key in sorted(merged_closed):
        prev = next((p for p in prev_prs if p['key'] == key), None)
        if prev:
            closed_items.append([
                Paragraph(f'<b>{key}</b>', cell_bold),
                Paragraph('Merged/Closed', cell_center),
            ])
    ct = Table(closed_items, colWidths=[avail*0.65, avail*0.35], hAlign='CENTER')
    ct_styles = [
        ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_COLOR),
        ('TEXTCOLOR', (0, 0), (-1, 0), TABLE_HEADER_TEXT),
        ('GRID', (0, 0), (-1, -1), 0.5, TEXT_MUTED),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
    ]
    for i in range(1, len(closed_items)):
        bg = TABLE_ROW_ODD if i % 2 == 0 else TABLE_ROW_EVEN
        ct_styles.append(('BACKGROUND', (0, i), (-1, i), bg))
    ct.setStyle(TableStyle(ct_styles))
    story.append(ct)
    story.append(Spacer(1, 18))

# ── All Open PRs Table ──
story.append(Paragraph('<b>All Open Pull Requests</b>', h1_style))
story.append(Paragraph('Sorted by repository, with review status assessment.', body_style))
story.append(Spacer(1, 10))

pr_table_data = [[
    Paragraph('<b>PR</b>', header_cell),
    Paragraph('<b>Title</b>', header_cell),
    Paragraph('<b>Created</b>', header_cell),
    Paragraph('<b>Status</b>', header_cell),
    Paragraph('<b>+/-</b>', header_cell),
]]

# Sort by repo then number
sorted_prs = sorted(prs, key=lambda p: (p['repo'], p['number']))

for pr in sorted_prs:
    key = pr['key']
    status, detail = assess_pr(pr)
    status_color = get_status_color(status)
    title_short = pr['title'][:55] + ('...' if len(pr['title']) > 55 else '')
    stats = f"+{pr['additions']}/-{pr['deletions']}"

    pr_table_data.append([
        Paragraph(f'<b>{key}</b>', cell_bold),
        Paragraph(title_short, cell_style),
        Paragraph(fmt_date(pr['created_at']), cell_center),
        Paragraph(f'<font color="{status_color.hexval()}">{status}</font>', status_style),
        Paragraph(stats, cell_center),
    ])

cw = [avail*0.20, avail*0.35, avail*0.15, avail*0.17, avail*0.13]
pr_table = Table(pr_table_data, colWidths=cw, hAlign='CENTER', repeatRows=1)
pr_ts = [
    ('BACKGROUND', (0, 0), (-1, 0), TABLE_HEADER_COLOR),
    ('TEXTCOLOR', (0, 0), (-1, 0), TABLE_HEADER_TEXT),
    ('GRID', (0, 0), (-1, -1), 0.5, TEXT_MUTED),
    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ('TOPPADDING', (0, 0), (-1, -1), 5),
    ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
]
for i in range(1, len(pr_table_data)):
    bg = TABLE_ROW_ODD if i % 2 == 0 else TABLE_ROW_EVEN
    pr_ts.append(('BACKGROUND', (0, i), (-1, i), bg))
pr_table.setStyle(TableStyle(pr_ts))
story.append(pr_table)
story.append(Spacer(1, 24))

# ── Detailed PR Analysis ──
story.append(Paragraph('<b>Detailed PR Analysis</b>', h1_style))
story.append(Paragraph('In-depth review of each open pull request, including review history, conversation summary, and recommended actions.', body_style))
story.append(Spacer(1, 12))

for pr in sorted_prs:
    key = pr['key']
    status, detail = assess_pr(pr)
    status_color = get_status_color(status)
    reviews = pr.get('reviews', [])
    issue_comments = pr.get('issue_comments', [])
    commits = pr.get('commits', [])
    rev_comments = pr.get('review_comments', [])
    labels = pr.get('labels', [])

    # Section header
    story.append(HRFlowable(width='100%', thickness=0.5, color=BG_SURFACE, spaceAfter=8))
    story.append(Paragraph(f'<b>{key}</b> -- {pr["title"]}', h2_style))

    # Meta line
    meta_parts = [
        f'Created: {fmt_date(pr["created_at"])}',
        f'Updated: {fmt_date(pr["updated_at"])}',
        f'Draft: {"Yes" if pr["draft"] else "No"}',
        f'+{pr["additions"]}/-{pr["deletions"]}',
        f'{pr["changed_files"]} files',
    ]
    if labels:
        meta_parts.append(f'Labels: {", ".join(labels)}')
    story.append(Paragraph(' | '.join(meta_parts), small_style))

    # Status
    story.append(Paragraph(
        f'<font color="{status_color.hexval()}"><b>{status}</b></font> -- {detail}',
        ParagraphStyle('StatusLine', parent=body_style, fontSize=10.5, spaceAfter=6)
    ))

    # Reviews
    if reviews:
        review_lines = []
        for r in reviews:
            ruser = r.get('user', 'unknown')
            rstate = r.get('state', '')
            rdate = fmt_date(r.get('submitted_at', ''))
            review_lines.append(f'{ruser}: {rstate} ({rdate})')
        story.append(Paragraph(f'<b>Reviews ({len(reviews)}):</b> {"; ".join(review_lines)}', small_style))

    # Review comments summary
    if rev_comments:
        story.append(Paragraph(f'<b>Review Comments:</b> {len(rev_comments)} inline comments on code', small_style))

    # Issue comments summary
    if issue_comments:
        last_ic = issue_comments[-1]
        story.append(Paragraph(
            f'<b>Issue Comments ({len(issue_comments)}):</b> Latest by {last_ic.get("user", "?")} on {fmt_date(last_ic.get("created_at", ""))} -- "{last_ic.get("body", "")[:100]}"',
            small_style
        ))

    # Commits
    if commits:
        story.append(Paragraph(f'<b>Commits:</b> {len(commits)} total. Latest: {commits[-1].get("message", "")[:80]}', small_style))

    # CI status
    ci = pr.get('ci_status')
    ci_info = f'{pr.get("ci_total", 0)} checks'
    if ci:
        ci_info += f' ({ci})'
    story.append(Paragraph(f'<b>CI:</b> {ci_info}', small_style))

    story.append(Spacer(1, 10))

# ── Action Items ──
story.append(HRFlowable(width='100%', thickness=1, color=ACCENT, spaceAfter=10))
story.append(Paragraph('<b>Action Items</b>', h1_style))

action_prs = []
for pr in sorted_prs:
    status, detail = assess_pr(pr)
    if status in ('Changes Requested', 'Stalled', 'Awaiting Review'):
        action_prs.append((pr, status, detail))

if action_prs:
    for pr, status, detail in action_prs:
        story.append(Paragraph(f'<b>{pr["key"]}</b> -- <font color="{get_status_color(status).hexval()}">{status}</font>', body_style))
        story.append(Paragraph(f'{detail}', ParagraphStyle('ActionDetail', parent=body_style, leftIndent=12, textColor=TEXT_MUTED)))
        story.append(Spacer(1, 6))
else:
    story.append(Paragraph('No PRs currently require immediate action.', body_style))

# ── Build ──
doc.build(story)
print(f'PDF saved to: {output_path}')
print(f'Pages: approx {len(story)} elements')
