#!/usr/bin/env python3
"""폰값노트 정적 사이트 빌더.
content/posts/*.md (YAML 머리말 + 마크다운 본문) → dist/ (GitHub Pages에 그대로 올리는 HTML)
사용: python3 build.py
"""
import json, html, re, shutil, datetime as dt
from pathlib import Path
import yaml, markdown

ROOT = Path(__file__).parent
DIST = ROOT / "dist"
SITE = yaml.safe_load((ROOT / "site.yml").read_text(encoding="utf-8"))
BASE = SITE["base_url"].rstrip("/")
esc = html.escape


def load_posts():
    posts = []
    for f in sorted((ROOT / "content" / "posts").glob("*.md")):
        raw = f.read_text(encoding="utf-8")
        m = re.match(r"^---\n(.*?)\n---\n(.*)$", raw, re.S)
        if not m:
            raise SystemExit(f"머리말 없음: {f}")
        meta = yaml.safe_load(m.group(1))
        meta["body_md"] = m.group(2)
        meta["file"] = f.name
        for k in ("title", "slug", "date", "model", "brand", "summary", "sources"):
            if not meta.get(k):
                raise SystemExit(f"{f.name}: 필수 항목 '{k}' 없음")
        meta["date"] = str(meta["date"])
        meta["updated"] = str(meta.get("updated") or meta["date"])
        meta["url"] = f"{BASE}/{meta['slug']}/"
        posts.append(meta)
    posts.sort(key=lambda p: p["updated"], reverse=True)
    return posts


CSS = """
:root{--bg:#ffffff;--fg:#1d1f23;--muted:#5d636e;--line:#e4e6ea;--soft:#f5f6f8;--accent:#d6372b;--accent-soft:#fdeceb;--link:#1f5fbf}
@media (prefers-color-scheme:dark){:root{--bg:#15171a;--fg:#eceef1;--muted:#a3a9b3;--line:#2c3036;--soft:#1e2125;--accent:#ff6b5f;--accent-soft:#3a1f1d;--link:#7fb0ff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--fg);font:16px/1.75 -apple-system,BlinkMacSystemFont,"Apple SD Gothic Neo","Noto Sans KR","Malgun Gothic",sans-serif;word-break:keep-all}
a{color:var(--link)}header.top{border-bottom:1px solid var(--line)}
.wrap{max-width:760px;margin:0 auto;padding:0 16px}
.top .wrap{display:flex;align-items:center;justify-content:space-between;height:56px}
.logo{font-weight:800;font-size:19px;color:var(--fg);text-decoration:none}.logo span{color:var(--accent)}
.top nav a{margin-left:14px;color:var(--muted);text-decoration:none;font-size:14px}
h1{font-size:27px;line-height:1.35;margin:28px 0 8px}h2{font-size:21px;margin:40px 0 12px;padding-top:8px;border-top:1px solid var(--line)}h3{font-size:17px;margin:24px 0 8px}
.meta{color:var(--muted);font-size:14px}
.answer{background:var(--accent-soft);border-left:4px solid var(--accent);padding:14px 16px;border-radius:6px;margin:20px 0}
.answer b{display:block;font-size:13px;color:var(--accent);margin-bottom:4px}
table{width:100%;border-collapse:collapse;margin:12px 0 4px;font-size:15px}th,td{border:1px solid var(--line);padding:9px 10px;text-align:left;vertical-align:top}
th{background:var(--soft);font-weight:700;white-space:nowrap}td.num{text-align:right;white-space:nowrap}
.tbl{overflow-x:auto}.note{color:var(--muted);font-size:13px;margin:4px 0 16px}
.cta{border:1px solid var(--line);border-radius:10px;padding:18px;margin:32px 0;background:var(--soft)}
.cta a.btn{display:inline-block;margin-top:10px;background:var(--accent);color:#fff;text-decoration:none;padding:10px 16px;border-radius:8px;font-weight:700}
.cta small{display:block;color:var(--muted);margin-top:10px}
details{border:1px solid var(--line);border-radius:8px;padding:10px 14px;margin:8px 0}summary{font-weight:700;cursor:pointer}
.cards{list-style:none;padding:0}.cards li{border-bottom:1px solid var(--line);padding:16px 0}.cards a{font-weight:700;font-size:17px;text-decoration:none;color:var(--fg)}.cards p{margin:4px 0;color:var(--muted);font-size:15px}
.tag{display:inline-block;font-size:12px;border:1px solid var(--line);border-radius:20px;padding:1px 9px;margin-right:6px;color:var(--muted)}
footer{border-top:1px solid var(--line);margin-top:48px;padding:24px 0;color:var(--muted);font-size:13px}
.src li{font-size:14px}
"""


