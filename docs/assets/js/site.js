const menuButton = document.querySelector(".nav-toggle");
const mainNav = document.querySelector(".main-nav");

if (menuButton && mainNav) {
  menuButton.addEventListener("click", () => {
    const isOpen = menuButton.getAttribute("aria-expanded") === "true";
    menuButton.setAttribute("aria-expanded", String(!isOpen));
    mainNav.classList.toggle("open", !isOpen);
    document.body.classList.toggle("menu-open", !isOpen);
  });

  mainNav.addEventListener("click", (event) => {
    if (event.target instanceof HTMLAnchorElement) {
      menuButton.setAttribute("aria-expanded", "false");
      mainNav.classList.remove("open");
      document.body.classList.remove("menu-open");
    }
  });
}

const projectCards = Array.from(document.querySelectorAll("[data-project-card]"));
const projectSearch = document.querySelector("[data-project-search]");
const filterControls = Array.from(document.querySelectorAll("[data-project-filter]"));
const emptyState = document.querySelector("[data-empty-state]");

function normalize(value) {
  return String(value || "").trim().toLowerCase();
}

function cardMatches(card, key, value) {
  if (!value || value === "all") return true;
  return normalize(card.dataset[key]).includes(normalize(value));
}

function filterProjects() {
  if (!projectCards.length) return;

  const query = normalize(projectSearch?.value);
  let visibleCount = 0;

  projectCards.forEach((card) => {
    const searchable = normalize(card.textContent);
    const matchesSearch = !query || searchable.includes(query);
    const matchesFilters = filterControls.every((control) =>
      cardMatches(card, control.dataset.projectFilter, control.value)
    );

    const isVisible = matchesSearch && matchesFilters;
    card.hidden = !isVisible;
    if (isVisible) visibleCount += 1;
  });

  if (emptyState) {
    emptyState.hidden = visibleCount !== 0;
  }
}

if (projectSearch) {
  projectSearch.addEventListener("input", filterProjects);
}

filterControls.forEach((control) => {
  control.addEventListener("change", filterProjects);
});

document.querySelectorAll("[data-reset-filters]").forEach((button) => {
  button.addEventListener("click", () => {
    if (projectSearch) projectSearch.value = "";
    filterControls.forEach((control) => {
      control.value = "all";
    });
    filterProjects();
  });
});

filterProjects();
