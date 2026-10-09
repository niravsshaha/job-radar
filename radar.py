# Job Radar: pulls public job boards, scores roles against Nirav's resume,
# and writes index.html (the dashboard) + jobs.json (used to flag new roles).
# Usage: python3 radar.py
import json, re, html, os, sys, datetime, concurrent.futures as cf, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)

# Companies to search. Greenhouse board slugs and Ashby board slugs.
GH = """abnormalsecurity adyen affirm airbnb airtable akunacapital algolia alloy alphasights anthropic appian applovin asana attentive axios axon betterment billcom bitgo bitwarden blend block blockchain bloomreach braze brex buildkite builtin calendly calm carta carvana chainguard checkr chime clear cloudflare cockroachlabs coinbase collibra consensys contentful coreweave coupang coursera current databricks datadog dataiku deliveroo descript dialpad discord doordashusa doximity dremio dropbox druva duolingo earnin elastic epicgames everlaw faire fanduel fastly fetch figma fireblocks fivetran flatironhealth flexport forter fubotv gemini gitlab gocardless gofundme grafanalabs greenhouse gusto hellofresh honeycomb hudl imc imply instacart intercom invisible janestreet jfrog jumptrading justworks khanacademy kickstarter klaviyo komodohealth labelbox lattice launchdarkly lithic lucidmotors lyft masterclass medium melio mercury mirakl mixpanel modernhealth mongodb monzo mozilla neo4j netlify netskope newrelic newsela nextdoor nextroll nuro offerup okta onemedical oscar oura pagerduty peloton pendo pinterest planetlabs prizepicks purestorage qualtrics reddit redwoodmaterials relativity riotgames ripple robinhood roblox rocketlab rubrik samsara scaleai scopely seatgeek sendbird sigmacomputing singlestore smartsheet snorkelai sofi splice squarespace stabilityai starburst stitchfix stripe sumologic sweetgreen tanium taskrabbit tide toast tripadvisor twilio twitch udacity udemy underdog upgrade upstart vercel verkada via waymo webflow wikimedia workato yext yugabyte zocdoc zscaler zuora""".split()
ASH = """airbyte alchemy amplitude anyscale applied ashby benchling brightwheel bubble cerebras character circle classdojo clearco clickup cohere confluent cursor deepgram docker drata dune eightsleep elevenlabs envoy expensify flock hackerone handshake harvey headway hex hightouch hopper incident iterable kayak linear mapbox materialize modal motherduck mux neon nerdwallet notion nuna openai orca patreon paxos perplexity persona pinecone plaid poshmark posthog quora railway ramp recharge render replit runway sardine sentilink sentry sift skydio snapdocs snowflake snyk sonder strava supabase tekion temporal thumbtack vanta vivid warp watershed weave xero zapier zip""".split()
LEV = """aircall anchorage arcadia binance gopuff metabase outreach palantir pipedrive ro spotify tala veeva wealthfront zoox""".split()
# Workday career sites: name|tenant|wd number|site (checked only in the daily build; Workday blocks browser requests)
WD = [l.split("|") for l in """Salesforce|salesforce|12|External_Career_Site
Nvidia|nvidia|5|NVIDIAExternalCareerSite
Adobe|adobe|5|external_experienced
Capital One|capitalone|12|Capital_One
Intel|intel|1|External
Workday|workday|5|Workday
PayPal|paypal|1|jobs
Target|target|5|targetcareers
Mastercard|mastercard|1|CorporateCareers
HP|hp|5|ExternalCareerSite
Autodesk|autodesk|1|Ext
Snap|snapchat|1|snap
Disney|disney|5|disneycareer
Bank of America|ghr|1|Lateral-US
Wells Fargo|wf|1|WellsFargoJobs
Broadcom|broadcom|1|External_Career
Micron|micron|1|External
Zillow|zillow|5|Zillow_Group_External
CrowdStrike|crowdstrike|5|crowdstrikecareers
Athenahealth|athenahealth|1|External
Fidelity|fmr|1|FidelityCareers
Red Hat|redhat|5|jobs
Motorola Solutions|motorolasolutions|5|Careers
eBay|ebay|5|apply
CVS Health|cvshealth|1|cvs_health_careers
Humana|humana|5|Humana_External_Career_Site
T-Mobile|tmobile|1|External
Verizon|verizon|12|verizon-careers
Lowes|lowes|5|LWS_External_CS
Home Depot|homedepot|5|CareerDepot
Boeing|boeing|1|EXTERNAL_CAREERS
General Motors|generalmotors|5|Careers_GM
Morgan Stanley|ms|5|External
Nike|nike|1|nke
Pfizer|pfizer|1|PfizerCareers
Thomson Reuters|thomsonreuters|5|External_Career_Site
Accenture|accenture|103|AccentureCareers
Allstate|allstate|5|allstate_careers
Nordstrom|nordstrom|501|nordstrom_careers
Gap|gapinc|1|GAPINC
Sony|sonyglobal|1|SonyGlobalCareers
Warner Bros Discovery|warnerbros|5|global
Fox|fox|1|Domestic
Equifax|equifax|5|External
TransUnion|transunion|5|TransUnion
S&P Global|spgi|5|SPGI_Careers
Cisco|cisco|5|Cisco_Careers
Analog Devices|analogdevices|1|External
Ciena|ciena|5|Careers
GE Healthcare|gehc|5|GEHC_ExternalSite
Medtronic|medtronic|1|MedtronicCareers
Abbott|abbott|5|abbottcareers
Johnson & Johnson|jj|5|JJ
Elevance|elevancehealth|1|ANT
Cigna|cigna|5|cignacareers
Visa|visa|5|Visa""".splitlines()]
SR = """ServiceNow BoschGroup Canva Experian WesternDigital Freshworks AbbVie""".split()  # SmartRecruiters company ids
WD_TERMS = ["data engineer", "software engineer", "analytics engineer", "data platform"]

