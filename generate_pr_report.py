#!/usr/bin/env python3
"""Generate GitHub PR Report PDF for euxaristia."""
import json
from datetime import datetime, timezone
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.colors import HexColor, white, black
from reportlab.lib.units import mm
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
    PageBreak, HRFlowable, KeepTogether
)
from reportlab.platypus.flowables import Flowable
from reportlab.lib import colors

# Load data
with open("/home/z/my-project/pr_report_data.json") as f:
    prs = json.load(f)

open_prs = [r for r in prs if r.get("state") == "open"]
closed_prs = [r for r in prs if r.get("state") != "open"]

def fmt_date(iso):
    if not iso:
        return "N/A"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        return dt.strftime("%b %d, %Y")
    except:
        return iso[:10]

def days_ago(iso):
    if not iso:
        return "?"
    try:
        dt = datetime.fromisoformat(iso.replace("Z", "+00:00"))
        days = (datetime.now(timezone.utc) - dt).days
        return f"{days}d ago"
    except:
        return "?"

# Colors
C_PRIMARY = HexColor("#1a1a2e")
C_ACCENT = HexColor("#4361ee")
C_ACCENT2 = HexColor("#3a86ff")
C_MUTED = HexColor("#6b7280")
C_BG = HexColor("#f8fafc")
C_SUCCESS = HexColor("#06d6a0")
C_WARNING = HexColor("#f59e0b")
C_DANGER = HexColor("#ef4444")
C_STALE = HexColor("#9ca3af")
C_TABLE_HEAD = HexColor("#1e293b")
C_TABLE_ALT = HexColor("#f1f5f9")

output_path = "/home/z/my-project/download/GitHub_PR_Report_euxaristia_2026-05-18.pdf"

doc = SimpleDocTemplate(
    output_path,
    pagesize=A4,
    leftMargin=18*mm, rightMargin=18*mm,
    topMargin=20*mm, bottomMargin=20*mm,
)

styles = getSampleStyleSheet()

# Custom styles
s_title = ParagraphStyle("Title2", parent=styles["Title"], fontSize=22, leading=26, 
    textColor=C_PRIMARY, spaceAfter=4, fontName="Helvetica-Bold")
s_subtitle = ParagraphStyle("Sub2", parent=styles["Normal"], fontSize=10, 
    textColor=C_MUTED, spaceAfter=16, fontName="Helvetica")
s_h1 = ParagraphStyle("H1", parent=styles["Heading1"], fontSize=16, leading=20,
    textColor=C_PRIMARY, spaceBefore=18, spaceAfter=8, fontName="Helvetica-Bold",
    borderWidth=0, borderPadding=0)
s_h2 = ParagraphStyle("H2", parent=styles["Heading2"], fontSize=12, leading=15,
    textColor=C_PRIMARY, spaceBefore=14, spaceAfter=6, fontName="Helvetica-Bold")
s_body = ParagraphStyle("Body2", parent=styles["Normal"], fontSize=9, leading=13,
    textColor=HexColor("#374151"), spaceAfter=4, fontName="Helvetica")
s_small = ParagraphStyle("Small", parent=styles["Normal"], fontSize=8, leading=11,
    textColor=C_MUTED, fontName="Helvetica")
s_pr_title = ParagraphStyle("PRTitle", parent=styles["Normal"], fontSize=9.5, leading=13,
    textColor=C_PRIMARY, fontName="Helvetica-Bold")
s_status = ParagraphStyle("Status", parent=styles["Normal"], fontSize=8, leading=11,
    fontName="Helvetica-Bold", textColor=white)
s_section_label = ParagraphStyle("SecLabel", parent=styles["Normal"], fontSize=8,
    leading=10, textColor=C_ACCENT, fontName="Helvetica-Bold", 
    spaceBefore=8, spaceAfter=2, leftIndent=4)

class ColorDot(Flowable):
    def __init__(self, color, size=6):
        Flowable.__init__(self)
        self.color = color
        self.size = size
        self.width = size
        self.height = size
    def draw(self):
        self.canv.setFillColor(self.color)
        self.canv.circle(self.size/2, self.size/2, self.size/2, fill=1, stroke=0)

story = []

# === COVER ===
story.append(Spacer(1, 60*mm))
story.append(Paragraph("GitHub Pull Request", s_title))
story.append(Paragraph("Status Report", s_title))
story.append(Spacer(1, 8*mm))

