from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

# ── Font Registration ──
pdfmetrics.registerFont(TTFont('Tinos', '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Tinos-Bold', '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'))
pdfmetrics.registerFont(TTFont('Tinos-Italic', '/usr/share/fonts/truetype/liberation/LiberationSerif-Italic.ttf'))
registerFontFamily('Tinos', normal='Tinos', bold='Tinos-Bold', italic='Tinos-Italic')

# ── Color Palette ──
ACCENT = colors.HexColor('#1f7692')
TEXT_PRIMARY = colors.HexColor('#212324')
TEXT_MUTED = colors.HexColor('#7c8488')
BG_PAGE = colors.HexColor('#f1f3f3')

# ── Styles ──
name_style = ParagraphStyle(
    'Name', fontName='Tinos', fontSize=26,
    leading=30, alignment=TA_CENTER, spaceAfter=2,
    textColor=TEXT_PRIMARY
)
subtitle_style = ParagraphStyle(
    'Subtitle', fontName='Tinos', fontSize=11,
    leading=14, alignment=TA_CENTER, spaceAfter=2,
    textColor=ACCENT
)
contact_style = ParagraphStyle(
    'Contact', fontName='Tinos', fontSize=9.5,
    leading=13, alignment=TA_CENTER, textColor=TEXT_MUTED,
    spaceAfter=10
)
section_title_style = ParagraphStyle(
    'SectionTitle', fontName='Tinos', fontSize=12,
    leading=15, spaceBefore=10, spaceAfter=3,
    textColor=ACCENT
)
body_style = ParagraphStyle(
    'Body', fontName='Tinos', fontSize=10,
    leading=13.5, spaceAfter=2
)
bullet_style = ParagraphStyle(
    'Bullet', fontName='Tinos', fontSize=9.5,
    leading=13, leftIndent=14, bulletIndent=0,
    spaceBefore=1, spaceAfter=1.5
)
meta_style = ParagraphStyle(
    'Meta', fontName='Tinos', fontSize=9.5,
    leading=12.5, textColor=TEXT_MUTED, spaceAfter=3
)
project_title_style = ParagraphStyle(
    'ProjectTitle', fontName='Tinos', fontSize=10.5,
    leading=13.5, spaceAfter=1
)

# ── Helpers ──
def section_header(title):
    return [
        Paragraph(f'<b>{title}</b>', section_title_style),
        HRFlowable(width='100%', thickness=0.7, color=ACCENT,
                   spaceBefore=0, spaceAfter=5),
    ]

def project_entry(name, desc, bullets):
    elements = [
        Paragraph(f'<b>{name}</b>  --  {desc}', project_title_style),
    ]
    for b in bullets:
        elements.append(Paragraph(f'\xe2\x80\xa2 {b}', bullet_style))
    elements.append(Spacer(1, 3))
    return elements

# ── Build Document ──
output_path = '/home/z/my-project/download/CV_Mateo_Pineda.pdf'
doc = SimpleDocTemplate(
    output_path, pagesize=A4,
    leftMargin=1.5*cm, rightMargin=1.5*cm,
    topMargin=1.4*cm, bottomMargin=1.4*cm,
    title='CV - Mateo Pineda',
    author='Mateo Pineda', creator='Z.ai'
)

story = []

# Header
story.append(Paragraph('<b>Mateo Pineda</b>', name_style))
story.append(Paragraph('Agentic Engineer', subtitle_style))
story.append(Paragraph(
    'github.com/euxaristia  |  euxaristia.github.io',
    contact_style
))

# Summary
story.extend(section_header('PROFILE'))
story.append(Paragraph(
    'Agentic engineer who leverages AI tools to ship real, non-trivial contributions to production codebases. '
    'Contributor to open-source projects maintained by Google, Qwen (Alibaba), and others, with accepted PRs '
    'spanning CLI tooling, security fixes, and core runtime behavior. Builds personal systems projects -- '
    'including a C compiler, a POSIX-compatible shell, and a Make alternative -- using AI-assisted development '
    'to move fast and iterate on complex domains.',
    body_style
))

# Open Source Contributions
story.extend(section_header('OPEN SOURCE CONTRIBUTIONS (MERGED)'))
story.append(Paragraph(
    'All contributions below are merged into upstream repositories. '
    'Trivial changes (typo fixes, documentation-only updates, and link corrections) are excluded.',
    meta_style
))
story.append(Spacer(1, 3))

story.extend(project_entry(
    'google-gemini/gemini-cli',
    'Google\'s official CLI for Gemini models',
    [
        '<b>Text sanitization data loss fix (PR #22624)</b> -- Resolved a bug where C1 control characters caused '
        'silent data loss during text sanitization, corrupting CLI output. Labeled area/core, help wanted.',

        '<b>Detached mode child process fix (PR #22620)</b> -- Disabled detached mode in Bun runtime to prevent '
        'child processes from receiving immediate SIGHUP on spawn. Labeled area/core, area/platform, help wanted.',

        '<b>AbortError log suppression (PR #22621)</b> -- Suppressed unhandled AbortError logs that appeared '
        'during normal request cancellation. Labeled area/core, help wanted.',
    ]
))

