"""Check every `path[:lines]` citation in the reports against the pinned source trees."""
import os, re, sys, json
REPORTS = sys.argv[1]
ROOTS = {"pdfcraft": "/home/claude/artcraft-src/pdfcraft",
         "wordcraft": "/home/claude/artcraft-src/wordcraft",
         "craft-libs": "/home/claude/artcraft-src/craft-libs@pdfcraft",
         "craft-libs@wordcraft": "/home/claude/artcraft-src/craft-libs@wordcraft"}
pat = re.compile(r"`([A-Za-z0-9_@./-]+\.(?:rs|toml|md|txt|json|yml|yaml))(?::([0-9][0-9,\s–-]*))?`")
INDEX = {}
for r in ROOTS.values():
    acc = []
    for dp, dn, fn in os.walk(r):
        dn[:] = [d for d in dn if d not in (".git", "target", "node_modules")]
        acc += [os.path.join(dp, x) for x in fn]
    INDEX[r] = acc
results = []
for f in sorted(os.listdir(REPORTS)):
    if not f.endswith(".md"): continue
    text = open(os.path.join(REPORTS, f)).read()
    for m in pat.finditer(text):
        path, lines = m.group(1), (m.group(2) or "").strip()
        if path.startswith(("evidence/", "diagrams/", "reports/", "tools/", "corpus/")):
            ok = os.path.exists(os.path.join(REPORTS, path)) or os.path.exists(os.path.join(REPORTS, "..", path))
            results.append((f, path, lines, ok, "local")); continue
        cands = []
        first = path.split("/")[0]
        if first in ("pdfcraft", "wordcraft", "craft-libs"):
            rel = path[len(first)+1:]
            roots = [ROOTS[first]] + ([ROOTS["craft-libs@wordcraft"]] if first == "craft-libs" else [])
        elif first == "craft-pdf":
            rel = "crates/pdf/" + path[len("craft-pdf/"):]; roots = [ROOTS["craft-libs"], ROOTS["craft-libs@wordcraft"]]
        else:
            rel = path; roots = list(ROOTS.values())
        for r in roots:
            p = os.path.join(r, rel)
            if os.path.isfile(p): cands.append(p)
        if not cands:
            suffix = path
            if re.match(r"craft-[a-z0-9-]+/", suffix):
                suffix = "crates/" + suffix[len("craft-"):]
            suffix = "/" + suffix.lstrip("/")
            for r in ROOTS.values():
                for c in INDEX[r]:
                    if c.endswith(suffix): cands.append(c)
            if len(set(os.path.relpath(c, r2) for c in cands for r2 in [os.path.commonpath([c, "/home/claude/artcraft-src"])])) > 6 and "/" not in path:
                results.append((f, path, lines, True, "ambiguous-basename")); continue
        if not cands:
            results.append((f, path, lines, False, "missing")); continue
        if not lines:
            results.append((f, path, lines, True, cands[0])); continue
        nums = [int(x) for x in re.findall(r"\d+", lines)]
        ok = any(max(nums) <= sum(1 for _ in open(c, errors="replace")) for c in cands)
        results.append((f, path, lines, ok, cands[0] if ok else "line out of range"))
bad = [r for r in results if not r[3]]
print(f"{len(results)} citations checked, {len(bad)} problems")
for r in bad: print("PROBLEM", r)
json.dump(results, open(os.path.join(REPORTS, "evidence", "citation-check.json"), "w"), indent=1)
