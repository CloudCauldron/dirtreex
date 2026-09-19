# /// script
# requires-python = ">=3.12"
# dependencies = ["Pillow==12.0.0"]
# ///
"""Compile directory-tree fixtures and compare reviewed regression observations.

Run with uv from Windows-native Git Bash. Results and shared font caches go
under tests/work by default; --output and DIRTREEX_TEST_CACHE can redirect them.
"""
from pathlib import Path
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
import argparse,gzip,hashlib,json,os,re,shutil,subprocess,time,sys
import xml.etree.ElementTree as ET
from PIL import Image

ROOT=Path(__file__).resolve().parent
ENGINES=("lualatex","pdflatex","xelatex")
REPO=ROOT.parent
BIN=os.environ.get("DIRTREEX_TEX_BIN")
EFFECTS=("nodes","entries","pieces","tail","tails","events","bounds","begin","effects","marks")
AUX=("aux","toc","out")
def digest(data):return hashlib.sha256(data).hexdigest()
def read_json(path):
    raw=path.read_bytes()
    return json.loads(gzip.decompress(raw) if path.suffix==".gz" else raw)
def write_json(path,data):path.write_text(json.dumps(data,indent=2,ensure_ascii=False),encoding="utf8")
def tool(name):
    if BIN:
        path=Path(BIN)/(name+(".exe" if os.name=="nt" else ""))
        if path.is_file():return str(path.resolve())
    else:
        path=shutil.which(name)
        if path:return path
    raise FileNotFoundError(f"Missing tool: {name}; check PATH or DIRTREEX_TEX_BIN")

def select_cases(cases,wanted):
    ids=[c["id"] for c in cases]
    if len(ids)!=len(set(ids)):raise ValueError("Duplicate catalog case ID")
    if wanted is None:return [c for c in cases if not c.get("advisory")]
    if len(wanted)!=len(set(wanted)):raise ValueError("Duplicate case selection")
    missing=set(wanted)-set(ids)
    if missing:raise ValueError("Unknown case: "+", ".join(sorted(missing)))
    return [c for c in cases if c["id"] in wanted]

def final_log_errors(log):
    return re.findall(r"^(?:.*Rerun LaTeX.*|.*Label\(s\) may have changed.*|.*undefined references.*|Missing character:.*)$",log,re.M)

def run_command(args,out,log=None,env=None,timeout=180):
    with (out/(log or "tool.stdout.txt")).open("wb") as stream:
        result=subprocess.run(args,cwd=out,env=env,stdin=subprocess.DEVNULL,stdout=stream,stderr=subprocess.STDOUT,timeout=timeout)
    return result.returncode
def auxiliary(out):
    return {ext:digest((out/("input."+ext)).read_bytes()) for ext in AUX if (out/("input."+ext)).is_file()}