UA = {'User-Agent': 'Mozilla/5.0'}
TITLE = re.compile(r'data|analytics|etl|elt|pipeline|warehouse|lakehouse|business intelligence|\bbi\b|ml platform|ml infra|machine learning (platform|infra)|backend|back-end|software engineer|platform engineer|infrastructure engineer', re.I)
EXCL = re.compile(r'manager|director|head of|vp|principal|intern|scientist|analyst|sales|account|solutions|customer|support|recruit|counsel|marketing|product manager|designer', re.I)
SKIP_TITLE = re.compile(r'product management|network|machine learning engineer|research engineer|field engineer|security|hardware|full-stack|frontend|embedded|firmware|flight software|avionics|datacenter|data center|consultant', re.I)
MIN_SCORE = 40  # roles below this fit score are dropped; the page has its own fit filter
NAMES = {'doordashusa': 'DoorDash', 'scaleai': 'Scale AI', 'openai': 'OpenAI', 'sigmacomputing': 'Sigma Computing', 'prizepicks': 'PrizePicks', 'gitlab': 'GitLab', 'mongodb': 'MongoDB'}

def get(u):
    try:
        return json.load(urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25))
    except Exception:
        return None

def gh(c):
    d = get(f"https://boards-api.greenhouse.io/v1/boards/{c}/jobs?content=true")
    out = []
    for j in (d or {}).get('jobs', []):
        t = j['title']
        if TITLE.search(t) and not EXCL.search(t):
            loc = (j.get('location') or {}).get('name', '')
            offs = '; '.join(o.get('name', '') for o in (j.get('offices') or []) if o.get('name'))
            if offs and (VAGUE.match(loc) or not (USPLACE.search(loc) or NONUS.search(loc))): loc = offs
            out.append(dict(company=c, title=t, loc=loc, url=j['absolute_url'],
                            updated=j.get('updated_at', ''), desc=html.unescape(j.get('content', '')), comp='', remote=None))
    return out

def lev(c):
    d = get(f"https://api.lever.co/v0/postings/{c}?mode=json")
    out = []
    for j in (d if isinstance(d, list) else []):
        t = j.get('text', '')
        if TITLE.search(t) and not EXCL.search(t):
            cat = j.get('categories') or {}
            locs = cat.get('allLocations') or [cat.get('location', '')]
            sal = j.get('salaryRange') or {}
            comp = f"${sal['min']:,} \u2013 ${sal['max']:,}" if sal.get('min') and sal.get('max') else ''
            out.append(dict(company=c, title=t, loc='; '.join(x for x in locs if x), url=j.get('hostedUrl', ''),
                            updated='', desc=(j.get('descriptionPlain') or '') + ' ' + (j.get('additionalPlain') or ''), comp=comp,
                            remote=(j.get('workplaceType') == 'remote')))
    return out

