import json
from datetime import datetime, timezone
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
GREEN = colors.HexColor('#16a34a')
RED = colors.HexColor('#dc2626')
AMBER = colors.HexColor('#d97706')
BG_ALT = colors.HexColor('#f9fafb')

ct = ParagraphStyle('ct', fontName='LASB', fontSize=28, leading=34, alignment=TA_CENTER, spaceAfter=6, textColor=TP)
cs = ParagraphStyle('cs', fontName='LSI', fontSize=14, leading=18, alignment=TA_CENTER, textColor=TM)
cd = ParagraphStyle('cd', fontName='LAS', fontSize=12, leading=16, alignment=TA_CENTER, textColor=ACCENT)
h1 = ParagraphStyle('h1', fontName='LASB', fontSize=18, leading=22, spaceBefore=14, spaceAfter=8, textColor=TP)
h2 = ParagraphStyle('h2', fontName='LASB', fontSize=13, leading=16, spaceBefore=10, spaceAfter=5, textColor=ACCENT)
h3 = ParagraphStyle('h3', fontName='LASB', fontSize=10, leading=13, spaceBefore=6, spaceAfter=3, textColor=TP)
bd = ParagraphStyle('bd', fontName='LS', fontSize=10, leading=14, spaceAfter=4, alignment=TA_JUSTIFY)
mt = ParagraphStyle('mt', fontName='LSI', fontSize=9, leading=12, textColor=TM, spaceAfter=2)
sm = ParagraphStyle('sm', fontName='LAS', fontSize=8.5, leading=11, textColor=TM)
ft = ParagraphStyle('ft', fontName='LAS', fontSize=8, leading=10, textColor=TM, alignment=TA_CENTER)
tb = ParagraphStyle('tb', fontName='LS', fontSize=9, leading=12, textColor=TM, spaceAfter=1)

def fd(iso):
    if not iso: return 'N/A'
    try:
        dt = datetime.fromisoformat(iso.replace('Z','+00:00'))
        return dt.strftime('%B %d, %Y')
    except:
        return iso[:10]

def ci_badge(s):
    if s == 'success': return '<font color="#16a34a"><b>Passed</b></font>'
    elif s == 'failure': return '<font color="#dc2626"><b>Failed</b></font>'
    return '<font color="#d97706">Pending</font>'

def pr_detail_block(p):
    els = []
    pt = ParagraphStyle('pt', fontName='LASB', fontSize=9.5, leading=12.5, spaceAfter=1)
    els.append(Paragraph(f'<b>{p["repo"]}</b> #{p["number"]}: {p["title"]}', pt))
    meta_parts = [p['repo'], f'Created: {fd(p["created"])}', f'Updated: {fd(p["updated"])}']
    if p['labels']:
        meta_parts.append('Labels: ' + ', '.join(p['labels']))
    els.append(Paragraph('  |  '.join(meta_parts), mt))
    diff_text = f'+{p["additions"]} / -{p["deletions"]} across {p["changed_files"]} file(s)  |  {p["commit_count"]} commit(s)'
    if p['draft']:
        diff_text += '  |  <b>Draft</b>'
    merge_text = ''
    if p['mergeable'] is False:
        merge_text = '  |  <font color="#dc2626">Merge conflict</font>'
    elif p['mergeable'] is True:
        merge_text = '  |  <font color="#16a34a">Mergeable</font>'
    els.append(Paragraph(diff_text + merge_text, sm))
    rc = ParagraphStyle('rc', fontName='LAS', fontSize=8.5, leading=11, spaceAfter=2)
    state_html = state_badge(p['state'], None)
    ci_html = ci_badge(p['ci_state'])
    review_text = p.get('review_summary', 'No reviews')
    els.append(Paragraph(f'State: {state_html}  |  CI: {ci_html}  |  Review: {review_text}', rc))
    if p.get('state_desc'):
        els.append(Paragraph(f'<i>{p["state_desc"]}</i>', ParagraphStyle('sd', fontName='LSI', fontSize=8.5, leading=11, textColor=TM, spaceAfter=1)))
    if p['ci_failures']:
        for fail_name in p['ci_failures']:
            els.append(Paragraph(f'<font color="#dc2626">CI Failed: {fail_name}</font>', ParagraphStyle('cf', fontName='LAS', fontSize=8, leading=10, spaceAfter=1, leftIndent=8)))
    body = p.get('body', '')
    if body:
        els.append(Paragraph(body[:200] + ('...' if len(body) > 200 else ''),
            ParagraphStyle('be', fontName='LS', fontSize=9, leading=12, textColor=TM, spaceAfter=1)))
    if p['human_comments'] > 0 or p['bot_comments'] > 0 or p['review_comment_count'] > 0:
        comment_parts = []
        if p['human_comments'] > 0:
            comment_parts.append(f'{p["human_comments"]} human comment(s)')
        if p['bot_comments'] > 0:
            comment_parts.append(f'{p["bot_comments"]} bot comment(s)')
        if p['review_comment_count'] > 0:
            comment_parts.append(f'{p["review_comment_count"]} inline review comment(s)')
        els.append(Paragraph('Activity: ' + ', '.join(comment_parts),
            ParagraphStyle('act', fontName='LAS', fontSize=8, leading=10, textColor=TM, spaceAfter=1)))
    els.append(Paragraph(f'Link: {p["url"]}',
        ParagraphStyle('lnk', fontName='LAS', fontSize=8, leading=10, textColor=ACCENT, spaceAfter=6)))
    els.append(Spacer(1,4))
    return els

