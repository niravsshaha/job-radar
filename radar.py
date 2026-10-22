# Job Radar: pulls public job boards, scores roles against Nirav's resume,
# and writes index.html (the dashboard) + jobs.json (used to flag new roles).
# Usage: python3 radar.py
import json, re, html, os, sys, datetime, concurrent.futures as cf, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)

# Companies to search. Greenhouse board slugs and Ashby board slugs.
GH = """6sense abacus abnormalsecurity adyen affirm airbnb airship airtable akunacapital algolia alloy alpaca alphasights anaplan anthropic appian applovin apptronik asana attentive aura axios axon axonius backblaze betterment billcom bitgo bitwarden blend blinkhealth block blockchain bloomreach boxinc branch brave braze brex bugcrowd buildkite buildops builtin calendly calm cameo careem carta carvana chainguard checkr chime circleci clear clever cloudflare coalition cockroachlabs cognite coinbase collibra consensys contentful coreweave coupang coursera current dashlane databento databricks datadog dataiku deliveroo descript devrev dialpad discord doordashusa doximity dremio dropbox druva duolingo earnest earnin elastic epicgames epirus esri everlane everlaw expel extend faire fanduel fastly federato fetch fieldwire figma fireblocks fivetran flatironhealth fleetio flexport flowcode formlabs forter freenome fubotv gemini gitlab gocardless gofundme grafanalabs gravity greenhouse gusto hellofresh honeycomb honor hover hudl huntress imc imply instacart instawork insurify intercom invisible janestreet jfrog jumptrading justworks kaseya khanacademy kickstarter klaviyo knowbe4 komodohealth labelbox lattice launchdarkly liftoff lightmatter lithic logicgate lucidmotors lyft masterclass mavenclinic medium melio mercury mindbody mirakl mixpanel modernhealth moloco mongodb monzo mozilla nayya neo4j netlify netskope neuralink newrelic newsela nextdoor nextroll nooks nuro offerup okta onemedical oscar oura pagerduty peloton pendo pinterest planetlabs planetscale prenuvo prizepicks purestorage qualia qualtrics quince reddit redwoodmaterials relativity riotgames ripple robinhood roblox rocketlab roku rubrik salesloft samsara scaleai scopely seatgeek sendbird sigmacomputing simplisafe singlestore smartrent smartsheet snorkelai sofi splice squarespace stabilityai stackadapt stackblitz starburst stitchfix stripe sumologic sumup sweetgreen tailscale tanium taskrabbit taxbit tebra tide toast tripactions tripadvisor truebill twilio twitch udacity udemy underdog upgrade upstart vercel verkada via waymo webflow wikimedia wonderschool workato wrike xometry yext yotpo yugabyte zocdoc zscaler zuora""".split()
ASH = """1password abridge acorns airbyte airwallex alchemy amplitude andela anyscale appfolio applied aptible ashby astronomer attio benchling benevity brightwheel brigit bubble buildops cambly cerebras character circle citizen classdojo clearco clickhouse clickup close clubhouse cognition cohere collective commure conductor confluent crusoe cursor dandy decagon deepgram delinea dispatch docker drata dune eightsleep elevenlabs envoy expensify extend flock glide graphite hackerone handshake harvey headway hex hightouch hopper incident indigo influxdata insitro iterable jobber kayak kin lemonade level linear mapbox materialize maven mercor merge modal montecarlodata motherduck multiverse mural mutiny mux neon nerdwallet nooks notion nubank numeric nuna nylas onebrief openai orb orca outschool overjet owner parafin patreon paxos perplexity persona photoroom pinecone plaid playground poshmark posthog prefect primer qumulo quora radiant railway ramp recharge redis render replit resend rho rula runway sardine secureframe semgrep sentilink sentry shift sierra sift skydio slope snapdocs snowflake snyk sonder sprig strava substack suno supabase synthesia tabs tekion temporal tennr thumbtack titan tracksuit unit upside vanta vise vivid warp watershed wealthsimple weave whoop writer xero zapier zip""".split()
LEV = """activecampaign aircall anchorage angellist arcadia basis binance captivateiq emburse everbridge goodleap gopuff houzz jumpcloud linkedin metabase olo outreach palantir peerspace pipedrive ro rover spotify tala toptal veeva voltus wealthfront zeta zoox""".split()
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
Visa|visa|5|Visa
Chevron|chevron|5|jobs
3M|3m|1|Search
Northrop Grumman|ngc|1|Northrop_Grumman_External_Site
RTX|globalhr|5|REC_RTX_Ext_Gateway
GE Aerospace|geaerospace|5|GE_ExternalSite
Caterpillar|cat|5|CaterpillarCareers
Centene|centene|5|Centene_External
Merck|msd|5|SearchJobs
Bristol Myers Squibb|bristolmyerssquibb|5|BMS
Moderna|modernatx|1|M_tx
Amgen|amgen|1|Careers
Gilead|gilead|1|gileadcareers
Regeneron|regeneron|1|Careers
Illumina|illumina|1|illumina-careers
Applied Materials|amat|1|External
KLA|kla|1|Search
Marvell|marvell|1|MarvellCareers
US Bank|usbank|1|US_Bank_Careers
PNC|pnc|5|External
Truist|truist|1|Careers
Fannie Mae|fanniemae|1|FannieMaeCareers
Freddie Mac|freddiemac|5|External
State Street|statestreet|1|Global
Northern Trust|ntrs|1|northerntrust
T. Rowe Price|troweprice|5|TRowePrice
BlackRock|blackrock|1|BlackRock_Professional
Travelers|travelers|5|External
Nationwide|nationwide|1|Nationwide_Career
Prudential|pru|5|Careers
AT&T|att|1|ATTGeneral
McKesson|mckesson|3|External_Careers
Cardinal Health|cardinalhealth|1|EXT
Chewy|chewy|5|External
Citi|citi|5|2
Mondelez|mdlz|3|External
Coca-Cola|coke|1|coca-cola-careers
Procter & Gamble|pg|5|1000
Johnson Controls|jci|5|JCI
General Dynamics|gdit|5|External_Career_Site
Booz Allen|bah|1|BAH_Jobs
Leidos|leidos|5|External
CACI|caci|1|External
Fiserv|fiserv|5|EXT
FIS|fis|5|SearchJobs
Global Payments|tsys|1|TSYS
Equinix|equinix|1|External
UPS|hcmportal|5|Search""".splitlines()]
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

# Jooble collects listings from many boards (LinkedIn, Indeed, ZipRecruiter, Glassdoor, staffing firms).
# It needs a free key stored as the GitHub Actions secret JOOBLE_KEY; without it this source is skipped.
AGG_TERMS = ["data engineer", "analytics engineer", "data platform engineer", "big data engineer", "etl developer", "backend engineer python"]
CORP = re.compile(r'[,.]?\s*\b(inc|llc|ltd|corp|corporation|co|company|incorporated)\b\.?$', re.I)

def jooble():
    key = os.environ.get("JOOBLE_KEY")
    if not key: return []
    out = []
    for term in AGG_TERMS:
        for page in range(1, 4):
            d = post(f"https://jooble.org/api/{key}", {"keywords": term, "location": "United States", "page": str(page)}) or {}
            js = d.get("jobs") or []
            for r in js:
                t = html.unescape(r.get("title", ""))
                if not TITLE.search(t) or EXCL.search(t): continue
                loc = r.get("location") or "United States"
                if not (USPLACE.search(loc) or USSTATE.search(loc)): loc += ", United States"
                out.append(dict(company=CORP.sub("", html.unescape(r.get("company") or "")).strip() or "Unknown", title=t, loc=loc,
                                url=r.get("link", ""), updated=r.get("updated", ""), desc=r.get("snippet", ""), comp=r.get("salary") or "",
                                remote=bool(re.search(r"remote", t + " " + loc + " " + (r.get("type") or ""), re.I)), src="jooble"))
            if len(js) < 20: break
    return out

# Big tech career sites (public JSON behind their own search pages).
BIG_TERMS = ["data engineer", "analytics engineer", "data platform", "software engineer data", "big data"]

def amazon():
    out, seen = [], set()
    for term in BIG_TERMS:
        for off in range(0, 300, 100):
            q = urllib.parse.urlencode({"base_query": term, "country": "USA", "result_limit": 100, "offset": off, "sort": "recent"})
            js = (get(f"https://www.amazon.jobs/en/search.json?{q}") or {}).get("jobs") or []
            for r in js:
                t = r.get("title", "")
                if r.get("id") in seen or not TITLE.search(t) or EXCL.search(t): continue
                seen.add(r.get("id"))
                try: up = datetime.datetime.strptime(r.get("posted_date", ""), "%B %d, %Y").strftime("%Y-%m-%d")
                except Exception: up = ""
                out.append(dict(company="Amazon", title=t, loc=r.get("normalized_location") or r.get("location", ""), url="https://www.amazon.jobs" + r.get("job_path", ""),
                                updated=up, desc=" ".join(r.get(k) or "" for k in ("description", "basic_qualifications", "preferred_qualifications")),
                                comp="", remote=False, src="big"))
            if len(js) < 100: break
    return out

def microsoft():
    base, out, ids = "https://apply.careers.microsoft.com/api/pcsx", [], {}
    for term in BIG_TERMS:
        for start in range(0, 100, 10):
            q = urllib.parse.urlencode({"domain": "microsoft.com", "query": term, "location": "United States", "start": start})
            ps = ((retry(get, f"{base}/search?{q}") or {}).get("data") or {}).get("positions") or []
            __import__("time").sleep(0.5)  # Microsoft rate-limits fast clients
            for p in ps:
                t = p.get("name", "")
                if TITLE.search(t) and not EXCL.search(t) and any(x == "US" or x.endswith(", US") for x in (p.get("standardizedLocations") or [])): ids.setdefault(p["id"], p)
            if len(ps) < 10: break
    for pid, p in list(ids.items())[:100]:
        __import__("time").sleep(0.5)
        d = (retry(get, f"{base}/position_details?" + urllib.parse.urlencode({"position_id": pid, "domain": "microsoft.com", "hl": "en"})) or {}).get("data") or {}
        locs = "; ".join(p.get("locations") or [])
        out.append(dict(company="Microsoft", title=p.get("name", ""), loc=locs if USPLACE.search(locs) else (locs + ", United States").strip(", "),
                        url=d.get("publicUrl") or "https://apply.careers.microsoft.com" + p.get("positionUrl", ""),
                        updated=datetime.datetime.fromtimestamp(int(p.get("postedTs") or 0), datetime.timezone.utc).strftime("%Y-%m-%d") if p.get("postedTs") else "",
                        desc=d.get("jobDescription") or "", comp="", remote=(p.get("workLocationOption") == "remote"), src="big"))
    return out

def google():
    out, seen = [], set()
    for term in BIG_TERMS:
        for page in range(1, 6):
            q = urllib.parse.urlencode({"q": term, "location": "United States", "page": page})
            try:
                s = urllib.request.urlopen(urllib.request.Request(f"https://www.google.com/about/careers/applications/jobs/results/?{q}", headers=UA), timeout=25).read().decode("utf-8", "replace")
                i = s.index("AF_initDataCallback({key: 'ds:1'"); a = s.index("data:", i) + 5; b = s.index(", sideChannel", a)
                jobs = (json.loads(s[a:b]) or [[]])[0] or []
            except Exception:
                break
            for x in jobs:
                t = x[1] or ""
                if x[0] in seen or not TITLE.search(t) or EXCL.search(t): continue
                seen.add(x[0])
                locs = [l[0] for l in (x[9] or []) if l and l[0]]
                if not any(l[-1] == "US" for l in (x[9] or []) if l): continue
                txt = lambda v: (v[1] if isinstance(v, list) and len(v) > 1 and v[1] else "")
                out.append(dict(company="Google", title=t, loc="; ".join(locs), url=f"https://www.google.com/about/careers/applications/jobs/results/{x[0]}",
                                updated=datetime.datetime.fromtimestamp((x[12] or [0])[0], datetime.timezone.utc).strftime("%Y-%m-%d") if x[12] else "",
                                desc=" ".join(txt(x[k]) for k in (3, 4, 10, 19)), comp="", remote=bool(re.search(r"remote", t, re.I)), src="big"))
            if len(jobs) < 20: break
    return out

def apple():
    out, seen = [], set()
    try:
        r = urllib.request.urlopen(urllib.request.Request("https://jobs.apple.com/api/v1/CSRFToken", headers=UA), timeout=25)
        tok, ck = r.headers.get("x-apple-csrf-token", ""), "; ".join(c.split(";")[0] for c in r.headers.get_all("Set-Cookie") or [])
    except Exception:
        return out
    hdr = {**UA, "x-apple-csrf-token": tok, "Cookie": ck, "Content-Type": "application/json", "Origin": "https://jobs.apple.com", "Referer": "https://jobs.apple.com/en-us/search"}
    for term in BIG_TERMS:
        for page in range(1, 6):
            body = {"query": term, "filters": {"postingpostLocation": ["postLocation-USA"]}, "page": page, "locale": "en-us", "sort": "relevance",
                    "format": {"longDate": "MMMM D, YYYY", "mediumDate": "MMM D, YYYY"}}
            try:
                res = json.load(urllib.request.urlopen(urllib.request.Request("https://jobs.apple.com/api/v1/search", data=json.dumps(body).encode(), headers=hdr), timeout=25))["res"]
            except Exception:
                break
            rs = res.get("searchResults") or []
            for x in rs:
                t = x.get("postingTitle", "")
                locs = x.get("locations") or []
                if x.get("id") in seen or not TITLE.search(t) or EXCL.search(t) or not any(l.get("countryID") == "iso-country-USA" or l.get("countryName") == "United States" for l in locs): continue
                seen.add(x.get("id"))
                out.append(dict(company="Apple", title=t, loc="; ".join(filter(None, (", ".join(filter(None, (l.get("city"), l.get("stateProvince")))) or l.get("name", "") for l in locs))) + ", United States",
                                url=f"https://jobs.apple.com/en-us/details/{x.get('positionId')}/{x.get('transformedPostingTitle', '')}",
                                updated=(x.get("postDateInGMT") or "")[:10], desc=x.get("jobSummary", ""), comp="", remote=bool(x.get("homeOffice")), src="big"))
            if len(rs) < 20: break
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
# Years of experience a posting asks for: every "5+ years", "3-5 years", "at least 4 years", "5 years of ... experience";
# the highest one is the real bar (e.g. "7+ years overall, 3+ years with Spark" -> 7).
YRQ = re.compile('|'.join('(?:%s)' % p for p in (
    r'(\d{1,2})\s*(?:\+|plus|or more)\s*(?:years?|yrs)', r'(\d{1,2})\s*(?:-|–|to)\s*\d{1,2}\s*(?:years?|yrs)',
    r'(?:at least|minimum(?: of)?|min\.)\s*(\d{1,2})\s*(?:years?|yrs)', r'(\d{1,2})\s*(?:years?|yrs)(?:\s+of)?(?:\s+[\w/&.,-]+){0,5}?\s+experience')), re.I)
def years_req(d):
    v = [int(g) for m in YRQ.finditer(d) for g in m.groups() if g and 1 <= int(g) <= 15]
    return max(v) if v else None
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
                posted=(j.get('updated') or '')[:10], score=max(0, min(99, round(s))), level=lvl, years=years_req(d), salary=sal,
                remote=bool(re.search(r'remote', loc, re.I)) or bool(j.get('remote')), match=match, gaps=gap)

def main():
    with cf.ThreadPoolExecutor(24) as ex:
        raw = [x for lst in list(ex.map(gh, GH)) + list(ex.map(ash, ASH)) + list(ex.map(lev, LEV)) + list(ex.map(sr, SR)) for x in lst]
    with cf.ThreadPoolExecutor(8) as ex:  # fewer parallel Workday sites to avoid throttling
        raw += [x for lst in ex.map(wd, WD) for x in lst]
    # Aggregator listings often repeat a company-board posting; keep the company-board copy.
    nk = lambda c, t: re.sub(r"[^a-z0-9]", "", (c + "|" + t).lower())
    direct = {nk(NAMES.get(j["company"], j["company"]), j["title"]) for j in raw}
    for f in (amazon, microsoft, google, apple):
        try: raw += f()
        except Exception as e: print(f.__name__, "failed:", e)
    for j in jooble():
        k = nk(j["company"], j["title"])
        if k not in direct: direct.add(k); raw.append(j)
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
