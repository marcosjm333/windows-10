"use strict";
(() => {
  const search = document.querySelector("#api-search");
  if (!search) return;
  const status = document.querySelector("#api-status");
  const subsystem = document.querySelector("#api-subsystem");
  const rows = [...document.querySelectorAll("[data-api-row]")];
  const query = new URLSearchParams(location.search);
  search.value = query.get("q") || "";
  if ([...status.options].some(o => o.value === query.get("status"))) status.value = query.get("status");
  if ([...subsystem.options].some(o => o.value === query.get("subsystem"))) subsystem.value = query.get("subsystem");
  function filter() {
    const term = search.value.trim().toLowerCase();
    let visible = 0;
    for (const row of rows) {
      row.hidden = !(row.dataset.search.includes(term) && (!status.value || row.dataset.status === status.value) && (!subsystem.value || row.dataset.subsystem === subsystem.value));
      if (!row.hidden) visible++;
    }
    document.querySelector("#result-count").textContent = `${visible} of ${rows.length} known API contracts`;
    document.querySelector("#no-results").hidden = visible !== 0;
    const params = new URLSearchParams();
    if (search.value) params.set("q", search.value);
    if (status.value) params.set("status", status.value);
    if (subsystem.value) params.set("subsystem", subsystem.value);
    history.replaceState(null, "", location.pathname + (params.size ? "?" + params : ""));
  }
  search.addEventListener("input", filter);
  status.addEventListener("change", filter);
  subsystem.addEventListener("change", filter);
  filter();
})();
