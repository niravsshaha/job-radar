// "Refresh jobs": re-checks every company job board from the browser and rescores the roles.
(function(){
  // Two dashboards share this file: index.html (data roles) and swe.html (software roles, window.PROFILE = "swe"). Same rules as radar.py.
  var SWE = window.PROFILE === "swe";
  var TITLE_DE = /data|analytics|etl|elt|pipeline|warehouse|lakehouse|business intelligence|\bbi\b|ml platform|ml infra|machine learning (platform|infra)/i;
  var TITLE_SWE = /software (?:engineer|developer|development engineer)|\bswe\b|\bsde\b|backend|back-end|platform engineer|infrastructure engineer|systems software|distributed systems|site reliability|\bsre\b|developer/i;
  var DATA_FIRST = /data engineer|analytics engineer|\betl\b|business intelligence|\bbi\b|data analyst|data warehouse|analytics/i;
  var TITLE = SWE ? TITLE_SWE : TITLE_DE;
  var EXCL = /manager|director|head of|vp|principal|intern|scientist|(?<!data )(?<!intelligence )(?<!bi )(?<!analytics )analyst|sales|account|solutions|customer|support|recruit|counsel|marketing|product manager|designer/i;
  var SKIP_TITLE = SWE ? /product management|machine learning engineer|research engineer|field engineer|security|hardware|full[- ]?stack|front[- ]?end|\bios\b|android|mobile|embedded|firmware|flight software|avionics|datacenter|data center|consultant|salesforce|servicenow|\bsap\b|game|graphics/i
    : /product management|network|machine learning engineer|research engineer|field engineer|security|hardware|full-stack|frontend|embedded|firmware|flight software|avionics|datacenter|data center|consultant/i;
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
  if (SWE) SK = [
    ["Python", /python/i, 8, 1], ["C/C++", /\bc\+\+|\bc\/c\+\+|\bc or c\+\+|\bc, c\+\+/i, 8, 0.7], ["Java", /\bjava\b/i, 4, 0.5], ["Go", /\bgolang\b|\bgo\b,|\bin go\b|\bgo\)/i, 5, 0],
    ["Distributed systems", /distributed system|high[- ]throughput|large[- ]scale (?:distributed|systems|services)/i, 8, 1], ["Linux", /linux|unix/i, 5, 1], ["REST APIs", /\brest\b|restful|microservice/i, 3, 1],
    ["System design", /re-?architect|system design|design doc|architect(?:ed|ing)? (?:and|scalable|systems|services)/i, 3, 1], ["SQL", /\bsql\b/i, 4, 1], ["GCP", /\bgcp\b|google cloud/i, 5, 1], ["AWS", /\baws\b|\bec2\b|\bs3\b|lambda/i, 4, 0.3],
    ["Azure", /azure/i, 2, 0.5], ["Kubernetes/Docker", /kubernetes|\bk8s\b|docker|container/i, 5, 0.8], ["CI/CD", /ci\/cd|jenkins|github actions|continuous (integration|delivery)/i, 4, 0.8],
    ["Terraform/IaC", /terraform|infrastructure as code/i, 2, 0.6], ["Streaming (Kafka/Pub/Sub)", /kafka|pub\/?sub|kinesis|streaming|event[- ]driven/i, 5, 1],
    ["Data processing (Spark/Beam)", /spark|apache beam|dataflow|hadoop/i, 3, 0.8], ["Airflow", /airflow/i, 2, 1], ["BigQuery", /bigquery/i, 3, 1],
    ["Concurrency", /multi-?thread|concurren|parallel/i, 4, 0.8], ["TCP/IP networking", /\btcp\b|\budp\b|socket|ip networking|networking protocol/i, 4, 0.7],
    ["Testing", /unit test|automated test|test automation|integration test|pytest|test infrastructure/i, 4, 0.8], ["Debugging", /debug|troubleshoot|root.cause/i, 4, 1],
    ["Reliability/on-call", /on-?call|\bsla\b|incident response|high availability|site reliability/i, 3, 1], ["Monitoring", /monitoring|observab|alerting|telemetry/i, 3, 1],
    ["Performance/cost", /performance|latency|scalab/i, 2, 1], ["Caching", /cach/i, 2, 0.8], ["AI agents/LLMs", /\bllm|agentic|ai[- ]agent|generative ai|\bgenai\b/i, 3, 0.8],
    ["gRPC", /grpc|protobuf/i, 2, 0], ["Rust", /\brust\b/i, 2, 0], ["JavaScript/TypeScript", /javascript|typescript|react|node\.?js/i, 4, 0.3],
    ["Layer 2/3 protocols", /layer ?2|layer ?3|\bbgp\b|ospf|vlan|vxlan|evpn|lacp|\bstp\b|mpls/i, 4, 0.1], ["Low-level hardware", /\bphys?\b|transceiver|optics|device driver|kernel|\bpcie\b|asic|fpga/i, 4, 0.1]
  ];
  var LIVE_KEY = SWE ? "radarLiveSwe" : "radarLive";
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

  // Skip roles that need a US security clearance or won't sponsor a visa (same rules as radar.py).
  var CLEARANCE = new RegExp("security clearance|secret clearance|top secret|\\bts\\s*/\\s*sci\\b|\\bsci\\b eligib|active clearance|clearance (?:is )?required|(?:obtain|hold|maintain|possess)(?: and maintain)? (?:a |an )?(?:active |current )?(?:us |u\\.s\\. )?(?:government |dod |federal )?(?:security )?clearance|public trust|polygraph|dod secret|clearance eligib|(?:possess|obtain)\\s*:\\s*(?:secret|top secret|ts\\b)", "gi"), NO_SPONSOR = new RegExp("(?:unable|not able|cannot|can ?not|can't|will not|won't|do not|does not|don't|doesn't|not)(?: be)?(?: able)? to (?:currently )?(?:provide|offer|support|consider)? ?(?:any )?(?:visa |immigration |employment |h-?1b )?sponsor|(?:will not|won't|do not|does not|don't|doesn't|cannot|can't|unable to|not) (?:currently )?(?:provide |offer )?(?:visa |immigration |employment |h-?1b )?sponsor|without (?:the )?(?:need for |requiring |requirement of )?(?:current or future |now or in the future |future )?(?:visa |immigration |employment |employer )?sponsorship|no (?:visa |immigration |h-?1b )?sponsorship|sponsorship (?:is |will )?not (?:be )?(?:available|provided|offered|considered)|not (?:eligible|available) for (?:visa |immigration )?sponsorship|must be (?:a )?(?:u\\.?s\\.? |us |united states )citizen|(?:u\\.?s\\.?|us|united states) citizenship (?:is )?required|requires? (?:u\\.?s\\.?|us) citizenship|green card holders? only|citizens? (?:or green card holders? )?only", "gi"), NEGATED = new RegExp("(?:\\bno\\b|\\bnot\\b|n't|without)[^.;]{0,25}$", "i");
  function blocked(title, d){
    var text = title + " " + d, kinds = [["clearance", CLEARANCE], ["sponsorship", NO_SPONSOR]];
    for (var k = 0; k < kinds.length; k++){
      var rx = kinds[k][1], m; rx.lastIndex = 0;
      while ((m = rx.exec(text))){
        var before = text.slice(Math.max(0, m.index - 40), m.index), after = text.slice(m.index + m[0].length, m.index + m[0].length + 40);
        if (!m[0].length) { rx.lastIndex++; continue; }
        if (kinds[k][0] === "clearance" && NEGATED.test(before)) continue;
        if (/^[\s:\/\w-]{0,25}?\b(?:none|not required|n\/a)\b/i.test(after)) continue;
        if (/^\s*(?:protection act|for an export|for export)/i.test(after)) continue;
        return kinds[k][0];
      }
    }
    return "";
  }

  function score(j){
    var loc = j.loc || "", d = strip(j.desc);
    if (NONUS.test(loc) && !USPLACE.test(loc)) return null;
    if (!(USPLACE.test(loc) || USSTATE.test(loc))) return null;
    var head = d.slice(0, 4000), m;
    RESIDE.lastIndex = 0;
    while ((m = RESIDE.exec(head))) { if (NONUS.test(m[1]) && !USPLACE.test(m[1])) return null; }
    if (SKIP_TITLE.test(j.title) || (SWE && DATA_FIRST.test(j.title))) return null;
    if (blocked(j.title, d)) return null;
    var text = j.title + " " + d, match = [], gap = [], tot = 0, got = 0;
    SK.forEach(function(s){ if (s[1].test(text)) { tot += s[2]; got += s[2] * s[3]; (s[3] >= 0.5 ? match : gap).push(s[0]); } });
    if (!tot) return null;
    var sc = (0.55 * (got / tot) + 0.45 * Math.min(1, got / (SWE ? 70 : 45))) * 100;  // software postings list more skills
    var yrs = []; var yr = /(\d{1,2})\s*\+\s*years/g, ym;
    while ((ym = yr.exec(d))) { var n = +ym[1]; if (n >= 1 && n <= 15) yrs.push(n); }
    var y = yrs.length ? Math.min.apply(null, yrs) : null, t = j.title;
    // Shown and filtered on: the highest experience the posting asks for (same rule as radar.py).
    var YRQ = /(\d{1,2})\s*(?:\+|plus|or more)\s*(?:years?|yrs)|(\d{1,2})\s*(?:-|\u2013|to)\s*\d{1,2}\s*(?:years?|yrs)|(?:at least|minimum(?: of)?|min\.)\s*(\d{1,2})\s*(?:years?|yrs)|(\d{1,2})\s*(?:years?|yrs)(?:\s+of)?(?:\s+[\w\/&.,-]+){0,5}?\s+experience/gi, yq, yreq = null;
    while ((yq = YRQ.exec(d))) { for (var gi = 1; gi <= 4; gi++) { var gv = +yq[gi]; if (yq[gi] && gv >= 1 && gv <= 15 && (yreq === null || gv > yreq)) yreq = gv; } }
    var lvl = /staff|principal|lead/i.test(t) ? "Staff+" : (/senior|sr\.?\b|\biii\b|\biv\b/i.test(t) ? "Senior" : "Mid");
    sc -= lvl === "Staff+" ? 25 : (lvl === "Senior" ? 5 : 0);
    sc -= (y && y >= 8) ? 15 : ((y && y >= 6) ? 6 : 0);
    if (SWE) { if (/software|backend|back-end|platform|infrastructure|systems|distributed/i.test(t)) sc += 6; }
    else { if (/bigquery/i.test(text)) sc += 6; if (/data (engineer|infrastructure|platform)/i.test(t)) sc += 6; }
    var sal = j.comp || "";
    if (!sal) { var sm = SAL.exec(d); if (sm) sal = "$" + sm[1] + " – $" + sm[2]; }
    return {company: NAMES[j.company] || cap(j.company), title: t, loc: loc.split("•").join(";").slice(0, 90), url: j.url,
      posted: (j.updated || "").slice(0, 10), score: Math.max(0, Math.min(99, Math.round(sc))), level: lvl, years: yreq, salary: sal,
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
    // Use the uploaded resume (resumes.json) for what you have, same rule as radar.py.
    fetch("resumes.json", {cache: "no-store"}).then(function(r){ return r.ok ? r.json() : null; }).catch(function(){ return null; }).then(function(R){
      var e = R && R[SWE ? "swe" : "de"];
      if (e && e.body) SK.forEach(function(s){ s[3] = s[1].test(e.body) ? 1 : (s[1].test(e.skills || "") ? 0.6 : 0); });
      return fetch("radar.py", {cache: "no-store"});
    }).then(function(r){ return r.text(); }).then(function(src){
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
        if (!j.src) return;  // Workday, SmartRecruiters, big-tech sites, Jooble: only the daily build fetches these
        var k = j.company + "|" + j.title + "|" + j.loc;
        if (!seen.has(k)) { seen.add(k); out.push(Object.assign({}, j, {isNew: false})); }
      });
      out.sort(function(a, b){ return b.score - a.score; });
      if (!out.length) throw new Error("no matches");
      var added = out.filter(function(o){ return o.isNew; }).length;
      try { localStorage.setItem(LIVE_KEY, JSON.stringify({at: Date.now(), jobs: out})); }
      catch (e) { throw new Error("storage"); }
      msg.textContent = out.length + " roles, " + added + " new. Reloading…";
      setTimeout(function(){ location.reload(); }, 900);
    }).catch(function(err){
      btn.disabled = false; btn.textContent = "Refresh jobs";
      msg.textContent = err && err.message === "storage" ? "Refresh worked but your browser would not save the results." : "Could not refresh right now. Check your connection and try again.";
    });
  });
})();
