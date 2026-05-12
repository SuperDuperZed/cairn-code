import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, HRFlowable
)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase.pdfmetrics import registerFontFamily

pdfmetrics.registerFont(TTFont('Carlito', '/usr/share/fonts/truetype/english/Carlito-Regular.ttf'))
pdfmetrics.registerFont(TTFont('Carlito-Bold', '/usr/share/fonts/truetype/english/Carlito-Bold.ttf'))
pdfmetrics.registerFont(TTFont('LiberationSerif', '/usr/share/fonts/truetype/liberation/LiberationSerif-Regular.ttf'))
pdfmetrics.registerFont(TTFont('LiberationSerif-Bold', '/usr/share/fonts/truetype/liberation/LiberationSerif-Bold.ttf'))
registerFontFamily('LiberationSerif', normal='LiberationSerif', bold='LiberationSerif-Bold')
registerFontFamily('Carlito', normal='Carlito', bold='Carlito-Bold')

ACCENT = colors.HexColor('#1b7896')
TEXT_PRIMARY = colors.HexColor('#1f1e1c')
TEXT_MUTED = colors.HexColor('#8f8a83')
BORDER = colors.HexColor('#d4d0c2')

name_style = ParagraphStyle(name='Name', fontName='Carlito-Bold', fontSize=26, leading=32, textColor=TEXT_PRIMARY, alignment=TA_LEFT, spaceAfter=2)
headline_style = ParagraphStyle(name='Headline', fontName='Carlito', fontSize=12, leading=16, textColor=ACCENT, alignment=TA_LEFT, spaceAfter=4)
contact_style = ParagraphStyle(name='Contact', fontName='Carlito', fontSize=9.5, leading=14, textColor=TEXT_MUTED, alignment=TA_LEFT, spaceAfter=1)
section_title_style = ParagraphStyle(name='SectionTitle', fontName='Carlito-Bold', fontSize=12, leading=16, textColor=TEXT_PRIMARY, alignment=TA_LEFT, spaceBefore=14, spaceAfter=6)
body_style = ParagraphStyle(name='Body', fontName='LiberationSerif', fontSize=10, leading=15, textColor=TEXT_PRIMARY, alignment=TA_LEFT, spaceAfter=4)
bullet_style = ParagraphStyle(name='Bullet', fontName='LiberationSerif', fontSize=10, leading=15, textColor=TEXT_PRIMARY, alignment=TA_LEFT, spaceAfter=2, leftIndent=18, bulletIndent=6)
project_title_style = ParagraphStyle(name='ProjectTitle', fontName='Carlito-Bold', fontSize=10.5, leading=15, textColor=TEXT_PRIMARY, alignment=TA_LEFT, spaceAfter=1)
project_meta_style = ParagraphStyle(name='ProjectMeta', fontName='Carlito', fontSize=9, leading=13, textColor=TEXT_MUTED, alignment=TA_LEFT, spaceAfter=2)
tag_style = ParagraphStyle(name='Tag', fontName='Carlito', fontSize=8.5, leading=12, textColor=ACCENT, alignment=TA_LEFT)
small_style = ParagraphStyle(name='Small', fontName='LiberationSerif', fontSize=9, leading=13, textColor=TEXT_MUTED, alignment=TA_LEFT, spaceAfter=2)

def bullet(text):
    return Paragraph('<bullet>&bull;</bullet> ' + text, bullet_style)

def section(title):
    return [
        Paragraph(title, section_title_style),
        HRFlowable(width="100%", thickness=0.6, color=BORDER, spaceAfter=6),
    ]

def project(name, meta, tags="", bullets_list=None):
    elems = []
    elems.append(Paragraph(name, project_title_style))
    elems.append(Paragraph(meta, project_meta_style))
    if tags:
        elems.append(Paragraph(tags, tag_style))
    if bullets_list:
        for b in bullets_list:
            elems.append(bullet(b))
    elems.append(Spacer(1, 4))
    return elems

