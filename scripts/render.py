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
    featured_only: bool = False,
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

        if featured_only and not to_bool(place.get("featured", False)):
            continue

        results.append(place)

    results.sort(
        key=lambda p: (
            not to_bool(p.get("featured", False)),
            p.get("name", "").lower(),
        )
    )
    return results


def exclude_by_slug(places: list[dict], slugs_to_exclude: set[str]) -> list[dict]:
    return [place for place in places if place.get("slug") not in slugs_to_exclude]


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


def place_description(place: dict) -> str:
    return place.get("description_short") or place.get("description_long") or ""


def render_place_card(place: dict) -> str:
    name = place.get("name", "")
    description = place_description(place)
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
def build_hotels_content(places: list[dict]) -> str:
    featured_hotels = filter_places(
        places,
        category="hotels",
        subcategory="hotel",
        featured_only=True,
    )

    all_hotels = filter_places(
        places,
        category="hotels",
        subcategory="hotel",
    )

    featured_slugs = {place.get("slug") for place in featured_hotels}
    remaining_hotels = exclude_by_slug(all_hotels, featured_slugs)

    content = HOTELS_TEMPLATE
    content = content.replace("{{ featured_hotels }}", render_place_cards(featured_hotels))
    content = content.replace("{{ all_hotels }}", render_place_cards(remaining_hotels))

    return content


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


def build_things_to_do_content(places: list[dict]) -> str:
    hidden_gems = filter_places(
        places,
        category="things-to-do",
        subcategory="hidden-gem",
    )

    day_trips = filter_places(
        places,
        category="things-to-do",
        subcategory="day-trip",
    )

    cotswolds = filter_places(
        places,
        category="things-to-do",
        subcategory="cotswolds",
    )

    garden_centres = filter_places(
        places,
        category="things-to-do",
        subcategory="garden-centre",
    )

    content = THINGS_TO_DO_TEMPLATE
    content = content.replace("{{ hidden_gems }}", render_place_cards(hidden_gems))
    content = content.replace("{{ day_trips }}", render_place_cards(day_trips))
    content = content.replace("{{ cotswolds }}", render_place_cards(cotswolds))
    content = content.replace("{{ garden_centres }}", render_place_cards(garden_centres))

    return content


def build_plan_content(places: list[dict]) -> str:
    transport = filter_places(
        places,
        category="plan",
        subcategory="transport",
    )

    salons = filter_places(
        places,
        category="plan",
        subcategory="salon",
    )

    useful_services = filter_places(
        places,
        category="plan",
        subcategory="useful-service",
    )

    content = PLAN_TEMPLATE
    content = content.replace("{{ transport }}", render_place_cards(transport))
    content = content.replace("{{ salons }}", render_place_cards(salons))
    content = content.replace("{{ useful_services }}", render_place_cards(useful_services))

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


def render_hotels_page(places: list[dict]) -> None:
    html = render_page(
        title="Hotels Near Bicester Village | Bicester Guide",
        meta_description="Find the best hotels near Bicester Village, from practical overnight stays to more relaxed weekend options.",
        content=build_hotels_content(places),
    )
    write_page(OUTPUT_DIR / "hotels" / "index.html", html)


def render_eat_drink_page(places: list[dict]) -> None:
    html = render_page(
        title="Eat & Drink Near Bicester Village | Bicester Guide",
        meta_description="Find restaurants, gastropubs, pubs, bars and farm shops near Bicester Village.",
        content=build_eat_drink_content(places),
    )
    write_page(OUTPUT_DIR / "eat-drink" / "index.html", html)


def render_things_to_do_page(places: list[dict]) -> None:
    html = render_page(
        title="Things To Do Near Bicester Village | Bicester Guide",
        meta_description="Discover hidden gems, day trips, the Cotswolds and more things to do near Bicester Village.",
        content=build_things_to_do_content(places),
    )
    write_page(OUTPUT_DIR / "things-to-do" / "index.html", html)


def render_plan_page(places: list[dict]) -> None:
    html = render_page(
        title="Plan Your Visit | Bicester Guide",
        meta_description="Transport, salons and useful services near Bicester Village.",
        content=build_plan_content(places),
    )
    write_page(OUTPUT_DIR / "plan" / "index.html", html)


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    places = load_json(PLACES_JSON)

    render_homepage()
    render_hotels_page(places)
    render_eat_drink_page(places)
    render_things_to_do_page(places)
    render_plan_page(places)

    print("Site render complete.")


if __name__ == "__main__":
    main()
