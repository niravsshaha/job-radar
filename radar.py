# Job Radar: pulls public job boards, scores roles against Nirav's resume,
# and writes index.html (the dashboard) + jobs.json (used to flag new roles).
# Usage: python3 radar.py
import json, re, html, os, sys, datetime, concurrent.futures as cf, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
P = lambda f: os.path.join(HERE, f)

# Companies to search. Greenhouse board slugs and Ashby board slugs.
GH = """figma databricks stripe airbnb dropbox pinterest reddit discord robinhood coinbase instacart lyft doordashusa gitlab datadog cloudflare mongodb elastic twilio okta samsara brex affirm chime gusto asana airtable squarespace roblox duolingo fivetran starburst anthropic scaleai faire nextdoor vercel webflow mercury block toast zscaler yext carta flexport checkr sofi sigmacomputing monzo cockroachlabs singlestore dagsterlabs pagerduty newrelic launchdarkly mixpanel braze iterable lattice oscar calm peloton tripadvisor waymo nuro gemini ripple prizepicks""".split()
ASH = """notion ramp openai linear plaid confluent snowflake vanta deel cohere perplexity replit supabase posthog sentry modal anyscale harvey runway character pinecone watershed""".split()

UA = {'User-Agent': 'Mozilla/5.0'}
TITLE = re.compile(r'data (engineer|infrastructure|platform)|analytics engineer|(engineer|swe).{0,25}data|data.{0,20}(pipeline|warehouse)|big data|etl', re.I)
EXCL = re.compile(r'manager|director|head of|vp|principal|intern|scientist|analyst|sales|account|solutions|customer|support|recruit|counsel|marketing|product manager|designer', re.I)
SKIP_TITLE = re.compile(r'product management|network|machine learning engineer|research engineer|field engineer|security|hardware|full-stack|frontend', re.I)
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
    return dict(company=NAMES.get(j['company'], j['company'].capitalize()), title=t, loc=loc.replace('•', ';')[:90], url=j['url'],
                posted=(j.get('updated') or '')[:10], score=max(0, min(99, round(s))), level=lvl, years=y, salary=sal,
                remote=bool(re.search(r'remote', loc, re.I)) or bool(j.get('remote')), match=match, gaps=gap)

def main():
    with cf.ThreadPoolExecutor(24) as ex:
        raw = [x for lst in list(ex.map(gh, GH)) + list(ex.map(ash, ASH)) for x in lst]
    if not raw:
        sys.exit("No jobs fetched; keeping the previous dashboard.")
    prev = set()
    if os.path.exists(P('jobs.json')):
        try: prev = {j['url'] for j in json.load(open(P('jobs.json')))}
        except Exception: pass
    seen, out = set(), []
    for o in sorted(filter(None, map(score, raw)), key=lambda x: -x['score']):
        k = (o['company'], o['title'], o['loc'])
        if k in seen or o['score'] < 65: continue
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
