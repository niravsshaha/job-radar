// "Hide titles with" filter: drop roles whose title has Senior, Staff, etc.
(function(){
  var GROUPS = [
    {key: "senior", label: "Senior", words: ["senior", "sr", "seniority"]},
    {key: "staff", label: "Staff", words: ["staff"]},
    {key: "principal", label: "Principal", words: ["principal", "distinguished"]},
    {key: "lead", label: "Lead", words: ["lead"]},
    {key: "level3", label: "III / IV", words: ["iii", "iv"]},
    {key: "manager", label: "Manager", words: ["manager", "management", "head", "director", "vp"]},
    {key: "junior", label: "Junior / New grad", words: ["junior", "jr", "entry", "grad", "graduate", "apprentice"]},
    {key: "intern", label: "Intern", words: ["intern", "internship", "co-op"]},
    {key: "contract", label: "Contract", words: ["contract", "contractor", "temporary", "temp"]}
  ];

  var css = document.createElement("style");
  css.textContent = ".exrow{display:flex;flex-wrap:wrap;align-items:center;gap:6px;font-size:13px;color:var(--muted)}" +
    ".exrow .exlab{margin-right:2px}" +
    ".exchip{border:1px solid var(--line);background:var(--surface);color:var(--fg);padding:4px 10px;border-radius:999px;font:inherit;font-size:12.5px;cursor:pointer}" +
    ".exchip[aria-pressed=true]{background:var(--warn-soft);border-color:var(--warn);color:var(--warn);text-decoration:line-through}" +
    ".exchip:focus-visible{outline:2px solid var(--accent);outline-offset:2px}" +
    ".exrow input{padding:5px 10px;border:1px solid var(--line);border-radius:999px;background:var(--bg);color:var(--fg);font:inherit;font-size:12.5px;min-width:0;width:200px;max-width:100%}" +
    ".exrow .excount{margin-left:auto;font-variant-numeric:tabular-nums}" +
    ".exrow .exclear{background:none;border:0;color:var(--accent);font:inherit;font-size:12.5px;cursor:pointer;text-decoration:underline}";
  document.head.appendChild(css);

  var on = new Set(state.exTitle || []);
  var extra = state.exWords || "";
  var box = document.getElementById("exFilter");
  if (!box) return;
  box.className = "exrow";
  box.innerHTML = '<span class="exlab">Hide titles with</span>' +
    GROUPS.map(function(g){ return '<button type="button" class="exchip" data-ex="' + g.key + '" aria-pressed="' + on.has(g.key) + '">' + g.label + '</button>'; }).join("") +
    '<input type="text" id="exWords" placeholder="Other words, comma separated" aria-label="Other title words to hide">' +
    '<button type="button" class="exclear" id="exClear">Clear</button>' +
    '<span class="excount" id="exCount"></span>';
  document.getElementById("exWords").value = extra;

  function words(){
    var w = [];
    GROUPS.forEach(function(g){ if (on.has(g.key)) w = w.concat(g.words); });
    return w;
  }
  function custom(){
    return extra.split(",").map(function(s){ return s.trim().toLowerCase(); }).filter(Boolean);
  }
  window.titleHidden = function(title){
    var t = String(title || "").toLowerCase();
    var tokens = t.split(/[^a-z0-9-]+/).filter(Boolean);
    var w = words();
    for (var i = 0; i < w.length; i++) { if (tokens.indexOf(w[i]) >= 0) return true; }
    var c = custom();
    for (var k = 0; k < c.length; k++) { if (t.indexOf(c[k]) >= 0) return true; }
    return false;
  };
  function count(){
    var n = JOBS.filter(function(j){ return window.titleHidden(j.title); }).length;
    document.getElementById("exCount").textContent = n ? ("Hiding " + n + " roles by title") : "";
  }
  function save(){ state.exTitle = Array.from(on); state.exWords = extra; persist(); }
  function update(){ save(); count(); render(); }

  box.addEventListener("click", function(e){
    var b = e.target.closest("[data-ex]");
    if (b){ var k = b.dataset.ex; if (on.has(k)) on.delete(k); else on.add(k); b.setAttribute("aria-pressed", String(on.has(k))); update(); return; }
    if (e.target.id === "exClear"){ on.clear(); extra = ""; document.getElementById("exWords").value = "";
      box.querySelectorAll("[data-ex]").forEach(function(x){ x.setAttribute("aria-pressed", "false"); }); update(); }
  });
  document.getElementById("exWords").addEventListener("input", function(e){ extra = e.target.value; update(); });
  count(); render();
})();
