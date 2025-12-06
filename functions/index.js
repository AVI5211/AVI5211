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
 * Format time difference as HH:MM:SS
 * @param {Date} targetDate - Target date
 * @param {Date} now - Current date
 * @return {string} Formatted time string
 */
function formatEta(targetDate, now = new Date()) {
  const diffMs = targetDate - now;
  const totalSeconds = Math.max(0, Math.floor(diffMs / 1000));
  const h = String(Math.floor(totalSeconds / 3600)).padStart(2, "0");
  const m = String(Math.floor((totalSeconds % 3600) / 60)).padStart(2, "0");
  const s = String(totalSeconds % 60).padStart(2, "0");
  return `${h}:${m}:${s}`;
}

/**
 * Parse timestamp from query parameter
 * @param {string|number} raw - Raw timestamp value
 * @return {Date|null} Parsed date or null
 */
function parseTimestamp(raw) {
  if (!raw) return null;
  const num = Number(raw);
  if (!Number.isNaN(num)) {
    // Accept either ms or s epoch values
    const epochMs = num > 1e12 ? num : num * 1000;
    const d = new Date(epochMs);
    return Number.isNaN(d.getTime()) ? null : d;
  }
  const iso = new Date(raw);
  return Number.isNaN(iso.getTime()) ? null : iso;
}

/**
 * Compute ETA relative to the last successful workflow run.
 * If no timestamp is supplied, fall back to cron-based cadence.
 * @param {Date|null} lastRunAt - Timestamp of last workflow completion
 * @param {number} hoursBetween - Hours between runs
 * @return {string}
 */
function nextEta(lastRunAt, hoursBetween = 8) {
  if (lastRunAt instanceof Date && !Number.isNaN(lastRunAt.getTime())) {
    const target = new Date(lastRunAt.getTime() + hoursBetween * 3600 * 1000);
    return formatEta(target);
  }

  // Fallback: scheduled cron windows (00:00, 08:00, 16:00 UTC)
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

  return formatEta(nextRun, utcNow);
}

/**
 * HTTP endpoint for live countdown SVG badge
 * @param {Object} req - Express request
 * @param {Object} res - Express response
 * @return {void}
 */
exports.nextUpdate = onRequest((req, res) => {
  const hoursBetween = Number(
      req.query.window || req.query.hours || req.query.duration,
  ) || 8;
  const lastRunAt = parseTimestamp(
      req.query.t || req.query.timestamp || req.query.lastRun,
  );
  const eta = nextEta(lastRunAt, hoursBetween);

  // SVG badge with bright colors for visibility
  // eslint-disable-next-line max-len
  const svg = `<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" xmlns:xlink="http://www.w3.org/1999/xlink" width="200" height="28" role="img" aria-label="Next Update: ${eta}">
  <title>Next Update: ${eta}</title>
  <defs>
    <linearGradient id="grad" x1="0%" y1="0%" x2="100%" y2="100%">
      <stop offset="0%" style="stop-color:#00ff00;stop-opacity:1" />
      <stop offset="100%" style="stop-color:#00cc00;stop-opacity:1" />
    </linearGradient>
  </defs>
  <rect width="200" height="28" rx="4" fill="url(#grad)"/>
  <rect x="2" y="2" width="196" height="24" rx="3" fill="#000"/>
  <text x="100" y="20" font-family="Arial, sans-serif" font-size="16" 
        font-weight="bold" fill="#00ff00" text-anchor="middle">⏱️ ${eta}</text>
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
