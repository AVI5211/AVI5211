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
 * HTTP endpoint for live countdown badge via shields.io
 * @param {Object} req - Express request
 * @param {Object} res - Express response
 * @return {void}
 */
exports.nextUpdate = onRequest((req, res) => {
  const eta = nextEta(8); // 8-hour cron cadence

  // Force no caching to ensure real-time updates
  res.set(
      "Cache-Control",
      "no-store, no-cache, must-revalidate, proxy-revalidate, max-age=0",
  );
  res.set("Pragma", "no-cache");
  res.set("Expires", "0");
  res.set("Surrogate-Control", "no-store");

  res.json({
    schemaVersion: 1,
    label: "⏱️ Next Update",
    message: eta,
    color: "brightgreen",
    cacheSeconds: 0,
  });
});
