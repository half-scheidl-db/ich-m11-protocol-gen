"""
ich_m11_renderer.py

HTML -> PDF helpers for ICH M11-style protocol drafts.

Design:
- CSS lives in a standalone .css file.
- HTML wrapper lives in a standalone .html template file.
- Optional PDF rendering uses WeasyPrint when installed.
"""

from pathlib import Path
import html

try:
    from weasyprint import HTML
except ImportError as exc:
    raise ImportError("Install WeasyPrint with: pip install weasyprint") from exc


def esc(value) -> str:
    if value is None:
        return ""
    return html.escape(str(value))


def render_markdown_fragment(text: str) -> str:
    """
    Optional: only use Markdown for free-text narrative fields.
    """
    if not text:
        return ""

    import markdown

    return markdown.markdown(
        text,
        extensions=["extra", "sane_lists"]
    )

def semicolon_text_to_html_bullets(text: str) -> str:
    """
    Convert semicolon-separated criteria text into HTML bullets.
    """
    if not text:
        return ""

    items = [item.strip() for item in str(text).split(";") if item.strip()]

    if not items:
        return ""

    out = ["<ul>"]
    for item in items:
        out.append(f"<li>{esc(item)}</li>")
    out.append("</ul>")

    return "\n".join(out)
def rows_to_table(headers: list[str], rows: list[list[str]], class_name: str = "") -> str:
    cls = f' class="{class_name}"' if class_name else ""

    out = [f"<table{cls}>"]
    out.append("<thead><tr>")
    for h in headers:
        out.append(f"<th>{esc(h)}</th>")
    out.append("</tr></thead>")

    out.append("<tbody>")
    for row in rows:
        out.append("<tr>")
        for cell in row:
            out.append(f"<td>{esc(cell)}</td>")
        out.append("</tr>")
    out.append("</tbody></table>")

    return "\n".join(out)


