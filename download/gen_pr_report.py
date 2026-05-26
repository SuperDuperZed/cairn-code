#!/usr/bin/env python3
"""Generate GitHub PR Report PDF for euxaristia."""

import json
import os
from datetime import datetime

from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm, cm
from reportlab.lib.colors import HexColor
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    PageBreak, KeepTogether, HRFlowable
)

C_PRIMARY = HexColor('#1a1a2e')
C_ACCENT = HexColor('#e94560')
C_TEXT = HexColor('#2d2d2d')
C_MUTED = HexColor('#6b7280')
C_LIGHT_BG = HexColor('#f8fafc')
C_WHITE = HexColor('#ffffff')
C_GREEN = HexColor('#059669')
C_RED = HexColor('#dc2626')
C_YELLOW = HexColor('#d97706')
C_BLUE = HexColor('#2563eb')

OUTPUT = '/home/z/my-project/download/GitHub_PR_Report_euxaristia_2026-05-17.pdf'

def load_data():
    with open('/tmp/pr_report.json') as f:
        return json.load(f)

def build_styles():
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle('CoverTitle', fontName='Helvetica-Bold', fontSize=28, textColor=C_PRIMARY, leading=34, alignment=TA_LEFT, spaceAfter=8*mm))
    styles.add(ParagraphStyle('CoverSub', fontName='Helvetica', fontSize=13, textColor=C_MUTED, leading=18, alignment=TA_LEFT, spaceAfter=4*mm))
    styles.add(ParagraphStyle('SectionHead', fontName='Helvetica-Bold', fontSize=16, textColor=C_PRIMARY, leading=20, spaceBefore=10*mm, spaceAfter=4*mm))
    styles.add(ParagraphStyle('SubHead', fontName='Helvetica-Bold', fontSize=12, textColor=C_PRIMARY, leading=16, spaceBefore=6*mm, spaceAfter=3*mm))
    styles.add(ParagraphStyle('Body', fontName='Helvetica', fontSize=9.5, textColor=C_TEXT, leading=14, spaceAfter=2*mm))
    styles.add(ParagraphStyle('PRTitle', fontName='Helvetica-Bold', fontSize=10, textColor=C_TEXT, leading=14, spaceAfter=1*mm))
    styles.add(ParagraphStyle('PRMeta', fontName='Helvetica', fontSize=8.5, textColor=C_MUTED, leading=12, spaceAfter=1.5*mm))
    styles.add(ParagraphStyle('PRAnalysis', fontName='Helvetica-Oblique', fontSize=9, textColor=C_TEXT, leading=13, spaceAfter=2*mm, leftIndent=4*mm))
    styles.add(ParagraphStyle('TableCell', fontName='Helvetica', fontSize=7.5, textColor=C_TEXT, leading=10))
    styles.add(ParagraphStyle('TableHeader', fontName='Helvetica-Bold', fontSize=7.5, textColor=C_WHITE, leading=10))
    return styles

def state_badge(state):
    colors = {'ACTIVE': C_GREEN, 'IN_REVIEW': C_BLUE, 'CHANGES_REQUESTED': C_RED, 'STALE': C_YELLOW, 'STALE_EXTERNAL': C_RED, 'AWAITING_REVIEWER': C_YELLOW, 'SELF_MERGE_READY': C_GREEN, 'CI_PENDING': C_YELLOW}
    color = C_MUTED
    for s in state:
        if s in colors:
            color = colors[s]
            break
    # Show only the most important state
    priority = ['CHANGES_REQUESTED', 'STALE_EXTERNAL', 'AWAITING_REVIEWER', 'IN_REVIEW', 'STALE', 'SELF_MERGE_READY', 'ACTIVE', 'CI_PENDING']
    for s in priority:
        if s in state:
            return f'<font color="{colors.get(s, C_MUTED).hexval()}">{s}</font>'
    return f'<font color="{C_MUTED.hexval()}">{state[0]}</font>'

def ci_badge(ci_status, ci_failing=False):
    if ci_failing:
        return '<font color="#dc2626">FAILING</font>'
    if ci_status == 'success':
        return '<font color="#059669">PASSING</font>'
    if ci_status == 'pending':
        return '<font color="#d97706">PENDING</font>'
    return f'<font color="#6b7280">{ci_status.upper() if ci_status else "N/A"}</font>'

def review_summary(pr):
    reviews = pr.get('reviews', [])
    if not reviews:
        return 'No reviews'
    states = {}
    for r in reviews:
        s = r['state']
        states[s] = states.get(s, 0) + 1
    return ', '.join(f"{count} {state.lower()}" for state, count in states.items())

def build_cover(styles, data):
    elements = []
    elements.append(Spacer(1, 40*mm))
    elements.append(Paragraph('GitHub Pull Request Report', styles['CoverTitle']))
    elements.append(Paragraph('euxaristia', styles['CoverTitle']))
    elements.append(Spacer(1, 8*mm))
    elements.append(Paragraph(data['generated_at'], styles['CoverSub']))
    s = data['summary']
    stats = [f'<b>{s["total_open_prs"]}</b> open PRs', f'<b>{s["own_repos"]}</b> own repos', f'<b>{s["external_repos"]}</b> external repos']
    elements.append(Paragraph(' &nbsp; | &nbsp; '.join(stats), styles['CoverSub']))
    elements.append(Spacer(1, 15*mm))
    analysis = data.get('analysis', {})
    if analysis.get('urgent_actions'):
        elements.append(Paragraph('Urgent Actions', styles['SubHead']))
        for action in analysis['urgent_actions']:
            elements.append(Paragraph(f"&bull; {action}", styles['Body']))
    if analysis.get('quick_wins'):
        elements.append(Paragraph('Quick Wins', styles['SubHead']))
        for win in analysis['quick_wins']:
            elements.append(Paragraph(f"&bull; {win}", styles['Body']))
    if analysis.get('ready_to_merge_own_repo'):
        elements.append(Paragraph('Ready to Merge (Own Repos)', styles['SubHead']))
        for item in analysis['ready_to_merge_own_repo']:
            elements.append(Paragraph(f"&bull; {item}", styles['Body']))
    if analysis.get('awaiting_external_response'):
        elements.append(Paragraph('Awaiting External Response', styles['SubHead']))
        for item in analysis['awaiting_external_response']:
            elements.append(Paragraph(f"&bull; {item}", styles['Body']))
    return elements

