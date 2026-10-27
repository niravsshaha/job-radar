// Use jobs from the last "Refresh jobs" click if they are newer than this page's daily build.
window.liveJobs = function(snapshot){
  var KEY = window.PROFILE === "swe" ? "radarLiveSwe" : "radarLive";  // each dashboard keeps its own refresh
  try {
    var saved = JSON.parse(localStorage.getItem(KEY) || "null");
    var built = Date.parse(document.lastModified) || 0;
    if (saved && saved.jobs && saved.jobs.length && saved.at > built) { window.liveAt = saved.at; return saved.jobs; }
    if (saved) localStorage.removeItem(KEY);
  } catch (e) {}
  return snapshot;
};
