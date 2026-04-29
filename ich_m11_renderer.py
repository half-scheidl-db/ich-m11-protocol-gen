"""
ich_m11_renderer.py

Markdown -> HTML -> PDF helpers for ICH M11-style protocol drafts.

Design:
- CSS lives in a standalone .css file.
- HTML wrapper lives in a standalone .html template file.
- Generated Markdown is converted to HTML.
- Optional PDF rendering uses WeasyPrint when installed.
"""

from __future__ import annotations

from pathlib import Path
import html

try:
    import markdown
except ImportError as exc:
    raise ImportError("Install markdown with: pip install markdown") from exc


def load_text(path: str | Path) -> str:
    return Path(path).read_text(encoding="utf-8")


def markdown_to_body_html(markdown_text: str) -> str:
    return markdown.markdown(
        markdown_text,
        extensions=["extra", "toc", "sane_lists"]
    )


def render_html_document(
    markdown_text: str,
    css_path: str | Path,
    template_path: str | Path,
    document_title: str = "ICH M11 Protocol Draft"
) -> str:
    css = load_text(css_path)
    template = load_text(template_path)
    body_html = markdown_to_body_html(markdown_text)

    return (
        template
        .replace("{{ document_title }}", html.escape(document_title))
        .replace("{{ css }}", css)
        .replace("{{ body_html }}", body_html)
    )


def write_html(
    markdown_text: str,
    css_path: str | Path,
    template_path: str | Path,
    output_html_path: str | Path,
    document_title: str = "ICH M11 Protocol Draft"
) -> str:
    protocol_html = render_html_document(
        markdown_text=markdown_text,
        css_path=css_path,
        template_path=template_path,
        document_title=document_title,
    )
    Path(output_html_path).write_text(protocol_html, encoding="utf-8")
    return protocol_html


def html_to_pdf(
    output_pdf_path: str | Path,
    *,
    html_path: str | Path | None = None,
    html_string: str | None = None,
) -> None:
    """Convert HTML to PDF using WeasyPrint.

    Provide exactly one of *html_path* (file on disk) or
    *html_string* (in-memory HTML document).
    """
    try:
        from weasyprint import HTML
    except ImportError as exc:
        raise ImportError("Install WeasyPrint with: pip install weasyprint") from exc

    if html_string is not None:
        HTML(string=html_string).write_pdf(str(output_pdf_path))
    elif html_path is not None:
        HTML(filename=str(html_path)).write_pdf(str(output_pdf_path))
    else:
        raise ValueError("Provide either html_path or html_string")


def markdown_to_pdf(
    markdown_text: str,
    css_path: str | Path,
    template_path: str | Path,
    output_pdf_path: str | Path,
    document_title: str = "ICH M11 Protocol Draft"
) -> str:
    protocol_html = render_html_document(
        markdown_text=markdown_text,
        css_path=css_path,
        template_path=template_path,
        document_title=document_title,
    )
    html_to_pdf(output_pdf_path=output_pdf_path, html_string=protocol_html)
    return protocol_html