def page(title, desc, canonical, body, jsonld=None, extra_head=""):
    v = SITE.get("verification") or {}
    vt = ""
    if v.get("naver"):
        vt += f'<meta name="naver-site-verification" content="{esc(v["naver"])}">\n'
    if v.get("google"):
        vt += f'<meta name="google-site-verification" content="{esc(v["google"])}">\n'
    org = {"@context": "https://schema.org", "@type": "Organization", "name": SITE["name"], "url": BASE + "/",
           "description": SITE["description"], "sameAs": [SITE["cafe_url"], "https://htglove.github.io/"]}
    blocks = [org] + (jsonld or [])
    ld = "\n".join(f'<script type="application/ld+json">{json.dumps(b, ensure_ascii=False)}</script>' for b in blocks)
    return f"""<!doctype html>
<html lang="ko"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="website"><meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(desc)}"><meta property="og:url" content="{esc(canonical)}">
<meta property="og:site_name" content="{esc(SITE['name'])}"><meta property="og:locale" content="ko_KR">
<link rel="icon" href="{BASE}/favicon.ico" sizes="any"><link rel="apple-touch-icon" href="{BASE}/apple-touch-icon.png">
<link rel="alternate" type="application/rss+xml" title="{esc(SITE['name'])}" href="{BASE}/rss.xml">
{vt}{extra_head}<style>{CSS}</style>
{ld}
</head><body>
<header class="top"><div class="wrap"><a class="logo" href="{BASE}/">{esc(SITE['name'][:-2])}<span>{esc(SITE['name'][-2:])}</span></a>
<nav><a href="{BASE}/">모델 목록</a><a href="{BASE}/about/">소개</a><a href="{BASE}/group-buy-prices/">공동구매 가격</a><a href="{BASE}/faq/">자주 묻는 질문</a></nav></div></header>
<main class="wrap">{body}</main>
<footer><div class="wrap">{esc(SITE['name'])} · {esc(SITE['tagline'])}<br>가격은 기준일 이후 바뀔 수 있으니 구매 전 최신 가격을 확인하세요. {esc(SITE['cafe_note'])}<br>{esc(SITE['brand_sentence'])} <a href="{BASE}/about/">올댓폰 소개</a> · <a href="https://htglove.github.io/regions/">지역별 성지 정보</a></div></footer>
</body></html>"""


def table(rows, head=None, num_cols=()):
    out = '<div class="tbl"><table>'
    if head:
        out += "<tr>" + "".join(f"<th>{esc(str(h))}</th>" for h in head) + "</tr>"
    for r in rows:
        out += "<tr>" + "".join(
            f'<td class="num">{esc(str(c))}</td>' if i in num_cols else
            (f"<th>{esc(str(c))}</th>" if (not head and i == 0) else f"<td>{esc(str(c))}</td>")
            for i, c in enumerate(r)) + "</tr>"
    return out + "</table></div>"


