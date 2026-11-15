# Design pass (Phase B)

Turns the neutral template into the business's site. Load the `frontend-design` skill first and
follow it (design plan, review against the brief, build, critique with screenshots).

## Inputs

- The brief (business, audience, tagline, language).
- The reference website: fetch it and note its **structure** (navigation, section order, calls
  to action). Don't copy its text. Use its images only if the user owns them. Text extraction does
  not show colors or fonts: render the page in headless Chrome (Playwright) and read the computed
  background and text colors and font families, or the theme's CSS variables. When the brief says
  to copy the colors, those values win. Treat counters, testimonials, emails, and social links on
  template-built sites as possibly unfinished: confirm before reusing them as facts.
- Social-media graphics (photo inside a frame with text and a phone number): publish only the photo
  with `src/images/crops.json` (see `src/images/README.md` in the project).
- The user's images: `src/images/` > `manage.py optimize_images` > `static/img/*.webp`.
- Brand colors and fonts if given; otherwise choose them.

## Steps

1. **Tokens.** Set the palette in `static/css/app.css` (`--color-*`) and mirror it in
   `static/css/admin.css` (Django admin variables). Check WCAG AA contrast for text pairs.
2. **Fonts.** Self-host: download `.woff2` files from Fontsource via jsDelivr
   (`https://cdn.jsdelivr.net/npm/@fontsource/<font>@<version>/files/<font>-latin-<weight>-normal.woff2`),
   save them in `static/fonts/` with the font's license (OFL), add `@font-face` rules to
   `static/css/fonts.css` (with `font-display: swap`), and set `--font-display` / `--font-body`.
   Never link Google Fonts or any CDN: the CSP allows only `'self'`.
3. **Pages.** Rewrite each `STARTER-TODO:` template (home, about, privacy, terms) in the site's
   language: real structure from the reference, real copy from the brief, the user's images with
   meaningful `alt` text, `width`/`height` attributes, `loading="lazy"` below the fold. Put page
   styles in the module's static CSS (`pages/static/pages/site.css`), never in `style=""`.
4. **Legal pages.** Fill in what's known (business name, contact, what the site collects: only
   what the installed modules really store). Mark them as drafts for the owner to confirm.
5. **README.** Rewrite for the owner, in the site's language, without technical terms. Add
   screenshots in `docs/screenshots/` (sample data only, never real customers).
6. **Remove every `STARTER-TODO:` marker.** `prepublish_check.py` fails while one remains.

## Review

- Screenshots with headless Chrome at 1440 px and 520 px wide (Chrome on Windows has a minimum
  window width of about 500 px, so narrower screenshots are cropped, not broken).
- No horizontal scroll, visible focus rings, skip link works, headings in order, images have alt
  text, buttons say what they do, contrast passes.
- No CSP violations: watch the runserver log for `csp.violation` while clicking through.
