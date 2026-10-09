# Job Radar

Personal job search dashboard. Pulls US data engineering and data platform roles from public company job boards (Greenhouse and Ashby), scores each one against my experience, and builds a single page: index.html.

- radar.py: fetches postings, scores them, writes index.html and jobs.json
- template.html: the dashboard page (data is inserted at build time)
- .github/workflows/refresh.yml: rebuilds the page every morning at 7 AM Central

Run locally: python3 radar.py, then open index.html.
Edit the GH and ASH company lists in radar.py to change which companies are searched.