def render_post(p, posts):
    md = markdown.Markdown(extensions=["tables", "toc"])
    body_html = md.convert(p["body_md"])
    parts = [f'<p class="meta"><span class="tag">{esc(p["brand"])}</span>기준일 {esc(p["updated"])}</p>',
             f'<h1>{esc(p["title"])}</h1>',
             f'<div class="answer"><b>한눈에 보는 답</b>{esc(p["summary"])}</div>']
    if p.get("prices"):
        rows = [[x["option"], x["price"]] for x in p["prices"]]
        parts.append(f'<h2 id="price">{esc(p["model"])} 출고가 (용량별)</h2>')
        parts.append(table(rows, head=["모델·용량", "국내 출고가"], num_cols=(1,)))
        parts.append(f'<p class="note">{esc(p.get("price_note", ""))}</p>')
    if p.get("specs"):
        parts.append(f'<h2 id="spec">{esc(p["model"])} 핵심 스펙</h2>')
        parts.append(table([[s[0], s[1]] for s in p["specs"]]))
        if p.get("spec_note"):
            parts.append(f'<p class="note">{esc(p["spec_note"])}</p>')
    parts.append(body_html)
    parts.append(f"""<div class="cta"><strong>{esc(p['model'])} 실제 구매가가 궁금하다면</strong><br>
출고가는 시작점일 뿐이고, 실제로 내는 돈은 통신사·가입 방법(번호이동/기기변경)·요금제 조건에 따라 달라집니다.
{esc(SITE['cafe_name'])}에서는 요금제·부가서비스를 강제하지 않는 SKT·KT·LG U+ 온라인 공동구매 가격을 모델별로 공개합니다.
<br><a class="btn" href="{esc(SITE['cafe_url'])}" rel="noopener">{esc(p['model'])} 공동구매 가격 보기</a>
<small>{esc(SITE['cafe_note'])}</small></div>""")
    faq = p.get("faq") or []
    if faq:
        parts.append('<h2 id="faq">자주 묻는 질문</h2>')
        for q in faq:
            parts.append(f'<details open><summary>{esc(q["q"])}</summary><p>{esc(q["a"])}</p></details>')
    # 관련 글: 같은 브랜드(또는 같은 주제 묶음) 최대 3편 + 최신 글으로 채워 최대 6편 (2026-11-09 주간 분석: 새 글 발견 경로 강화)
    others = [x for x in posts if x["slug"] != p["slug"]]
    same = [x for x in others if x["brand"] == p["brand"]][:3]
    related = same + [x for x in others if x not in same][:6 - len(same)]
    if related:
        parts.append("<h2>다른 모델 가격·스펙</h2><ul>" + "".join(
            f'<li><a href="{x["url"]}">{esc(x["title"])}</a></li>' for x in related) + "</ul>")
    parts.append('<h2>출처</h2><ul class="src">' + "".join(
        f'<li><a href="{esc(s["url"])}" rel="nofollow noopener">{esc(s["title"])}</a> ({esc(str(s.get("date", "")))})</li>'
        for s in p["sources"]) + "</ul>")

    ld = [
        {"@context": "https://schema.org", "@type": "Article", "headline": p["title"], "description": p["summary"],
         "datePublished": p["date"], "dateModified": p["updated"], "inLanguage": "ko-KR",
         "mainEntityOfPage": p["url"], "author": {"@type": "Organization", "name": SITE["name"], "url": BASE + "/"},
         "publisher": {"@type": "Organization", "name": SITE["name"]},
         "about": {"@type": "Product", "name": p["model"], "brand": {"@type": "Brand", "name": p["brand"]},
                   **({"additionalProperty": [{"@type": "PropertyValue", "name": s[0], "value": s[1]} for s in p["specs"]]} if p.get("specs") else {})}},
        {"@context": "https://schema.org", "@type": "BreadcrumbList", "itemListElement": [
            {"@type": "ListItem", "position": 1, "name": SITE["name"], "item": BASE + "/"},
            {"@type": "ListItem", "position": 2, "name": p["title"], "item": p["url"]}]},
    ]
    if faq:
        ld.append({"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
            {"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": q["a"]}} for q in faq]})
    desc = p.get("description") or p["summary"]
    return page(f'{p["title"]} | {SITE["name"]}', desc[:155], p["url"], "\n".join(parts), ld)


