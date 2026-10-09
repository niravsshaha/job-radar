// "Did you apply?" prompt shown after clicking Apply on a job card.
(function(){
  var css = document.createElement("style");
  css.textContent = ".askwrap{position:fixed;inset:0;z-index:50;display:grid;place-items:center;background:rgba(10,16,22,.45);padding:16px}.askwrap[hidden]{display:none}" +
    ".askbox{background:var(--surface);color:var(--fg);border:1px solid var(--line);border-radius:12px;box-shadow:0 20px 50px rgba(0,0,0,.3);width:100%;max-width:420px;padding:20px;display:flex;flex-direction:column;gap:12px}" +
    ".askbox h2{font-size:18px;margin:0}" +
    ".askbox p{margin:0;color:var(--muted);font-size:13.5px}" +
    ".askbox .asktitle{color:var(--fg);font-weight:600}" +
    ".askacts{display:flex;flex-wrap:wrap;gap:8px;margin-top:4px}" +
    ".askacts .btn{flex:1 1 auto;padding:9px 12px;font-size:13.5px}";
  document.head.appendChild(css);

  var wrap = document.createElement("div");
  wrap.className = "askwrap"; wrap.hidden = true;
  wrap.innerHTML = '<div class="askbox" role="dialog" aria-modal="true" aria-labelledby="askH">' +
    '<h2 id="askH">Did you apply?</h2>' +
    '<p>The posting opened in a new tab. Come back here when you are done.</p>' +
    '<p class="asktitle" id="askJob"></p>' +
    '<div class="askacts">' +
      '<button type="button" class="btn primary" id="askYes">Yes, I applied</button>' +
      '<button type="button" class="btn" id="askSave">Save for later</button>' +
      '<button type="button" class="btn" id="askNo">Not yet</button>' +
    '</div></div>';
  document.body.appendChild(wrap);

  var current = null;
  function close(){ wrap.hidden = true; current = null; }
  function refresh(){ render(); if (typeof dashPanel === "function") dashPanel(); }

  window.askApplied = function(id){
    var j = JOBS.find(function(x){ return x.id === id; });
    current = id;
    document.getElementById("askJob").textContent = j ? (j.company + " · " + j.title) : "";
    wrap.hidden = false;
    document.getElementById("askYes").focus();
  };

  document.getElementById("askYes").addEventListener("click", function(){
    var id = current; if (!id) return close();
    var j = JOBS.find(function(x){ return x.id === id; });
    state.applied[id] = new Date().toISOString(); delete state.saved[id]; persist();
    close(); refresh();
    toast("Moved " + (j ? j.company : "role") + " to Applied", function(){ delete state.applied[id]; persist(); refresh(); });
  });
  document.getElementById("askSave").addEventListener("click", function(){
    var id = current; if (!id) return close();
    var j = JOBS.find(function(x){ return x.id === id; });
    state.saved[id] = true; persist(); close(); refresh();
    toast("Saved " + (j ? j.company : "role") + " for later");
  });
  document.getElementById("askNo").addEventListener("click", close);
  wrap.addEventListener("click", function(e){ if (e.target === wrap) close(); });
  document.addEventListener("keydown", function(e){ if (e.key === "Escape" && !wrap.hidden) close(); });
})();
