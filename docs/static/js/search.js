const form = document.getElementById("search-form");
const input = document.getElementById("search-input");
const resultsEl = document.getElementById("search-results");
const summaryEl = document.getElementById("search-summary");

if (!form || !input || !resultsEl || !summaryEl) {
  console.error("Search elements missing", {
    form,
    input,
    resultsEl,
    summaryEl
  });
}

function normalise(value) {
  return String(value || "")
    .toLowerCase()
    .replaceAll("-", " ")
    .trim();
}

function isHotel(place) {
  return normalise(place.category).includes("hotels") ||
         normalise(place.categories).includes("hotels");
}

function placeUrl(place) {
  if (isHotel(place) && place.slug) {
    return `../hotels/${place.slug}/`;
  }

  return place.website || place.google_maps_url || "#";
}

function placeImage(place) {
  if (isHotel(place) && place.slug) {
    return `../static/hotels/${place.slug}/main.jpg`;
  }

  if (place.slug) {
    return `../static/images/${place.slug}.jpg`;
  }

  return "../static/images/holding.jpg";
}

function placeLabel(place) {
  if (isHotel(place) && place.slug) {
    return "View Hotel";
  }

  if (place.affiliate_url || place.booking_url) {
    return "Check availability";
  }

  if (place.website) {
    return "Visit website";
  }

  if (place.google_maps_url) {
    return "View map";
  }

  return "View details";
}


function card(place) {
  const url = placeUrl(place);

  return `
    <article class="listing-card">

      <a href="${url}" target="_blank" rel="noopener noreferrer" class="card-image-link">
        <img
          src="${placeImage(place)}"
          alt="${place.name || ""}"
          class="listing-card-image"
          onerror="this.src='../static/images/placeholder.png'"
        >
      </a>

      <h3>
        <a href="${url}" target="_blank" rel="noopener noreferrer">
          ${place.name || ""}
        </a>
      </h3>

      <p>${place.description_short || ""}</p>

      <div class="card-meta">
        ${String(place.area || "").replaceAll("-", " ")}
      </div>

      <div class="card-actions">
	<a href="${url}" target="_blank" rel="noopener noreferrer" class="button button-secondary">
  	${placeLabel(place)}
	</a>
      </div>

    </article>
  `;
}

function matches(place, query) {
  const searchableText = [
    place.name,
    place.category,
    place.categories,
    place.subcategory,
    place.subcategories,
    place.area,
    place.description_short,
    place.description_long,
    place.tags,
    place.search_terms
  ].map(normalise).join(" ");

  return searchableText.includes(query);
}

async function runSearch(query) {
  query = normalise(query).trim();

  if (!query) {
    summaryEl.textContent = "";
    resultsEl.innerHTML = "";
    return;
  }

  summaryEl.textContent = `Searching for "${query}"...`;

  try {
    const response = await fetch("../data/places.json");

    if (!response.ok) {
      throw new Error(`places.json failed: ${response.status}`);
    }

    const places = await response.json();

    const results = places
      .filter(place => normalise(place.status) === "live")
      .filter(place => matches(place, query))
      .slice(0, 50);

    summaryEl.textContent = `${results.length} result${results.length === 1 ? "" : "s"} for "${query}"`;

    resultsEl.innerHTML = results.length
      ? results.map(card).join("")
      : `<p>No results found. Try searching for hotels, taxis, restaurants, parking or shops.</p>`;

  } catch (error) {
    console.error("Search failed:", error);
    summaryEl.textContent = "Search error";
    resultsEl.innerHTML = `<p>${error.message}</p>`;
  }
}

const params = new URLSearchParams(window.location.search);
const initialQuery = params.get("q") || "";

if (initialQuery) {
  input.value = initialQuery;
  runSearch(initialQuery);
}

form.addEventListener("submit", function (event) {
  event.preventDefault();

  const query = input.value.trim();

  const url = new URL(window.location.href);

  if (query) {
    url.searchParams.set("q", query);
  } else {
    url.searchParams.delete("q");
  }

  window.history.pushState({}, "", url);

  runSearch(query);
});