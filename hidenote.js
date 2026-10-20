// Hide with a reason: clicking Hide asks why (dropdown + optional note). The reason is saved with the
// hidden job (so it syncs) and shown as the first tag on that job in the Hidden tab.
(function(){
  var REASONS = ["No visa sponsorship", "Too much experience required", "Level too senior", "Tech stack mismatch",
    "Location / on-site only", "Salary too low", "Duplicate posting", "Not interested in company", "Other"];
  var css = document.createElement("style");
  css.textContent = ".hidewrap{position:fixed;inset:0;z-index:50;display:grid;place-items:center;background:rgba(10,16,22,.45);padding:16px}.hidewrap[hidden]{display:none}" +
    ".hidebox{background:var(--surface);color:var(--fg);border:1px solid var(--line);border-radius:12px;box-shadow:0 20px 50px rgba(0,0,0,.3);width:100%;max-width:420px;padding:20px;display:flex;flex-direction:column;gap:10px}" +
    ".hidebox h2{font-size:18px;margin:0}.hidebox p{margin:0;color:var(--muted);font-size:13.5px}.hidebox .hjob{color:var(--fg);font-weight:600}" +
    ".hidebox label{font-size:12.5px;color:var(--muted);display:flex;flex-direction:column;gap:4px}" +
    ".hidebox select,.hidebox textarea{font:inherit;font-size:13.5px;padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--surface);color:var(--fg)}" +
    ".hidebox textarea{min-height:64px;resize:vertical}" +
    ".hideacts{display:flex;gap:8px;justify-content:flex-end;margin-top:4px}.hideacts .btn{padding:9px 12px;font-size:13.5px}" +
    ".chip.hidenote{background:var(--warn-soft);color:var(--warn);font-weight:600;white-space:normal}";
  document.head.appendChild(css);

  var wrap = document.createElement("div");
  wrap.className = "hidewrap"; wrap.hidden = true;
  wrap.innerHTML = '<div class="hidebox" role="dialog" aria-modal="true" aria-labelledby="hideH">' +
    '<h2 id="hideH">Why hide this job?</h2><p class="hjob" id="hideJob"></p>' +
    '<label>Reason<select id="hideReason"><option value="">Choose a reason…</option>' +
    REASONS.map(function(r){ return "<option>" + r + "</option>"; }).join("") + "</select></label>" +
    '<label>Note (optional)<textarea id="hideNote" placeholder="e.g. Requires 10+ years, US citizens only"></textarea></label>' +
    '<div class="hideacts"><button type="button" class="btn" id="hideCancel">Cancel</button>' +
    '<button type="button" class="btn" id="hideSkip">Hide without note</button>' +
    '<button type="button" class="btn primary" id="hideOk">Hide</button></div></div>';
  document.body.appendChild(wrap);
  var current = null, $id = function(x){ return document.getElementById(x); };

  function close(){ wrap.hidden = true; current = null; }
  function hide(val){
    var id = current; close(); if (!id) return;
    var j = JOBS.find(function(x){ return x.id === id; });
    state.hidden[id] = val; persist(); render(); if (typeof dashPanel === "function") dashPanel();
    toast("Hid " + (j ? j.company : "role") + (val && val.reason ? " · " + val.reason : ""), function(){ delete state.hidden[id]; persist(); render(); });
  }
  $id("hideOk").onclick = function(){
    var r = $id("hideReason").value, n = $id("hideNote").value.trim();
    if (!r && !n){ $id("hideReason").focus(); return; }
    hide({reason: r || "Other", note: n, at: new Date().toISOString()});
  };
  $id("hideSkip").onclick = function(){ hide(true); };
  $id("hideCancel").onclick = close;
  wrap.addEventListener("click", function(e){ if (e.target === wrap) close(); });
  document.addEventListener("keydown", function(e){ if (e.key === "Escape" && !wrap.hidden) close(); });

  // Catch "Hide" before the page's own handler; "Unhide" still works as before.
  document.addEventListener("click", function(e){
    var b = e.target.closest('[data-act="hidden"]');
    if (!b || state.hidden[b.dataset.id]) return;
    e.stopPropagation(); e.preventDefault();
    var j = JOBS.find(function(x){ return x.id === b.dataset.id; });
    current = b.dataset.id;
    $id("hideJob").textContent = j ? j.company + " · " + j.title : "";
    $id("hideReason").value = ""; $id("hideNote").value = "";
    wrap.hidden = false; $id("hideReason").focus();
  }, true);

  // Show the reason as the first tag on hidden jobs.
  function decorate(){
    document.querySelectorAll("#list article.job").forEach(function(card){
      var b = card.querySelector('[data-act="hidden"]'), v = b && state.hidden[b.dataset.id], chips = card.querySelector(".chips");
      if (!chips || !v || typeof v !== "object" || chips.querySelector(".hidenote")) return;
      var s = document.createElement("span");
      s.className = "chip hidenote";
      s.textContent = "Hidden: " + (v.reason || "Other") + (v.note ? " — " + v.note : "");
      if (v.at) s.title = "Hidden " + new Date(v.at).toLocaleDateString("en-US", {month: "short", day: "numeric"});
      chips.insertBefore(s, chips.firstChild);
    });
  }
  var list = $id("list");
  if (list) new MutationObserver(function(){ try { decorate(); } catch (e) {} }).observe(list, {childList: true});
  decorate();
})();
