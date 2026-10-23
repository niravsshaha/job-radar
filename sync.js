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
      applying = true; put("radar", J(state)); applying = false; lastApplied = J(state.applied || {});
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
    return fetch(API, {method: "PUT", headers: Object.assign(hdr(), {"Content-Type": "application/json"}), body: J(body), keepalive: J(body).length < 60000}).then(function(r){
      if (r.status === 409 || r.status === 422) throw new Error("conflict");
      if (!r.ok) throw new Error(r.status === 401 || r.status === 403 ? "token" : "HTTP " + r.status);
    });
  }

  function run(){
    timer = null;
    if (busy){ again = true; return; }
    busy = true; show("Syncing…");
    pull().then(function(R){
      // Read this browser's changes only after the download finishes, so a job marked applied
      // while the request was in flight isn't overwritten by the older copy.
      var M = merge(localMap(), R.entries); apply(M);
      if (!tok()) return "ro";
      if (J(M) === J(R.entries)) return "ok";
      return push(M, R.sha).then(function(){ return "ok"; });
    }).then(function(res){
      show(res === "ro" ? "Read-only" : (appliedPending ? "Applied synced ✓ " : "Synced ") + when(Date.now())); appliedPending = false;
    }).catch(function(e){
      if (e.message === "conflict") again = true;
      else show(e.message === "token" ? "Token rejected" : "Sync failed", true);
    }).then(function(){ busy = false; if (again){ again = false; setTimeout(run, 800); } });
  }
  function soon(ms){ clearTimeout(timer); timer = setTimeout(run, ms == null ? 1200 : ms); }
  var lastApplied = J(state.applied || {}), appliedPending = false;

  // Every change the page saves locally also gets synced.
  Storage.prototype.setItem = function(k, v){
    rawSet.call(this, k, v);
    if (applying || k !== "radar" || this !== window.localStorage) return;
    // Marking a job applied (or undoing it) syncs right away; other changes are batched for a moment.
    var a = J(state.applied || {});
    if (a !== lastApplied){ lastApplied = a; appliedPending = true; soon(100); } else soon();
  };
  document.addEventListener("visibilitychange", function(){
    if (document.visibilityState === "visible") soon();
    else if (timer){ clearTimeout(timer); timer = null; run(); }  // leaving the tab: send pending changes now
  });
  window.addEventListener("pagehide", function(){ if (timer){ clearTimeout(timer); timer = null; run(); } });
  // Pick up changes made in your other browser while this tab stays open.
  setInterval(function(){ if (document.visibilityState === "visible" && !busy) run(); }, tok() ? 45000 : 120000);

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

  // Locked token: the token encrypted with a passphrase (PBKDF2 600k + AES-GCM), stored in sync-key.json.
  // Only the encrypted copy is ever uploaded; the passphrase never leaves this browser.
  var KEY_API = "https://api.github.com/repos/niravsshaha/job-radar/contents/sync-key.json", ITER = 600000;
  function b64(u){ var s = ""; for (var i = 0; i < u.length; i++) s += String.fromCharCode(u[i]); return btoa(s); }
  function unb64(s){ var b = atob(s), u = new Uint8Array(b.length); for (var i = 0; i < b.length; i++) u[i] = b.charCodeAt(i); return u; }
  function derive(pass, salt){
    return crypto.subtle.importKey("raw", new TextEncoder().encode(pass), "PBKDF2", false, ["deriveKey"]).then(function(k){
      return crypto.subtle.deriveKey({name: "PBKDF2", salt: salt, iterations: ITER, hash: "SHA-256"}, k, {name: "AES-GCM", length: 256}, false, ["encrypt", "decrypt"]);
    });
  }
  function getKey(){
    return fetch(KEY_API + "?ts=" + Date.now(), {headers: hdr(), cache: "no-store"}).then(function(r){
      if (!r.ok) return null;
      return r.json().then(function(j){ try { return {sha: j.sha, d: JSON.parse(dec(j.content))}; } catch (e) { return null; } });
    }).catch(function(){ return null; });
  }
  function lockToken(pass){
    var salt = crypto.getRandomValues(new Uint8Array(16)), iv = crypto.getRandomValues(new Uint8Array(12));
    return derive(pass, salt).then(function(key){ return crypto.subtle.encrypt({name: "AES-GCM", iv: iv}, key, new TextEncoder().encode(tok())); }).then(function(ct){
      return getKey().then(function(old){
        var body = {message: "Update locked sync token", content: enc(J({v: 1, kdf: "PBKDF2-SHA256", iter: ITER, salt: b64(salt), iv: b64(iv), ct: b64(new Uint8Array(ct))}))};
        if (old) body.sha = old.sha;
        return fetch(KEY_API, {method: "PUT", headers: Object.assign(hdr(), {"Content-Type": "application/json"}), body: J(body)});
      });
    }).then(function(r){ if (!r.ok) throw new Error("save"); });
  }
  function unlockToken(pass, d){
    return derive(pass, unb64(d.salt)).then(function(key){ return crypto.subtle.decrypt({name: "AES-GCM", iv: unb64(d.iv)}, key, unb64(d.ct)); })
      .then(function(pt){ return new TextDecoder().decode(pt); });
  }
  function checkToken(t){
    return fetch(REPO, {headers: hdr(t), cache: "no-store"}).then(function(r){ return r.ok ? r.json() : null; })
      .then(function(j){ return !!(j && j.permissions && j.permissions.push); });
  }
  function turnOn(t){ put(TK, t); panel.hidden = true; draw(); run(); }

  function draw(mode){
    if (tok()){
      panel.innerHTML = '<b>Sync is on in this browser.</b><p style="margin:6px 0 12px">Applied, saved, hidden and added-by-link jobs you change here are saved to your repo, so the dashboard shows them in every browser.</p>' +
        '<div class="row"><button type="button" class="btn" id="syOff">Turn off here</button><button type="button" class="btn primary" id="syNow">Sync now</button></div>' +
        '<hr style="border:0;border-top:1px solid var(--line);margin:14px 0 10px"><b>Lock token for other browsers</b>' +
        '<p style="margin:4px 0 6px" id="syLockInfo">Pick a passphrase. On another browser you can then type it instead of pasting the token.</p>' +
        '<input type="password" id="syPass" placeholder="Long passphrase (4+ random words)" autocomplete="new-password" spellcheck="false">' +
        '<div class="row"><button type="button" class="btn" id="syLock">Save locked token</button></div><p class="syncmsg" id="syErr" style="margin:8px 0 0"></p>';
      panel.querySelector("#syNow").onclick = function(){ panel.hidden = true; run(); };
      panel.querySelector("#syOff").onclick = function(){ del(TK); draw(); show("Read-only"); };
      getKey().then(function(k){ if (k && panel.querySelector("#syLockInfo")) panel.querySelector("#syLockInfo").textContent = "A locked token is already saved. Saving again replaces it (and its passphrase)."; });
      panel.querySelector("#syLock").onclick = function(){
        var p = panel.querySelector("#syPass").value, err = panel.querySelector("#syErr");
        if (p.length < 16){ err.textContent = "Use at least 16 characters, e.g. 4 random words."; return; }
        err.textContent = "Locking…";
        lockToken(p).then(function(){ panel.querySelector("#syPass").value = ""; err.textContent = "Saved. Use this passphrase on your other browsers."; })
          .catch(function(){ err.textContent = "Couldn't save it. Try again."; });
      };
      return;
    }
    if (mode !== "token"){
      panel.innerHTML = '<b>Turn on sync</b><p style="margin:4px 0 6px">Checking for a locked token…</p>';
      getKey().then(function(k){
        if (panel.hidden || tok()) return;
        if (!k){ draw("token"); return; }
        panel.innerHTML = '<b>Turn on sync</b> (once per browser)<p style="margin:4px 0 6px">Type the passphrase you used to lock your token.</p>' +
          '<input type="password" id="syPass" placeholder="Passphrase" autocomplete="current-password" spellcheck="false">' +
          '<div class="row"><button type="button" class="btn" id="syAlt">Paste a token instead</button><button type="button" class="btn primary" id="syUnlock">Unlock</button></div>' +
          '<p class="syncmsg" id="syErr" style="margin:8px 0 0"></p>';
        panel.querySelector("#syAlt").onclick = function(){ draw("token"); };
        panel.querySelector("#syUnlock").onclick = function(){
          var p = panel.querySelector("#syPass").value, err = panel.querySelector("#syErr");
          if (!p){ err.textContent = "Type the passphrase first."; return; }
          err.textContent = "Unlocking…";
          unlockToken(p, k.d).then(function(t){
            return checkToken(t).then(function(ok){ if (ok) turnOn(t); else err.textContent = "Unlocked, but that token no longer works. Paste a new one."; });
          }, function(){ err.textContent = "Wrong passphrase."; });
        };
        panel.querySelector("#syPass").addEventListener("keydown", function(e){ if (e.key === "Enter") panel.querySelector("#syUnlock").click(); });
      });
      return;
    }
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
      checkToken(t).then(function(ok){ if (ok) turnOn(t); else err.textContent = "That token can't write to job-radar. Check step 2 and 3."; })
        .catch(function(){ err.textContent = "Couldn't reach GitHub. Try again."; });
    };
  }
  btn.onclick = function(){ if (panel.hidden){ draw(); panel.hidden = false; } else panel.hidden = true; };
  document.addEventListener("click", function(e){ if (!panel.hidden && e.target.isConnected && !w.contains(e.target)) panel.hidden = true; });

  run();
})();