output = '/home/z/my-project/download/euxaristia_CV.pdf'
doc = SimpleDocTemplate(
    output, pagesize=A4,
    leftMargin=0.75*inch, rightMargin=0.75*inch,
    topMargin=0.6*inch, bottomMargin=0.6*inch,
    title='euxaristia - Curriculum Vitae', author='euxaristia', creator='Z.ai',
    subject='Agentic Engineer & Open Source Contributor'
)
story = []

# ━━ Header ━━
story.append(Paragraph('<b>euxaristia</b>', name_style))
story.append(Paragraph('Agentic Engineer &amp; Open Source Contributor', headline_style))
story.append(Paragraph(
    'github.com/euxaristia &nbsp;&bull;&nbsp; euxaristia.github.io &nbsp;&bull;&nbsp; Open to opportunities',
    contact_style))
story.append(Spacer(1, 6))

# ━━ Summary ━━
story.extend(section('Professional Summary'))
story.append(Paragraph(
    'Agentic engineer who leverages AI coding assistants and agentic workflows to design, build, and ship '
    'software across diverse domains. Active open-source contributor since 2017 with 17 merged pull requests '
    'to projects including Google Gemini CLI, posva/catimg, QwenLM/qwen-code, clockworklabs/SpacetimeDB, '
    'and swiftlang/swift-org-website. Author of 14 original projects spanning systems programming, game engines, '
    'compilers, and developer tooling, produced through iterative AI-assisted development. Strengths include '
    'prompt engineering, agent workflow design, code review, debugging complex codebases, and driving contributions '
    'to unfamiliar codebases by combining domain understanding with AI pair programming.', body_style))
story.append(Spacer(1, 4))

# ━━ Skills ━━
story.extend(section('Technical Skills'))
story.append(Paragraph(
    '<b>Agentic Development:</b> AI pair programming, prompt engineering, multi-step agent workflows, '
    'iterative build-test-debug cycles with AI, context window management, cross-codebase comprehension, '
    'AI-assisted code review and debugging', body_style))
story.append(Paragraph(
    '<b>Languages Worked In (AI-assisted):</b> Rust, Pony, TypeScript, Go, C, Assembly (x86_64), Zig, '
    'Shell, Swift, Java, C++, JavaScript', body_style))
story.append(Paragraph(
    '<b>Domains:</b> CLI tools, game engines, compiler toolchains, terminal emulators, kernel internals, '
    'build systems, WebAssembly, OpenGL, AI coding agents', body_style))
story.append(Paragraph(
    '<b>Platforms &amp; Tools:</b> Git, GitHub, GitHub Actions, Bun runtime, Linux, GCC/Clang, SDL3, '
    'Rayon, STB image libraries, Docker', body_style))
story.append(Spacer(1, 2))

# ━━ Open Source Contributions ━━
story.extend(section('Open Source Contributions'))

story.extend(project(
    'google-gemini/gemini-cli',
    'Google | TypeScript | 3 merged PRs',
    'google-gemini/gemini-cli',
    [
        'Fixed text sanitization data loss caused by C1 control characters in CLI output rendering',
        'Resolved Bun detached mode SIGHUP issue causing process termination on signal delivery',
        'Suppressed unhandled AbortError log noise during command cancellation workflows',
    ]
))

story.extend(project(
    'posva/catimg',
    'posva | C | Contributor rank #3 | 4 commits | 2 merged PRs',
    'posva/catimg',
    [
        'Upgraded stb_image from v2.28 to v2.30, enabling MJPEG and YUYV color-space decoding support',
        'Refreshed man page documentation to reflect current CLI behavior and flag options',
    ]
))

story.extend(project(
    'QwenLM/qwen-code',
    'Alibaba Qwen Team | TypeScript | 5 merged PRs',
    'QwenLM/qwen-code',
    [
        'Enhanced AI agent loop detection with stagnation detection and validation-retry mechanisms',
        'Fixed shell output box overflow causing terminal buffer corruption on long outputs',
        'Resolved CLI build failures by migrating from Node to tsx execution, and fixed input lag',
    ]
))

