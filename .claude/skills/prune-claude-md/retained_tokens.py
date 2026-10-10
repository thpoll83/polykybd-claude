import pathlib, re, sys
orig=pathlib.Path(sys.argv[1]).read_text()
hay=""
for a in sys.argv[2:]:
    p=pathlib.Path(a)
    fs=[p] if p.is_file() else [x for x in p.rglob("*") if x.suffix in (".md",) and "/archive/" not in str(x) and "/lib/" not in str(x)]
    hay+="".join(x.read_text() for x in fs)
hayn=re.sub(r'\s+',' ',hay)
# split into bullets/paragraphs
paras=re.split(r'\n(?=\s*- |\s*\n|#)',orig)
bad=0
for p in paras:
    toks=set(re.findall(r'`([^`]{3,})`',p))|set(re.findall(r'#\d{2,4}\b',p))|set(re.findall(r'\b20\d\d-\d\d-\d\d\b',p))|set(re.findall(r'\b\d+(?:\.\d+)?\s?(?:ms|MB|KB|B|s|min|MHz|V|%)\b',p))
    toks={t for t in toks if not t.startswith("../")}
    if not toks: continue
    miss=[t for t in toks if t not in hay and re.sub(r'\s+',' ',t) not in hayn]
    if miss:
        bad+=1; print("MISS",miss,"::",re.sub(r'\s+',' ',p.strip())[:110])
print("paragraphs with missing tokens:",bad)
