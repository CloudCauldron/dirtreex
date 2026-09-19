# Regression tests

Run from the repository root using **Windows-native Git Bash**:

~~~bash
export DIRTREEX_TEX_BIN='C:/texlive/2026/bin/windows'
uv run --python 3.12 tests/run.py
~~~

Adjust the tool directory for your installation. It must contain the LaTeX engines and **Poppler** tools (pdftotext with -bbox-layout, pdftoppm, pdftocairo), plus kpsewhich. Without the override, tools are resolved from PATH; an Xpdf pdftotext is not compatible. The script declares its pinned Pillow dependency for uv.

The default run compares **114 cases on three engines (342 configurations)** against reviewed observations. The unsupported nested-environment/capture case (S1) is advisory and excluded by default. Existing runtime and release metadata are unchanged.

## Focused runs

~~~bash
uv run --python 3.12 tests/run.py \
  --engines lualatex pdflatex xelatex \
  --cases regression-bare-start regression-framed-start page-start-transitions
~~~

Use exact IDs from [cases.json](cases.json) or [COVERAGE.md](COVERAGE.md). An explicit selection may include advisory known-capture-boundary; its known behavior is reported as XFAIL. Unknown/duplicate IDs or duplicate engines are errors. There are no CLI wildcard, profile or exclusion options.

--package selects an alternative dirtreex.sty; the default is the repository source. The runner freezes its bytes once for the entire run, so every fixture tests the same revision. --output selects a new results directory; existing directories are never overwritten.

The [coverage map](COVERAGE.md) traces fixes from cba577a through a366fc7 and the later capture, geometry, lifecycle and topology contracts.

## Requirements and results

The qualified reference toolchain is recorded in [baseline.json](baseline.json): native Windows TeX Live 2026, LuaHBTeX 1.24.0, pdfTeX 1.40.29, XeTeX 0.999998, Poppler 25.02.0 and Pillow 12.0.0. Exact glyph coordinates and RGB hashes depend on matching fonts and tools. A different installation can run the suite, but a difference needs investigation before changing references.

Required TeX packages/classes are supplied by the qualified TeX Live installation. The small bundled parskip source distribution preserves that dependency's reviewed behavior and license. The gallery and its images are read from the repository root; they are not duplicated here.

Results go to ignored tests/work/verify-<timestamp>/, grouped by engine and case. Each group contains input/package copies, logs, PDF/PNGs, extracted positions, observed.json and result.json. summary.json reports the source identity and every outcome; any FAIL gives a nonzero exit status.

The shared font cache defaults to tests/work/tex-cache; DIRTREEX_TEST_CACHE can redirect it. The configured TeX user cache is retained as fallback for LuaTeX installations unable to write through Unicode paths. Caches are shared across cases, never copied per fixture.

PASS includes intentional diagnostic controls: ten cases must terminate on exactly the twentieth unconsumed deferral; the Large-font and two impossible-size cases must retain their exact recorded box warnings. Ordinary cases reject all overfull/underfull boxes, unresolved references and missing glyphs. Isolated successful cases converge within two passes; the clean gallery within three.

For runner safeguards without compiling TeX:

~~~bash
uv run --no-project --python 3.12 --with pillow==12.0.0 \
  python -m unittest discover -s tests -p test_runner.py
~~~

## Reviewing a reference change

1. State the intended behavior and select affected cases. Preserve the old expectation and source identity.
2. Run the tests. Inspect semantic assertions, retention/effects, diagnostics, coordinates and generated images; a changed observation is a review event.
3. Only after review, write the accepted observed.json as expected/<engine>/<case>.json.gz using UTF-8 JSON and deterministic gzip (mtime=0), then update baseline.json provenance/hash. Do not replace unrelated expectations.
4. Re-run the affected cases and the complete applicable suite. Source changes, reference changes and publication remain distinct review actions.

The runner has no automatic bless, historical import or bootstrap mode. Compressed files preserve all observation data; no visual or numerical assertions were discarded to reduce repository size. To inspect one:

~~~bash
uv run --python 3.12 python -c \
  'import gzip,json; print(json.dumps(json.loads(gzip.open("tests/expected/pdflatex/regression-bare-start.json.gz","rt",encoding="utf-8").read()),indent=2,ensure_ascii=False))'
~~~

Update a fixture's source_sha256 in cases.json when intentionally changing its input. The gallery checksum also changes after a header-only edit; establish body equivalence or revalidate output instead of automatically recording new reference images.

The preserved evidence archive is not an execution dependency. S1 remains unsupported and no CI service or production-package dependency is introduced.
