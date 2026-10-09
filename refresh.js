// "Refresh jobs": re-checks every company job board from the browser and rescores the roles.
(function(){
  var TITLE = /data|analytics|etl|elt|pipeline|warehouse|lakehouse|business intelligence|\bbi\b|ml platform|ml infra|machine learning (platform|infra)|backend|back-end|software engineer|platform engineer|infrastructure engineer/i;
  var EXCL = /manager|director|head of|vp|principal|intern|scientist|analyst|sales|account|solutions|customer|support|recruit|counsel|marketing|product manager|designer/i;
  var SKIP_TITLE = /product management|network|machine learning engineer|research engineer|field engineer|security|hardware|full-stack|frontend/i;
  var USPLACE = /united states|usa|u\.s\.|\bus\b|new york|nyc|san francisco|bay area|seattle|austin|chicago|boston|denver|atlanta|dallas|houston|los angeles|california|texas|mountain view|palo alto|menlo park|sunnyvale|san jose|san mateo|oakland|portland|miami|pittsburgh|philadelphia|salt lake|bellevue|raleigh|minneapolis|nashville|washington, dc|colorado springs|omaha|st\. louis/i;
  var USSTATE = /,\s*(AL|AK|AZ|AR|CA|CO|CT|DE|DC|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b/;
  var RESIDE = /(?:residing|resident|located|based|living|reside|work)\s+(?:in|within|from)\s+(?:the\s+)?([A-Za-z ,]{3,60})/gi;
  var VAGUE = /^\s*(in-office|hybrid|remote|on-?site|office|flexible)?\s*$/i;
  var NONUS = /london|uk\b|united kingdom|india|bengaluru|bangalore|hyderabad|pune|dublin|ireland|toronto|canada|vancouver|berlin|germany|paris|amsterdam|singapore|tokyo|sydney|australia|brazil|mexico|poland|warsaw|spain|madrid|tel aviv|israel|lisbon|portugal|emea|apac|latam|europe|japan|korea|seoul|philippines|argentina|colombia|costa rica|czech|romania|netherlands/i;
  var SAL = /\$\s?(\d{2,3}(?:,\d{3})+|\d{2,3}k)\s*(?:-|–|—|to)\s*\$?\s?(\d{2,3}(?:,\d{3})+|\d{2,3}k)/i;
  var SK = [
    ["BigQuery", /bigquery/i, 10, 1], ["GCP", /\bgcp\b|google cloud/i, 8, 1], ["Airflow", /airflow|cloud composer/i, 8, 1],
    ["SQL", /\bsql\b/i, 6, 1], ["Python", /python/i, 6, 1], ["Dataproc/Hadoop", /dataproc|hadoop|\bpig\b|hive|oozie/i, 4, 1],
    ["Data quality", /data quality|anomal|observab|data validation|monitoring/i, 6, 1], ["ETL/ELT", /\betl\b|\belt\b|pipeline/i, 5, 1],
    ["Cost optimization", /cost/i, 4, 1], ["Migration", /migrat|moderniz/i, 4, 1], ["Data modeling", /data model|dimensional|schema/i, 4, 1],
    ["Analytics/BI", /analytics|looker|dashboard|metrics/i, 3, 1], ["ML data", /machine learning|\bml\b|feature/i, 3, 1],
    ["Near real-time", /real[- ]time|streaming|intraday/i, 4, 0.5], ["GCS", /\bgcs\b|cloud storage/i, 2, 1],
    ["Spark", /spark|pyspark/i, 5, 0.4], ["dbt", /\bdbt\b/i, 4, 0.3], ["Snowflake", /snowflake/i, 4, 0.2], ["Kafka", /kafka|pub\/?sub|kinesis/i, 4, 0.2],
    ["Databricks", /databricks|delta lake/i, 4, 0.1], ["Flink", /flink/i, 3, 0], ["AWS", /\baws\b|redshift|s3\b|glue|emr/i, 3, 0.2],
    ["Scala/Java", /\bscala\b|\bjava\b/i, 3, 0.2], ["Go", /\bgolang\b|\bgo\b,/i, 2, 0], ["Terraform", /terraform/i, 2, 0.2], ["Dagster", /dagster/i, 2, 0.3]
  ];
  var NAMES = {doordashusa: "DoorDash", scaleai: "Scale AI", openai: "OpenAI", sigmacomputing: "Sigma Computing", prizepicks: "PrizePicks", gitlab: "GitLab", mongodb: "MongoDB"};
  var MIN_SCORE = 40;

  var ta = document.createElement("textarea");
  function unesc(s){ ta.innerHTML = s || ""; return ta.value; }
  function strip(s){ return unesc(s).replace(/<[^>]+>/g, " ").replace(/\s+/g, " "); }
  function cap(c){ return c.charAt(0).toUpperCase() + c.slice(1).toLowerCase(); }
  function getJSON(u){ return fetch(u).then(function(r){ return r.ok ? r.json() : null; }).catch(function(){ return null; }); }

  function gh(c){ return getJSON("https://boards-api.greenhouse.io/v1/boards/" + c + "/jobs?content=true").then(function(d){
    return ((d && d.jobs) || []).filter(function(j){ return TITLE.test(j.title) && !EXCL.test(j.title); }).map(function(j){
      var loc = (j.location || {}).name || "";
      var offs = (j.offices || []).map(function(o){ return o.name; }).filter(Boolean).join("; ");
      if (offs && (VAGUE.test(loc) || !(USPLACE.test(loc) || NONUS.test(loc)))) loc = offs;
      return {company: c, title: j.title, loc: loc, url: j.absolute_url, updated: j.updated_at || "", desc: unesc(j.content || ""), comp: "", remote: null};
    }); }); }
  function ash(c){ return getJSON("https://api.ashbyhq.com/posting-api/job-board/" + c + "?includeCompensation=true").then(function(d){
    return ((d && d.jobs) || []).filter(function(j){ return TITLE.test(j.title) && !EXCL.test(j.title); }).map(function(j){
      return {company: c, title: j.title, loc: j.location || "", url: j.jobUrl || "", updated: j.publishedAt || "", desc: j.descriptionPlain || "",
        comp: (j.compensation || {}).compensationTierSummary || "", remote: j.isRemote};
    }); }); }
  function lev(c){ return getJSON("https://api.lever.co/v0/postings/" + c + "?mode=json").then(function(d){
    return (Array.isArray(d) ? d : []).filter(function(j){ var t = j.text || ""; return TITLE.test(t) && !EXCL.test(t); }).map(function(j){
      var cat = j.categories || {}, locs = cat.allLocations || [cat.location || ""], sal = j.salaryRange || {};
      var comp = (sal.min && sal.max) ? ("$" + sal.min.toLocaleString("en-US") + " – $" + sal.max.toLocaleString("en-US")) : "";
      return {company: c, title: j.text, loc: locs.filter(Boolean).join("; "), url: j.hostedUrl || "", updated: "",
        desc: (j.descriptionPlain || "") + " " + (j.additionalPlain || ""), comp: comp, remote: j.workplaceType === "remote"};
    }); }); }

  function score(j){
    var loc = j.loc || "", d = strip(j.desc);
    if (NONUS.test(loc) && !USPLACE.test(loc)) return null;
    if (!(USPLACE.test(loc) || USSTATE.test(loc))) return null;
    var head = d.slice(0, 4000), m;
    RESIDE.lastIndex = 0;
    while ((m = RESIDE.exec(head))) { if (NONUS.test(m[1]) && !USPLACE.test(m[1])) return null; }
    if (SKIP_TITLE.test(j.title)) return null;
    var text = j.title + " " + d, match = [], gap = [], tot = 0, got = 0;
    SK.forEach(function(s){ if (s[1].test(text)) { tot += s[2]; got += s[2] * s[3]; (s[3] >= 0.5 ? match : gap).push(s[0]); } });
    if (!tot) return null;
    var sc = (0.55 * (got / tot) + 0.45 * Math.min(1, got / 45)) * 100;
    var yrs = []; var yr = /(\d{1,2})\s*\+\s*years/g, ym;
    while ((ym = yr.exec(d))) { var n = +ym[1]; if (n >= 1 && n <= 15) yrs.push(n); }
    var y = yrs.length ? Math.min.apply(null, yrs) : null, t = j.title;
    var lvl = /staff|principal|lead/i.test(t) ? "Staff+" : (/senior|sr\.?\b|\biii\b|\biv\b/i.test(t) ? "Senior" : "Mid");
    sc -= lvl === "Staff+" ? 25 : (lvl === "Senior" ? 5 : 0);
    sc -= (y && y >= 8) ? 15 : ((y && y >= 6) ? 6 : 0);
    if (/bigquery/i.test(text)) sc += 6;
    if (/data (engineer|infrastructure|platform)/i.test(t)) sc += 6;
    var sal = j.comp || "";
    if (!sal) { var sm = SAL.exec(d); if (sm) sal = "$" + sm[1] + " – $" + sm[2]; }
    return {company: NAMES[j.company] || cap(j.company), title: t, loc: loc.split("•").join(";").slice(0, 90), url: j.url,
      posted: (j.updated || "").slice(0, 10), score: Math.max(0, Math.min(99, Math.round(sc))), level: lvl, years: y, salary: sal,
      remote: /remote/i.test(loc) || !!j.remote, match: match, gaps: gap};
  }

  function pool(items, size, fn, onEach){
    var i = 0, out = [];
    function next(){ if (i >= items.length) return Promise.resolve();
      var k = i++; return fn(items[k]).then(function(r){ out[k] = r; onEach(); return next(); }); }
    var workers = []; for (var w = 0; w < size; w++) workers.push(next());
    return Promise.all(workers).then(function(){ return out; });
  }
  function lists(src){
    function grab(name){ var m = src.match(new RegExp("^" + name + ' = """([^"]*)"""', "m")); return m ? m[1].split(/\s+/).filter(Boolean) : []; }
    return {GH: grab("GH"), ASH: grab("ASH"), LEV: grab("LEV")};
  }

  var css = document.createElement("style");
  css.textContent = ".stamp{display:flex;flex-wrap:wrap;align-items:center;gap:6px 14px;text-align:left;width:100%}.stamp br{display:none}" +
    ".stamp #srcCount::before{content:'\\00b7';margin-right:14px}" +
    ".refreshbar{display:flex;align-items:center;gap:10px;margin-left:auto}" +
    ".refreshbar .btn{font-family:var(--f-body)}" +
    ".refreshbar .rmsg{font-family:var(--f-mono);font-size:11.5px;color:var(--muted)}";
  document.head.appendChild(css);
  var stamp = document.querySelector(".stamp");
  if (!stamp) return;
  var bar = document.createElement("div");
  bar.className = "refreshbar";
  bar.innerHTML = '<span class="rmsg" id="rMsg"></span><button type="button" class="btn primary" id="rBtn">Refresh jobs</button>';
  stamp.appendChild(bar);
  var msg = document.getElementById("rMsg"), btn = document.getElementById("rBtn");
  function when(ms){ var d = new Date(ms); return d.toLocaleDateString("en-US", {month: "short", day: "numeric"}) + ", " + d.toLocaleTimeString("en-US", {hour: "numeric", minute: "2-digit"}); }
  if (window.liveAt) msg.textContent = "Refreshed " + when(window.liveAt);

  btn.addEventListener("click", function(){
    btn.disabled = true; btn.textContent = "Refreshing…"; msg.textContent = "Loading company list…";
    fetch("radar.py", {cache: "no-store"}).then(function(r){ return r.text(); }).then(function(src){
      var L = lists(src);
      var tasks = L.GH.map(function(c){ return function(){ return gh(c); }; })
        .concat(L.ASH.map(function(c){ return function(){ return ash(c); }; }))
        .concat(L.LEV.map(function(c){ return function(){ return lev(c); }; }));
      if (!tasks.length) throw new Error("no boards");
      var done = 0;
      return pool(tasks, 12, function(f){ return f(); }, function(){ done++; msg.textContent = "Checking job boards: " + done + " of " + tasks.length; });
    }).then(function(results){
      var raw = [].concat.apply([], results);
      if (!raw.length) throw new Error("no postings");
      msg.textContent = "Scoring " + raw.length + " postings…";
      var prev = new Set(JOBS.map(function(j){ return j.url; }));
      var seen = new Set(), out = [];
      raw.map(score).filter(Boolean).sort(function(a, b){ return b.score - a.score; }).forEach(function(o){
        var k = o.company + "|" + o.title + "|" + o.loc;
        if (seen.has(k) || o.score < MIN_SCORE) return;
        seen.add(k); o.isNew = !prev.has(o.url); out.push(o);
      });
      JOBS.forEach(function(j){
        if (j.src !== "wd" && j.src !== "sr") return;
        var k = j.company + "|" + j.title + "|" + j.loc;
        if (!seen.has(k)) { seen.add(k); out.push(Object.assign({}, j, {isNew: false})); }
      });
      out.sort(function(a, b){ return b.score - a.score; });
      if (!out.length) throw new Error("no matches");
      var added = out.filter(function(o){ return o.isNew; }).length;
      try { localStorage.setItem("radarLive", JSON.stringify({at: Date.now(), jobs: out})); }
      catch (e) { throw new Error("storage"); }
      msg.textContent = out.length + " roles, " + added + " new. Reloading…";
      setTimeout(function(){ location.reload(); }, 900);
    }).catch(function(err){
      btn.disabled = false; btn.textContent = "Refresh jobs";
      msg.textContent = err && err.message === "storage" ? "Refresh worked but your browser would not save the results." : "Could not refresh right now. Check your connection and try again.";
    });
  });
})();
