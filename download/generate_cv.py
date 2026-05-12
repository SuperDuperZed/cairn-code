import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY, TA_RIGHT
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
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

# ━━ Palette ━━
ACCENT = colors.HexColor('#1b7896')
TEXT_PRIMARY = colors.HexColor('#1f1e1c')
TEXT_MUTED = colors.HexColor('#8f8a83')
BG_SURFACE = colors.HexColor('#e5e2de')
BORDER = colors.HexColor('#d4d0c2')

# ━━ Styles ━━
name_style = ParagraphStyle(
    name='Name', fontName='Carlito-Bold', fontSize=26, leading=32,
    textColor=TEXT_PRIMARY, alignment=TA_LEFT, spaceAfter=2
)
headline_style = ParagraphStyle(
    name='Headline', fontName='Carlito', fontSize=12, leading=16,
    textColor=ACCENT, alignment=TA_LEFT, spaceAfter=4
)
contact_style = ParagraphStyle(
    name='Contact', fontName='Carlito', fontSize=9.5, leading=14,
    textColor=TEXT_MUTED, alignment=TA_LEFT, spaceAfter=1
)
section_title_style = ParagraphStyle(
    name='SectionTitle', fontName='Carlito-Bold', fontSize=12, leading=16,
    textColor=TEXT_PRIMARY, alignment=TA_LEFT, spaceBefore=14, spaceAfter=6
)
body_style = ParagraphStyle(
    name='Body', fontName='LiberationSerif', fontSize=10, leading=15,
    textColor=TEXT_PRIMARY, alignment=TA_LEFT, spaceAfter=4
)
bullet_style = ParagraphStyle(
    name='Bullet', fontName='LiberationSerif', fontSize=10, leading=15,
    textColor=TEXT_PRIMARY, alignment=TA_LEFT, spaceAfter=2,
    leftIndent=18, bulletIndent=6
)
project_title_style = ParagraphStyle(
    name='ProjectTitle', fontName='Carlito-Bold', fontSize=10.5, leading=15,
    textColor=TEXT_PRIMARY, alignment=TA_LEFT, spaceAfter=1
)
project_meta_style = ParagraphStyle(
    name='ProjectMeta', fontName='Carlito', fontSize=9, leading=13,
    textColor=TEXT_MUTED, alignment=TA_LEFT, spaceAfter=2
)
tag_style = ParagraphStyle(
    name='Tag', fontName='Carlito', fontSize=8.5, leading=12,
    textColor=ACCENT, alignment=TA_LEFT
)
small_style = ParagraphStyle(
    name='Small', fontName='LiberationSerif', fontSize=9, leading=13,
    textColor=TEXT_MUTED, alignment=TA_LEFT, spaceAfter=2
)

# ━━ Helpers ━━
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

# ━━ Build ━━
output = '/home/z/my-project/download/euxaristia_CV.pdf'
doc = SimpleDocTemplate(
    output, pagesize=A4,
    leftMargin=0.75*inch, rightMargin=0.75*inch,
    topMargin=0.6*inch, bottomMargin=0.6*inch,
    title='euxaristia - Curriculum Vitae', author='euxaristia', creator='Z.ai',
    subject='Open Source Contributor & Systems Programmer'
)
story = []

# ━━ Header ━━
story.append(Paragraph('<b>euxaristia</b>', name_style))
story.append(Paragraph('Systems Programmer &amp; Open Source Contributor', headline_style))
story.append(Paragraph(
    'github.com/euxaristia &nbsp;&bull;&nbsp; euxaristia.github.io &nbsp;&bull;&nbsp; Open to opportunities',
    contact_style))
story.append(Spacer(1, 6))

# ━━ Summary ━━
story.extend(section('Professional Summary'))
story.append(Paragraph(
    'Systems-oriented software engineer with deep expertise in low-level programming, compiler design, '
    'and terminal tooling. Active open-source contributor since 2017 with 27+ merged pull requests to '
    'major projects including Google Gemini CLI, posva/catimg, QwenLM/qwen-code, microsoft/node-pty, '
    'and clockworklabs/SpacetimeDB. Author of 14 original projects spanning a vi text editor in Pony, '
    'a POSIX-compliant shell in Rust, a Minecraft-inspired voxel engine, a C compiler written in TypeScript, '
    'and a UNIX-style hobby kernel in Assembly. Proficient across 18 programming languages with primary '
    'focus on Rust, Pony, TypeScript, Go, C, and Assembly.',
    body_style))
story.append(Spacer(1, 4))

# ━━ Languages ━━
story.extend(section('Technical Skills'))
story.append(Paragraph(
    '<b>Languages:</b> Rust, Pony, TypeScript, Go, C, Assembly (x86_64), Zig, Shell (POSIX), '
    'Swift, HolyC, V, Java, C++, JavaScript, HTML/CSS, Ruby, Processing', body_style))
