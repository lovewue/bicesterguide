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
# Load helpers
# -----------------------------------------------------------------------------
def load_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def load_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


# -----------------------------------------------------------------------------
# Templates
# -----------------------------------------------------------------------------
BASE_TEMPLATE = load_text(TEMPLATES_DIR / "base.html")
HEADER_TEMPLATE = load_text(PARTIALS_DIR / "header.html")
FOOTER_TEMPLATE = load_text(PARTIALS_DIR / "footer.html")

HOMEPAGE_TEMPLATE = load_text(TEMPLATES_DIR / "homepage.html")
HOTELS_TEMPLATE = load_text(TEMPLATES_DIR / "hotels.html")
EAT_DRINK_TEMPLATE = load_text(TEMPLATES_DIR / "eat-drink.html")
THINGS_TO_DO_TEMPLATE = load_text(TEMPLATES_DIR / "things-to-do.html")
PLAN_TEMPLATE = load_text(TEMPLATES_DIR / "plan.html")


# -----------------------------------------------------------------------------
# Core render helpers
# -----------------------------------------------------------------------------
def render_page(title: str, meta_description: str, content: str) -> str:
    html = BASE_TEMPLATE
    html = html.replace("{{ title }}", title)
    html = html.replace("{{ meta_description }}", meta_description)
    html = html.replace("{{ header }}", HEADER_TEMPLATE)
    html = html.replace("{{ footer }}", FOOTER_TEMPLATE)
    html = html.replace("{{ content }}", content)
    return html