cover_date = datetime.now(timezone.utc).strftime("%B %d, %Y")
story.append(Paragraph(f"euxaristia  |  {cover_date}", s_subtitle))
story.append(Spacer(1, 12*mm))

# Summary stats
summary_data = [
    [Paragraph("<b>Open PRs</b>", ParagraphStyle("c", fontSize=10, textColor=C_ACCENT, alignment=TA_CENTER, fontName="Helvetica-Bold")),
     Paragraph("<b>Merged Since Last</b>", ParagraphStyle("c", fontSize=10, textColor=C_SUCCESS, alignment=TA_CENTER, fontName="Helvetica-Bold")),
     Paragraph("<b>Awaiting Action</b>", ParagraphStyle("c", fontSize=10, textColor=C_WARNING, alignment=TA_CENTER, fontName="Helvetica-Bold")),
     Paragraph("<b>Stale</b>", ParagraphStyle("c", fontSize=10, textColor=C_STALE, alignment=TA_CENTER, fontName="Helvetica-Bold"))],
    [Paragraph(f"{len(open_prs)}", ParagraphStyle("c", fontSize=24, textColor=C_PRIMARY, alignment=TA_CENTER, fontName="Helvetica-Bold")),
     Paragraph(f"{len(closed_prs)}", ParagraphStyle("c", fontSize=24, textColor=C_PRIMARY, alignment=TA_CENTER, fontName="Helvetica-Bold")),
     Paragraph(f"{sum(1 for p in open_prs if 'stale' in p.get('pr_status','').lower() or 'awaiting' in p.get('pr_status','').lower())}", ParagraphStyle("c", fontSize=24, textColor=C_PRIMARY, alignment=TA_CENTER, fontName="Helvetica-Bold")),
     Paragraph(f"{sum(1 for p in open_prs if 'stale' in p.get('pr_status','').lower())}", ParagraphStyle("c", fontSize=24, textColor=C_PRIMARY, alignment=TA_CENTER, fontName="Helvetica-Bold"))],
]

summary_table = Table(summary_data, colWidths=[38*mm]*4)
summary_table.setStyle(TableStyle([
    ('ALIGN', (0,0), (-1,-1), 'CENTER'),
    ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
    ('TOPPADDING', (0,0), (-1,0), 4),
    ('BOTTOMPADDING', (0,0), (-1,0), 2),
    ('TOPPADDING', (0,1), (-1,1), 8),
    ('BOTTOMPADDING', (0,1), (-1,1), 12),
    ('LINEBELOW', (0,0), (-1,0), 0.5, C_TABLE_ALT),
]))
story.append(summary_table)

story.append(PageBreak())

# === CHANGES SINCE LAST REPORT ===
story.append(Paragraph("Changes Since Last Report", s_h1))

if closed_prs:
    for pr in closed_prs:
        action = "MERGED" if pr.get("merged") else "CLOSED"
        action_color = C_SUCCESS if pr.get("merged") else C_DANGER
        status_text = f'<font color="{action_color.hexval()}">{action}</font>'
        story.append(Paragraph(
            f'{status_text}  <b>{pr["key"]}</b> - {pr["title"]}',
            s_body
        ))
        if pr.get("merged_at"):
            story.append(Paragraph(f'Merged on {fmt_date(pr["merged_at"])}', s_small))
        story.append(Spacer(1, 2*mm))

# New PRs (not in previous report)
new_prs = [p for p in open_prs if p.get("created_at", "")[:10] >= "2026-05-16"]
if new_prs:
    story.append(Paragraph("New PRs", s_section_label))
    for pr in new_prs:
        story.append(Paragraph(
            f'NEW  <b>{pr["key"]}</b> - {pr["title"]}',
            s_body
        ))
        story.append(Paragraph(f'Opened {fmt_date(pr["created_at"])}  |  {pr.get("pr_status","")}', s_small))
        story.append(Spacer(1, 2*mm))

# === OPEN PRs DETAIL ===
story.append(Paragraph("Open Pull Requests", s_h1))

# Status legend
legend_items = [
    ("In Review", C_ACCENT), ("In Review Cycle", HexColor("#8b5cf6")),
    ("Awaiting Review", C_WARNING), ("Awaiting Author", C_DANGER),
    ("Approved", C_SUCCESS), ("Stale", C_STALE),
]
legend_text = "  |  ".join([f'<font color="{c.hexval()}">{t}</font>' for t,c in legend_items])
story.append(Paragraph(legend_text, s_small))
story.append(Spacer(1, 4*mm))

