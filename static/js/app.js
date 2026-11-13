function toggleSidebar() {
  document.getElementById("sidebar")?.classList.toggle("open");
}
function openModal(id) {
  document.getElementById(id)?.classList.add("show");
}
function closeModal(id) {
  document.getElementById(id)?.classList.remove("show");
}
document.addEventListener("click", (e) => {
  if (e.target.classList.contains("modal")) e.target.classList.remove("show");
});
document.querySelectorAll("[data-search]").forEach(input => {
  input.addEventListener("input", () => {
    const value = input.value.toLowerCase();
    const tableId = input.dataset.search;
    document.querySelectorAll(`#${tableId} [data-search-row]`).forEach(row => {
      row.style.display = row.innerText.toLowerCase().includes(value) ? "" : "none";
    });
  });
});
document.querySelectorAll("input[type=date]").forEach(input => {
  input.addEventListener("change", () => {
    const form = input.closest("form");
    const entry = form?.querySelector('[name="data_entrada"]');
    const exit = form?.querySelector('[name="data_saida"]');
    if (entry && exit && entry.value) exit.min = entry.value;
  });
});
setTimeout(() => document.querySelectorAll(".flash").forEach(el => {
  setTimeout(() => el.remove(), 5000);
}), 100);
