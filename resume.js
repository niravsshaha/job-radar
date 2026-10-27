// "Resumes" button: upload a new resume PDF and the job matches are rescored from it.
// The PDF is read in this browser; only its text (from SUMMARY down, so no phone or email) is saved to
// resumes.json in the GitHub repo, using the same token as Sync. Saving starts the daily build, which
// rescores both dashboards (about 40 minutes). Every browser then sees the new matches.
(function(){
  var API = "https://api.github.com/repos/niravsshaha/job-radar/contents/resumes.json";
  var PDFJS = "https://cdnjs.cloudflare.com/ajax/libs/pdf.js/3.11.174/";
  var KINDS = [["de", "Data Engineer"], ["swe", "Software Engineer"]];
  function tok(){ try { return localStorage.getItem("radarSyncToken") || ""; } catch (e) { return ""; } }
  function hdr(){ var h = {"Accept": "application/vnd.github+json"}, t = tok(); if (t) h.Authorization = "Bearer " + t; return h; }
  function enc(s){ var b = new TextEncoder().encode(s), out = ""; for (var i = 0; i < b.length; i++) out += String.fromCharCode(b[i]); return btoa(out); }
  function dec(s){ var b = atob(String(s).replace(/\s/g, "")), u = new Uint8Array(b.length); for (var i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); return new TextDecoder().decode(u); }
  function esc(s){ return String(s == null ? "" : s).replace(/[&<>"]/g, function(c){ return {"&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;"}[c]; }); }
  function day(iso){ return iso ? new Date(iso).toLocaleDateString("en-US", {month: "short", day: "numeric", year: "numeric"}) : "never"; }

  var css = document.createElement("style");
  css.textContent = ".reswrap{position:relative}.respanel{position:absolute;right:0;top:calc(100% + 6px);z-index:40;width:340px;max-width:calc(100vw - 32px);background:var(--surface);color:var(--fg);" +
    "border:1px solid var(--line);border-radius:10px;box-shadow:0 14px 34px rgba(0,0,0,.18);padding:14px;font:13px/1.45 var(--f-body, system-ui, sans-serif);text-align:left}.respanel[hidden]{display:none}" +
    ".respanel h3{margin:0 0 4px;font-size:14px}.respanel p{margin:0 0 10px;color:var(--muted);font-size:12.5px}" +
    ".resrow{display:flex;align-items:center;gap:10px;padding:8px 0;border-top:1px solid var(--line)}.resrow div{flex:1}.resrow b{display:block;font-size:13px}" +
    ".resrow span{font-size:12px;color:var(--muted)}.resmsg{margin-top:8px;font-size:12.5px}.resmsg.bad{color:var(--warn)}";
  document.head.appendChild(css);

  var host = document.querySelector(".refreshbar") || document.querySelector(".stamp");
  if (!host) return;
  var w = document.createElement("div");
  w.className = "reswrap";
  w.innerHTML = '<button type="button" class="btn" id="resBtn">Resumes</button><div class="respanel" id="resPanel" hidden></div>';
  host.insertBefore(w, host.firstChild);
  var panel = w.querySelector("#resPanel"), current = null, sha = null;

  function load(){
    return fetch(API + "?ts=" + Date.now(), {headers: hdr(), cache: "no-store"}).then(function(r){
      if (r.status === 404) { current = {}; sha = null; return; }
      if (!r.ok) throw new Error("read");
      return r.json().then(function(d){ sha = d.sha; current = JSON.parse(dec(d.content)); });
    });
  }
  function draw(note, bad){
    panel.innerHTML = '<h3>Your resumes</h3><p>Upload a new PDF after you change a resume. Matches on both pages are rescored from it in about 40 minutes, on every device.</p>' +
      KINDS.map(function(k){
        var r = (current || {})[k[0]];
        return '<div class="resrow"><div><b>' + k[1] + '</b><span>' + (r ? esc(r.file || "PDF") + " · updated " + day(r.updated) : "Not uploaded yet") + '</span></div>' +
          '<button type="button" class="btn" data-k="' + k[0] + '">Upload PDF</button><input type="file" accept="application/pdf" data-f="' + k[0] + '" hidden></div>';
      }).join("") +
      '<div class="resmsg' + (bad ? " bad" : "") + '" id="resMsg">' + (note || (tok() ? "" : "To save, turn on Sync in this browser first.")) + '</div>';
    panel.querySelectorAll("button[data-k]").forEach(function(b){ b.onclick = function(){ panel.querySelector('input[data-f="' + b.dataset.k + '"]').click(); }; });
    panel.querySelectorAll("input[data-f]").forEach(function(inp){ inp.onchange = function(){ if (inp.files[0]) upload(inp.dataset.f, inp.files[0]); }; });
  }
  function say(t, bad){ var m = panel.querySelector("#resMsg"); if (m) { m.textContent = t; m.className = "resmsg" + (bad ? " bad" : ""); } }

  function script(src){ return new Promise(function(ok, no){ var s = document.createElement("script"); s.src = src; s.onload = ok; s.onerror = no; document.head.appendChild(s); }); }
  function pdfText(file){
    return (window.pdfjsLib ? Promise.resolve() : script(PDFJS + "pdf.min.js")).then(function(){
      pdfjsLib.GlobalWorkerOptions.workerSrc = PDFJS + "pdf.worker.min.js";
      return file.arrayBuffer();
    }).then(function(buf){ return pdfjsLib.getDocument({data: buf}).promise; }).then(function(pdf){
      var pages = []; for (var i = 1; i <= pdf.numPages; i++) pages.push(pdf.getPage(i).then(function(p){ return p.getTextContent(); }));
      return Promise.all(pages);
    }).then(function(contents){
      return contents.map(function(c){ return c.items.map(function(it){ return it.str; }).join(" "); }).join("\n").replace(/\s+/g, " ").trim();
    });
  }
  function upload(kind, file){
    if (!tok()) { say("Turn on Sync in this browser first, so it can save to GitHub.", true); return; }
    say("Reading " + file.name + "…");
    pdfText(file).then(function(text){
      var i = text.search(/\bSUMMARY\b/i); if (i < 0) i = text.search(/\bEXPERIENCE\b/i);
      if (i < 0 || text.length < 500) throw new Error("This PDF has no readable text (is it a scanned image?).");
      text = text.slice(i);                                  // drop the name / phone / email line
      var s = text.search(/\bTECHNICAL SKILLS\b|\bSKILLS\b/i);
      var entry = {file: file.name, updated: new Date().toISOString(), body: s > 0 ? text.slice(0, s) : text, skills: s > 0 ? text.slice(s) : ""};
      say("Saving to GitHub…");
      return load().then(function(){
        var next = Object.assign({}, current); next[kind] = entry;
        var body = {message: "Update " + (kind === "de" ? "Data Engineer" : "Software Engineer") + " resume", content: enc(JSON.stringify(next, null, 1))};
        if (sha) body.sha = sha;
        return fetch(API, {method: "PUT", headers: Object.assign(hdr(), {"Content-Type": "application/json"}), body: JSON.stringify(body)}).then(function(r){
          if (r.status === 401 || r.status === 403) throw new Error("GitHub refused the token. Check Sync is on and the token can write to job-radar.");
          if (!r.ok) throw new Error("Could not save (GitHub said " + r.status + "). Try again.");
          return r.json();
        }).then(function(d){ sha = d.content && d.content.sha; current = next; draw("Saved. Both pages are being rescored; check back in about 40 minutes."); });
      });
    }).catch(function(e){ say(e && e.message && !/^read$/.test(e.message) ? e.message : "Could not read or save the resume. Try again.", true); });
  }

  w.querySelector("#resBtn").onclick = function(){
    if (!panel.hidden) { panel.hidden = true; return; }
    panel.hidden = false; panel.innerHTML = '<p>Loading…</p>';
    load().then(function(){ draw(); }, function(){ current = current || {}; draw("Couldn't check the saved resumes right now.", true); });
  };
  document.addEventListener("click", function(e){ if (!panel.hidden && !w.contains(e.target)) panel.hidden = true; });
})();
