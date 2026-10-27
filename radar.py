# Job Radar: pulls public job boards once, scores roles against both of Nirav's resumes, and writes two dashboards:
#   index.html + jobs.json          data engineering roles (Data Engineer resume)
#   swe.html   + jobs_swe.json      software / systems engineering roles (Software Engineer resume)
# Usage: python3 radar.py
import json, re, html, os, sys, datetime, concurrent.futures as cf, urllib.request, urllib.parse

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)

# Companies to search. Greenhouse board slugs and Ashby board slugs.
GH = """6sense abacus abnormalsecurity adyen affirm airbnb airship airtable akunacapital algolia alloy alpaca alphasights anaplan anthropic appian applovin apptronik asana attentive aura axios axon axonius backblaze betterment billcom bitgo bitwarden blend blinkhealth block blockchain bloomreach boxinc branch brave braze brex bugcrowd buildkite buildops builtin calendly calm cameo careem carta carvana chainguard checkr chime circleci clear clever cloudflare coalition cockroachlabs cognite coinbase collibra consensys contentful coreweave coupang coursera current dashlane databento databricks datadog dataiku deliveroo descript devrev dialpad discord doordashusa doximity dremio dropbox druva duolingo earnest earnin elastic epicgames epirus esri everlane everlaw expel extend faire fanduel fastly federato fetch fieldwire figma fireblocks fivetran flatironhealth fleetio flexport flowcode formlabs forter freenome fubotv gemini gitlab gocardless gofundme grafanalabs gravity greenhouse gusto hellofresh honeycomb honor hootsuite hover hudl huntress imc imply instacart instawork insurify intercom invisible janestreet jfrog jumptrading justworks kaseya khanacademy kickstarter klaviyo knowbe4 komodohealth labelbox lattice launchdarkly liftoff lightmatter lithic logicgate lucidmotors lyft masterclass mavenclinic medium melio mercury mindbody mirakl mixpanel modernhealth moloco mongodb monzo mozilla nayya neo4j netlify netskope neuralink newrelic newsela nextdoor nextroll nooks nuro offerup okta onemedical oscar oura pagerduty peloton pendo pinterest planetlabs planetscale prenuvo prizepicks purestorage qualia qualtrics quince reddit redwoodmaterials relativity riotgames ripple robinhood roblox rocketlab roku rubrik salesloft samsara scaleai scopely seatgeek sendbird sigmacomputing simplisafe singlestore smartrent smartsheet snorkelai sofi splice sproutsocial squarespace stabilityai stackadapt stackblitz starburst stitchfix stripe sumologic sumup sweetgreen tailscale tanium taskrabbit taxbit tebra tide toast tripactions tripadvisor truebill twilio twitch udacity udemy underdog upgrade upstart vercel verkada via waymo webflow wikimedia wonderschool workato wrike xometry yext yotpo yugabyte zocdoc zoominfo zscaler zuora""".split()
ASH = """1password abridge acorns airbyte airwallex alchemy amplitude andela anyscale appfolio applied aptible ashby astronomer attio benchling benevity brightwheel brigit bubble buildops cambly cerebras character circle citizen classdojo clearco clickhouse clickup close clubhouse cognition cohere collective commure conductor confluent crusoe cursor dandy decagon deepgram delinea dispatch docebo docker drata dune eightsleep elevenlabs envoy expensify extend flock glide graphite hackerone handshake harvey headway hex hightouch hopper illumio incident indigo influxdata insitro iterable jobber kayak kin lemonade level linear mapbox materialize maven mercor merge midjourney modal montecarlodata motherduck multiverse mural mutiny mux neon nerdwallet nooks notion nubank numeric nuna nylas onebrief openai orb orca outschool overjet owner oyster parafin patreon paxos perplexity persona photoroom pinecone plaid playground poshmark posthog prefect primer qumulo quora radiant railway ramp recharge redis render replit resend rho rula runway sardine secureframe semgrep sentilink sentry shift sierra sift skydio slope snapdocs snowflake snyk sonder sprig strava substack suno supabase surveymonkey synthesia tabs tekion temporal tennr thumbtack titan tracksuit unit upside vanta vise vivid warp watershed wealthsimple weave whoop writer xero zapier zip""".split()
LEV = """activecampaign aircall anchorage angellist arcadia basis bazaarvoice binance captivateiq coupa emburse everbridge goodleap gopuff houzz jumpcloud linkedin metabase olo outreach palantir peerspace pipedrive ro rover sonatype spotify tala toptal veeva voltus wealthfront zeta zoox""".split()
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
UPS|hcmportal|5|Search
Cohesity|cohesity|5|Cohesity_Careers
Sprinklr|sprinklr|1|careers
ServiceTitan|servicetitan|1|ServiceTitan
Zoom|zoom|5|Zoom
Synchrony|synchronyfinancial|5|careers
Ameriprise|ameriprise|5|Ameriprise
Vanguard|vanguard|5|vanguard_external
Raymond James|raymondjames|1|RaymondJamesCareers
Hartford|thehartford|5|Careers_External
Stryker|stryker|1|StrykerCareers
Thermo Fisher|thermofisher|5|ThermoFisherCareers
Danaher|danaher|1|DanaherJobs
Novartis|novartis|3|Novartis_Careers
GSK|gsk|5|GSKCareers
AstraZeneca|astrazeneca|3|Careers
Sanofi|sanofi|3|SanofiCareers
Expedia|expedia|108|search
Samsung|sec|3|Samsung_Careers""".splitlines()]
SR = """ServiceNow BoschGroup Canva Experian WesternDigital Freshworks AbbVie""".split()  # SmartRecruiters company ids
WD_TERMS = ["data engineer", "software engineer", "analytics engineer", "data platform"]

UA = {'User-Agent': 'Mozilla/5.0'}
# Titles for each dashboard. The job boards are read once with both lists combined (TITLE).
TITLE_DE = re.compile(r'data|analytics|etl|elt|pipeline|warehouse|lakehouse|business intelligence|\bbi\b|ml platform|ml infra|machine learning (platform|infra)', re.I)
TITLE_SWE = re.compile(r'software (?:engineer|developer|development engineer)|\bswe\b|\bsde\b|backend|back-end|platform engineer|infrastructure engineer|systems software|distributed systems|site reliability|\bsre\b|developer', re.I)
DATA_FIRST = re.compile(r'data engineer|analytics engineer|\betl\b|business intelligence|\bbi\b|data analyst|data warehouse|analytics', re.I)  # these stay on the data page only
TITLE = re.compile(TITLE_DE.pattern + '|' + TITLE_SWE.pattern, re.I)
EXCL = re.compile(r'manager|director|head of|vp|principal|intern|scientist|(?<!data )(?<!intelligence )(?<!bi )(?<!analytics )analyst|sales|account|solutions|customer|support|recruit|counsel|marketing|product manager|designer', re.I)
SKIP_TITLE = re.compile(r'product management|network|machine learning engineer|research engineer|field engineer|security|hardware|full-stack|frontend|embedded|firmware|flight software|avionics|datacenter|data center|consultant', re.I)
# Software page: networking and systems software are in; front-end, mobile and hardware-only roles are out.
SKIP_SWE = re.compile(r'product management|machine learning engineer|research engineer|field engineer|security|hardware|full[- ]?stack|front[- ]?end|\bios\b|android|mobile|embedded|firmware|flight software|avionics|datacenter|data center|consultant|salesforce|servicenow|\bsap\b|game|graphics', re.I)
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
BIG_TERMS = ["data engineer", "analytics engineer", "data platform", "software engineer data", "big data", "data analyst", "business intelligence",
             "software engineer", "backend engineer", "distributed systems"]

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
    for pid, p in list(ids.items())[:160]:
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

# Oracle Recruiting Cloud sites: name | host | site number
ORA = [("JPMorgan Chase", "jpmc.fa.oraclecloud.com", "CX_1001"), ("Oracle", "eeho.fa.us2.oraclecloud.com", "CX_45001"),
       ("American Express", "egug.fa.us2.oraclecloud.com", "CX_1"), ("Honeywell", "ibqbjb.fa.ocs.oraclecloud.com", "CX_1"),
       ("Kroger", "eluq.fa.us2.oraclecloud.com", "CX_2001"), ("Dell", "enterpriseplatform.dell.com", "CX_1")]

def oracle_hcm(entry):
    name, host, site = entry
    api, out, reqs = f"https://{host}/hcmRestApi/resources/latest", [], {}
    for term in BIG_TERMS:
        for off in range(0, 200, 50):
            q = f"onlyData=true&expand=requisitionList&finder=findReqs;siteNumber={site},keyword={urllib.parse.quote(term)},limit=50,offset={off}"
            items = (get(f"{api}/recruitingCEJobRequisitions?{q}") or {}).get("items") or [{}]
            rl = items[0].get("requisitionList") or []
            for r in rl:
                t = r.get("Title", "")
                if r.get("PrimaryLocationCountry") == "US" and TITLE.search(t) and not EXCL.search(t): reqs.setdefault(r["Id"], r)
            if len(rl) < 50: break
    for rid, r in list(reqs.items())[:120]:
        q = f'expand=all&onlyData=true&finder=ById;Id=%22{rid}%22,siteNumber={site}'
        d = ((get(f"{api}/recruitingCEJobRequisitionDetails?{q}") or {}).get("items") or [{}])[0]
        out.append(dict(company=name, title=r.get("Title", ""), loc=r.get("PrimaryLocation", "") or "United States",
                        url=f"https://{host}/hcmUI/CandidateExperience/en/sites/{site}/job/{rid}", updated=r.get("PostedDate", ""),
                        desc=" ".join(d.get(k) or "" for k in ("ExternalDescriptionStr", "ExternalResponsibilitiesStr", "ExternalQualificationsStr")) or r.get("ShortDescriptionStr", ""),
                        comp="", remote=bool(re.search(r"remote", r.get("WorkplaceType") or "", re.I)), src="big"))
    return out

def atlassian():
    out = []
    for r in get("https://www.atlassian.com/endpoint/careers/listings") or []:
        t, locs = r.get("title", ""), [l for l in (r.get("locations") or []) if re.search(r"united states|\bUSA\b", l, re.I)]
        if not locs or not TITLE.search(t) or EXCL.search(t): continue
        out.append(dict(company="Atlassian", title=t, loc="; ".join(locs), url=r.get("applyUrl", ""), updated=((r.get("portalJobPost") or {}).get("updatedDate") or "")[:10],
                        desc=" ".join(r.get(k) or "" for k in ("overview", "responsibilities", "qualifications")), comp="", remote=any("remote" in l.lower() for l in locs), src="big"))
    return out

def tiktok():
    out, seen = [], set()
    hdr = {**UA, "Content-Type": "application/json", "website-path": "tiktok"}
    for term in BIG_TERMS:
        for off in range(0, 300, 100):
            body = {"recruitment_id_list": [], "job_category_id_list": [], "subject_id_list": [], "location_code_list": [], "keyword": term, "limit": 100, "offset": off}
            try:
                d = json.load(urllib.request.urlopen(urllib.request.Request("https://api.lifeattiktok.com/api/v1/public/supplier/search/job/posts", data=json.dumps(body).encode(), headers=hdr), timeout=25))
            except Exception:
                break
            js = ((d or {}).get("data") or {}).get("job_post_list") or []
            for x in js:
                t, c, chain = x.get("title", ""), x.get("city_info") or {}, []
                n = c
                while n: chain.append(n.get("en_name") or ""); n = n.get("parent")
                if x.get("id") in seen or "United States of America" not in chain or not TITLE.search(t) or EXCL.search(t): continue
                seen.add(x.get("id"))
                out.append(dict(company="TikTok", title=t, loc=", ".join(chain[:2]) + ", United States", url=f"https://lifeattiktok.com/search/{x.get('id')}",
                                updated="", desc=(x.get("description") or "") + " " + (x.get("requirement") or ""), comp="", remote=False, src="big"))
            if len(js) < 100: break
    return out

def ibm():
    out, seen = [], set()
    for term in BIG_TERMS:
        body = {"appId": "careers", "scopes": ["careers2"], "query": {"bool": {"must": [{"simple_query_string": {"query": term, "fields": ["title^3", "description^2"]}}],
                "filter": [{"term": {"field_keyword_05": "United States"}}]}}, "size": 100, "lang": "zz", "localeSelector": {}, "sm": {"query": term, "lang": "zz"},
                "_source": ["title", "url", "description", "field_keyword_05", "field_keyword_19"]}
        d = post("https://www-api.ibm.com/search/api/v2", body) or {}
        for h in (d.get("hits") or {}).get("hits") or []:
            x = h.get("_source") or {}; t = x.get("title", "")
            if x.get("url") in seen or x.get("field_keyword_05") != "United States" or not TITLE.search(t) or EXCL.search(t): continue
            seen.add(x.get("url"))
            loc = x.get("field_keyword_19") or ""
            out.append(dict(company="IBM", title=t, loc=(loc.replace(", US", ", United States") if loc and loc != "Multiple Cities" else "Multiple Cities, United States"),
                            url=x.get("url", ""), updated="", desc=x.get("description", ""), comp="", remote=False, src="big"))
    return out

def netflix():
    base, out, ids = "https://explore.jobs.netflix.net/api/apply/v2/jobs", [], {}
    for term in BIG_TERMS:
        for start in range(0, 100, 10):
            q = urllib.parse.urlencode({"domain": "netflix.com", "query": term, "location": "United States", "start": start})
            ps = (retry(get, f"{base}?{q}") or {}).get("positions") or []
            __import__("time").sleep(0.3)  # Netflix throttles fast clients
            for p in ps:
                t = p.get("name", "")
                if TITLE.search(t) and not EXCL.search(t) and "United States" in (p.get("location") or ""): ids.setdefault(p["id"], p)
            if len(ps) < 10: break
    for pid, p in list(ids.items())[:80]:
        __import__("time").sleep(0.3)
        d = retry(get, f"{base}/{pid}?domain=netflix.com") or {}
        out.append(dict(company="Netflix", title=p.get("name", ""), loc="; ".join(p.get("locations") or [p.get("location", "")]),
                        url=p.get("canonicalPositionUrl") or f"https://explore.jobs.netflix.net/careers/job/{pid}",
                        updated=datetime.datetime.fromtimestamp(int(p.get("t_update") or 0), datetime.timezone.utc).strftime("%Y-%m-%d") if p.get("t_update") else "",
                        desc=d.get("job_description") or "", comp="", remote="remote" in (p.get("location") or "").lower(), src="big"))
    return out

def meta():
    """Meta's career site has no public feed, so read its search pages with a headless browser (allowed by its robots.txt)."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return []
    out, links = [], {}
    with sync_playwright() as pw:
        b = pw.chromium.launch()
        pg = b.new_context(user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0 Safari/537.36").new_page()
        for term in ["Data Engineer", "Software Engineer", "Analytics Engineer", "Data Infrastructure"]:
            for page in range(1, 9):
                try:
                    pg.goto("https://www.metacareers.com/jobsearch/?" + urllib.parse.urlencode({"q": term, "offices[0]": "North America", "page": page}), wait_until="networkidle", timeout=45000)
                    got = pg.eval_on_selector_all('a[href*="/job_details/"]', "as => as.map(a => [a.href, a.innerText])")
                except Exception:
                    break
                new = 0
                for h, txt in got:
                    h = h.split("?")[0]
                    if h in links: continue
                    links[h] = txt; new += 1
                if not new: break
        keep = []
        for h, txt in links.items():
            lines = [l.strip() for l in txt.split("\n") if l.strip() and l.strip() != "\u22c5"]
            t = lines[0] if lines else ""
            locs = [l for l in lines[1:] if USSTATE.search(l) or re.search(r"remote, us|united states", l, re.I)]
            if t and locs and TITLE.search(t) and not EXCL.search(t) and not (SKIP_TITLE.search(t) and SKIP_SWE.search(t)): keep.append((h, t, locs))
        for h, t, locs in keep[:80]:
            try:
                pg.goto(h, wait_until="networkidle", timeout=45000); body = pg.inner_text("body")
            except Exception:
                body = ""
            out.append(dict(company="Meta", title=t, loc="; ".join(locs), url=h, updated="", desc=body, comp="",
                            remote=any("remote" in l.lower() for l in locs), src="big"))
        b.close()
    return out

# Career sites on Jibe (their robots.txt allow it, with a 5 s crawl delay)
JIBE = [("AMD", "careers.amd.com"), ("Rivian", "careers.rivian.com"), ("Booking.com", "jobs.booking.com"), ("Costco", "careers.costco.com")]

def jibe(entry):
    name, host = entry
    out, seen, sleep = [], set(), __import__("time").sleep
    for term in BIG_TERMS:
        for page in range(1, 4):
            sleep(5)
            q = urllib.parse.urlencode({"keywords": term, "page": page, "sortBy": "relevance", "descending": "false", "internal": "false"})
            js = (get(f"https://{host}/api/jobs?{q}") or {}).get("jobs") or []
            for x in js:
                d = x.get("data") or {}
                t, rid = d.get("title", ""), d.get("req_id") or d.get("slug")
                if rid in seen or not TITLE.search(t) or EXCL.search(t): continue
                if (d.get("country_code") or "").upper() not in ("US", "USA") and "united states" not in (d.get("full_location") or "").lower(): continue
                seen.add(rid)
                out.append(dict(company=name, title=t, loc=(d.get("full_location") or d.get("location_name") or "") + ", United States",
                                url=d.get("apply_url") or f"https://{host}/careers-home/jobs/{rid}", updated=(d.get("posted_date") or d.get("create_date") or "")[:10],
                                desc=(d.get("description") or "") + " " + (d.get("qualifications") or "") + " " + (d.get("responsibilities") or ""),
                                comp="", remote=bool(re.search(r"remote", (d.get("location_type") or "") + (d.get("full_location") or ""), re.I)), src="big"))
            if len(js) < 10: break
    return out

# Career sites on Radancy: their robots.txt block the search pages but allow the sitemap and job pages,
# so list jobs from the sitemap and read each job page's structured JobPosting data.
RADANCY = [("Charles Schwab", "https://www.schwabjobs.com/sitemap.xml"), ("UnitedHealth Group", "https://careers.unitedhealthgroup.com/sitemap.xml"),
           ("Comcast", "https://jobs.comcast.com/sitemap.xml"), ("Intuit", "https://jobs.intuit.com/sitemap.xml"),
           ("Palo Alto Networks", "https://jobs.paloaltonetworks.com/en/sitemap.xml")]
SLUG = re.compile(r"/job/[^/]+/[^/]*(?:data|analytic|software|backend|back-end|etl|platform|intelligence)[^/]*/", re.I)
NONUS_SLUG = re.compile(r"/job/(?:bangalore|bengaluru|hyderabad|chennai|pune|noida|gurgaon|gurugram|mumbai|dublin|london|toronto|manila|makati|krakow|warsaw|singapore|sydney|tel-aviv|prague|costa-rica|heredia|mexico|guadalajara)", re.I)

def radancy(entry):
    name, sm = entry
    try:
        xml = urllib.request.urlopen(urllib.request.Request(sm, headers=UA), timeout=40).read().decode("utf-8", "replace")
    except Exception:
        return []
    urls = [u for u in re.findall(r"<loc>([^<]+)</loc>", xml) if SLUG.search(u) and not NONUS_SLUG.search(u)]
    out = []
    for u in urls[:90]:
        __import__("time").sleep(1)
        try:
            page = urllib.request.urlopen(urllib.request.Request(u, headers=UA), timeout=25).read().decode("utf-8", "replace")
        except Exception:
            continue
        for blob in re.findall(r'<script[^>]*application/ld\+json[^>]*>(.*?)</script>', page, re.S):
            try: d = json.loads(blob)
            except Exception: continue
            if not (isinstance(d, dict) and d.get("@type") == "JobPosting"): continue
            t = html.unescape(d.get("title", ""))
            places = d.get("jobLocation") or []
            places = places if isinstance(places, list) else [places]
            addr = [p.get("address") or {} for p in places if isinstance(p, dict)]
            if not any((a.get("addressCountry") or "").upper() in ("US", "USA", "UNITED STATES") for a in addr): break
            if not TITLE.search(t) or EXCL.search(t): break
            loc = "; ".join(", ".join(filter(None, (a.get("addressLocality"), a.get("addressRegion")))) for a in addr) + ", United States"
            out.append(dict(company=name, title=t, loc=loc, url=d.get("url") or u, updated=(d.get("datePosted") or "")[:10],
                            desc=html.unescape(d.get("description") or ""), comp="", remote=bool(re.search(r"remote", t + " " + loc, re.I)), src="big"))
            break
    return out

def toyota():
    out, seen = [], set()
    hdr = {**UA, "Content-Type": "application/json"}
    for term in BIG_TERMS:
        for start in range(0, 100, 50):
            body = {"lang": "en_us", "deviceType": "desktop", "country": "us", "pageName": "search-results", "ddoKey": "refineSearch", "sortBy": "", "subsearch": "",
                    "from": start, "jobs": True, "counts": True, "all_fields": ["category", "country", "state", "city"], "size": 50, "clearAll": False,
                    "jdsource": "facets", "isSliderEnable": False, "pageId": "page20", "siteType": "external", "keywords": term, "global": True, "selected_fields": {}, "locationData": {}}
            try:
                d = json.load(urllib.request.urlopen(urllib.request.Request("https://careers.toyota.com/widgets", data=json.dumps(body).encode(), headers=hdr), timeout=25))
            except Exception:
                break
            js = ((d.get("refineSearch") or {}).get("data") or {}).get("jobs") or []
            for x in js:
                t = x.get("title", "")
                if x.get("jobId") in seen or "United States" not in (x.get("country") or "") or not TITLE.search(t) or EXCL.search(t): continue
                seen.add(x.get("jobId"))
                out.append(dict(company="Toyota", title=t, loc=(x.get("cityState") or x.get("city") or "") + ", United States",
                                url=x.get("applyUrl") or f"https://careers.toyota.com/us/en/job/{x.get('jobId')}", updated=(x.get("postedDate") or "")[:10],
                                desc=(x.get("descriptionTeaser") or "") + " " + " ".join(x.get("ml_skills") or []), comp="", remote=False, src="big"))
            if len(js) < 50: break
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
# Software Engineer resume: (regex, weight, how much Nirav has it 0..1)
SK_SWE = {
    'Python': (r'python', 8, 1), 'C/C++': (r'\bc\+\+|\bc/c\+\+|\bc or c\+\+|\bc, c\+\+', 8, 0.7), 'Java': (r'\bjava\b', 4, 0.5), 'Go': (r'\bgolang\b|\bgo\b,|\bin go\b|\bgo\)', 5, 0),
    'Distributed systems': (r'distributed system|high[- ]throughput|large[- ]scale (?:distributed|systems|services)', 8, 1), 'Linux': (r'linux|unix', 5, 1), 'REST APIs': (r'\brest\b|restful|microservice', 3, 1),
    'System design': (r're-?architect|system design|design doc|architect(?:ed|ing)? (?:and|scalable|systems|services)', 3, 1), 'SQL': (r'\bsql\b', 4, 1), 'GCP': (r'\bgcp\b|google cloud', 5, 1), 'AWS': (r'\baws\b|\bec2\b|\bs3\b|lambda', 4, 0.3),
    'Azure': (r'azure', 2, 0.5), 'Kubernetes/Docker': (r'kubernetes|\bk8s\b|docker|container', 5, 0.8), 'CI/CD': (r'ci/cd|jenkins|github actions|continuous (integration|delivery)', 4, 0.8),
    'Terraform/IaC': (r'terraform|infrastructure as code', 2, 0.6), 'Streaming (Kafka/Pub/Sub)': (r'kafka|pub/?sub|kinesis|streaming|event[- ]driven', 5, 1),
    'Data processing (Spark/Beam)': (r'spark|apache beam|dataflow|hadoop', 3, 0.8), 'Airflow': (r'airflow', 2, 1), 'BigQuery': (r'bigquery', 3, 1),
    'Concurrency': (r'multi-?thread|concurren|parallel', 4, 0.8), 'TCP/IP networking': (r'\btcp\b|\budp\b|socket|ip networking|networking protocol', 4, 0.7),
    'Testing': (r'unit test|automated test|test automation|integration test|pytest|test infrastructure', 4, 0.8), 'Debugging': (r'debug|troubleshoot|root.cause', 4, 1),
    'Reliability/on-call': (r'on-?call|\bsla\b|incident response|high availability|site reliability', 3, 1), 'Monitoring': (r'monitoring|observab|alerting|telemetry', 3, 1),
    'Performance/cost': (r'performance|latency|scalab', 2, 1), 'Caching': (r'cach', 2, 0.8), 'AI agents/LLMs': (r'\bllm|agentic|ai[- ]agent|generative ai|\bgenai\b', 3, 0.8),
    'gRPC': (r'grpc|protobuf', 2, 0), 'Rust': (r'\brust\b', 2, 0), 'JavaScript/TypeScript': (r'javascript|typescript|react|node\.?js', 4, 0.3),
    'Layer 2/3 protocols': (r'layer ?2|layer ?3|\bbgp\b|ospf|vlan|vxlan|evpn|lacp|\bstp\b|mpls', 4, 0.1), 'Low-level hardware': (r'\bphys?\b|transceiver|optics|device driver|kernel|\bpcie\b|asic|fpga', 4, 0.1),
}
PROFILES = {
    'de': dict(name='Data Engineer', sat=45, title=TITLE_DE, notitle=None, skip=SKIP_TITLE, sk=SK, json='jobs.json', html='index.html',
               bonus=lambda t, text: (6 if re.search(r'bigquery', text, re.I) else 0) + (6 if re.search(r'data (engineer|infrastructure|platform)', t, re.I) else 0),
               blurb="US data engineering and data platform roles pulled from company job boards and ranked against your Data Engineer resume: GCP, BigQuery, Airflow, SQL, Python, data quality and pipeline migrations."),
    'swe': dict(name='Software Engineer', sat=70,  # software postings list more skills
                title=TITLE_SWE, notitle=DATA_FIRST, skip=SKIP_SWE, sk=SK_SWE, json='jobs_swe.json', html='swe.html',
                bonus=lambda t, text: 6 if re.search(r'software|backend|back-end|platform|infrastructure|systems|distributed', t, re.I) else 0,
                blurb="US software, backend, platform and systems engineering roles pulled from company job boards and ranked against your Software Engineer resume: Python, C++, distributed systems, Linux, TCP/IP, Kubernetes and cloud."),
}
# If resumes were uploaded from the dashboard ("Resumes" button -> resumes.json), score from them instead of the
# hand-set values above: a skill used in a bullet or project counts fully, one only under Technical Skills counts 0.6.
def from_resume(sk, entry):
    body, skills = entry.get('body', ''), entry.get('skills', '')
    return {k: (rx, w, 1 if re.search(rx, body, re.I) else 0.6 if re.search(rx, skills, re.I) else 0) for k, (rx, w, h) in sk.items()}
try:
    RESUMES = json.load(open(P('resumes.json')))
    for _k, _p in PROFILES.items():
        if (RESUMES.get(_k) or {}).get('body'): _p['sk'] = from_resume(_p['sk'], RESUMES[_k])
except (OSError, ValueError):
    pass
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

# Roles you can't take: they need a US security clearance, or they won't sponsor a work visa.
CLEARANCE = re.compile(r"security clearance|secret clearance|top secret|\bts\s*/\s*sci\b|\bsci\b eligib|active clearance|clearance (?:is )?required|"
                       r"(?:obtain|hold|maintain|possess)(?: and maintain)? (?:a |an )?(?:active |current )?(?:us |u\.s\. )?(?:government |dod |federal )?"
                       r"(?:security )?clearance|public trust|polygraph|dod secret|clearance eligib|(?:possess|obtain)\s*:\s*(?:secret|top secret|ts\b)", re.I)
NO_SPONSOR = re.compile(r"(?:unable|not able|cannot|can ?not|can't|will not|won't|do not|does not|don't|doesn't|not)(?: be)?(?: able)? to (?:currently )?"
                        r"(?:provide|offer|support|consider)? ?(?:any )?(?:visa |immigration |employment |h-?1b )?sponsor|"
                        r"(?:will not|won't|do not|does not|don't|doesn't|cannot|can't|unable to|not) (?:currently )?(?:provide |offer )?(?:visa |immigration |employment |h-?1b )?sponsor|"
                        r"without (?:the )?(?:need for |requiring |requirement of )?(?:current or future |now or in the future |future )?(?:visa |immigration |employment |employer )?sponsorship|"
                        r"no (?:visa |immigration |h-?1b )?sponsorship|sponsorship (?:is |will )?not (?:be )?(?:available|provided|offered|considered)|"
                        r"not (?:eligible|available) for (?:visa |immigration )?sponsorship|"
                        r"must be (?:a )?(?:u\.?s\.? |us |united states )citizen|(?:u\.?s\.?|us|united states) citizenship (?:is )?required|requires? (?:u\.?s\.?|us) citizenship|"
                        r"green card holders? only|citizens? (?:or green card holders? )?only", re.I)
NEGATED = re.compile(r"(?:\bno\b|\bnot\b|n't|without)[^.;]{0,25}$", re.I)

def blocked(title, d):
    """Return 'clearance' / 'sponsorship' when a posting rules you out, else ''."""
    text = title + " " + d
    for kind, rx in (("clearance", CLEARANCE), ("sponsorship", NO_SPONSOR)):
        for m in rx.finditer(text):
            before, after = text[max(0, m.start() - 40):m.start()], text[m.end():m.end() + 40]
            if kind == "clearance" and NEGATED.search(before): continue           # "no security clearance required"
            if re.match(r"[\s:/\w-]{0,25}?\b(?:none|not required|n/a)\b", after, re.I): continue  # "Clearance ... Required: None"
            if re.match(r"\s*(?:protection act|for an export|for export)", after, re.I): continue   # legal boilerplate
            return kind
    return ""

def score(j, prof=PROFILES['de']):
    if not prof['title'].search(j['title']) or (prof['notitle'] and prof['notitle'].search(j['title'])): return None
    loc = j.get('loc') or ''
    d = strip(j.get('desc', ''))
    if NONUS.search(loc) and not USPLACE.search(loc): return None
    if not (USPLACE.search(loc) or USSTATE.search(loc)): return None
    for m in RESIDE.finditer(d[:4000]):  # e.g. 'open to candidates residing in Canada'
        if NONUS.search(m.group(1)) and not USPLACE.search(m.group(1)): return None
    if prof['skip'].search(j['title']): return None
    if blocked(j['title'], d): return None
    text = j['title'] + ' ' + d
    match, gap, tot, got = [], [], 0, 0
    for k, (rx, w, h) in prof['sk'].items():
        if re.search(rx, text, re.I):
            tot += w; got += w * h
            (match if h >= 0.5 else gap).append(k)
    if tot == 0: return None
    s = (0.55 * (got / tot) + 0.45 * min(1, got / prof['sat'])) * 100
    yrs = [int(x) for x in re.findall(r'(\d{1,2})\s*\+\s*years', d) if 1 <= int(x) <= 15]
    y = min(yrs) if yrs else None
    t = j['title']
    lvl = 'Staff+' if re.search(r'staff|principal|lead', t, re.I) else 'Senior' if re.search(r'senior|sr\.?\b|\biii\b|\biv\b', t, re.I) else 'Mid'
    s -= 25 if lvl == 'Staff+' else 5 if lvl == 'Senior' else 0
    s -= 15 if (y and y >= 8) else 6 if (y and y >= 6) else 0
    s += prof['bonus'](t, text)
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
    with cf.ThreadPoolExecutor(9) as ex:  # slow sites with crawl delays, in parallel
        raw += [x for lst in ex.map(jibe, JIBE) for x in lst] + [x for lst in ex.map(radancy, RADANCY) for x in lst]
    for f in (amazon, microsoft, google, apple, netflix, meta, atlassian, tiktok, ibm) + tuple((lambda e=e: oracle_hcm(e)) for e in ORA) + (toyota,):
        try: raw += f()
        except Exception as e: print(f.__name__, "failed:", e)
    for j in jooble():
        k = nk(j["company"], j["title"])
        if k not in direct: direct.add(k); raw.append(j)
    if not raw:
        sys.exit("No jobs fetched; keeping the previous dashboard.")
    label = datetime.datetime.now(datetime.timezone(datetime.timedelta(hours=-5))).strftime('%b %d, %Y').replace(' 0', ' ')
    tpl = open(P('template.html')).read()
    for key, prof in PROFILES.items():
        prev = set()
        if os.path.exists(P(prof['json'])):
            try: prev = {j['url'] for j in json.load(open(P(prof['json'])))}
            except Exception: pass
        seen, out = set(), []
        for o in sorted(filter(None, (score(j, prof) for j in raw)), key=lambda x: -x['score']):
            k = (o['company'], o['title'], o['loc'])
            if k in seen or o['score'] < MIN_SCORE: continue
            seen.add(k)
            o['isNew'] = bool(prev) and o['url'] not in prev
            out.append(o)
        if not out:
            print(prof['name'], "page: no roles matched; keeping the previous page."); continue
        json.dump(out, open(P(prof['json']), 'w'), separators=(',', ':'))
        other = PROFILES['swe' if key == 'de' else 'de']
        nav = ('<nav class="pages" style="display:flex;gap:6px;margin:6px 0 4px;font-size:13px">' +
               ''.join('<a href="%s" style="padding:4px 10px;border-radius:999px;text-decoration:none;%s">%s roles</a>' % (
                   p['html'] if p['html'] != 'index.html' else './', 'background:var(--accent);color:var(--surface);font-weight:600' if p is prof else 'border:1px solid var(--line);color:var(--fg)', p['name'])
                   for p in PROFILES.values()) + '</nav>')
        body = (tpl.replace('__DATA__', json.dumps(out, separators=(',', ':')).replace('</', '<\\/')).replace('__DATE__', label)
                .replace("<title>Nirav's Job Radar</title>", "<title>Nirav's Job Radar · %s</title>" % prof['name'])
                .replace("<h1>Nirav's Job Radar</h1>", "<h1>Nirav's Job Radar</h1>" + nav))
        body = re.sub(r'(<h1>.*?</nav>\s*<p>)[^<]*(</p>)', lambda m: m.group(1) + prof['blurb'] + m.group(2), body, count=1, flags=re.S)
        page = ('<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">'
                '<style>:root{color-scheme:light}body{margin:0;font:14px/1.5 system-ui,sans-serif}img{max-width:100%}[hidden]{display:none!important}</style></head><body>'
                + ('<script>window.PROFILE = "%s";</script>' % key) + body + '</body></html>')
        open(P(prof['html']), 'w').write(page)
        print(f"{prof['name']} page: {len(raw)} postings scanned, {len(out)} roles kept, {sum(o['isNew'] for o in out)} new")

if __name__ == '__main__':
    main()