def post(u, body):
    try:
        r = urllib.request.urlopen(urllib.request.Request(u, data=json.dumps(body).encode(), headers={**UA, 'Content-Type': 'application/json', 'Accept': 'application/json'}), timeout=25)
        return json.load(r)
    except Exception:
        return None

def retry(f, *a):
    for k in range(3):  # Workday throttles bursts from shared CI runners; back off and retry
        r = f(*a)
        if r is not None: return r
        __import__("time").sleep(2 * (k + 1))
    return None

def wd(entry):
    name, ten, n, site = entry
    base = f"https://{ten}.wd{n}.myworkdayjobs.com/wday/cxs/{ten}/{site}"
    paths = {}
    for term in WD_TERMS:
        for off in range(0, 100, 20):
            d = retry(post, base + "/jobs", {"appliedFacets": {}, "limit": 20, "offset": off, "searchText": term})
            posts = (d or {}).get("jobPostings") or []
            for p in posts:
                t, lt = p.get("title", ""), p.get("locationsText", "")
                if TITLE.search(t) and not EXCL.search(t) and not (NONUS.search(lt) and not USPLACE.search(lt)):
                    paths.setdefault(p.get("externalPath"), t)
            if len(posts) < 20: break
    out = []
    for path in list(paths)[:120]:
        d = retry(get, base + path) if path else None
        i = (d or {}).get("jobPostingInfo") or {}
        if not i: continue
        cc = ((i.get("jobRequisitionLocation") or {}).get("country") or {}).get("alpha2Code", "")
        loc = i.get("location", "") + ("; " + "; ".join(i.get("additionalLocations") or []) if i.get("additionalLocations") else "")
        if cc not in ("", "US") and not re.search(r"united states|\bUSA?\b", loc): continue
        if cc == "US" and not (USPLACE.search(loc) or USSTATE.search(loc)): loc = (loc + ", United States").strip(", ")
        out.append(dict(company=name, title=i.get("title", paths[path]), loc=loc, url=i.get("externalUrl", ""), updated=i.get("startDate", ""),
                        desc=html.unescape(i.get("jobDescription", "")), comp="", remote=bool(re.search(r"remote", loc, re.I)), src="wd"))
    return out

def sr(c):
    out, seen = [], set()
    for term in WD_TERMS:
        d = get(f"https://api.smartrecruiters.com/v1/companies/{c}/postings?limit=100&country=us&q=" + urllib.parse.quote(term))
        for p in (d or {}).get("content") or []:
            t = p.get("name", "")
            if p.get("id") in seen or not TITLE.search(t) or EXCL.search(t): continue
            seen.add(p.get("id"))
            det = get(f"https://api.smartrecruiters.com/v1/companies/{c}/postings/{p['id']}") or {}
            secs = (det.get("jobAd") or {}).get("sections") or {}
            desc = " ".join((secs.get(k) or {}).get("text", "") for k in ("jobDescription", "qualifications", "additionalInformation"))
            loc = (p.get("location") or {}).get("fullLocation", "")
            out.append(dict(company=(p.get("company") or {}).get("name", c), title=t, loc=loc, url=det.get("postingUrl", ""), updated=p.get("releasedDate", ""),
                            desc=desc, comp="", remote=bool((p.get("location") or {}).get("remote")), src="sr"))
    return out

def ash(c):
    d = get(f"https://api.ashbyhq.com/posting-api/job-board/{c}?includeCompensation=true")
    out = []
    for j in (d or {}).get('jobs', []):
        t = j['title']
        if TITLE.search(t) and not EXCL.search(t):
            out.append(dict(company=c, title=t, loc=j.get('location', ''), url=j.get('jobUrl', ''), updated=j.get('publishedAt', ''),
                            desc=j.get('descriptionPlain', '') or '', comp=(j.get('compensation') or {}).get('compensationTierSummary', ''),
                            remote=j.get('isRemote')))
    return out