def state_badge(state, color):
    colors_map = {
        'awaiting_review': '#6366f1',
        'in_review_cycle': '#d97706',
        'awaiting_author': '#dc2626',
        'ci_failure': '#ef4444',
        'awaiting_maintainer': '#6366f1',
        'ready_to_merge': '#16a34a',
        'blocked': '#9333ea',
    }
    c = colors_map.get(state, '#73787f')
    labels = {
        'awaiting_review': 'Awaiting Review',
        'in_review_cycle': 'In Review Cycle',
        'awaiting_author': 'Awaiting Author',
        'ci_failure': 'CI Failure',
        'awaiting_maintainer': 'Awaiting Maintainer',
        'ready_to_merge': 'Ready to Merge',
        'blocked': 'Blocked',
    }
    label = labels.get(state, state)
    return f'<font color="{c}"><b>{label}</b></font>'

# Load data
raw = json.load(open('/tmp/pr_data.json'))

# Determine actual state for each PR
def determine_state(pr):
    reviews = pr.get('reviews', [])
    issue_comments = pr.get('issue_comments', [])
    review_comments = pr.get('review_comments', [])
    commits = pr.get('commits', [])
    status = pr.get('status', {}).get('state', 'pending')
    check_runs = pr.get('check_runs', {}).get('check_runs', [])
    mergeable = pr.get('mergeable')
    draft = pr.get('draft', False)
    updated = pr.get('updated_at', '')
    created = pr.get('created_at', '')
    
    # Check for human reviews
    human_reviews = [r for r in reviews if not r.get('user', {}).get('login', '').endswith('[bot]')]
    bot_reviews = [r for r in reviews if r.get('user', {}).get('login', '').endswith('[bot]')]
    human_issue_comments = [c for c in issue_comments if not c.get('user', {}).get('login', '').endswith('[bot]') and c.get('user', {}).get('login', '') != 'github-actions[bot]']
    
    # Check for changes requested by humans
    changes_requested = any(r.get('state') == 'CHANGES_REQUESTED' for r in reviews)
    human_changes_requested = any(r.get('state') == 'CHANGES_REQUESTED' and not r.get('user', {}).get('login', '').endswith('[bot]') for r in reviews)
    
    # Check if author pushed after reviews
    last_review_date = None
    if reviews:
        last_review_date = max(r.get('submitted_at', '') for r in reviews if r.get('submitted_at'))
    
    # Last commit by the author
    author_commits_after_review = 0
    for cm in commits:
        cm_date = cm.get('commit', {}).get('author', {}).get('date', '')
        if last_review_date and cm_date > last_review_date:
            author_commits_after_review += 1
    
    # Check CI failures
    ci_failed = any(cr.get('conclusion') == 'failure' for cr in check_runs)
    ci_passed = all(cr.get('conclusion') in ('success', 'skipped', 'neutral') for cr in check_runs) if check_runs else False
    ci_has_runs = len(check_runs) > 0
    
    # Check for human reviewer engagement
    has_human_feedback = len(human_reviews) > 0 or len(human_issue_comments) > 0
    
    # Microsoft CLA check
    cla_check = any('CLA' in cr.get('name', '').upper() or 'cla' in cr.get('name', '').lower() for cr in check_runs)
    community_check = any('Community' in cr.get('name', '') or 'community' in cr.get('name', '') for cr in check_runs)
    community_in_progress = any('Community' in cr.get('name', '') and cr.get('status') == 'in_progress' for cr in check_runs)
    
    repo = pr.get('repo', '')
    
    # --- State determination logic ---
    
    # Draft PRs
    if draft:
        return 'awaiting_review', 'Draft - not yet ready for review'
    
    # CI failure with no follow-up
    if ci_failed and author_commits_after_review == 0:
        return 'ci_failure', 'CI checks are failing; no fix pushed yet'
    
    # Human changes requested + follow-up pushed (re-review cycle)
    if human_changes_requested and author_commits_after_review > 0:
        return 'in_review_cycle', 'Changes requested, but author pushed follow-up commits'
    
    # Human changes requested, no follow-up
    if human_changes_requested and author_commits_after_review == 0:
        return 'awaiting_author', 'Maintainer requested changes; awaiting author response'
    
    # CLA/community approval process (e.g. microsoft)
    if community_in_progress:
        return 'blocked', 'CLA signed; waiting for community approval process'
    
    # Bot review with feedback + author pushed follow-up
    if bot_reviews and author_commits_after_review > 0:
        return 'in_review_cycle', 'Bot review received; author addressed feedback'
    
    # Bot review with feedback, no follow-up
    if bot_reviews and author_commits_after_review == 0 and len(review_comments) > 0:
        return 'awaiting_author', 'Bot review feedback pending; awaiting author response'
    
    # Has human engagement (questions, discussion)
    if has_human_feedback:
        # Check if last activity was from author (responded to questions)
        if human_issue_comments:
            last_human_comment = max(human_issue_comments, key=lambda c: c.get('created_at', ''))
            last_author_activity = updated
            if last_human_comment.get('user', {}).get('login', '') != 'euxaristia':
                # Maintainer asked question, check if author responded
                author_replies = [c for c in issue_comments if c.get('user', {}).get('login', '') == 'euxaristia' and c.get('created_at', '') > last_human_comment.get('created_at', '')]
                if not author_replies:
                    return 'awaiting_author', 'Maintainer engagement pending author response'
                else:
                    return 'awaiting_maintainer', 'Author responded; awaiting maintainer review'
        return 'awaiting_maintainer', 'Maintainer engaged; awaiting further review'
    
    # All CI passed and mergeable
    if ci_passed and mergeable and ci_has_runs:
        return 'ready_to_merge', 'All checks passed; ready to merge'
    
    # No reviews, no CI runs - brand new PR
    if len(reviews) == 0 and not ci_has_runs:
        return 'awaiting_review', 'No reviews or CI runs yet'
    
    # Default: awaiting maintainer review
    return 'awaiting_maintainer', 'Awaiting maintainer attention'

