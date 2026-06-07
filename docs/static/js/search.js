const input = document.getElementById("search-input");
const resultsEl = document.getElementById("search-results");
const summaryEl = document.getElementById("search-summary");

function normalise(value) {
  return String(value || "").toLowerCase();
}

function placeUrl(place) {
  if (normalise(place.category).includes("hotels")) {
    return `../hotels/${place.slug}/`;
  }

  return place.website || place.google_maps_url || "#";
}

function card(place) {
  const url = placeUrl(place);
  const image = place.image || `../static/images/${place.slug}.jpg`;

  return `
    <article class="listing-card">
      <a href="${url}" class="card-image-link">
        <img
          src="${image}"
          alt="${place.name || ""}"
          class="listing-card-image"
          onerror="this.src='../static/images/holding.jpg'"
        >
      </a>

      <h3>
        <a href="${url}">${place.name || ""}</a>
      </h3>

      <p>${place.description_short || ""}</p>

      <div class="card-meta">${place.area || ""}</div>

      <div class="card-actions">
        <a href="${url}" class="button button-secondary">View details</a>
      </div>
    </article>
  `;
}

function matches(place, query) {
  const text = [
    place.name,
    place.category,
    place.categories,
    place.subcategory,
    place.subcategories,
    place.area,
    place.description_short,
    place.description_long,
    place.tags
  ].map(normalise).join(" ");

  return text.includes(query);
}

async function runSearch(query) {
  query = normalise(query).trim();

  if (!query) {
    summaryEl.textContent = "";
    resultsEl.innerHTML = "";
    return;
  }

  const response = await fetch("../data/places.json");
  const places = await response.json();

  const results = places
    .filter(place => normalise(place.status) === "live")
    .filter(place => matches(place, query))
    .slice(0, 50);

  summaryEl.textContent = `${results.length} result${results.length === 1 ? "" : "s"} for "${query}"`;

  resultsEl.innerHTML = results.length
    ? results.map(card).join("")
    : `<p>No results found. Try searching for hotels, taxis, restaurants, parking or shops.</p>`;
}

const params = new URLSearchParams(window.location.search);
const initialQuery = params.get("q") || "";

if (initialQuery) {
  input.value = initialQuery;
  runSearch(initialQuery);
}

document.querySelector(".search-page-form").addEventListener("submit", event => {
  event.preventDefault();

  const query = input.value.trim();
  const url = new URL(window.location.href);
  url.searchParams.set("q", query);
  window.history.pushState({}, "", url);

  runSearch(query);
});