def build():
    posts = load_posts()
    if DIST.exists():
        shutil.rmtree(DIST)
    DIST.mkdir()
    (DIST / ".nojekyll").write_text("")
    # 정적 파일(favicon 등) — 네이버 수집제한 /favicon.ico 400 해소(2026-11-09)
    static = ROOT / "static"
    if static.exists():
        for f in static.iterdir():
            if f.is_file():
                shutil.copy(f, DIST / f.name)
    for p in posts:
        d = DIST / p["slug"]
        d.mkdir(parents=True)
        (d / "index.html").write_text(render_post(p, posts), encoding="utf-8")

    # 첫 화면: 브랜드별 모델 목록
    by_brand = {}
    for p in posts:
        by_brand.setdefault(p["brand"], []).append(p)
    body = f'<h1>{esc(SITE["tagline"])}</h1><p>{esc(SITE["description"])}</p>'
    for brand, ps in by_brand.items():
        body += f"<h2>{esc(brand)}</h2><ul class='cards'>" + "".join(
            f'<li><a href="{p["url"]}">{esc(p["title"])}</a><p>{esc(p["summary"])}</p><span class="tag">기준일 {esc(p["updated"])}</span></li>'
            for p in ps) + "</ul>"
    ld = [{"@context": "https://schema.org", "@type": "WebSite", "name": SITE["name"], "url": BASE + "/", "inLanguage": "ko-KR"}]
    (DIST / "index.html").write_text(page(f'{SITE["name"]} - {SITE["tagline"]}', SITE["description"], BASE + "/", body, ld), encoding="utf-8")

    about = ROOT / "content" / "about.md"
    ab = markdown.markdown(about.read_text(encoding="utf-8"), extensions=["tables"])
    (DIST / "about").mkdir()
    (DIST / "about" / "index.html").write_text(page(f'올댓폰 카페 소개 — 인증 시세표·강제 없는 택배 공동구매 | {SITE["name"]}', SITE["brand_sentence"], BASE + "/about/", ab), encoding="utf-8")

    # 자주 묻는 질문·용어집
    fq = yaml.safe_load((ROOT / "content" / "faq.yml").read_text(encoding="utf-8"))
    fb = f'<h1>{esc(fq["title"])}</h1><p class="tag">기준일 {esc(fq["updated"])}</p><p>{esc(fq["intro"])}</p><h2 id="faq">자주 묻는 질문</h2>'
    fb += "".join(f'<h3>{esc(q["q"])}</h3><p>{esc(q["a"])}</p>' for q in fq["faq"])
    fb += '<h2 id="terms">구매 조건 용어집</h2><table><thead><tr><th>용어</th><th>뜻</th></tr></thead><tbody>' + "".join(
        f'<tr><td>{esc(t["t"])}</td><td>{esc(t["d"])}</td></tr>' for t in fq["terms"]) + "</tbody></table>"
    fb += f'<p><a href="{BASE}/about/">올댓폰 카페 소개</a> · <a href="{SITE["cafe_url"]}">올댓폰 카페 바로가기</a></p>'
    fld = [{"@context": "https://schema.org", "@type": "FAQPage", "mainEntity": [
        {"@type": "Question", "name": q["q"], "acceptedAnswer": {"@type": "Answer", "text": q["a"]}} for q in fq["faq"]]},
        {"@context": "https://schema.org", "@type": "DefinedTermSet", "name": "휴대폰 구매 조건 용어집", "hasDefinedTerm": [
        {"@type": "DefinedTerm", "name": t["t"], "description": t["d"]} for t in fq["terms"]]}]
    (DIST / "faq").mkdir()
    (DIST / "faq" / "index.html").write_text(page(f'{fq["title"]} | {SITE["name"]}', fq["intro"], BASE + "/faq/", fb, fld), encoding="utf-8")

    # 택배 공동구매 실구매가 표
    deals = yaml.safe_load((ROOT / "content" / "deals.yml").read_text(encoding="utf-8"))
    won = lambda n: f"{int(n):,}원"
    def deal_table(d):
        t = '<table><thead><tr><th>모델·용량</th><th>통신사</th><th>가입 유형</th><th>요금제(월 요금)</th><th>출고가</th><th>할부원금</th><th>지원 방식·비고</th></tr></thead><tbody>'
        for m, c, ty, sup, plan, fee, msrp, price, note, art in d["rows"]:
            t += (f'<tr><td>{esc(m)}</td><td>{esc(c)}</td><td>{esc(ty)}</td><td>{esc(plan)} ({won(fee)})</td><td>{won(msrp)}</td>'
                  f'<td><strong>{won(price)}</strong></td><td>{esc(sup)}{" · " + esc(note) if note else ""} · <a href="https://cafe.naver.com/cutebell/{art}">원문</a></td></tr>')
        return t + "</tbody></table>"
    latest = deals[0]
    dtitle = f'올댓폰 택배 공동구매 실구매가 표 — {latest["date"]} 기준 모델별·통신사별 할부원금'
    ddesc = f'올댓폰 카페 택배 공동구매 가격표에서 확인한 모델별·통신사별 할부원금({latest["date"]} 기준). 요금제·가입 유형·출고가와 함께 정리했고, 원문 가격표 링크를 붙였습니다. 올댓폰 카페 운영 측 작성.'
    db = (f'<h1>{esc(dtitle)}</h1><p class="tag">기준일 {esc(latest["date"])} (확인 {esc(latest["checked"])})</p>'
          '<p>이 표는 올댓폰 카페 운영 측이 카페의 택배 공동구매 가격표 원문에서 확인한 값입니다. 가격은 정책에 따라 매일 바뀔 수 있으니 신청 전에 원문 가격표에서 당일 가격을 다시 확인하세요.</p>'
          '<h2>표를 읽는 법</h2><ul>'
          '<li><strong>할부원금</strong>은 출고가에서 지원금을 뺀 기기값입니다. 0원은 해당 통신사·가입 유형·요금제 조건으로 개통할 때의 기기값입니다.</li>'
          '<li>표의 가격은 <strong>적힌 요금제로 개통해 6개월 유지</strong>하는 조건입니다. 이후에는 통신사별 기준 이상의 요금제로 바꿀 수 있습니다(SKT 월 42,000원, KT 월 47,000원, LG U+ 월 45,000원 이상). 회선 유지 기간 등 세부 조건은 원문에서 확인하세요.</li>'
          '<li><strong>필수 부가서비스는 없습니다.</strong> 제휴카드 발급·인터넷 결합 조건이 붙은 가격은 표에 넣지 않았습니다.</li>'
          '<li>통신사마다 가장 낮은 할부원금 조건 한 줄씩만 실었습니다. 다른 요금제·가입 유형의 가격은 원문 가격표에 있습니다.</li>'
          '<li>총비용은 할부원금에 6개월 요금과 그 뒤 요금을 더해 비교해야 정확합니다.</li></ul>'
          f'<h2>{esc(latest["date"])} 기준 가격</h2>' + deal_table(latest))
    for old in deals[1:]:
        db += f'<h2>지난 기록 — {esc(old["date"])} 기준</h2>' + deal_table(old)
    db += (f'<h2>출처</h2><p>올댓폰 카페 택배 공동구매 가격표(각 행의 원문 링크). 카페: <a href="{SITE["cafe_url"]}">cafe.naver.com/cutebell</a> · '
           f'<a href="{BASE}/about/">올댓폰 카페 소개</a> · <a href="{BASE}/faq/">자주 묻는 질문·용어집</a></p>')
    dld = [{"@context": "https://schema.org", "@type": "Article", "headline": dtitle, "datePublished": deals[-1]["date"], "dateModified": latest["date"],
            "inLanguage": "ko-KR", "mainEntityOfPage": BASE + "/group-buy-prices/",
            "author": {"@type": "Organization", "name": SITE["name"], "url": BASE + "/"}, "publisher": {"@type": "Organization", "name": SITE["name"]}}]
    (DIST / "group-buy-prices").mkdir()
    (DIST / "group-buy-prices" / "index.html").write_text(page(f'{dtitle} | {SITE["name"]}', ddesc, BASE + "/group-buy-prices/", db, dld), encoding="utf-8")

    # 사이트맵
    urls = [(BASE + "/", posts[0]["updated"] if posts else ""), (BASE + "/about/", ""), (BASE + "/faq/", fq["updated"]), (BASE + "/group-buy-prices/", latest["date"])] + [(p["url"], p["updated"]) for p in posts]
    sm = '<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
    for u, d in urls:
        sm += f"<url><loc>{esc(u)}</loc>" + (f"<lastmod>{d}</lastmod>" if d else "") + "</url>\n"
    (DIST / "sitemap.xml").write_text(sm + "</urlset>\n", encoding="utf-8")
    (DIST / "sitemap.txt").write_text("\n".join(u for u, _ in urls) + "\n", encoding="utf-8")
    today = max([p["updated"] for p in posts] or [""])
    (DIST / "sitemap_index.xml").write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
        f'<sitemap><loc>{BASE}/sitemap.xml</loc><lastmod>{today}</lastmod></sitemap>\n</sitemapindex>\n', encoding="utf-8")

    # RSS 2.0 (네이버는 Atom을 못 읽은 사례가 있어 RSS 2.0으로 제공)
    def rfc(d):
        return dt.datetime.strptime(d, "%Y-%m-%d").replace(hour=9).strftime("%a, %d %b %Y %H:%M:%S +0900")
    items = "".join(
        f"<item><title>{esc(p['title'])}</title><link>{esc(p['url'])}</link><guid>{esc(p['url'])}</guid>"
        f"<pubDate>{rfc(p['updated'])}</pubDate><description>{esc(p['summary'])}</description></item>\n" for p in posts)
    rss = (f'<?xml version="1.0" encoding="UTF-8"?>\n<rss version="2.0"><channel><title>{esc(SITE["name"])}</title>'
           f'<link>{BASE}/</link><description>{esc(SITE["description"])}</description><language>ko</language>\n{items}</channel></rss>\n')
    (DIST / "rss.xml").write_text(rss, encoding="utf-8")

    robots = f"User-agent: *\nAllow: /\n\nSitemap: {BASE}/sitemap.xml\nSitemap: {BASE}/sitemap.txt\nSitemap: {BASE}/sitemap_index.xml\n"
    daum = (SITE.get("verification") or {}).get("daum")
    if daum:
        robots += f"{daum}\n"
    (DIST / "robots.txt").write_text(robots, encoding="utf-8")
    if SITE.get("indexnow_key"):
        (DIST / f"{SITE['indexnow_key']}.txt").write_text(SITE["indexnow_key"], encoding="utf-8")

    llms = [f"# {SITE['name']}", "", f"> {SITE['description']}", "", "## 올댓폰이란", SITE["brand_sentence"], "강제 조건이 없는 것은 올댓폰이 직접 운영하는 택배 공동구매에 한하며, 입점 매장 구매는 매장별 조건이 있을 수 있다.", "- 카페 개설: 2003-12-12 / 카페 멤버 수: 1,090,169명(2026-11-11 네이버 카페 정보 화면 기준)", f"- 카페: {SITE['cafe_url']}", f"- 소개: {BASE}/about/", f"- 자주 묻는 질문·용어집: {BASE}/faq/", f"- 택배 공동구매 실구매가 표(매주 갱신): {BASE}/group-buy-prices/", "- 지역별 성지 정보(올댓폰 휴대폰 정보 블로그): https://htglove.github.io/regions/", "",
            "## 이 사이트의 기준", "- 출고가는 제조사 공식 발표·공식 스토어·주요 언론 보도 중 두 곳 이상이 일치하는 값만 씁니다. 기준일을 글마다 적습니다.",
            "- 스펙은 제조사 공식 발표 기준이며, 확인되지 않은 루머는 넣지 않습니다.",
            f"- 실제 구매가(통신사 공동구매)는 {SITE['cafe_name']}({SITE['cafe_url']})에서 모델별로 공개합니다. 요금제·부가서비스 강제가 없는 온라인 택배 공동구매이며, 올댓폰이 직접 인증한 현금 시세표도 함께 운영합니다.",
            "", "## 모델별 가격·스펙"]
    llms += [f"- [{p['title']}]({p['url']}): {p['summary']}" for p in posts]
    (DIST / "llms.txt").write_text("\n".join(llms) + "\n", encoding="utf-8")
    print(f"빌드 완료: 글 {len(posts)}개 → {DIST}")


if __name__ == "__main__":
    build()