# Process all PRs
prs = []
for pr in raw:
    state, state_desc = determine_state(pr)
    
    # Get review summary
    reviews = pr.get('reviews', [])
    review_summary = ''
    if reviews:
        human_revs = [r for r in reviews if not r.get('user', {}).get('login', '').endswith('[bot]')]
        bot_revs = [r for r in reviews if r.get('user', {}).get('login', '').endswith('[bot]')]
        states = set(r.get('state', '') for r in reviews)
        if 'CHANGES_REQUESTED' in states:
            reviewer = next((r.get('user', {}).get('login', '') for r in reviews if r.get('state') == 'CHANGES_REQUESTED'), 'unknown')
            review_summary = f'CHANGES_REQUESTED by {reviewer}'
        elif 'APPROVED' in states:
            review_summary = 'APPROVED'
        elif human_revs:
            hs = set(r.get('state', '') for r in human_revs)
            review_summary = ', '.join(hs) + ' (human)'
        elif bot_revs:
            review_summary = f'COMMENTED by bot ({len(bot_revs)} review(s))'
    
    # CI summary
    check_runs = pr.get('check_runs', {}).get('check_runs', [])
    ci_state = pr.get('status', {}).get('state', 'pending')
    ci_conclusions = [cr.get('conclusion') for cr in check_runs if cr.get('conclusion')]
    ci_failures = [cr.get('name', '') for cr in check_runs if cr.get('conclusion') == 'failure']
    ci_summary = ci_state
    if ci_failures:
        ci_summary = 'failure'
    elif all(c in ('success', 'skipped', 'neutral') for c in ci_conclusions) and ci_conclusions:
        ci_summary = 'success'
    
    # Commit count
    commit_count = len(pr.get('commits', []))
    
    # Issue comments count (exclude bots for human context)
    human_comments = [c for c in pr.get('issue_comments', []) if not c.get('user', {}).get('login', '').endswith('[bot]') and c.get('user', {}).get('login', '') != 'github-actions[bot]']
    bot_comments = [c for c in pr.get('issue_comments', []) if c.get('user', {}).get('login', '').endswith('[bot]') or c.get('user', {}).get('login', '') == 'github-actions[bot]']
    
    prs.append({
        'repo': pr['repo'],
        'number': pr['number'],
        'title': pr['title'],
        'url': pr['html_url'],
        'created': pr['created_at'],
        'updated': pr['updated_at'],
        'draft': pr['draft'],
        'additions': pr['additions'],
        'deletions': pr['deletions'],
        'changed_files': pr['changed_files'],
        'mergeable': pr['mergeable'],
        'labels': pr['labels'],
        'review_summary': review_summary,
        'ci_state': ci_summary,
        'ci_failures': ci_failures,
        'state': state,
        'state_desc': state_desc,
        'commit_count': commit_count,
        'human_comments': len(human_comments),
        'bot_comments': len(bot_comments),
        'review_comment_count': len(pr.get('review_comments', [])),
        'body': (pr.get('body', '') or '')[:250],
        'base_ref': pr.get('base_ref', ''),
    })