US = re.compile(r'united states|usa|\bus\b|u\.s\.|remote|new york|san francisco|seattle|austin|chicago|boston|denver|atlanta|dallas|los angeles|bay area|california|texas|washington|nyc|sf|mountain view|palo alto|menlo|sunnyvale|san jose|oakland|portland|miami|pittsburgh|philadelphia|salt lake|bellevue|cambridge|raleigh|minneapolis|nashville', re.I)
# US-only filter: a role is kept only when its location names a US place or state.
USPLACE = re.compile(r'united states|usa|u\.s\.|\bus\b|new york|nyc|san francisco|bay area|seattle|austin|chicago|boston|denver|atlanta|dallas|houston|los angeles|california|texas|mountain view|palo alto|menlo park|sunnyvale|san jose|san mateo|oakland|portland|miami|pittsburgh|philadelphia|salt lake|bellevue|raleigh|minneapolis|nashville|washington, dc|colorado springs|omaha|st\. louis', re.I)
USSTATE = re.compile(r',\s*(AL|AK|AZ|AR|CA|CO|CT|DE|DC|FL|GA|HI|ID|IL|IN|IA|KS|KY|LA|ME|MD|MA|MI|MN|MS|MO|MT|NE|NV|NH|NJ|NM|NY|NC|ND|OH|OK|OR|PA|RI|SC|SD|TN|TX|UT|VT|VA|WA|WV|WI|WY)\b')
RESIDE = re.compile(r'(?:residing|resident|located|based|living|reside|work)\s+(?:in|within|from)\s+(?:the\s+)?([A-Za-z ,]{3,60})', re.I)
VAGUE = re.compile(r'^\s*(in-office|hybrid|remote|on-?site|office|flexible)?\s*$', re.I)
NONUS = re.compile(r'london|uk\b|united kingdom|india|bengaluru|bangalore|hyderabad|pune|dublin|ireland|toronto|canada|vancouver|berlin|germany|paris|amsterdam|singapore|tokyo|sydney|australia|brazil|mexico|poland|warsaw|spain|madrid|tel aviv|israel|lisbon|portugal|emea|apac|latam|europe|japan|korea|seoul|philippines|argentina|colombia|costa rica|czech|romania|netherlands', re.I)

# skill: (regex, weight, how much Nirav has it 0..1)
SK = {
    'BigQuery': (r'bigquery', 10, 1), 'GCP': (r'\bgcp\b|google cloud', 8, 1), 'Airflow': (r'airflow|cloud composer', 8, 1),
    'SQL': (r'\bsql\b', 6, 1), 'Python': (r'python', 6, 1), 'Dataproc/Hadoop': (r'dataproc|hadoop|\bpig\b|hive|oozie', 4, 1),
    'Data quality': (r'data quality|anomal|observab|data validation|monitoring', 6, 1), 'ETL/ELT': (r'\betl\b|\belt\b|pipeline', 5, 1),
    'Cost optimization': (r'cost', 4, 1), 'Migration': (r'migrat|moderniz', 4, 1), 'Data modeling': (r'data model|dimensional|schema', 4, 1),
    'Analytics/BI': (r'analytics|looker|dashboard|metrics', 3, 1), 'ML data': (r'machine learning|\bml\b|feature', 3, 1),
    'Near real-time': (r'real[- ]time|streaming|intraday', 4, 0.5), 'GCS': (r'\bgcs\b|cloud storage', 2, 1),
    'Spark': (r'spark|pyspark', 5, 0.4), 'dbt': (r'\bdbt\b', 4, 0.3), 'Snowflake': (r'snowflake', 4, 0.2), 'Kafka': (r'kafka|pub/?sub|kinesis', 4, 0.2),
    'Databricks': (r'databricks|delta lake', 4, 0.1), 'Flink': (r'flink', 3, 0), 'AWS': (r'\baws\b|redshift|s3\b|glue|emr', 3, 0.2),
    'Scala/Java': (r'\bscala\b|\bjava\b', 3, 0.2), 'Go': (r'\bgolang\b|\bgo\b,', 2, 0), 'Terraform': (r'terraform', 2, 0.2), 'Dagster': (r'dagster', 2, 0.3),
}
strip = lambda s: re.sub(r'\s+', ' ', re.sub(r'<[^>]+>', ' ', html.unescape(s or '')))
SAL = re.compile('\\$\\s?(\\d{2,3}(?:,\\d{3})+|\\d{2,3}k)\\s*(?:-|–|—|to)\\s*\\$?\\s?(\\d{2,3}(?:,\\d{3})+|\\d{2,3}k)', re.I)