# Build table data
def status_badge(status):
    color_map = {
        "In Review": C_ACCENT, "In Review Cycle": HexColor("#8b5cf6"),
        "Awaiting Review": C_WARNING, "Awaiting Author": C_DANGER,
        "Approved": C_SUCCESS, "Draft": C_STALE,
    }
    base = status.split(" (")[0]
    color = color_map.get(base, C_MUTED)
    is_stale = "(stale)" in status
    if is_stale:
        return f'<font color="{C_STALE.hexval()}">{status}</font>'
    return f'<font color="{color.hexval()}">{status}</font>'

# Group PRs by target repo
from collections import OrderedDict
by_target = OrderedDict()
for pr in open_prs:
    target = pr.get("base_repo", pr["repo"])
    if target not in by_target:
        by_target[target] = []
    by_target[target].append(pr)

for target_repo, repo_prs in by_target.items():
    story.append(Paragraph(f'{target_repo}', s_h2))
    
    for pr in repo_prs:
        # PR header
        title_text = pr["title"][:80]
        status = pr.get("pr_status", "Unknown")
        draft_tag = " [DRAFT]" if pr.get("draft") else ""
        
        pr_header = f'<b>{pr["key"]}{draft_tag}</b> - {title_text}'
        story.append(Paragraph(pr_header, s_pr_title))
        
        # Meta line
        meta_parts = [
            status_badge(status),
            f'+{pr["additions"]}/-{pr["deletions"]}',
            f'{pr["changed_files"]} files',
            f'{len(pr["reviews"])} reviews',
            f'{len(pr.get("review_comments",[]))} review comments',
            days_ago(pr["updated_at"]),
        ]
        if pr.get("ci_status") and pr["ci_status"] != "unknown":
            ci = pr["ci_status"]
            ci_color = C_SUCCESS if ci == "success" else (C_DANGER if ci == "failure" else C_WARNING)
            meta_parts.append(f'<font color="{ci_color.hexval()}">CI: {ci}</font>')
        
        story.append(Paragraph("  |  ".join(meta_parts), s_small))
        
        # Labels
        if pr.get("labels"):
            story.append(Paragraph(f'Labels: {", ".join(pr["labels"])}', s_small))
        
        # Review summary
        reviews = pr.get("reviews", [])
        if reviews:
            review_summary = []
            for r in reviews[-3:]:  # Last 3 reviews
                reviewer = r.get("user", {}).get("login", "?")
                rstate = r.get("state", "?")
                rdate = fmt_date(r.get("submitted_at", ""))
                review_summary.append(f'{reviewer} ({rstate}, {rdate})')
            story.append(Paragraph(f'Reviews: {"; ".join(review_summary)}', s_small))
        
        # Issue comments summary
        ic = pr.get("issue_comments", [])
        if ic:
            comment_summary = []
            for c in ic[-3:]:
                author = c.get("user", {}).get("login", "?")
                cdate = fmt_date(c.get("created_at", ""))
                body = c.get("body", "")[:60].replace("<", "&lt;").replace(">", "&gt;")
                comment_summary.append(f'{author} ({cdate}): {body}...')
            story.append(Paragraph(f'Comments: {"; ".join(comment_summary)}', s_small))
        
        story.append(Spacer(1, 3*mm))

# === ACTION ITEMS ===
story.append(Paragraph("Action Items", s_h1))

action_prs = [p for p in open_prs if "awaiting" in p.get("pr_status", "").lower() or "stale" in p.get("pr_status", "").lower()]
if action_prs:
    for pr in action_prs:
        status = pr.get("pr_status", "")
        story.append(Paragraph(
            f'<font color="{C_WARNING.hexval()}">&#9654;</font> <b>{pr["key"]}</b> - {status}: {pr["title"][:70]}',
            s_body
        ))
        story.append(Paragraph(f'  Last updated {days_ago(pr["updated_at"])}. {len(pr["reviews"])} reviews, {len(pr.get("review_comments",[]))} review comments.', s_small))
        story.append(Spacer(1, 2*mm))
else:
    story.append(Paragraph("No PRs currently require action.", s_body))

# Build and save
doc.build(story)
print(f"PDF saved to {output_path}")
