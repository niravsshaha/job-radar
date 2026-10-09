// Multi-select company filter for Job Radar.
(function(){
  var css = document.createElement("style");
  css.textContent = ".cofilter{position:relative}" +
    ".cobtn{padding:8px 30px 8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--fg);font:inherit;cursor:pointer;min-width:150px;text-align:left;position:relative}" +
    ".cobtn::after{content:'';position:absolute;right:11px;top:50%;width:6px;height:6px;border-right:1.5px solid var(--muted);border-bottom:1.5px solid var(--muted);transform:translateY(-70%) rotate(45deg)}" +
    ".copanel{position:absolute;z-index:20;top:calc(100% + 6px);left:0;width:260px;max-width:calc(100vw - 32px);background:var(--surface);border:1px solid var(--line);border-radius:10px;box-shadow:0 10px 30px rgba(0,0,0,.18);padding:10px;display:flex;flex-direction:column;gap:8px}" +
    ".copanel input[type=search]{padding:8px 10px;border:1px solid var(--line);border-radius:8px;background:var(--bg);color:var(--fg);font:inherit;min-width:0}" +
    ".coacts{display:flex;gap:6px}.coacts .btn{flex:1}" +
    ".colist{max-height:280px;overflow:auto;display:flex;flex-direction:column}" +
    ".coitem{display:flex;align-items:center;gap:8px;padding:5px 4px;border-radius:6px;cursor:pointer;font-size:13px}" +
    ".coitem:hover{background:var(--surface-2)}" +
    ".coitem span:first-of-type{flex:1;min-width:0;overflow-wrap:anywhere}" +
    ".coitem .con{color:var(--muted);font-size:12px;font-variant-numeric:tabular-nums}";
  document.head.appendChild(css);

  var counts = {};
  JOBS.forEach(function(j){ counts[j.company] = (counts[j.company] || 0) + 1; });
  GMAIL_APPS.concat(EXTRA_APPS, state.manual || []).forEach(function(a){ if (!(a.company in counts)) counts[a.company] = 0; });
  var names = Object.keys(counts).sort(function(a, b){ return a.localeCompare(b, undefined, {sensitivity: "base"}); });
  var picked = new Set((state.coPicked || []).filter(function(c){ return c in counts; }));

  window.coSel = function(){ return (picked.size === 0 || picked.size === names.length) ? null : picked; };
  function save(){ state.coPicked = Array.from(picked); persist(); }
  function label(){
    var s = window.coSel();
    $("#coBtn").textContent = !s ? "All companies" : (s.size === 1 ? Array.from(s)[0] : s.size + " companies");
  }
  function list(){
    var f = $("#coSearch").value.trim().toLowerCase();
    var shown = names.filter(function(c){ return !f || c.toLowerCase().indexOf(f) >= 0; });
    $("#coList").innerHTML = shown.length ? shown.map(function(c){
      return '<label class="coitem"><input type="checkbox" value="' + esc(c) + '"' + (picked.has(c) ? " checked" : "") + '><span>' + esc(c) + '</span><span class="con">' + (counts[c] || "") + '</span></label>';
    }).join("") : '<p class="addhint">No company matches.</p>';
  }
  function update(){ save(); label(); render(); }
  function close(){ $("#coPanel").hidden = true; $("#coBtn").setAttribute("aria-expanded", "false"); }

  $("#coBtn").addEventListener("click", function(){
    var p = $("#coPanel"); p.hidden = !p.hidden;
    $("#coBtn").setAttribute("aria-expanded", String(!p.hidden));
    if (!p.hidden){ $("#coSearch").value = ""; list(); $("#coSearch").focus(); }
  });
  $("#coSearch").addEventListener("input", list);
  $("#coList").addEventListener("change", function(e){
    var c = e.target.value; if (e.target.checked) picked.add(c); else picked.delete(c); update();
  });
  $("#coAll").addEventListener("click", function(){ names.forEach(function(c){ picked.add(c); }); list(); update(); });
  $("#coNone").addEventListener("click", function(){ picked.clear(); list(); update(); });
  document.addEventListener("click", function(e){ if (!e.target.closest("#coFilter")) close(); });
  document.addEventListener("keydown", function(e){ if (e.key === "Escape") close(); });
  label(); render();
})();