def score(j):
    loc = j.get('loc') or ''
    d = strip(j.get('desc', ''))
    if NONUS.search(loc) and not USPLACE.search(loc): return None
    if not (USPLACE.search(loc) or USSTATE.search(loc)): return None
    for m in RESIDE.finditer(d[:4000]):  # e.g. 'open to candidates residing in Canada'
        if NONUS.search(m.group(1)) and not USPLACE.search(m.group(1)): return None
    if SKIP_TITLE.search(j['title']): return None
    text = j['title'] + ' ' + d
    match, gap, tot, got = [], [], 0, 0
    for k, (rx, w, h) in SK.items():
        if re.search(rx, text, re.I):
            tot += w; got += w * h
            (match if h >= 0.5 else gap).append(k)
    if tot == 0: return None
    s = (0.55 * (got / tot) + 0.45 * min(1, got / 45)) * 100
    yrs = [int(x) for x in re.findall(r'(\d{1,2})\s*\+\s*years', d) if 1 <= int(x) <= 15]
    y = min(yrs) if yrs else None
    t = j['title']
    lvl = 'Staff+' if re.search(r'staff|principal|lead', t, re.I) else 'Senior' if re.search(r'senior|sr\.?\b|\biii\b|\biv\b', t, re.I) else 'Mid'
    s -= 25 if lvl == 'Staff+' else 5 if lvl == 'Senior' else 0
    s -= 15 if (y and y >= 8) else 6 if (y and y >= 6) else 0
    if re.search(r'bigquery', text, re.I): s += 6
    if re.search(r'data (engineer|infrastructure|platform)', t, re.I): s += 6
    sal = j.get('comp') or ''
    if not sal:
        m = SAL.search(d)
        if m: sal = f"${m.group(1)} – ${m.group(2)}"
    return dict(src=j.get('src', ''), company=NAMES.get(j['company'], j['company'] if j.get('src') else j['company'].capitalize()), title=t, loc=loc.replace('•', ';')[:90], url=j['url'],
                posted=(j.get('updated') or '')[:10], score=max(0, min(99, round(s))), level=lvl, years=y, salary=sal,
                remote=bool(re.search(r'remote', loc, re.I)) or bool(j.get('remote')), match=match, gaps=gap)

def main():
    with cf.ThreadPoolExecutor(24) as ex:
        raw = [x for lst in list(ex.map(gh, GH)) + list(ex.map(ash, ASH)) + list(ex.map(lev, LEV)) + list(ex.map(sr, SR)) for x in lst]
    with cf.ThreadPoolExecutor(6) as ex:  # fewer parallel Workday sites to avoid throttling
        raw += [x for lst in ex.map(wd, WD) for x in lst]
    if not raw:
        sys.exit("No jobs fetched; keeping the previous dashboard.")
    prev = set()
    if os.path.exists(P('jobs.json')):
        try: prev = {j['url'] for j in json.load(open(P('jobs.json')))}
        except Exception: pass
    seen, out = set(), []
    for o in sorted(filter(None, map(score, raw)), key=lambda x: -x['score']):
        k = (o['company'], o['title'], o['loc'])
        if k in seen or o['score'] < MIN_SCORE: continue
        seen.add(k)
        o['isNew'] = bool(prev) and o['url'] not in prev
        out.append(o)
    json.dump(out, open(P('jobs.json'), 'w'), separators=(',', ':'))
    label = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-5))).strftime('%b %d, %Y').replace(' 0', ' ')
    body = open(P('template.html')).read().replace('__DATA__', json.dumps(out, separators=(',', ':')).replace('</', '<\\/')).replace('__DATE__', label)
    page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
            '<style>:root{color-scheme:light}body{margin:0;font:14px/1.5 system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style></head><body>'
            + body + '</body></html>')
    open(P('index.html'), 'w').write(page)
    print(f"{len(raw)} postings scanned, {len(out)} roles kept, {sum(o['isNew'] for o in out)} new")

if __name__ == '__main__':
    main()
