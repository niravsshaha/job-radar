// Cross-device sync for Applied / Saved / Hidden / Added-by-link.
// Each browser keeps its own copy in localStorage ("radar"); this file merges it with sync.json in the
// GitHub repo. Reading works for everyone (public repo); writing needs a fine-grained token that only
// has Contents read/write on job-radar, pasted once per browser and kept only in that browser.
(function(){
  var API = "https://api.github.com/repos/niravsshaha/job-radar/contents/sync.json";
  var REPO = "https://api.github.com/repos/niravsshaha/job-radar";
  var TK = "radarSyncToken", BASE = "radarSyncBase";
  var rawSet = Storage.prototype.setItem, applying = false, busy = false, again = false, timer = null;

  function ls(k){ try { return localStorage.getItem(k); } catch (e) { return null; } }
  function put(k, v){ try { rawSet.call(localStorage, k, v); } catch (e) {} }
  function del(k){ try { localStorage.removeItem(k); } catch (e) {} }
  function tok(){ return ls(TK) || ""; }
  function hdr(t){ var h = {"Accept": "application/vnd.github+json"}; t = t || tok(); if (t) h.Authorization = "Bearer " + t; return h; }
  function enc(s){ var b = new TextEncoder().encode(s), out = ""; for (var i = 0; i < b.length; i++) out += String.fromCharCode(b[i]); return btoa(out); }
  function dec(s){ var b = atob(String(s).replace(/\s/g, "")), u = new Uint8Array(b.length); for (var i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); return new TextDecoder().decode(u); }
  function J(x){ return JSON.stringify(x); }

  // state <-> flat map of "a|url", "s|url", "h|url", "m|id"
  var KINDS = {a: "applied", s: "saved", h: "hidden"};
  function flat(s){
    var m = {};
    Object.keys(KINDS).forEach(function(k){ var o = s[KINDS[k]] || {}; Object.keys(o).forEach(function(id){ if (o[id]) m[k + "|" + id] = o[id]; }); });
    (s.manual || []).forEach(function(a){ if (a && a.mid) m["m|" + a.mid] = a; });
    return m;
  }
  function unflat(M){
    var s = {applied: {}, saved: {}, hidden: {}, manual: []};
    Object.keys(M).forEach(function(k){
      var e = M[k]; if (!e || e.v == null) return;
      var t = k.charAt(0), id = k.slice(2);
      if (KINDS[t]) s[KINDS[t]][id] = e.v; else if (t === "m") s.manual.push(e.v);
    });
    s.manual.sort(function(a, b){ return Number(b.mid) - Number(a.mid); });
    return s;
  }
  function base(){ try { return JSON.parse(ls(BASE) || "{}"); } catch (e) { return {}; } }

  // What this browser has now, stamped with when each entry last changed here.
  function localMap(){
    var B = base(), cur = flat(state), L = {}, now = Date.now();
    Object.keys(cur).forEach(function(k){ L[k] = (B[k] && B[k].v != null && J(B[k].v) === J(cur[k])) ? B[k] : {v: cur[k], t: now}; });
    Object.keys(B).forEach(function(k){ if (!(k in cur)) L[k] = (B[k].v == null) ? B[k] : {v: null, t: now}; });
    return L;
  }
  function merge(L, R){
    var M = {};
    Object.keys(L).concat(Object.keys(R)).forEach(function(k){
      var a = L[k], b = R[k];
      M[k] = !a ? b : !b ? a : ((a.t || 0) > (b.t || 0) ? a : b);
    });
    return M;
  }
  function apply(M){
    var n = unflat(M), changed = false;
    ["applied", "saved", "hidden", "manual"].forEach(function(k){ if (J(n[k]) !== J(state[k] || (k === "manual" ? [] : {}))) { state[k] = n[k]; changed = true; } });
    put(BASE, J(M));
    if (changed){
      applying = true; put("radar", J(state)); applying = false;
      try { render(); } catch (e) {}
      try { if (typeof dashPanel === "function") dashPanel(); } catch (e) {}
    }
  }

  function pull(){
    return fetch(API + "?ts=" + Date.now(), {headers: hdr(), cache: "no-store"}).then(function(r){
      if (r.status === 404) return {sha: null, entries: {}};
      if (!r.ok) throw new Error(r.status === 401 ? "token" : "HTTP " + r.status);
      return r.json().then(function(j){ var d = {}; try { d = JSON.parse(dec(j.content)); } catch (e) {} return {sha: j.sha, entries: d.entries || {}}; });
    });
  }
  function push(M, sha){
    var body = {message: "Sync applied list", content: enc(JSON.stringify({updated: new Date().toISOString(), entries: M}, null, 1))};
    if (sha) body.sha = sha;
    return fetch(API, {method: "PUT", headers: Object.assign(hdr(), {"Content-Type": "application/json"}), body: J(body)}).then(function(r){
      if (r.status === 409 || r.status === 422) throw new Error("conflict");
      if (!r.ok) throw new Error(r.status === 401 || r.status === 403 ? "token" : "HTTP " + r.status);
    });
  }

  function run(){
    if (busy){ again = true; return; }
    busy = true; show("Syncing…");
    var L = localMap();
    pull().then(function(R){
      var M = merge(L, R.entries); apply(M);
      if (!tok()) return "ro";
      if (J(M) === J(R.entries)) return "ok";
      return push(M, R.sha).then(function(){ return "ok"; });
    }).then(function(res){
      show(res === "ro" ? "Read-only" : "Synced " + when(Date.now()));
    }).catch(function(e){
      if (e.message === "conflict") again = true;
      else show(e.message === "token" ? "Token rejected" : "Sync failed", true);
    }).then(function(){ busy = false; if (again){ again = false; setTimeout(run, 800); } });
  }
  function soon(){ clearTimeout(timer); timer = setTimeout(run, 1200); }

  // Every change the page saves locally also gets synced.
  Storage.prototype.setItem = function(k, v){
    rawSet.call(this, k, v);
    if (!applying && k === "radar" && this === window.localStorage) soon();
  };
  document.addEventListener("visibilitychange", function(){ if (document.visibilityState === "visible") soon(); });

  // UI: a Sync button next to Refresh jobs, with a small panel for the token.
  function when(ms){ var d = new Date(ms); return d.toLocaleTimeString("en-US", {hour: "numeric", minute: "2-digit"}); }
  var css = document.createElement("style");
  css.textContent = ".syncwrap{position:relative;display:inline-flex;align-items:center;gap:8px}" +
    ".syncmsg{font-family:var(--f-mono);font-size:11.5px;color:var(--muted)}.syncmsg.bad{color:var(--warn)}" +
    ".syncpanel{position:absolute;right:0;top:calc(100% + 8px);z-index:50;width:min(360px,calc(100vw - 32px));background:var(--surface);color:var(--fg);border:1px solid var(--line);border-radius:10px;padding:14px;box-shadow:0 8px 30px rgba(0,0,0,.18);font-family:var(--f-body);font-size:13px;line-height:1.45;text-align:left}" +
    ".syncpanel[hidden]{display:none}.syncpanel ol{margin:6px 0 10px;padding-left:18px}.syncpanel input{width:100%;box-sizing:border-box;margin:4px 0 10px;padding:7px 9px;border:1px solid var(--line);border-radius:7px;background:var(--surface);color:var(--fg);font:inherit}" +
    ".syncpanel .row{display:flex;gap:8px;justify-content:flex-end}.syncpanel a{color:var(--accent)}";
  document.head.appendChild(css);

  var host = document.querySelector(".refreshbar") || document.querySelector(".stamp");
  if (!host) return run();
  var w = document.createElement("div");
  w.className = "syncwrap";
  w.innerHTML = '<span class="syncmsg" id="syMsg"></span><button type="button" class="btn" id="syBtn">Sync</button>' +
    '<div class="syncpanel" id="syPanel" hidden></div>';
  host.insertBefore(w, host.firstChild);
  var msg = w.querySelector("#syMsg"), btn = w.querySelector("#syBtn"), panel = w.querySelector("#syPanel");
  function show(t, bad){ if (!msg) return; msg.textContent = t; msg.className = "syncmsg" + (bad ? " bad" : ""); }

  function draw(){
    if (tok()){
      panel.innerHTML = '<b>Sync is on in this browser.</b><p style="margin:6px 0 12px">Applied, saved, hidden and added-by-link jobs you change here are saved to your repo, so the dashboard shows them in every browser.</p>' +
        '<div class="row"><button type="button" class="btn" id="syOff">Turn off here</button><button type="button" class="btn primary" id="syNow">Sync now</button></div>';
      panel.querySelector("#syNow").onclick = function(){ panel.hidden = true; run(); };
      panel.querySelector("#syOff").onclick = function(){ del(TK); draw(); show("Read-only"); };
    } else {
      panel.innerHTML = '<b>Turn on sync</b> (once per browser)' +
        '<ol><li><a href="https://github.com/settings/personal-access-tokens/new" target="_blank" rel="noopener">Create a fine-grained token</a></li>' +
        '<li>Repository access: <i>Only select repositories</i> → <b>job-radar</b></li>' +
        '<li>Repository permissions: <b>Contents → Read and write</b></li>' +
        '<li>Generate, copy, and paste it here</li></ol>' +
        '<input type="password" id="syTok" placeholder="github_pat_…" autocomplete="off" spellcheck="false">' +
        '<div class="row"><button type="button" class="btn" id="syCancel">Cancel</button><button type="button" class="btn primary" id="sySave">Turn on</button></div>' +
        '<p class="syncmsg" id="syErr" style="margin:8px 0 0"></p>';
      panel.querySelector("#syCancel").onclick = function(){ panel.hidden = true; };
      panel.querySelector("#sySave").onclick = function(){
        var t = panel.querySelector("#syTok").value.trim(), err = panel.querySelector("#syErr");
        if (!t){ err.textContent = "Paste the token first."; return; }
        err.textContent = "Checking…";
        fetch(REPO, {headers: hdr(t), cache: "no-store"}).then(function(r){ return r.ok ? r.json() : null; }).then(function(j){
          if (!j || !j.permissions || !j.permissions.push){ err.textContent = "That token can't write to job-radar. Check step 2 and 3."; return; }
          put(TK, t); panel.hidden = true; draw(); run();
        }).catch(function(){ err.textContent = "Couldn't reach GitHub. Try again."; });
      };
    }
  }
  btn.onclick = function(){ if (panel.hidden){ draw(); panel.hidden = false; } else panel.hidden = true; };
  document.addEventListener("click", function(e){ if (!panel.hidden && !w.contains(e.target)) panel.hidden = true; });

  run();
})();