def observe(out,case):
    log=(out/"input.log").read_text(encoding="utf8",errors="replace")
    obs={"diagnostics":re.findall(r"(?:Overfull|Underfull) \\[hv]box[^\n]*",log),
         "aux":auxiliary(out),
         "effects":{ext:digest((out/("input."+ext)).read_bytes()) for ext in EFFECTS if (out/("input."+ext)).is_file()}}
    pattern=case.get("log_pattern",r"^(?:SD-COUNTS|CF-FORMATTED)[^\n]*")
    obs["log_events"]=re.findall(pattern,log,re.M)
    obs["retries"]=[int(x) for x in re.findall(r"DG-DEFER attempt=(\d+)",log)]
    obs["bug_present"]=False
    if case.get("bug_regex"):obs["bug_present"]=bool(re.search(case["bug_regex"],log))
    if case["kind"] in ("expected-error","known-error"):
        diagnostic=case["diagnostic"]
        # The driver sets max_print_line; normalize old wrapped error text too.
        obs["error_present"]=diagnostic in re.sub(r"\s+"," ",log)
        obs["diagnostic_count"]=log.count("Package dirtreex Error: "+diagnostic) if case["kind"]=="expected-error" else int(obs["error_present"])
        obs["required_log_present"]=case.get("requires_log","") in log
        return obs
    rc=run_command([tool("pdftotext"),"-bbox-layout","input.pdf","positions.html"],out)
    if rc:raise RuntimeError("pdftotext failed")
    # Some legacy PDF fonts map ligatures to XML-forbidden C0 codes.
    # Preserve those exact characters in JSON after safely parsing the markup.
    xml=(out/"positions.html").read_text(encoding="utf8")
    xml=re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f]",lambda m:"DTECONTROL%04XEND"%ord(m.group()),xml)
    pages=ET.fromstring(xml).findall(".//{*}page")
    expected=Counter(case.get("markers",{}));found=Counter();outside=[];coords=[];distribution=[]
    matcher=re.compile(r"(?<![A-Za-z0-9])(?:"+"|".join(re.escape(k) for k in sorted(expected,key=len,reverse=True))+r")(?![A-Za-z0-9])") if expected else None
    for number,page in enumerate(pages,1):
        words=[];count=0
        width=float(page.attrib["width"]);height=float(page.attrib["height"])
        for word in page.findall(".//{*}word"):
            text=re.sub(r"DTECONTROL([0-9A-F]{4})END",lambda m:chr(int(m.group(1),16)),word.text or "");box=[float(word.attrib[k]) for k in ("xMin","yMin","xMax","yMax")]
            words.append([text,*box])
            matches=matcher.findall(text) if matcher else []
            found.update(matches);count+=len(matches)
            if matches and not(0<=box[0]<=box[2]<=width and 0<=box[1]<=box[3]<=height):outside.append([number,text,box])
        coords.append({"width":width,"height":height,"words":words});distribution.append(count)
    obs.update(pages=coords,marker_distribution=distribution,markers=dict(found),missing=dict(expected-found),extra=dict(found-expected),outside=outside)
    if run_command([tool("pdftoppm"),"-png","-r","144","input.pdf","page"],out,timeout=240):raise RuntimeError("pdftoppm failed")
    images=sorted(out.glob("page-*.png"),key=lambda f:int(re.search(r"-(\d+)\.png$",f.name).group(1)))
    obs["raster"]=[]
    for f in images:
        with Image.open(f) as im:
            rgb=im.convert("RGB")
            obs["raster"].append({"size":list(rgb.size),"rgb_sha256":digest(rgb.tobytes())})
    if len(images)!=len(pages):raise RuntimeError("PDF/page raster count mismatch")
    if case.get("duplicate_boundary"):
        if run_command([tool("pdftocairo"),"-svg","-f","2","-l","2","input.pdf","page-2.svg"],out):raise RuntimeError("SVG conversion failed")
        paths=Counter(json.dumps(e.attrib,sort_keys=True) for e in ET.parse(out/"page-2.svg").getroot().iter()
                      if e.tag.endswith("path") and "stroke-opacity:0.5" in e.attrib.get("style",""))
        obs["max_identical_transparent_strokes"]=max(paths.values(),default=0)
        obs["bug_present"]=obs["max_identical_transparent_strokes"]>=3
    obs["required_log_present"]=case.get("requires_log","") in log
    return obs
def validate(obs,case,rc,stable,runs,engine):
    errors=[]
    if case["kind"] in ("expected-error","known-error"):
        if not rc or not obs.get("error_present") or not obs["required_log_present"]:errors.append("dedicated error/required control missing")
        if case["kind"]=="expected-error":
            if obs["retries"]!=list(range(1,case["retry_attempts"]+1)):errors.append("retry sequence is not exactly 1..20")
            if obs["diagnostic_count"]!=1:errors.append("fatal diagnostic count")
        return errors
    if rc:errors.append("compiler returned "+str(rc))
    if not stable or runs>case["max_runs"]:errors.append("auxiliary convergence")
    allowed=case.get("expected_diagnostics",[])
    if isinstance(allowed,dict):allowed=allowed[engine]
    if obs["diagnostics"]!=allowed:errors.append("unexpected box diagnostics")
    for key in ("missing","extra","outside"):
        if obs.get(key):errors.append(key)
    if not obs["required_log_present"]:errors.append("required control missing")
    if case["kind"]=="known-bug" and not obs["bug_present"]:errors.append("XPASS: known behavior changed; review and update this case explicitly")
    return errors
def compare(observed,expected):
    return [key for key in sorted(set(observed)|set(expected)) if observed.get(key)!=expected.get(key)]
