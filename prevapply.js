// On each job card: "+ Applied here N× · 3 in Oct, 1 in Sep" when you've applied to other roles at that company.
// Clicking the + lists those applications by month.
(function(){
  var css = document.createElement("style");
  css.textContent = ".chip.prevbtn{all:unset;box-sizing:border-box;display:inline-flex;align-items:center;gap:6px;font-size:11.5px;padding:2px 9px 2px 3px;border-radius:999px;background:var(--warn-soft);color:var(--warn);cursor:pointer;font-weight:600}" +
    ".chip.prevbtn:focus-visible{outline:2px solid var(--accent);outline-offset:2px}" +
    ".chip.prevbtn .pp{display:inline-grid;place-items:center;width:16px;height:16px;border-radius:50%;background:var(--warn);color:var(--surface);font-size:12px;line-height:1}" +
    ".prevlist{margin-top:8px;padding:8px 10px;border:1px solid var(--line);border-radius:8px;font-size:12.5px}" +
    ".prevlist b{display:block;margin:4px 0 2px;font-size:12px}.prevlist b:first-child{margin-top:0}" +
    ".prevlist div{display:flex;justify-content:space-between;gap:10px;padding:2px 0}.prevlist a{color:var(--fg)}" +
    ".prevlist span.d{font-family:var(--f-mono);font-size:11.5px;color:var(--muted);white-space:nowrap}";
  document.head.appendChild(css);

  var opened = {};
  function norm(s){ return String(s || "").toLowerCase().replace(/&/g, "and").replace(/[^a-z0-9]/g, ""); }
  function same(a, b){ a = norm(a); b = norm(b); if (!a || !b) return false; if (a === b) return true; var s = a.length < b.length ? a : b, l = s === a ? b : a; return s.length >= 4 && l.indexOf(s) === 0; }
  function apps(){
    var out = [];
    JOBS.forEach(function(j){ if (state.applied[j.id]) out.push({id: j.id, company: j.company, title: j.title, url: j.url, ms: stamp(state.applied[j.id], j)}); });
    (state.manual || []).forEach(function(a){ out.push({company: a.company, title: a.title, url: a.url, ms: a.at ? Date.parse(a.at) : Number(a.mid)}); });
    EXTRA_APPS.forEach(function(a){ if (!JOBS.some(function(j){ return j.url === a.url; })) out.push({company: a.company, title: a.title, url: a.url, ms: Date.parse(a.at)}); });
    GMAIL_APPS.forEach(function(a){ out.push({company: a.company, title: a.title, url: a.url, ms: Date.parse(a.at)}); });
    return out.sort(function(a, b){ return (b.ms || 0) - (a.ms || 0); });
  }
  function mon(ms, long){ return ms ? new Date(ms).toLocaleDateString("en-US", long ? {month: "long", year: "numeric"} : {month: "short"}) : "Date unknown"; }

  function decorate(){
    if (view !== "all" && view !== "saved") return;
    var all = apps(), byJob = {};
    JOBS.forEach(function(j){ byJob[j.id] = j; });
    document.querySelectorAll("#list article.job").forEach(function(card){
      var b = card.querySelector("[data-id]"), j = b && byJob[b.dataset.id], chips = card.querySelector(".chips");
      if (!j || !chips || state.applied[j.id]) return;
      chips.querySelectorAll(".chip.lvl").forEach(function(c){ if (/applied to another role/i.test(c.textContent)) c.remove(); });
      var mine = all.filter(function(a){ return a.id !== j.id && same(a.company, j.company); });
      if (!mine.length) return;
      var counts = [], seen = {};
      mine.forEach(function(a){ var m = mon(a.ms); if (!(m in seen)){ seen[m] = counts.length; counts.push([m, 0]); } counts[seen[m]][1]++; });
      var key = norm(j.company) + "|" + j.id, isOpen = !!opened[key];
      var btn = document.createElement("button");
      btn.type = "button"; btn.className = "chip prevbtn"; btn.setAttribute("aria-expanded", isOpen);
      btn.innerHTML = '<span class="pp">' + (isOpen ? "−" : "+") + "</span>Applied here " + mine.length + "× · " +
        counts.map(function(c){ return c[1] + " in " + c[0]; }).join(", ");
      btn.onclick = function(){ opened[key] = !opened[key]; render(); };
      chips.insertBefore(btn, chips.firstChild);
      if (isOpen){
        var box = document.createElement("div"); box.className = "prevlist"; var last = "", h = "";
        mine.forEach(function(a){
          var m = mon(a.ms, true); if (m !== last){ h += "<b>" + esc(m) + "</b>"; last = m; }
          var t = esc(a.title); h += "<div><span>" + (a.url ? '<a href="' + esc(a.url) + '" target="_blank" rel="noopener">' + t + "</a>" : t) + '</span><span class="d">' +
            (a.ms ? new Date(a.ms).toLocaleDateString("en-US", {month: "short", day: "numeric"}) : "") + "</span></div>";
        });
        box.innerHTML = h; chips.parentNode.insertBefore(box, chips.nextSibling);
      }
    });
  }
  // Re-run whenever the list is redrawn (search, filters, tabs, sync).
  var list = document.getElementById("list");
  if (list) new MutationObserver(function(){ try { decorate(); } catch (e) {} }).observe(list, {childList: true});
  decorate();
})();
