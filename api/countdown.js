/**
 * Vercel API endpoint for live countdown SVG badge
 * Returns a dynamic SVG that GitHub won't cache
 */

function nextEta(hoursBetween = 8) {
  const now = new Date();
  const utcNow = new Date(Date.UTC(
      now.getUTCFullYear(),
      now.getUTCMonth(),
      now.getUTCDate(),
      now.getUTCHours(),
      now.getUTCMinutes(),
      now.getUTCSeconds(),
  ));

  const hours = utcNow.getUTCHours();
  const nextHour = hours - (hours % hoursBetween) + hoursBetween;
  const nextRun = new Date(utcNow);
  nextRun.setUTCHours(nextHour, 0, 0, 0);

  if (nextRun <= utcNow) {
    nextRun.setUTCHours(nextRun.getUTCHours() + hoursBetween);
  }

  const diffMs = nextRun - utcNow;
  const totalSeconds = Math.max(0, Math.floor(diffMs / 1000));
  const h = String(Math.floor(totalSeconds / 3600)).padStart(2, "0");
  const m = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, "0");
  const s = String(totalSeconds % 60).padStart(2, "0");

  return `${h}:${m}:${s}`;
}

export default function handler(req, res) {
  const eta = nextEta(8);

  // SVG badge with no-cache headers
  const svg = `<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="180" height="20" role="img" aria-label="Next Update: ${eta}">
    <title>Next Update: ${eta}</title>
    <linearGradient id="s" x2="0" y2="100%">
      <stop offset="0" stop-color="#bbb"/>
      <stop offset="1" stop-color="#999"/>
    </linearGradient>
    <clipPath id="r">
      <rect width="180" height="20" rx="3" fill="#fff"/>
    </clipPath>
    <g clip-path="url(#r)">
      <rect width="120" height="20" fill="#555"/>
      <rect x="120" width="60" height="20" fill="#1cb841"/>
      <rect width="180" height="20" fill="url(#s)"/>
    </g>
    <g fill="#fff" text-anchor="middle" font-family="Verdana,Geneva,DejaVu Sans,sans-serif" text-rendering="geometricPrecision" font-size="11">
      <text aria-hidden="true" x="610" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="1100">⏱️ Next Update</text>
      <text x="610" y="140" transform="scale(.1)" fill="#fff" textLength="1100">⏱️ Next Update</text>
      <text aria-hidden="true" x="1485" y="150" fill="#010101" fill-opacity=".3" transform="scale(.1)" textLength="500">${eta}</text>
      <text x="1485" y="140" transform="scale(.1)" fill="#fff" textLength="500">${eta}</text>
    </g>
  </svg>`;

  // Force no-cache
  res.setHeader("Content-Type", "image/svg+xml");
  res.setHeader("Cache-Control", "no-store, no-cache, must-revalidate, max-age=0");
  res.setHeader("Pragma", "no-cache");
  res.setHeader("Expires", "0");
  res.setHeader("Surrogate-Control", "no-store");

  res.status(200).send(svg);
}
