from pathlib import Path
import json
import unicodedata


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
USEFUL_INFO_TEMPLATE = load_text(TEMPLATES_DIR / "useful-info.html")


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


def normalise(value) -> str:
    text = str(value).strip().lower()
    text = unicodedata.normalize("NFKD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return text


def to_bool(value) -> bool:
    return normalise(value) in {"true", "1", "yes"}


def is_live(place: dict) -> bool:
    return normalise(place.get("status", "")) == "live"


def get_categories(place: dict) -> list[str]:
    if place.get("categories"):
        return [normalise(v) for v in split_values(place.get("categories", ""))]
    if place.get("category"):
        return [normalise(place.get("category", ""))]
    return []


def get_subcategories(place: dict) -> list[str]:
    if place.get("subcategories"):
        return [normalise(v) for v in split_values(place.get("subcategories", ""))]
    if place.get("subcategory"):
        return [normalise(place.get("subcategory", ""))]
    return []


def get_tags(place: dict) -> list[str]:
    if place.get("tags"):
        return [normalise(v) for v in split_values(place.get("tags", ""))]
    return []


def get_area(place: dict) -> str:
    return normalise(place.get("area", ""))


def area_in(place: dict, valid_areas: set[str]) -> bool:
    return get_area(place) in {normalise(a) for a in valid_areas}


def get_distance_minutes(place: dict) -> int:
    value = place.get("distance_minutes", "")

    if value is None:
        return 999

    text = str(value).strip()
    if not text:
        return 999

    try:
        return int(float(text))
    except ValueError:
        return 999


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

    category = normalise(category) if category else None
    subcategory = normalise(subcategory) if subcategory else None
    area = normalise(area) if area else None
    tag = normalise(tag) if tag else None

    for place in places:
        if not is_live(place):
            continue

        categories = get_categories(place)
        subcategories = get_subcategories(place)
        tags = get_tags(place)

        if category and category not in categories:
            continue

        if subcategory and subcategory not in subcategories:
            continue

        if area and get_area(place) != area:
            continue

        if tag and tag not in tags:
            continue

        if featured_only and not to_bool(place.get("featured", False)):
            continue

        results.append(place)

    results.sort(
        key=lambda p: (
            not to_bool(p.get("featured", False)),
            get_distance_minutes(p),
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
    badge = ""
    tags = get_tags(place)
    area = get_area(place).replace("-", " ").title()
    meta = area

    if "luxury" in tags:
        badge = '<span class="badge">Luxury</span>'

    return f"""
<article class="listing-card">
  {badge}
  <h3>{place.get("name", "")}</h3>
  <p>{place.get("description_short", "")}</p>
  <div class="card-meta">{meta}</div>
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
    hotels = filter_places(
        places,
        category="hotels",
        subcategory="hotel",
    )

    within_10 = [p for p in hotels if get_distance_minutes(p) <= 10]
    within_20 = [p for p in hotels if 10 < get_distance_minutes(p) <= 20]
    countryside = [p for p in hotels if 20 < get_distance_minutes(p) <= 40]
    london = [p for p in hotels if get_area(p) == "london"]

    content = HOTELS_TEMPLATE
    content = content.replace("{{ hotels_within_10 }}", render_cards(within_10))
    content = content.replace("{{ hotels_within_20 }}", render_cards(within_20))
    content = content.replace("{{ hotels_countryside }}", render_cards(countryside))
    content = content.replace("{{ hotels_london }}", render_cards(london))

    return content


def build_eat_drink_content(places: list[dict]) -> str:
    content = EAT_DRINK_TEMPLATE

    eat_drink_places = filter_places(places, category="eat-drink")

    restaurants_in_village = [
        p for p in eat_drink_places
        if area_in(p, {"bicester-village"}) and "restaurant" in get_subcategories(p)
    ]

    cafes_in_village = [
        p for p in eat_drink_places
        if area_in(p, {"bicester-village"})
        and any(s in {"cafe", "bakery"} for s in get_subcategories(p))
    ]

    cafes_nearby = [
        p for p in eat_drink_places
        if not area_in(p, {"bicester-village"})
        and any(s in {"cafe", "bakery"} for s in get_subcategories(p))
        and get_distance_minutes(p) <= 20
    ]

    gastropubs_nearby = [
        p for p in eat_drink_places
        if "gastropub" in get_subcategories(p)
        and get_distance_minutes(p) <= 20
    ]

    pubs_and_bars_nearby = [
        p for p in eat_drink_places
        if "pub-bar" in get_subcategories(p)
        and get_distance_minutes(p) <= 20
    ]

    cafes_worth_drive = [
        p for p in eat_drink_places
        if any(s in {"cafe", "bakery"} for s in get_subcategories(p))
        and 20 < get_distance_minutes(p) <= 40
    ]

    gastropubs_worth_drive = [
        p for p in eat_drink_places
        if "gastropub" in get_subcategories(p)
        and 20 < get_distance_minutes(p) <= 40
    ]

    farm_shops_worth_drive = [
        p for p in eat_drink_places
        if "farm-shop" in get_subcategories(p)
        and 20 < get_distance_minutes(p) <= 40
    ]

    content = content.replace("{{ restaurants_in_village }}", render_cards(restaurants_in_village))
    content = content.replace("{{ cafes_in_village }}", render_cards(cafes_in_village))
    content = content.replace("{{ cafes_nearby }}", render_cards(cafes_nearby))
    content = content.replace("{{ gastropubs_nearby }}", render_cards(gastropubs_nearby))
    content = content.replace("{{ pubs_and_bars_nearby }}", render_cards(pubs_and_bars_nearby))
    content = content.replace("{{ cafes_worth_drive }}", render_cards(cafes_worth_drive))
    content = content.replace("{{ gastropubs_worth_drive }}", render_cards(gastropubs_worth_drive))
    content = content.replace("{{ farm_shops_worth_drive }}", render_cards(farm_shops_worth_drive))

    return content


def build_things_to_do_content(places: list[dict]) -> str:
    content = THINGS_TO_DO_TEMPLATE

    things_to_do_places = filter_places(places, category="things-to-do")

    hidden_gems_nearby = [
        p for p in things_to_do_places
        if "hidden-gem" in get_subcategories(p)
        and get_distance_minutes(p) <= 20
    ]

    garden_centres_nearby = [
        p for p in things_to_do_places
        if "garden-centre" in get_subcategories(p)
        and get_distance_minutes(p) <= 20
    ]

    day_trips_worth_drive = [
        p for p in things_to_do_places
        if "day-trip" in get_subcategories(p)
        and 20 < get_distance_minutes(p) <= 40
    ]

    cotswolds_worth_drive = [
        p for p in things_to_do_places
        if "cotswolds" in get_subcategories(p)
        and 20 < get_distance_minutes(p) <= 40
    ]

    breweries_vineyards = [
        p for p in things_to_do_places
        if any(
        "brewery" in s or "vineyard" in s
        for s in get_subcategories(p)
        )
    ]

    content = content.replace("{{ hidden_gems_nearby }}", render_cards(hidden_gems_nearby))
    content = content.replace("{{ garden_centres_nearby }}", render_cards(garden_centres_nearby))
    content = content.replace("{{ day_trips_worth_drive }}", render_cards(day_trips_worth_drive))
    content = content.replace("{{ cotswolds_worth_drive }}", render_cards(cotswolds_worth_drive))
    content = content.replace("{{ breweries_vineyards }}", render_cards(breweries_vineyards))

    return content


def build_useful_info_content(places: list[dict]) -> str:
    content = USEFUL_INFO_TEMPLATE

    transport = filter_places(places, category="useful-info", subcategory="transport")
    before_you_go = filter_places(places, category="useful-info", subcategory="before-you-go")
    on_the_day = filter_places(places, category="useful-info", subcategory="on-the-day")
    useful_services = filter_places(places, category="useful-info", subcategory="useful-service")
    salons = filter_places(places, category="useful-info", subcategory="salon")

    content = content.replace("{{ transport }}", render_cards(transport))
    content = content.replace("{{ before_you_go }}", render_cards(before_you_go))
    content = content.replace("{{ on_the_day }}", render_cards(on_the_day))
    content = content.replace("{{ useful_services }}", render_cards(useful_services))
    content = content.replace("{{ salons }}", render_cards(salons))

    return content


# -----------------------------------------------------------------------------
# Page renders
# -----------------------------------------------------------------------------
def render_homepage() -> None:
    write_page(
        OUTPUT_DIR / "index.html",
        render_page(
            "Bicester Guide",
            "Your guide to Bicester Village and beyond.",
            HOMEPAGE_TEMPLATE,
        ),
    )


def render_hotels(places: list[dict]) -> None:
    write_page(
        OUTPUT_DIR / "hotels" / "index.html",
        render_page(
            "Hotels Near Bicester Village",
            "Where to stay near Bicester Village, from convenient hotels just minutes away to countryside stays further out.",
            build_hotels_content(places),
        ),
    )


def render_eat(places: list[dict]) -> None:
    write_page(
        OUTPUT_DIR / "eat-drink" / "index.html",
        render_page(
            "Eat & Drink Near Bicester Village",
            "Restaurants, cafés, pubs, gastropubs and countryside favourites near Bicester Village.",
            build_eat_drink_content(places),
        ),
    )


def render_things(places: list[dict]) -> None:
    write_page(
        OUTPUT_DIR / "things-to-do" / "index.html",
        render_page(
            "Things to Do Near Bicester Village",
            "Hidden gems, day trips, breweries, vineyards, the Cotswolds and more things to do near Bicester Village.",
            build_things_to_do_content(places),
        ),
    )


def render_useful_info(places: list[dict]) -> None:
    write_page(
        OUTPUT_DIR / "useful-info" / "index.html",
        render_page(
            "Useful Info for Bicester Village",
            "Getting there, practical tips and useful information for planning your visit to Bicester Village.",
            build_useful_info_content(places),
        ),
    )


# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------
def main() -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    places = load_json(PLACES_JSON)

    render_homepage()
    render_hotels(places)
    render_eat(places)
    render_things(places)
    render_useful_info(places)

    print("Site build complete")


if __name__ == "__main__":
    main()