story.extend(project_entry(
    'QwenLM/qwen-code',
    'Qwen Code Agent (Alibaba)',
    [
        '<b>Loop detection and stagnation checks (PR #3236)</b> -- Implemented enhanced agent loop detection '
        'with read-file, action-stagnation, and repetitive-thought checks, injecting stop directives to break '
        'infinite retry cycles.',

        '<b>Tool validation retry loop fix (PR #3178)</b> -- Prevented the model from entering infinite retry '
        'loops when a tool call repeatedly failed schema validation with the same error.',

        '<b>Shell output overflow fix (PR #2857)</b> -- Constrained shell output width to prevent wide table '
        'output from overflowing the TUI bordered box container.',

        '<b>Input lag fix from quote-based drag detection (PR #2837)</b> -- Removed quote-based drag-and-drop '
        'detection that caused significant input lag when typing single or double quote characters.',
    ]
))

story.extend(project_entry(
    'Gitlawb/openclaude',
    'Open-source Claude implementation',
    [
        '<b>SSRF bypass fix in custom search provider (PR #610)</b> -- Closed multiple SSRF bypass vectors in '
        'the custom provider hostname guard that allowed requests to resolve to private/reserved IPs through '
        'literal-address forms.',

        '<b>Abort listener memory leak fix (PR #611)</b> -- Fixed a memory leak where fetchWithRetry attached '
        'a fresh abort listener to the AbortSignal on every retry attempt without ever removing them.',
    ]
))

story.extend(project_entry(
    'clockworklabs/SpacetimeDB',
    'Distributed relational database',
    [
        '<b>Version uninstall validation fix (PR #4774)</b> -- Prevented the CLI from showing a confirmation '
        'prompt for uninstalling versions that were not actually installed, which previously resulted in a cryptic '
        'OS-level error.',
    ]
))

story.extend(project_entry(
    'posva/catimg',
    'Popular terminal image renderer (C, ~2.7k stars)',
    [
        '<b>stb_image upgrade and MJPEG/YUYV decoding fix (PR #78)</b> -- Upgraded stb_image to v2.30 and '
        'improved MJPEG (AVI1) and raw YUYV decoding support.',
    ]
))

# Personal Projects
story.extend(section_header('PERSONAL PROJECTS'))
story.extend(project_entry(
    'meowsh',
    'POSIX-compatible shell implementation (Rust)',
    [
        'Implemented function-local variable scoping with snapshot/restore semantics.',
        'Built zsh compatibility layer enabling .zshrc parsing and oh-my-zsh skeleton execution.',
        'Added indexed arrays, variable substitution references (${var/old/new}), and compsys stubs.',
    ]
))

story.extend(project_entry(
    'pcc',
    'C compiler (TypeScript, porting to C)',
    [
        'Implemented a complete recursive descent C parser in C (~450 lines replacing 633 lines of TypeScript).',
        'Ported the lexer to C with full operator tokenization and test coverage.',
        'Fixed preprocessor to recursively process directives in included files.',
        'Achieved 67/67 tests passing across parser and semantic analyzer.',
    ]
))

story.extend(project_entry(
    'mkultra',
    'POSIX Make alternative (Pony)',
    [
        'Rewrote from Rust to Pony with stdlib-only dependencies and parallel job execution (-j N).',
        'Implemented POSIX recipe prefixes (-, +, -), expansion (${VAR}, substitution refs), and command-line macro overrides.',
    ]
))

story.extend(project_entry(
    'VoxelPopuli',
    'Voxel engine with OpenGL (Rust)',
    [
        'Fixed cloud transparency rendering over water when viewed from above (depth mask compositing).',
    ]
))

story.extend(project_entry(
    'colt',
    'Terminal text editor (Rust)',
    [
        'Fixed SHIFT+G normal-mode command to correctly navigate to bottom of file (vim behavior).',
    ]
))

# Skills
story.extend(section_header('APPROACH'))
story.append(Paragraph(
    'All projects and contributions are AI-assisted. I use large language models as force multipliers -- '
    'not to replace understanding, but to accelerate iteration on complex systems. This means I can contribute '
    'meaningfully across languages and domains I would not reach working alone: C compilers, POSIX shell '
    'semantics, runtime process management, and security-sensitive networking code.',
    body_style
))

story.append(Spacer(1, 6))

# Footer line
story.append(HRFlowable(width='100%', thickness=0.4, color=TEXT_MUTED,
                         spaceBefore=4, spaceAfter=4))
story.append(Paragraph(
    'github.com/euxaristia',
    ParagraphStyle('Footer', fontName='Tinos', fontSize=8.5,
                   leading=11, alignment=TA_CENTER, textColor=TEXT_MUTED)
))

doc.build(story)
print(f'CV saved to {output_path}')
