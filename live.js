// Use jobs from the last "Refresh jobs" click if they are newer than this page's daily build.
window.liveJobs = function(snapshot){
  try {
    var saved = JSON.parse(localStorage.getItem("radarLive") || "null");
    var built = Date.parse(document.lastModified) || 0;
    if (saved && saved.jobs && saved.jobs.length && saved.at > built) { window.liveAt = saved.at; return saved.jobs; }
    if (saved) localStorage.removeItem("radarLive");
  } catch (e) {}
  return snapshot;
};
