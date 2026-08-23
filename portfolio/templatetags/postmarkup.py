"""A deliberately small formatter for post bodies.

Supports what a technical write-up actually needs — paragraphs, subheadings,
bullets, fenced code and inline `code` — without pulling in a Markdown
dependency. Everything is escaped first, so a post can never inject HTML.
"""

import re

from django import template
from django.utils.html import escape
from django.utils.safestring import mark_safe

register = template.Library()

INLINE_CODE = re.compile(r"`([^`]+)`")
BOLD = re.compile(r"\*\*([^*]+)\*\*")
ITALIC = re.compile(r"(?<!\*)\*([^*\n]+)\*(?!\*)")
LINK = re.compile(r"\[([^\]]+)\]\((https?://[^\s)]+)\)")


def _inline(text: str) -> str:
    """Escape, then apply inline formatting to an already-escaped string."""
    out = escape(text)
    out = INLINE_CODE.sub(r"<code>\1</code>", out)
    out = BOLD.sub(r"<strong>\1</strong>", out)
    out = ITALIC.sub(r"<em>\1</em>", out)
    out = LINK.sub(r'<a href="\2" target="_blank" rel="noopener">\1</a>', out)
    return out


@register.filter
def render_post(body: str) -> str:
    if not body:
        return ""

    html: list[str] = []
    in_code = False
    code_lines: list[str] = []
    bullets: list[str] = []

    def flush_bullets():
        if bullets:
            items = "".join(f"<li>{_inline(b)}</li>" for b in bullets)
            html.append(f"<ul class='post-list'>{items}</ul>")
            bullets.clear()

    for raw_line in body.splitlines():
        line = raw_line.rstrip()

        # Fenced code blocks
        if line.strip().startswith("```"):
            if in_code:
                html.append(f"<pre class='post-code'><code>{escape(chr(10).join(code_lines))}</code></pre>")
                code_lines.clear()
                in_code = False
            else:
                flush_bullets()
                in_code = True
            continue

        if in_code:
            code_lines.append(raw_line)
            continue

        if not line.strip():
            flush_bullets()
            continue

        if line.strip() in ("---", "***", "___"):
            flush_bullets()
            html.append("<hr class='post-rule'>")
        elif line.startswith("## "):
            flush_bullets()
            html.append(f"<h2 class='post-h2'>{_inline(line[3:])}</h2>")
        elif line.startswith("### "):
            flush_bullets()
            html.append(f"<h3 class='post-h3'>{_inline(line[4:])}</h3>")
        elif line.startswith("> "):
            flush_bullets()
            html.append(f"<blockquote class='post-quote'>{_inline(line[2:])}</blockquote>")
        elif line.startswith("- ") or line.startswith("* "):
            bullets.append(line[2:])
        else:
            flush_bullets()
            html.append(f"<p>{_inline(line)}</p>")

    # Anything left open at the end
    if in_code and code_lines:
        html.append(f"<pre class='post-code'><code>{escape(chr(10).join(code_lines))}</code></pre>")
    flush_bullets()

    return mark_safe("".join(html))


@register.filter
def short_since(value):
    """Like `timesince` but a single unit: '3 months' rather than '3 months, 1 week'."""
    if not value:
        return ""
    from django.utils.timesince import timesince

    return timesince(value, depth=1)
