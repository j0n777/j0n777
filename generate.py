#!/usr/bin/env python3
"""Build the Matrix-style neofetch profile card (dark_mode.svg + light_mode.svg).

Run in GitHub Actions with a token in GH_TOKEN to refresh the live stats.
Run locally with --no-fetch to preview with the fallback numbers below.
"""
import json
import os
import random
import sys
import urllib.request
from datetime import datetime, timezone
from html import escape

USER = "j0n777"
FALLBACK = {  # used only with --no-fetch (local preview)
    "repos": 78, "stars": 0, "followers": 8, "contrib": 3281,
    "commits": 0, "created": "2020-01-01T00:00:00Z", "langs": "TypeScript, Python",
}

# Static profile lines: (key, value). "" key = blank spacer, "#" key = section title.
def profile_lines(s):
    return [
        ("OS", "Sovereign · Bitcoin since 2014"),
        ("Uptime", s["uptime"]),
        ("Host", "RS — Brazil"),
        ("Kernel", "Lawyer · 14 years of practice"),
        ("Shell", "Entrepreneur · Content creator"),
        ("Audience", "1M+ followers across networks"),
        ("Countries.Visited", "16"),
        ("", ""),
        ("Projects", "AdvPrático · JornalBitcoin · GasNow.tools"),
        ("Projects.More", "Saia do Sistema · End Times Monitor"),
        ("Stack", "Claude Code · n8n · Lovable · Supabase"),
        ("Hardware", "ESP32 · Raspberry Pi · Meshtastic"),
        ("Languages", s["langs"]),
        ("", ""),
        ("#", "Contact"),
        ("Web", "jonataribas.com"),
        ("X", "@jonataribastv"),
        ("", ""),
        ("#", "GitHub Stats"),
        ("Repos", f"{s['repos']:,}  {{Stars: {s['stars']:,}}}"),
        ("Contributions.1y", f"{s['contrib']:,}  {{Commits: {s['commits']:,}}}"),
        ("Followers", f"{s['followers']:,}"),
    ]