upstream = [p for p in prs if not p['repo'].startswith('euxaristia/')]
personal = [p for p in prs if p['repo'].startswith('euxaristia/')]
upstream.sort(key=lambda x: x['updated'], reverse=True)
personal.sort(key=lambda x: x['updated'], reverse=True)

# PDF generation
output = '/home/z/my-project/download/GitHub_PR_Report_euxaristia_2026-05-17.pdf'
doc = SimpleDocTemplate(output, pagesize=A4,
    leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm,
    title='GitHub PR Report - euxaristia', author='euxaristia', creator='Z.ai')

av = A4[0] - 3.0*cm
story = []

# === COVER PAGE ===
story.append(Spacer(1,4*cm))
story.append(Paragraph('<b>GitHub PR Report</b>', ct))
story.append(Spacer(1,12))
story.append(Paragraph('euxaristia', cs))
story.append(Spacer(1,6))
story.append(Paragraph('May 17, 2026', cd))
story.append(Spacer(1,2*cm))
ss = ParagraphStyle('ss', fontName='LS', fontSize=11, leading=16, alignment=TA_CENTER, textColor=TP)
story.append(Paragraph(f'{len(prs)} open pull requests across {len(set(p["repo"] for p in prs))} repositories', ss))
story.append(Spacer(1,8))
story.append(Paragraph(f'{len(upstream)} upstream contributions  |  {len(personal)} personal repositories',
    ParagraphStyle('sd', fontName='LAS', fontSize=10, leading=14, alignment=TA_CENTER, textColor=TM)))