story.extend(project(
    'Gitlawb/openclaude',
    'Claude Code fork | TypeScript | 3 merged PRs',
    'Gitlawb/openclaude',
    [
        'Fixed SSRF bypass vulnerabilities in hostname guard validation logic',
        'Resolved web-search AbortController listener memory leaks causing resource exhaustion',
        'Added display of the selected AI model in startup output for better user visibility',
    ]
))

story.extend(project(
    'clockworklabs/SpacetimeDB',
    'Clockwork Labs | Rust | 1 merged PR',
    'clockworklabs/SpacetimeDB',
    [
        'Added version existence check before confirming module uninstall in the CLI (#4774)',
    ]
))

story.extend(project(
    'swiftlang/swift-org-website',
    'Apple Swift | JavaScript | 1 merged PR',
    'swiftlang/swift-org-website',
    [
        'Fixed double-quoting of curl commands to enable shell substitution in Linux installation instructions (#1228)',
    ]
))

story.extend(project(
    'Other Merged Contributions',
    'posva/catimg, FedoraQt/MediaWriter, FyroxEngine/rg3d.rs',
    '',
    [
        'FedoraQt/MediaWriter: Fixed grammar in privacy documentation (#138)',
        'FyroxEngine/rg3d.rs: Fixed typos in download page template (#47)',
    ]
))

# ━━ Personal Projects ━━
story.extend(section('Selected Personal Projects'))

story.extend(project(
    'colt',
    'Pony | Vi-style text editor',
    '',
    [
        'Vi modal editor implementation in Pony with insert, normal, command, and visual modes',
        'Features: regex substitution, mouse click/drag selection, clipboard integration, dynamic status bar',
        'Actively developed with 4 open feature PRs',
    ]
))

story.extend(project(
    'meowsh',
    'Rust | POSIX-compliant shell',
    '',
    [
        'Shell implementation targeting zsh compatibility with indexed arrays, function scoping, and job control',
        'Designed for correctness against POSIX specification test suites',
    ]
))

story.extend(project(
    'VoxelPopuli',
    'Rust + OpenGL | Voxel sandbox engine',
    '',
    [
        'Minecraft-inspired voxel engine with chunk generation, cloud transparency, and rayon parallelization',
    ]
))

story.extend(project(
    'pcc',
    'TypeScript | C compiler (Pickle C Compiler)',
    '',
    [
        'Full C lexer, parser, and CLI compiler with gcc-compatible flag parsing',
    ]
))

story.extend(project(
    'Coatl',
    'Rust | Systems language compiler',
    '',
    [
        'Compiler targeting x86_64 and AArch64 Linux backends with code generation and ELF output',
    ]
))

story.extend(project(
    'Farmiga',
    'x86_64 Assembly | UNIX SysV hobby kernel',
    '',
    [
        'Hobby OS kernel in Assembly inspired by UNIX System V with interrupt handling and system calls',
    ]
))

story.extend(project(
    'Other Projects',
    'gitee-cli (Go), mkultra (Pony), adapt (Rust), cu-chulainn (Pony), Nimbus (Swift), ZigDoom (Zig), fireterm (Pony)',
    '',
    [
        'gitee-cli: Full-featured Gitee CLI modeled after GitHub CLI (gh)',
        'mkultra: Minimal Unix-philosophy build tool with parallel jobs and POSIX glob expansion',
        'adapt: Paru-like APT wrapper with shell completion; ZigDoom: Doom engine port in Zig',
    ]
))

# ━━ Education ━━
story.extend(section('Education'))
story.append(Paragraph(
    '<b>Self-Directed Study</b> | Agentic Engineering, Systems Programming, Software Architecture',
    body_style))
story.append(Paragraph(
    'Extensive self-directed learning in agentic development workflows, systems programming concepts, '
    'and software architecture. Developed expertise in working with AI coding assistants to produce '
    'meaningful contributions across unfamiliar codebases and languages, from Assembly kernels to TypeScript AI tools.',
    small_style
))

doc.build(story)
print(f"CV generated: {output} ({os.path.getsize(output):,} bytes)")
