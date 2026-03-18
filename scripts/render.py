from pathlib import Path


# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

TEMPLATES_DIR = PROJECT_ROOT / "templates"
PARTIALS_DIR = TEMPLATES_DIR / "partials"
OUTPUT_DIR = PROJECT_ROOT / "docs"


# -----------------------------------------------------------------------------
# Template loading
# -----------------------------------------------------------------------------
def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


BASE_TEMPLATE = load_text(TEMPLATES_DIR / "base.html")
HEADER_TEMPLATE = load_text(PARTIALS_DIR / "header.html")
FOOTER_TEMPLATE = load_text(PARTIALS_DIR / "footer.html")
HOMEPAGE_TEMPLATE = load_text(TEMPLATES_DIR / "homepage.html")
HOTELS_TEMPLATE = load_text(TEMPLATES_DIR / "hotels.html")


# -----------------------------------------------------------------------------
# Rendering helpers
# -----------------------------------------------------------------------------
def render_page(title: str, meta_description: str, content: str) -> str:
    html = BASE_TEMPLATE
    html = html.replace("{{ title }}", title)
    html = html.replace("{{ meta_description }}", meta_description)
    html = html.replace("{{ header }}", HEADER_TEMPLATE)
    html = html.replace("{{ footer }}", FOOTER_TEMPLATE)
    html = html.replace("{{ content }}", content)
    return html


def write_page(output_path: Path, html: str) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(html, encoding="utf-8")
    print(f"Rendered: {output_path.relative_to(PROJECT_ROOT)}")


# -----------------------------------------------------------------------------
# Page renders
# -----------------------------------------------------------------------------
def render_homepage() -> None:
    html = render_page(
        title="Bicester Guide",
        meta_description="Your guide to Bicester Village and beyond.",
        content=HOMEPAGE_TEMPLATE,
    )
    write_page(OUTPUT_DIR / "index.html", html)


def render_hotels_page() -> None:
    html = render_page(
        title="Best Hotels Near Bicester Village | Bicester Guide",
        meta_description="Find the best hotels near Bicester Village, from practical overnight stays to more relaxed weekend options.",
        content=HOTELS_TEMPLATE,
    )
    write_page(OUTPUT_DIR / "hotels" / "index.html", html)


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    render_homepage()
    render_hotels_page()
    print("Site render complete.")


if __name__ == "__main__":
    main()