def write_page(path: Path, html: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(html, encoding="utf-8")
    print(f"Rendered: {path.relative_to(PROJECT_ROOT)}")


# -----------------------------------------------------------------------------
# Data helpers
# -----------------------------------------------------------------------------
def split_values(value: str) -> list[str]:
    return [v.strip() for v in str(value).split("|") if v.strip()]


def to_bool(value) -> bool:
    return str(value).strip().lower() in {"true", "1", "yes"}


def is_live(place: dict) -> bool:
    return str(place.get("status", "")).lower() == "live"


def filter_places(
    places: list[dict],
    *,
    category: str | None = None,
    subcategory: str | None = None,
    area: str | None = None,
    tag: str | None = None,
    featured_only: bool = False,
) -> list[dict]:
    results = []

    for place in places:
        if not is_live(place):
            continue

        categories = split_values(place.get("categories", ""))
        subcategories = split_values(place.get("subcategories", ""))
        tags = split_values(place.get("tags", ""))

        if category and category not in categories:
            continue

        if subcategory and subcategory not in subcategories:
            continue

        if area and place.get("area") != area:
            continue

        if tag and tag not in tags:
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


# -----------------------------------------------------------------------------
# Card rendering
# -----------------------------------------------------------------------------
def place_link(place: dict) -> str:
    return (
        place.get("affiliate_url")
        or place.get("booking_url")
        or place.get("website")
        or place.get("google_maps_url")
        or "#"
    )


def place_label(place: dict) -> str:
    if place.get("affiliate_url"):
        return "Book now"
    if place.get("booking_url"):
        return "Check availability"
    if place.get("website"):
        return "Visit website"
    if place.get("google_maps_url"):
        return "View map"
    return "View details"


def render_card(place: dict) -> str:
    return f"""
<article class="listing-card">
  <h3>{place.get("name", "")}</h3>
  <p>{place.get("description_short", "")}</p>
  <a href="{place_link(place)}" class="button">{place_label(place)}</a>
</article>
""".strip()


def render_cards(places: list[dict]) -> str:
    if not places:
        return """
<article class="listing-card">
  <h3>Coming soon</h3>
  <p>We’re currently adding recommendations for this section.</p>
</article>
""".strip()

    return "\n".join(render_card(p) for p in places)


# -----------------------------------------------------------------------------
# Page builders
# -----------------------------------------------------------------------------
def build_hotels_content(places: list[dict]) -> str:

    luxury = filter_places(
        places,
        category="hotels",
        subcategory="hotel",
        tag="luxury",
    )

    bicester = filter_places(
        places,
        category="hotels",
        subcategory="hotel",
        area="bicester",
    )

    nearby = filter_places(
        places,
        category="hotels",
        subcategory="hotel",
        area="near-bicester",
    )

    cotswolds = filter_places(
        places,
        category="hotels",
        subcategory="hotel",
        area="cotswolds",
    )

    london = filter_places(
        places,
        category="hotels",
        subcategory="hotel",
        area="london",
    )

    content = HOTELS_TEMPLATE
    content = content.replace("{{ luxury_hotels }}", render_cards(luxury))
    content = content.replace("{{ hotels_bicester }}", render_cards(bicester))
    content = content.replace("{{ hotels_nearby }}", render_cards(nearby))
    content = content.replace("{{ hotels_cotswolds }}", render_cards(cotswolds))
    content = content.replace("{{ hotels_london }}", render_cards(london))

    return content


def build_eat_drink_content(places: list[dict]) -> str:
    content = EAT_DRINK_TEMPLATE

    content = content.replace(
        "{{ restaurants_in_village }}",
        render_cards(filter_places(places, category="eat-drink", subcategory="restaurant", area="bicester-village")),
    )

    content = content.replace(
        "{{ gastropubs }}",
        render_cards(filter_places(places, category="eat-drink", subcategory="gastropub")),
    )

    content = content.replace(
        "{{ pubs_and_bars }}",
        render_cards(filter_places(places, category="eat-drink", subcategory="pub-bar")),
    )

    content = content.replace(
        "{{ farm_shops }}",
        render_cards(filter_places(places, category="eat-drink", subcategory="farm-shop")),
    )

    return content


def build_things_to_do_content(places: list[dict]) -> str:
    content = THINGS_TO_DO_TEMPLATE

    content = content.replace(
        "{{ hidden_gems }}",
        render_cards(filter_places(places, category="things-to-do", subcategory="hidden-gem")),
    )

    content = content.replace(
        "{{ day_trips }}",
        render_cards(filter_places(places, category="things-to-do", subcategory="day-trip")),
    )

    content = content.replace(
        "{{ cotswolds }}",
        render_cards(filter_places(places, category="things-to-do", subcategory="cotswolds")),
    )

    content = content.replace(
        "{{ garden_centres }}",
        render_cards(filter_places(places, category="things-to-do", subcategory="garden-centre")),
    )

    return content


def build_plan_content(places: list[dict]) -> str:
    content = PLAN_TEMPLATE

    content = content.replace(
        "{{ transport }}",
        render_cards(filter_places(places, category="plan", subcategory="transport")),
    )

    content = content.replace(
        "{{ salons }}",
        render_cards(filter_places(places, category="plan", subcategory="salon")),
    )

    content = content.replace(
        "{{ useful_services }}",
        render_cards(filter_places(places, category="plan", subcategory="useful-service")),
    )

    return content


# -----------------------------------------------------------------------------
# Page renders
# -----------------------------------------------------------------------------
def render_homepage():
    write_page(
        OUTPUT_DIR / "index.html",
        render_page("Bicester Guide", "Your guide to Bicester Village and beyond.", HOMEPAGE_TEMPLATE),
    )


def render_hotels(places):
    write_page(
        OUTPUT_DIR / "hotels" / "index.html",
        render_page("Hotels Near Bicester Village", "", build_hotels_content(places)),
    )


def render_eat(places):
    write_page(
        OUTPUT_DIR / "eat-drink" / "index.html",
        render_page("Eat & Drink Near Bicester Village", "", build_eat_drink_content(places)),
    )


def render_things(places):
    write_page(
        OUTPUT_DIR / "things-to-do" / "index.html",
        render_page("Things to Do Near Bicester Village", "", build_things_to_do_content(places)),
    )


def render_plan(places):
    write_page(
        OUTPUT_DIR / "plan" / "index.html",
        render_page("Plan Your Visit", "", build_plan_content(places)),
    )


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    places = load_json(PLACES_JSON)

    render_homepage()
    render_hotels(places)
    render_eat(places)
    render_things(places)
    render_plan(places)

    print("Site build complete")


if __name__ == "__main__":
    main()