story.append(Spacer(1,1.2*cm))

# State breakdown on cover
state_counts = {}
for p in prs:
    s = p['state']
    state_counts[s] = state_counts.get(s, 0) + 1

state_order = ['ready_to_merge', 'in_review_cycle', 'awaiting_maintainer', 'awaiting_review', 'awaiting_author', 'ci_failure', 'blocked']
ths_cover = ParagraphStyle('ths_cov', fontName='LASB', fontSize=8.5, leading=11, textColor=colors.white)
tds_cover = ParagraphStyle('tds_cov', fontName='LS', fontSize=8.5, leading=11)
state_table_data = [[Paragraph('<b>State</b>', ths_cover), Paragraph('<b>Count</b>', ths_cover)]]
for s in state_order:
    if s in state_counts:
        state_table_data.append([Paragraph(state_badge(s, None), tds_cover), str(state_counts[s])])
state_table = Table(state_table_data, colWidths=[6*cm, 2.5*cm])
state_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), ACCENT), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e5e7eb')),
    ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_ALT]),
    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
]))
story.append(state_table)

story.append(Spacer(1,0.8*cm))
story.append(Paragraph('Cairn Organization: 0 open PRs', 
    ParagraphStyle('co', fontName='LAS', fontSize=9, leading=12, alignment=TA_CENTER, textColor=TM)))

story.append(PageBreak())

# === EXECUTIVE SUMMARY ===
story.append(Paragraph('<b>Executive Summary</b>', h1))
story.append(HRFlowable(width='100%', thickness=0.8, color=ACCENT, spaceBefore=0, spaceAfter=8))

ta = sum(p['additions'] for p in prs)
td = sum(p['deletions'] for p in prs)
tf = sum(p['changed_files'] for p in prs)
cp = sum(1 for p in prs if p['ci_state'] == 'success')
cf = sum(1 for p in prs if p['ci_state'] == 'failure')
cpe = sum(1 for p in prs if p['ci_state'] not in ('success', 'failure'))
cr = sum(1 for p in prs if 'CHANGES_REQUESTED' in p.get('review_summary', ''))
irc = state_counts.get('in_review_cycle', 0)
aa = state_counts.get('awaiting_author', 0)
am = state_counts.get('awaiting_maintainer', 0)

story.append(Paragraph(
    f'This report covers all <b>{len(prs)}</b> open pull requests authored by <b>euxaristia</b> across '
    f'<b>{len(set(p["repo"] for p in prs))}</b> repositories. The PRs touch <b>{ta:,}</b> lines added and '
    f'<b>{td:,}</b> lines deleted across <b>{tf}</b> files. Of these, <b>{len(upstream)}</b> are upstream '
    f'contributions to external projects and <b>{len(personal)}</b> are within personal repositories. '
    f'The <b>Cairn</b> organization has <b>0</b> open PRs.', bd))

story.append(Spacer(1,6))

# Key findings
story.append(Paragraph('<b>Key Findings</b>', h2))
findings = [
    f'<b>{irc}</b> PRs are in an active review cycle (feedback received and addressed)',
    f'<b>{aa}</b> PRs are awaiting author response to review feedback',
    f'<b>{am}</b> PRs are awaiting maintainer attention after author follow-up',
    f'<b>{cr}</b> PR(s) have formal changes requested by human reviewers',
    f'<b>{cf}</b> PR(s) have failing CI checks',
    f'<b>{cp}</b> PR(s) have all CI checks passing',
]
for f_text in findings:
    story.append(Paragraph(f'  &bull;  {f_text}', ParagraphStyle('fi', fontName='LS', fontSize=9.5, leading=13, leftIndent=12, spaceAfter=2)))

