import json
import os
import urllib.request
from datetime import datetime, timedelta, timezone

USERNAME = os.environ.get("USERNAME", "furqanzubair209-cell")
TOKEN = os.environ.get("GITHUB_TOKEN", "")
OUT = "activity-graph/activity-graph.svg"
DAYS = 31

QUERY = """
query($login: String!, $from: DateTime!, $to: DateTime!) {
  user(login: $login) {
    contributionsCollection(from: $from, to: $to) {
      contributionCalendar {
        weeks { contributionDays { date contributionCount } }
      }
    }
  }
}
"""


def fetch_days():
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=DAYS)
    payload = json.dumps({
        "query": QUERY,
        "variables": {
            "login": USERNAME,
            "from": start.strftime("%Y-%m-%dT00:00:00Z"),
            "to": end.strftime("%Y-%m-%dT%H:%M:%SZ"),
        },
    }).encode()
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=payload,
        headers={"Authorization": f"Bearer {TOKEN}", "Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req) as r:
        data = json.load(r)
    weeks = data["data"]["user"]["contributionsCollection"]["contributionCalendar"]["weeks"]
    days = {}
    for w in weeks:
        for d in w["contributionDays"]:
            days[d["date"]] = d["contributionCount"]
    cutoff = (end - timedelta(days=DAYS)).strftime("%Y-%m-%d")
    return sorted((d, c) for d, c in days.items() if d >= cutoff)


def build_svg(days):
    W, H = 900, 300
    L, R, T, B = 50, 30, 60, 45
    bg, line, text, grid = "#1a1b27", "#70a5fd", "#38bdae", "#2a2b3d"
    counts = [c for _, c in days]
    ymax = max(max(counts, default=0), 4)
    ymax = ymax + (-ymax % 4)
    pw, ph = W - L - R, H - T - B
    n = max(len(days) - 1, 1)
    pts = [(L + pw * i / n, T + ph - ph * c / ymax) for i, (_, c) in enumerate(days)]
    path = " ".join(f"{x:.1f},{y:.1f}" for x, y in pts)
    area = f"{L},{T + ph} {path} {L + pw},{T + ph}"

    o = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-family="Segoe UI, Ubuntu, sans-serif">']
    o.append(f'<rect width="{W}" height="{H}" rx="6" fill="{bg}"/>')
    o.append(f'<text x="{W/2}" y="34" text-anchor="middle" font-size="20" font-weight="600" fill="{text}">Muhammad Furqan\'s Contribution Graph</text>')
    for i in range(5):
        v = ymax * i / 4
        y = T + ph - ph * i / 4
        o.append(f'<line x1="{L}" y1="{y:.1f}" x2="{L + pw}" y2="{y:.1f}" stroke="{grid}"/>')
        o.append(f'<text x="{L - 8}" y="{y + 4:.1f}" text-anchor="end" font-size="11" fill="{text}">{int(v)}</text>')
    step = max(len(days) // 8, 1)
    for i in range(0, len(days), step):
        d = datetime.strptime(days[i][0], "%Y-%m-%d")
        o.append(f'<text x="{pts[i][0]:.1f}" y="{H - 18}" text-anchor="middle" font-size="11" fill="{text}">{d.strftime("%b")} {d.day}</text>')
    o.append(f'<polygon points="{area}" fill="{line}" fill-opacity="0.18"/>')
    o.append(f'<polyline points="{path}" fill="none" stroke="{line}" stroke-width="2.5" stroke-linejoin="round"/>')
    for x, y in pts:
        o.append(f'<circle cx="{x:.1f}" cy="{y:.1f}" r="3.2" fill="{line}"/>')
    o.append('</svg>')
    return "\n".join(o)


if __name__ == "__main__":
    days = fetch_days()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", encoding="utf-8") as f:
        f.write(build_svg(days))
    print(f"Wrote {OUT} with {len(days)} days")
