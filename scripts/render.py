from pathlib import Path
import json


# -----------------------------------------------------------------------------
# Paths
# -----------------------------------------------------------------------------
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

TEMPLATES_DIR = PROJECT_ROOT / "templates"
PARTIALS_DIR = TEMPLATES_DIR / "partials"
DATA_DIR = PROJECT_ROOT / "data"
OUTPUT_DIR = PROJECT_ROOT / "docs"

PLACES_JSON = DATA_DIR / "places.json"


# -----------------------------------------------------------------------------
# Template loading
# -----------------------------------------------------------------------------
def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


BASE_TEMPLATE = load_text(TEMPLATES_DIR / "base.html")
HEADER_TEMPLATE = load_text(PARTIALS_DIR / "header.html")
FOOTER_TEMPLATE = load_text(PARTIALS_DIR / "footer.html")

HOMEPAGE_TEMPLATE = load_text(TEMPLATES_DIR / "homepage.html")
HOTELS_TEMPLATE = load_text(TEMPLATES_DIR / "hotels.html")
EAT_DRINK_TEMPLATE = load_text(TEMPLATES_DIR / "eat-drink.html")
THINGS_TO_DO_TEMPLATE = load_text(TEMPLATES_DIR / "things-to-do.html")
PLAN_TEMPLATE = load_text(TEMPLATES_DIR / "plan.html")


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


def to_bool(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def is_live(place: dict) -> bool:
    return str(place.get("status", "")).strip().lower() == "live"


def filter_places(
    places: list[dict],
    *,
    category: str | None = None,
    subcategory: str | None = None,
    area: str | None = None,
) -> list[dict]:
    results = []

    for place in places:
        if not is_live(place):
            continue

        if category and place.get("category") != category:
            continue

        if subcategory and place.get("subcategory") != subcategory:
            continue

        if area and place.get("area") != area:
            continue

        results.append(place)

    results.sort(key=lambda p: (not to_bool(p.get("featured", False)), p.get("name", "")))
    return results


def place_button_link(place: dict) -> str:
    return (
        place.get("affiliate_url")
        or place.get("booking_url")
        or place.get("website")
        or place.get("google_maps_url")
        or "#"
    )


def place_button_label(place: dict) -> str:
    if place.get("affiliate_url"):
        return "Book now"
    if place.get("booking_url"):
        return "Check availability"
    if place.get("website"):
        return "Visit website"
    if place.get("google_maps_url"):
        return "View map"
    return "View details"


def render_place_card(place: dict) -> str:
    name = place.get("name", "")
    description = place.get("description_short") or place.get("description_long") or ""
    link = place_button_link(place)
    label = place_button_label(place)

    return f"""
<article class="listing-card">
  <h3>{name}</h3>
  <p>{description}</p>
  <a href="{link}" class="button">{label}</a>
</article>
""".strip()


def render_place_cards(places: list[dict]) -> str:
    if not places:
        return """
<article class="listing-card">
  <h3>Coming soon</h3>
  <p>We’re currently adding recommendations for this section.</p>
  <a href="#" class="button">Check back soon</a>
</article>
""".strip()

    return "\n".join(render_place_card(place) for place in places)


# -----------------------------------------------------------------------------
# Page content builders
# -----------------------------------------------------------------------------
def build_eat_drink_content(places: list[dict]) -> str:
    restaurants_in_village = filter_places(
        places,
        category="eat-drink",
        subcategory="restaurant",
        area="bicester-village",
    )

    gastropubs = filter_places(
        places,
        category="eat-drink",
        subcategory="gastropub",
    )

    pubs_and_bars = filter_places(
        places,
        category="eat-drink",
        subcategory="pub-bar",
    )

    farm_shops = filter_places(
        places,
        category="eat-drink",
        subcategory="farm-shop",
    )

    content = EAT_DRINK_TEMPLATE
    content = content.replace("{{ restaurants_in_village }}", render_place_cards(restaurants_in_village))
    content = content.replace("{{ gastropubs }}", render_place_cards(gastropubs))
    content = content.replace("{{ pubs_and_bars }}", render_place_cards(pubs_and_bars))
    content = content.replace("{{ farm_shops }}", render_place_cards(farm_shops))

    return content


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
        title="Hotels Near Bicester Village | Bicester Guide",
        meta_description="Find the best hotels near Bicester Village, from practical overnight stays to more relaxed weekend options.",
        content=HOTELS_TEMPLATE,
    )
    write_page(OUTPUT_DIR / "hotels" / "index.html", html)


def render_eat_drink_page(places: list[dict]) -> None:
    html = render_page(
        title="Eat & Drink Near Bicester Village | Bicester Guide",
        meta_description="Find restaurants, gastropubs, pubs, bars and farm shops near Bicester Village.",
        content=build_eat_drink_content(places),
    )
    write_page(OUTPUT_DIR / "eat-drink" / "index.html", html)


def render_things_to_do_page() -> None:
    html = render_page(
        title="Things To Do Near Bicester Village | Bicester Guide",
        meta_description="Discover hidden gems, day trips, the Cotswolds and more things to do near Bicester Village.",
        content=THINGS_TO_DO_TEMPLATE,
    )
    write_page(OUTPUT_DIR / "things-to-do" / "index.html", html)


def render_plan_page() -> None:
    html = render_page(
        title="Plan Your Visit | Bicester Guide",
        meta_description="Plan your visit to Bicester Village with transport, useful services and practical local information.",
        content=PLAN_TEMPLATE,
    )
    write_page(OUTPUT_DIR / "plan" / "index.html", html)


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    places = load_json(PLACES_JSON)

    render_homepage()
    render_hotels_page()
    render_eat_drink_page(places)
    render_things_to_do_page()
    render_plan_page()

    print("Site render complete.")


if __name__ == "__main__":
    main()