story.append(Paragraph(
    '<b>Domains:</b> Systems programming, compiler/toolchain development, terminal emulators and CLI tools, '
    'game engines, kernel development, WebAssembly, OpenGL, build systems, POSIX compliance', body_style))
story.append(Paragraph(
    '<b>Tools &amp; Platforms:</b> Git, GitHub Actions, Bun runtime, Linux, GCC/Clang, SDL3, Rayon, '
    'STB image libraries, WebAssembly modules, Docker', body_style))
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
        'Additional open PRs: Bun build script detection (#26280, #26498), loading phrases UI fix (#22618)',
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
    'Clockwork Labs | Rust | Open PR',
    'clockworklabs/SpacetimeDB',
    [
        'Authored Rust FFI crate (#4773) enabling WASM module interop via native bindings',
    ]
))

story.extend(project(
    'microsoft/node-pty',
    'Microsoft | C++ | Open PR',
    'microsoft/node-pty',
    [
        'Fix to swallow resize() errors after PTY process exit on both Windows and Unix (#901)',
    ]
))

story.extend(project(
    'Other Contributions',
    'Charmbracelet/glow, anomalyco/opencode, swiftlang/swift-org-website, FedoraQt/MediaWriter, FyroxEngine/rg3d.rs',
    '',
    [
        'charmbracelet/glow: Fixed markdown code block closing fence rendering (#937)',
        'anomalyco/opencode: Bound Home/End keys to line start/end in input field (#25355)',
        'swiftlang/swift-org-website: Contributed to Swift.org website improvements',
        'FedoraQt/MediaWriter: Contributions to cross-platform media writer tooling',
        'FyroxEngine/rg3d.rs: Bug fixes and improvements to the Fyrox game engine',
    ]
))

# ━━ Personal Projects ━━
story.extend(section('Selected Personal Projects'))

story.extend(project(
    'colt',
    'Pony | Vi-style text editor',
    '',
    [
        'Full vi modal editor implementation in the Pony programming language with insert, normal, '
        'command, and visual modes',
        'Features include regex substitution (:s/ command), mouse click and drag selection, clipboard '
        'integration, and a dynamic status bar',
        '4 open PRs representing active ongoing development of editor features and bug fixes',
    ]
))

story.extend(project(
    'meowsh',
    'Rust | POSIX-compliant shell',
    '',
    [
        'POSIX shell implementation in Rust targeting zsh compatibility including indexed arrays, '
        'function scoping rules, and job control',
        'Designed for correctness against the POSIX specification test suites',
    ]
))

story.extend(project(
    'VoxelPopuli',
    'Rust + OpenGL | Voxel sandbox engine',
    '',
    [
        'Minecraft-inspired voxel rendering engine with chunk generation, cloud transparency, '
        'and multi-threaded rayon worker pool for parallel chunk computation',
    ]
))

story.extend(project(
    'pcc',
    'TypeScript | C compiler (Pickle C Compiler)',
    '',
    [
        'Full C lexer, parser, and CLI compiler written in TypeScript with gcc-compatible flag parsing',
        'Demonstrates compiler design expertise applied in an unconventional language runtime',
    ]
))

story.extend(project(
    'Coatl',
    'Rust | Systems language compiler',
    '',
    [
        'Native compiler targeting x86_64 and AArch64 Linux backends from a custom systems language',
        'Includes code generation, register allocation, and ELF binary output',
    ]
))

story.extend(project(
    'Farmiga',
    'x86_64 Assembly | UNIX SysV hobby kernel',
    '',
    [
        'Hobby operating system kernel written in x86_64 Assembly inspired by UNIX System V design',
        'Implements kernel bootstrapping, interrupt handling, and basic system calls',
    ]
))

story.extend(project(
    'Other Projects',
    'gitee-cli (Go), mkultra (Pony), adapt (Rust), cu-chulainn (Pony), Nimbus (Swift), ZigDoom (Zig), fireterm (Pony)',
    '',
    [
        'gitee-cli: Full-featured Gitee CLI tool modeled after GitHub CLI (gh)',
        'mkultra: Minimal Unix-philosophy build tool with parallel job execution and POSIX glob expansion',
        'adapt: Paru-like APT wrapper with shell completion for Debian-based package management',
        'ZigDoom: Doom game engine port written in Zig',
    ]
))

# ━━ Education ━━
story.extend(section('Education'))
story.append(Paragraph(
    '<b>Self-Directed Study</b> | Systems Programming, Compiler Design, Operating Systems',
    body_style))
story.append(Paragraph(
    'Extensive self-study in low-level systems programming, including OS kernel development (Farmiga), '
    'compiler construction (Coatl, pcc), and language runtime internals. Active contributor to projects '
    'spanning the full stack from Assembly kernels to TypeScript AI coding assistants.',
    small_style
))

doc.build(story)
print(f"CV generated: {output} ({os.path.getsize(output):,} bytes)")