def protocol_to_html_body(protocol: dict) -> str:
    if "protocol" in protocol and "title_page" not in protocol:
        protocol = protocol["protocol"]

    parts = []

    title_page = protocol.get("title_page", {})
    full_title = title_page.get("full_title", "Untitled Protocol")

    document_id = protocol.get("document_id", "N/A")
    document_type = protocol.get("document_type", "ICH M11 Protocol Draft")
    created_at = protocol.get("created_at", "N/A")
    ich_m11_standard = protocol.get("ich_m11_standard", "N/A")

    parts.append(f"<h1>{esc(full_title)}</h1>")
    parts.append(
        f'<div class="traceability">Document ID: {esc(document_id)} · '
        f'Type: {esc(document_type)} · Created: {esc(created_at)}</div>'
    )
    parts.append(f'<div class="traceability">Standard: {esc(ich_m11_standard)}</div>')

    # Title Page
    parts.append("<h2>Title Page</h2>")

    title_rows = []
    title_fields = [
        ("Full title", "full_title"),
        ("Short title", "short_title"),
        ("Sponsor protocol identifier", "sponsor_protocol_identifier"),
        ("Trial phase", "trial_phase"),
        ("Sponsor", "sponsor_name"),
        ("Therapeutic area", "therapeutic_area"),
        ("Indication", "indication"),
    ]

    for label, key in title_fields:
        val = title_page.get(key)
        if val:
            title_rows.append([label, val])

    countries = title_page.get("countries", [])
    if countries:
        title_rows.append(["Countries", ", ".join(countries)])

    parts.append(rows_to_table(["Field", "Value"], title_rows, "title-page-table"))

    # Synopsis
    synopsis = protocol.get("protocol_synopsis", {})
    if synopsis:
        parts.append("<h2>Protocol Synopsis</h2>")

        if synopsis.get("brief_summary"):
            parts.append("<h3>Brief Summary</h3>")
            parts.append(f"<p>{esc(synopsis['brief_summary'])}</p>")

        if synopsis.get("study_rationale"):
            parts.append("<h3>Study Rationale</h3>")
            parts.append(f"<p>{esc(synopsis['study_rationale'])}</p>")

        primary = synopsis.get("primary_objectives", [])
        if primary:
            parts.append("<h3>Primary Objectives</h3>")
            parts.append("<ul>")
            for obj in primary:
                parts.append(f"<li>{esc(obj)}</li>")
            parts.append("</ul>")

        secondary = synopsis.get("secondary_objectives", [])
        if secondary:
            parts.append("<h3>Secondary Objectives</h3>")
            parts.append("<ul>")
            for obj in secondary:
                parts.append(f"<li>{esc(obj)}</li>")
            parts.append("</ul>")

    # Trial Design
    design = protocol.get("trial_design", {})
    if design:
        parts.append("<h2>Trial Design</h2>")
        parts.append("<ul>")
        for label, key in [
            ("Study type", "study_type"),
            ("Number of arms", "number_of_arms"),
            ("Blinding", "blinding"),
            ("Randomization", "randomization"),
            ("Control type", "control_type"),
        ]:
            parts.append(f"<li><strong>{label}:</strong> {esc(design.get(key, 'N/A'))}</li>")
        parts.append("</ul>")

        arms = design.get("arm_descriptions", [])
        if arms:
            rows = [
                [
                    arm.get("arm_name", "N/A"),
                    arm.get("arm_description", "N/A"),
                    arm.get("intervention", "N/A"),
                ]
                for arm in arms
            ]
            parts.append("<h3>Arm Descriptions</h3>")
            parts.append(rows_to_table(["Arm", "Description", "Intervention"], rows))

    # Protocol Sections
    sections = protocol.get("protocol_sections", [])
    if sections:
        parts.append("<h2>Protocol Body</h2>")

        for section in sections:
            number = section.get("section_number", "")
            title = section.get("section_title", "Untitled Section")
            level = number.count(".") + 3 if number else 3
            level = min(max(level, 3), 6)

            heading = f"{number} {title}".strip()
            parts.append(f"<h{level}>{esc(heading)}</h{level}>")

            content_status = section.get("content_status", "")
            source_domain = section.get("source_domain", "")

            metadata = []
            if content_status:
                metadata.append(f"Status: {content_status}")
            if source_domain and source_domain != "None":
                metadata.append(f"Source: {source_domain}")

            if metadata:
                parts.append(f'<div class="metadata">{esc(". ".join(metadata))}</div>')

            narrative = section.get("narrative_text", "")
            if narrative:
                # Use Markdown only inside narrative sections, if needed.
                parts.append(f'<div class="narrative">{render_markdown_fragment(narrative)}</div>')

    population = protocol.get("trial_population", {})
    if population:
        parts.append("<h2>Trial Population</h2>")
        parts.append("<ul>")
        parts.append(
            f"<li><strong>Planned minimum age:</strong> "
            f"{esc(population.get('planned_minimum_age', 'N/A'))}</li>"
        )
        parts.append(
            f"<li><strong>Planned maximum age:</strong> "
            f"{esc(population.get('planned_maximum_age', 'N/A'))}</li>"
        )
        parts.append(
            f"<li><strong>Sex of participants:</strong> "
            f"{esc(population.get('sex_of_participants', 'N/A'))}</li>"
        )
        parts.append("</ul>")

        inclusion = (
            population.get("inclusion_criteria")
            or population.get("key_inclusion_summary")
            or ""
        )

        if inclusion:
            parts.append("<h3>Inclusion Criteria</h3>")
            parts.append(semicolon_text_to_html_bullets(inclusion))

        exclusion = (
            population.get("exclusion_criteria")
            or population.get("key_exclusion_summary")
            or ""
        )

        if exclusion:
            parts.append("<h3>Exclusion Criteria</h3>")
            parts.append(semicolon_text_to_html_bullets(exclusion))
        
    return "\n".join(parts)


def render_html_document(
    body_html: str,
    css_path: str | Path,
    template_path: str | Path,
    document_title: str = "ICH M11 Protocol Draft",
) -> str:
    css = Path(css_path).read_text(encoding="utf-8")
    template = Path(template_path).read_text(encoding="utf-8")

    return (
        template
        .replace("{{ document_title }}", html.escape(document_title))
        .replace("{{ css }}", css)
        .replace("{{ body_html }}", body_html)
    )


def html_to_pdf(
    output_pdf_path: str | Path,
    *,
    html_path: str | Path | None = None,
    html_string: str | None = None,
) -> None:
    if html_string is not None:
        HTML(string=html_string).write_pdf(str(output_pdf_path))
    elif html_path is not None:
        HTML(filename=str(html_path)).write_pdf(str(output_pdf_path))
    else:
        raise ValueError("Provide either html_path or html_string")