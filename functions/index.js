/**
 * Import function triggers from their respective submodules:
 *
 * const {onCall} = require("firebase-functions/v2/https");
 * const {onDocumentWritten} = require("firebase-functions/v2/firestore");
 *
 * See a full list of supported triggers at https://firebase.google.com/docs/functions
 */

const {setGlobalOptions} = require("firebase-functions");
const {onRequest} = require("firebase-functions/https");

setGlobalOptions({maxInstances: 10});

/**
 * Compute next scheduled update ETA (8-hour cron window)
 * Cron runs at 00:00, 08:00, 16:00 UTC
 * @param {number} hoursBetween - Hours between cron runs
 * @return {string} - Time remaining in HH:MM:SS format
 */
function nextEta(hoursBetween = 8) {
  const now = new Date();
  // UTC time
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

/**
 * HTTP endpoint for live countdown SVG badge
 * @param {Object} req - Express request
 * @param {Object} res - Express response
 * @return {void}
 */
exports.nextUpdate = onRequest((req, res) => {
  const eta = nextEta(8); // 8-hour cron cadence

  // SVG badge with no-cache headers
  // eslint-disable-next-line max-len
  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="180" height="20" role="img" aria-label="Next Update: ${eta}">
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
  <g fill="#fff" text-anchor="middle"
     font-family="Verdana,Geneva,DejaVu Sans,sans-serif"
     text-rendering="geometricPrecision" font-size="11">
    <text aria-hidden="true" x="610" y="150" fill="#010101"
          fill-opacity=".3" transform="scale(.1)"
          textLength="1100">⏱️ Next Update</text>
    <text x="610" y="140" transform="scale(.1)" fill="#fff"
          textLength="1100">⏱️ Next Update</text>
    <text aria-hidden="true" x="1485" y="150" fill="#010101"
          fill-opacity=".3" transform="scale(.1)"
          textLength="500">${eta}</text>
    <text x="1485" y="140" transform="scale(.1)" fill="#fff"
          textLength="500">${eta}</text>
  </g>
</svg>`;

  // Force no caching to ensure real-time updates
  res.set(
      "Cache-Control",
      "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0",
  );
  res.set("Pragma", "no-cache");
  res.set("Expires", "0");
  res.set("Surrogate-Control", "no-store");
  res.set("Content-Type", "image/svg+xml");

  res.status(200).send(svg);
});