story.append(Spacer(1,8))

# CI Status table
story.append(Paragraph('<b>CI Status Overview</b>', h2))
ths2 = ParagraphStyle('ths2', fontName='LASB', fontSize=9, leading=12, textColor=colors.white)
tds2 = ParagraphStyle('tds2', fontName='LS', fontSize=9, leading=12)
ci_data = [
    [Paragraph('<b>Status</b>', ths2), Paragraph('<b>Count</b>', ths2), Paragraph('<b>Percentage</b>', ths2)],
    [Paragraph('<font color="#16a34a"><b>Passed</b></font>', tds2), str(cp), f'{cp/len(prs)*100:.0f}%' if prs else '0%'],
    [Paragraph('<font color="#d97706"><b>Pending / No Checks</b></font>', tds2), str(cpe), f'{cpe/len(prs)*100:.0f}%' if prs else '0%'],
    [Paragraph('<font color="#dc2626"><b>Failed</b></font>', tds2), str(cf), f'{cf/len(prs)*100:.0f}%' if prs else '0%'],
]
ci_table = Table(ci_data, colWidths=[5*cm, 2.5*cm, 2.5*cm])
ci_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), ACCENT), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e5e7eb')),
    ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_ALT]),
    ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
]))
story.append(ci_table)

story.append(Spacer(1,8))

# PR Size distribution
story.append(Paragraph('<b>PR Size Distribution</b>', h2))
sizes = {'Small (1-50 lines)': 0, 'Medium (51-200 lines)': 0, 'Large (201-500 lines)': 0, 'Very Large (500+ lines)': 0}
for p in prs:
    total = p['additions'] + p['deletions']
    if total <= 50: sizes['Small (1-50 lines)'] += 1
    elif total <= 200: sizes['Medium (51-200 lines)'] += 1
    elif total <= 500: sizes['Large (201-500 lines)'] += 1
    else: sizes['Very Large (500+ lines)'] += 1
size_data = [[Paragraph('<b>Size Category</b>', ths2), Paragraph('<b>Count</b>', ths2)]]
for label, cnt in sizes.items():
    size_data.append([Paragraph(label, tds2), str(cnt)])
size_table = Table(size_data, colWidths=[5*cm, 2.5*cm])
size_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), ACCENT), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('GRID', (0, 0), (-1, -1), 0.4, colors.HexColor('#e5e7eb')),
    ('TOPPADDING', (0, 0), (-1, -1), 4), ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ('LEFTPADDING', (0, 0), (-1, -1), 6),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_ALT]),
    ('ALIGN', (1, 0), (1, -1), 'CENTER'),
]))
story.append(size_table)

# === UPSTREAM CONTRIBUTIONS ===
story.append(Spacer(1,12))
story.append(Paragraph(f'<b>Upstream Contributions ({len(upstream)})</b>', h1))
story.append(HRFlowable(width='100%', thickness=0.8, color=ACCENT, spaceBefore=0, spaceAfter=8))
story.append(Paragraph('Pull requests open against third-party repositories maintained by other organizations.', bd))
story.append(Spacer(1,6))

# Upstream overview table
ths_t = ParagraphStyle('ths_t', fontName='LASB', fontSize=7.5, leading=10, textColor=colors.white)
tds_t = ParagraphStyle('tds_t', fontName='LS', fontSize=7.5, leading=10)
tda_t = ParagraphStyle('tda_t', fontName='LS', fontSize=7.5, leading=10, textColor=ACCENT)
tci_t = ParagraphStyle('tci_t', fontName='LAS', fontSize=7.5, leading=10)
cw = [3.0*cm, 6.5*cm, 1.8*cm, 1.8*cm, 1.5*cm, 1.5*cm]
cw = [w/sum(cw)*av for w in cw]

up_hdr = [Paragraph('<b>Repo</b>', ths_t), Paragraph('<b>Title</b>', ths_t),
    Paragraph('<b>Created</b>', ths_t), Paragraph('<b>Updated</b>', ths_t),
    Paragraph('<b>CI</b>', ths_t), Paragraph('<b>State</b>', ths_t)]