def build(case,engine,package_data,output):
    out=output/engine/case["id"]
    if out.exists():raise RuntimeError("Output case already exists: "+str(out))
    out.mkdir(parents=True)
    raw=(ROOT/case["fixture"]).read_bytes()
    if digest(raw)!=case["source_sha256"]:raise RuntimeError("Fixture checksum changed: "+case["id"])
    (out/"dirtreex.sty").write_bytes(package_data);(out/"input.tex").write_bytes(raw)
    if b"\\usepackage{parskip}" in raw:shutil.copy2(ROOT/"vendor/parskip/parskip.sty",out/"parskip.sty")
    if case["id"]=="gallery-gallery":shutil.copytree(REPO/"assets",out/"assets")
    if case.get("seed_aux"):shutil.copy2(ROOT/case["seed_aux"],out/"input.aux")
    env=os.environ.copy()
    env.update(TEXINPUTS=os.pathsep,max_print_line="10000")
    previous=None;stable=False;states=[];fatal=case["kind"] in ("expected-error","known-error")
    for n in range(1,(1 if fatal else case["max_runs"])+1):
        args=[tool(engine),"-recorder","-interaction=nonstopmode"]
        if case["kind"]!="expected-error":args.append("-halt-on-error")
        rc=run_command(args+["input.tex"],out,f"pass-{n}.stdout.txt",env,timeout=180)
        if rc or fatal:break
        state=auxiliary(out);states.append(state)
        if state==previous:stable=True;break
        previous=state
    if rc and not fatal:
        raise RuntimeError("Unexpected compile failure: "+(out/f"pass-{n}.stdout.txt").read_text(errors="replace")[-1400:])
    if "./dirtreex.sty" not in (out/"input.log").read_text(errors="replace"):raise RuntimeError("Isolated package load not confirmed")
    obs=observe(out,case)
    failures=validate(obs,case,rc,stable,n,engine)
    if not fatal:
        problems=final_log_errors((out/"input.log").read_text(encoding="utf8",errors="replace"))
        if problems:failures.append({"unresolved_or_missing_glyphs":problems})
    golden=ROOT/"expected"/engine/(case["id"]+".json.gz")
    if not golden.exists():failures.append("missing reviewed observation")
    else:
        differences=compare(obs,read_json(golden))
        if differences:failures.append({"changed_observations":differences})
    status="FAIL" if failures else "XFAIL" if case["kind"].startswith("known") else "PASS"
    result={"id":case["id"],"engine":engine,"status":status,"failures":failures,"runs":n,"stable":stable,
            "returncode":rc,"source_sha256":digest(package_data),"fixture_sha256":digest(raw),
            "marker_count":sum(obs.get("markers",{}).values()),"pages":len(obs.get("pages",[])),"aux_states":states}
    write_json(out/"observed.json",obs);write_json(out/"result.json",result)
    print(engine,case["id"],status,"runs="+str(n),flush=True)
    return result
def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--package",type=Path,default=REPO/"dirtreex.sty")
    parser.add_argument("--output",type=Path,default=ROOT/"work"/time.strftime("verify-%Y%m%d-%H%M%S"))
    parser.add_argument("--engines",nargs="+",choices=ENGINES,default=ENGINES)
    parser.add_argument("--cases",nargs="+",help="Exact IDs; explicit selection can include advisory cases")
    args=parser.parse_args()
    if len(args.engines)!=len(set(args.engines)):parser.error("Duplicate engine selection")
    try:
        cases=select_cases(read_json(ROOT/"cases.json"),args.cases)
        required=set(args.engines)|{"pdftotext","pdftoppm","kpsewhich"}
        if any(c.get("duplicate_boundary") for c in cases):required.add("pdftocairo")
        for name in sorted(required):tool(name)
        help_text=subprocess.run([tool("pdftotext"),"-h"],capture_output=True,text=True,errors="replace")
        if "-bbox-layout" not in help_text.stdout+help_text.stderr:
            raise ValueError("pdftotext must provide Poppler -bbox-layout; check DIRTREEX_TEX_BIN")
    except (ValueError,FileNotFoundError) as exc:parser.error(str(exc))
    package=args.package.resolve()
    if not package.is_file():parser.error("Package file does not exist")
    package_data=package.read_bytes()  # One immutable source snapshot for the entire run.
    output=args.output.resolve()
    if output.exists():parser.error("Choose a new output path")
    if output==ROOT or ROOT.is_relative_to(output):
        parser.error("Output must not contain the test inputs")
    if output.is_relative_to(REPO) and not output.is_relative_to(ROOT/"work"):
        parser.error("Repository output must be under tests/work")
    cache=Path(os.environ.get("DIRTREEX_TEST_CACHE",ROOT/"work/tex-cache")).resolve()
    cache.mkdir(parents=True,exist_ok=True)
    # LuaTeX on Windows may not write through a Unicode path; retain the
    # configured TeX user cache as the shared fallback, as in the baseline.
    fallback=subprocess.check_output([tool("kpsewhich"),"--var-value=TEXMFVAR"],text=True).strip()
    os.environ["TEXMFCACHE"]=cache.as_posix()+os.pathsep+fallback
    output.mkdir(parents=True)
    def worker(engine):
        results=[]
        for case in cases:
            try:
                result=build(case,engine,package_data,output)
            except Exception as exc:
                result={"id":case["id"],"engine":engine,"status":"FAIL","failures":[str(exc)]}
                print(engine,case["id"],"FAIL",str(exc)[-250:],flush=True)
            results.append(result)
        return results
    started=time.time()
    with ThreadPoolExecutor(max_workers=len(args.engines)) as pool:
        results=[r for batch in pool.map(worker,args.engines) for r in batch]
    summary={"package_sha256":digest(package_data),"seconds":round(time.time()-started,2),
             "counts":dict(Counter(r["status"] for r in results)),"results":results,
             "failures":[r for r in results if r["status"]=="FAIL"]}
    write_json(output/"summary.json",summary)
    print("SUMMARY",json.dumps({"counts":summary["counts"],"seconds":summary["seconds"],"output":str(output)}),flush=True)
    if summary["failures"]:sys.exit(1)

if __name__=="__main__":main()
