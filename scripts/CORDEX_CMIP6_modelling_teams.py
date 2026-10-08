"""Searchable table of registered modelling teams and models per CORDEX-CMIP6 domain.

Sources: CMIP6_downscaling_plans.csv and the CORDEX-CMIP6 CV
(institution_id, source_id) fetched from GitHub.
"""
import html
import pandas as pd
import requests

CV = "https://raw.githubusercontent.com/WCRP-CORDEX/cordex-cmip6-cv/refs/heads/main/CORDEX-CMIP6"
OUT = "docs/CORDEX_CMIP6_modelling_teams.html"


def fetch_cv(name):
  try:
    r = requests.get(f"{CV}_{name}.json", timeout=30)
    r.raise_for_status()
    return r.json()[name]
  except Exception as e:
    print(f"Warning: could not fetch {name} CV: {e}")
    return {}


def split(s):
  return [x.strip() for x in str(s).split(",") if x.strip() and x.strip() != "nan"]


institutions = fetch_cv("institution_id")
sources = fetch_cv("source_id")

plans = pd.read_csv("CMIP6_downscaling_plans.csv", dtype=str).fillna("")
plans = plans[plans.institution_id.isin(institutions) & plans.source_id.isin(sources)]
plans["domain_id"] = plans.domain_id.str.split("-").str[0]


def model_link(s):
  url = sources.get(s, {}).get("further_info_url", "")
  s = html.escape(s)
  return f'<a href="{html.escape(url)}">{s}</a>' if url else s


rows = []
for (dom, inst), g in plans.groupby(["domain_id", "institution_id"]):
  models = sorted(set(g.source_id))
  rows.append({
    "domain": dom,
    "institution_id": inst,
    "institution": institutions.get(inst, ""),
    "source_id": ", ".join(model_link(m) for m in models),
  })
df = pd.DataFrame(rows)
domains = sorted(df.domain.unique())

esc = lambda x: x if isinstance(x, int) or "<a " in str(x) else html.escape(str(x))
head = "".join(f"<th>{c}</th>" for c in df.columns)
body = "\n".join(
  "<tr>" + "".join(f"<td>{esc(v)}</td>" for v in r) + "</tr>"
  for r in df.itertuples(index=False)
)
options = "".join(f'<option value="{d}">{d}</option>' for d in domains)

page = f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8">
<title>CORDEX-CMIP6 modelling teams by domain</title>
<link rel="stylesheet" href="https://cdn.datatables.net/1.11.5/css/jquery.dataTables.css">
<script src="https://code.jquery.com/jquery-3.5.1.js"></script>
<script src="https://cdn.datatables.net/1.11.5/js/jquery.dataTables.js"></script>
<style>
body {{font-family: "Montserrat", sans-serif; padding: 15px;}}
.logo {{text-align: center; margin-bottom: 20px;}}
th, td {{text-align: left; padding: 2px;}}
a {{color: DodgerBlue; text-decoration: none;}}
</style></head><body>
<div class="logo">
<img src="https://cordex.org/wp-content/uploads/2025/02/CORDEX_RGB_logo_baseline_positive-300x133.png" alt="CORDEX Logo">
<h1>CORDEX-CMIP6 modelling teams by domain</h1>
</div>
<p>Modelling teams and models per CORDEX domain, as registered in the downscaling plans
and the CORDEX-CMIP6 CV. Use the search box (case-sensitive) as domain filter or for any other view.</p>
<p>Domain: <select id="dom"><option value="">All</option>{options}</select></p>
<table id="t" class="display"><thead><tr>{head}</tr></thead>
<tbody>
{body}
</tbody></table>
<script>
$(document).ready(function() {{
  var t = $('#t').DataTable({{pageLength: 50, lengthMenu: [20, 50, 100, 200], order: [[0, 'asc'], [1, 'asc']], search: {{caseInsensitive: false}}}});
  $('#dom').on('change', function() {{
    var v = this.value;
    t.column(0).search(v ? '^' + v + '$' : '', true, false).draw();
  }});
}});
</script>
</body></html>
"""

with open(OUT, "w") as f:
  f.write(page)
print(f"Wrote {OUT} ({len(df)} rows)")