def build_pr_section(styles, prs, title, filter_func=None):
    elements = []
    filtered = [p for p in prs if filter_func is None or filter_func(p)]
    if not filtered:
        return elements
    elements.append(Paragraph(f'{title} ({len(filtered)})', styles['SectionHead']))
    for pr in filtered:
        ref = pr['ref']
        elements.append(Paragraph(f'<b>{ref}</b> &mdash; {pr["title"]}', styles['PRTitle']))
        ci = ci_badge(pr.get('ci_status'), pr.get('ci_failing', False))
        meta = f'{pr["created_at"]} | +{pr.get("additions",0)}/-{pr.get("deletions",0)} in {pr.get("changed_files",0)} files | CI: {ci} | Reviews: {review_summary(pr)}'
        elements.append(Paragraph(meta, styles['PRMeta']))
        if pr.get('analysis'):
            elements.append(Paragraph(pr['analysis'], styles['PRAnalysis']))
        reviews = pr.get('reviews', [])
        for r in reviews[:2]:
            reviewer = r.get('reviewer', 'unknown')
            state = r['state']
            body = r.get('body', '')[:150]
            if body:
                body_text = body + ('...' if len(r.get('body', '')) > 150 else '')
                elements.append(Paragraph(f'<font color="#6b7280"><b>{reviewer}</b> ({state}): </font>{body_text}',
                    ParagraphStyle('ReviewDetail', parent=styles['Body'], fontSize=8.5, leftIndent=8*mm, textColor=C_MUTED, leading=12)))
        elements.append(HRFlowable(width='80%', thickness=0.5, color=HexColor('#e5e7eb'), spaceBefore=3*mm, spaceAfter=3*mm))
    return elements

def build_overview_table(styles, prs):
    elements = []
    elements.append(Paragraph('Overview Table', styles['SectionHead']))
    header = [Paragraph(h, styles['TableHeader']) for h in ['PR', 'Repo', 'State', 'CI', 'Rev', 'Updated', 'Cmts']]
    rows = [header]
    for pr in sorted(prs, key=lambda x: x.get('days_since_update', 0), reverse=True):
        ref_short = pr['ref'].split('#')[-1] if '#' in pr['ref'] else pr['ref']
        repo = pr['repo'].split('/')[-1]
        state = state_badge(pr['state'])
        ci = ci_badge(pr.get('ci_status'), pr.get('ci_failing', False))
        comments = pr.get('issue_comments', 0) + pr.get('review_comments', 0)
        row = [
            Paragraph(f'<b>{ref_short}</b>', styles['TableCell']),
            Paragraph(repo, styles['TableCell']),
            Paragraph(state, styles['TableCell']),
            Paragraph(ci, styles['TableCell']),
            Paragraph(str(len(pr.get('reviews', []))), styles['TableCell']),
            Paragraph(pr['updated_at'], styles['TableCell']),
            Paragraph(str(comments), styles['TableCell']),
        ]
        rows.append(row)
    col_widths = [22*mm, 28*mm, 38*mm, 18*mm, 12*mm, 26*mm, 12*mm]
    table = Table(rows, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), C_PRIMARY),
        ('TEXTCOLOR', (0, 0), (-1, 0), C_WHITE),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('ALIGN', (4, 0), (6, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('GRID', (0, 0), (-1, -1), 0.4, HexColor('#e5e7eb')),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [C_WHITE, C_LIGHT_BG]),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ]))
    elements.append(table)
    return elements

def main():
    data = load_data()
    styles = build_styles()
    prs = data.get('pull_requests', [])
    doc = SimpleDocTemplate(OUTPUT, pagesize=A4, leftMargin=18*mm, rightMargin=18*mm, topMargin=18*mm, bottomMargin=18*mm)
    elements = []
    elements.extend(build_cover(styles, data))
    elements.append(PageBreak())
    # Skip table, go straight to detailed sections
    elements.extend(build_pr_section(styles, prs, 'External PRs', lambda p: p.get('author_association') in ('CONTRIBUTOR', 'NONE')))
    elements.extend(build_pr_section(styles, prs, 'Own Repository PRs', lambda p: p.get('author_association') == 'OWNER'))
    analysis = data.get('analysis', {})
    needs_work = analysis.get('needs_work', [])
    if needs_work:
        elements.append(Paragraph('PRs Needing Work', styles['SectionHead']))
        for item in needs_work:
            elements.append(Paragraph(f"&bull; {item}", styles['Body']))
    doc.build(elements)
    print(f'PDF generated: {OUTPUT} ({os.path.getsize(OUTPUT)//1024}KB)')

if __name__ == '__main__':
    main()
