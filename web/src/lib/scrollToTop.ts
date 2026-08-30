/** Reset window and any in-app scroll containers to the top. */
export function scrollPageToTop() {
  window.scrollTo(0, 0);
  document.documentElement.scrollTop = 0;
  document.body.scrollTop = 0;

  const main = document.querySelector("main.main");
  if (main instanceof HTMLElement) {
    main.scrollTop = 0;
  }
}
