#!/usr/bin/env python3
"""빌드 결과 검사: JSON-LD 파싱, 필수 태그, 내부 링크, 사이트맵·RSS 형식."""
import json, re, sys
import xml.etree.ElementTree as ET
from pathlib import Path
import yaml

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
BASE = yaml.safe_load((ROOT / "site.yml").read_text(encoding="utf-8"))["base_url"].rstrip("/")
errors = []
pages = list(DIST.rglob("index.html"))
known = {BASE + "/" + str(p.parent.relative_to(DIST)).replace(".", "").strip("/") + ("/" if p.parent != DIST else "") for p in pages}
known = {u.replace(BASE + "//", BASE + "/") for u in known}
for p in pages:
    h = p.read_text(encoding="utf-8")
    for tag in ("<title>", 'name="description"', 'rel="canonical"', "<h1>"):
        if tag not in h:
            errors.append(f"{p}: {tag} 없음")
    for blk in re.findall(r'<script type="application/ld\+json">(.*?)</script>', h, re.S):
        try:
            json.loads(blk)
        except Exception as e:
            errors.append(f"{p}: JSON-LD 오류 {e}")
    for href in re.findall(r'href="(' + re.escape(BASE) + r'[^"]*)"', h):
        if href.endswith((".xml", ".txt")):
            continue
        if href not in known:
            errors.append(f"{p}: 깨진 내부 링크 {href}")
for x in ("sitemap.xml", "rss.xml", "sitemap_index.xml"):
    try:
        ET.parse(DIST / x)
    except Exception as e:
        errors.append(f"{x}: XML 오류 {e}")
print(f"검사한 페이지 {len(pages)}개, 오류 {len(errors)}개")
for e in errors:
    print(" -", e)
sys.exit(1 if errors else 0)