up_rows = [up_hdr]
for p in upstream:
    rn = p['repo'].split('/')[-1] if '/' in p['repo'] else p['repo']
    short_c = fd(p['created']).replace(', 2026', ', \'26')
    short_u = fd(p['updated']).replace(', 2026', ', \'26')
    up_rows.append([
        Paragraph(f'<b>{rn}</b>', tda_t),
        Paragraph(p['title'][:52] + ('...' if len(p['title']) > 52 else ''), tds_t),
        Paragraph(short_c, tds_t),
        Paragraph(short_u, tds_t),
        Paragraph(ci_badge(p['ci_state']), tci_t),
        Paragraph(state_badge(p['state'], None), tci_t),
    ])
up_table = Table(up_rows, colWidths=cw, repeatRows=1)
up_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), ACCENT), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTSIZE', (0, 0), (-1, -1), 7.5),
    ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ('LEFTPADDING', (0, 0), (-1, -1), 3), ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e5e7eb')),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_ALT]),
]))
story.append(up_table)
story.append(Spacer(1,10))

# Detailed upstream PR blocks
for p in upstream:
    story.extend(pr_detail_block(p))

# === PERSONAL REPOSITORIES ===
story.append(Paragraph(f'<b>Personal Repositories ({len(personal)})</b>', h1))
story.append(HRFlowable(width='100%', thickness=0.8, color=ACCENT, spaceBefore=0, spaceAfter=8))
story.append(Paragraph('Pull requests open within personal repositories under the euxaristia account.', bd))
story.append(Spacer(1,6))

per_hdr = list(up_hdr)
per_rows = [per_hdr]
for p in personal:
    rn = p['repo'].split('/')[-1] if '/' in p['repo'] else p['repo']
    short_c = fd(p['created']).replace(', 2026', ', \'26')
    short_u = fd(p['updated']).replace(', 2026', ', \'26')
    per_rows.append([
        Paragraph(f'<b>{rn}</b>', tda_t),
        Paragraph(p['title'][:52] + ('...' if len(p['title']) > 52 else ''), tds_t),
        Paragraph(short_c, tds_t),
        Paragraph(short_u, tds_t),
        Paragraph(ci_badge(p['ci_state']), tci_t),
        Paragraph(state_badge(p['state'], None), tci_t),
    ])
per_table = Table(per_rows, colWidths=cw, repeatRows=1)
per_table.setStyle(TableStyle([
    ('BACKGROUND', (0, 0), (-1, 0), ACCENT), ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
    ('FONTSIZE', (0, 0), (-1, -1), 7.5),
    ('TOPPADDING', (0, 0), (-1, -1), 3), ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
    ('LEFTPADDING', (0, 0), (-1, -1), 3), ('RIGHTPADDING', (0, 0), (-1, -1), 3),
    ('GRID', (0, 0), (-1, -1), 0.3, colors.HexColor('#e5e7eb')),
    ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_ALT]),
]))
story.append(per_table)
story.append(Spacer(1,10))

for p in personal:
    story.extend(pr_detail_block(p))

# === CAIRN ORG ===
story.append(Spacer(1,12))
story.append(Paragraph('<b>Cairn Organization</b>', h1))
story.append(HRFlowable(width='100%', thickness=0.8, color=ACCENT, spaceBefore=0, spaceAfter=8))
story.append(Paragraph('No open pull requests were found for the Cairn organization. The organization may not have any repositories with open PRs authored by euxaristia, or the authentication token may lack access to organization repositories.', bd))

# === FOOTER ===
story.append(Spacer(1,12))
story.append(HRFlowable(width='100%', thickness=0.4, color=TM, spaceBefore=4, spaceAfter=4))
story.append(Paragraph('Generated May 17, 2026  |  github.com/euxaristia', ft))

doc.build(story)
print(f'Report saved to {output}')