def fetch_stats(token):
    query = """
    query($login: String!) {
      user(login: $login) {
        createdAt
        followers { totalCount }
        contributionsCollection {
          totalCommitContributions
          contributionCalendar { totalContributions }
        }
        repositories(ownerAffiliations: OWNER, isFork: false, first: 100, privacy: PUBLIC) {
          totalCount
          nodes {
            stargazerCount
            languages(first: 10, orderBy: {field: SIZE, direction: DESC}) {
              edges { size node { name } }
            }
          }
        }
      }
    }"""
    req = urllib.request.Request(
        "https://api.github.com/graphql",
        data=json.dumps({"query": query, "variables": {"login": USER}}).encode(),
        headers={"Authorization": f"bearer {token}", "Content-Type": "application/json"},
    )
    data = json.load(urllib.request.urlopen(req))
    if "errors" in data:
        sys.exit(f"GraphQL error: {data['errors']}")
    u = data["data"]["user"]
    repos = u["repositories"]
    sizes = {}
    for r in repos["nodes"]:
        for e in r["languages"]["edges"]:
            sizes[e["node"]["name"]] = sizes.get(e["node"]["name"], 0) + e["size"]
    top = sorted(sizes, key=sizes.get, reverse=True)[:4]
    return {
        "repos": repos["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos["nodes"]),
        "followers": u["followers"]["totalCount"],
        "contrib": u["contributionsCollection"]["contributionCalendar"]["totalContributions"],
        "commits": u["contributionsCollection"]["totalCommitContributions"],
        "created": u["createdAt"],
        "langs": ", ".join(top) or "—",
    }


def uptime(created):
    start = datetime.fromisoformat(created.replace("Z", "+00:00"))
    now = datetime.now(timezone.utc)
    months = (now.year - start.year) * 12 + now.month - start.month - (now.day < start.day)
    y, m = divmod(months, 12)
    return f"{y} years, {m} months (on GitHub)"


THEMES = {
    "dark": dict(bg="#020a04", border="#0f3d1c", key="#00ff41", val="#c8ffd0",
                 dots="#1f6b35", title="#7dff9b", ascii="#00e639", rain="#00ff41",
                 head="#e6ffe9", rain_op="0.22", neo="#00ff41"),
}

W, H = 985, 580
FONT = "ConsolasFallback,Consolas,'Courier New',Courier,monospace"
GLYPHS = "ｱｲｳｴｵｶｷｸｹｺｻｼｽｾｿﾀﾁﾂﾃﾄﾅﾆﾇﾈﾉﾊﾋﾌﾍﾎﾏﾐﾑﾒﾓﾔﾕﾖﾗﾘﾙﾚﾛﾜﾝ0123456789Z:.=*+-<>¦"


def rain(t):
    rnd = random.Random(777)  # fixed seed: same rain every run, clean diffs
    out = []
    for i in range(52):
        x = 8 + i * 19
        n = rnd.randint(10, 22)
        chars = [rnd.choice(GLYPHS) for _ in range(n)]
        dur = rnd.uniform(6, 13)
        delay = -rnd.uniform(0, dur)
        spans = "".join(
            f'<tspan x="{x}" dy="18" fill-opacity="{0.15 + 0.85 * (k + 1) / n:.2f}"'
            + (f' fill="{t["head"]}"' if k == n - 1 else "")
            + f">{escape(c)}</tspan>"
            for k, c in enumerate(chars)
        )
        out.append(
            f'<text class="drop" style="animation-duration:{dur:.1f}s;animation-delay:{delay:.1f}s">{spans}</text>'
        )
    return "\n".join(out)


def build(theme, stats, ascii_art):
    t = THEMES[theme]
    lines = profile_lines(stats)
    rows = []
    y, step, x0, width = 62, 21, 395, 62
    rows.append(f'<tspan x="{x0}" y="{y}" class="key">{USER}</tspan>'
                f'<tspan class="val">@</tspan><tspan class="key">github</tspan>'
                )
    rule = lambda chars, yy: (f'<line x1="{x0 + (chars + 1) * 9}" y1="{yy - 5}" x2="{x0 + width * 9}" '
                              f'y2="{yy - 5}" stroke="{t["dots"]}" stroke-width="1.2"/>')
    rules = [(0, rule(len(USER) + 7, y))]
    for k, v in lines:
        y += step
        if k == "":
            continue
        if k == "#":
            rules.append((len(rows), rule(len(v) + 2, y)))
            rows.append(f'<tspan x="{x0}" y="{y}" class="title">- {escape(v)}</tspan>')
            continue
        dots = max(2, width - len(k) - len(v) - 4)
        rows.append(f'<tspan x="{x0}" y="{y}" class="key">. {escape(k)}</tspan>'
                    f'<tspan class="dots">:{(" ." * dots)[:dots]} </tspan>'
                    f'<tspan class="val">{escape(v)}</tspan>')
    reveal = "\n".join(
        f'<text class="line" xml:space="preserve" style="animation-delay:{0.25 + i * 0.09:.2f}s">{r}</text>'
        for i, r in enumerate(rows)
    ) + "\n" + "\n".join(
        f'<g class="line" style="animation-delay:{0.25 + i * 0.09:.2f}s">{r}</g>' for i, r in rules
    )
    art = "\n".join(
        f'<tspan x="22" y="{58 + i * 14.5:.1f}">{escape(l)}</tspan>' for i, l in enumerate(ascii_art)
    )
    neo_y = H - 26
    return f'''<svg xmlns="http://www.w3.org/2000/svg" font-family="{FONT}" width="{W}" height="{H}" viewBox="0 0 {W} {H}" font-size="15px">
<style>
.key {{fill:{t["key"]};font-weight:bold}}
.val {{fill:{t["val"]}}}
.dots {{fill:{t["dots"]}}}
.title {{fill:{t["title"]};font-weight:bold}}
.drop {{fill:{t["rain"]};font-size:15px;animation:fall linear infinite}}
@keyframes fall {{from {{transform:translateY(-420px)}} to {{transform:translateY({H + 40}px)}}}}
.line {{opacity:0;animation:show .01s forwards}}
@keyframes show {{to {{opacity:1}}}}
.art {{fill:{t["ascii"]};font-size:12px;white-space:pre}}
.neo {{fill:{t["neo"]};font-size:14px}}
.cursor {{animation:blink 1s step-end infinite}}
@keyframes blink {{50% {{opacity:0}}}}
</style>
<rect width="{W}" height="{H}" rx="15" fill="{t["bg"]}" stroke="{t["border"]}" stroke-width="2"/>
<clipPath id="c"><rect width="{W}" height="{H}" rx="15"/></clipPath>
<g clip-path="url(#c)" opacity="{t["rain_op"]}">
{rain(t)}
</g>
<text class="art" xml:space="preserve">
{art}
</text>
{reveal}
<text x="{x0}" y="{neo_y}" class="neo">&gt; Wake up, {USER}... The Matrix has you.<tspan class="cursor">█</tspan></text>
</svg>
'''


def main():
    here = os.path.dirname(os.path.abspath(__file__))
    if "--no-fetch" in sys.argv:
        stats = dict(FALLBACK)
    else:
        token = os.environ.get("GH_TOKEN")
        if not token:
            sys.exit("Set GH_TOKEN (or pass --no-fetch for a local preview).")
        stats = fetch_stats(token)
    stats["uptime"] = uptime(stats["created"])
    with open(os.path.join(here, "ascii.txt"), encoding="utf-8") as f:
        ascii_art = f.read().splitlines()
    for theme in THEMES:
        with open(os.path.join(here, f"{theme}_mode.svg"), "w", encoding="utf-8") as f:
            f.write(build(theme, stats, ascii_art))
    print("ok:", {k: v for k, v in stats.items()})


if __name__ == "__main__":
    main()
