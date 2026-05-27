# dirtreex

A self-contained LaTeX package for rendering directory trees inside an optionally breakable, fully styleable frame. Built directly on TikZ and `zref` — no `tcolorbox` or classic `dirtree` underneath.

## Features

- **Auto-tracked depth.** Nest `\dir` and `\file` as deeply as you want; the package derives the depth from the nesting — no per-entry depth argument.
- **Sharp or rounded elbows**, configurable per tree or per entry via a single `elbow radius` key (`0pt` = sharp, any positive length = rounded arc).
- **Per-entry overrides** for line colour, line width, and elbow radius.
- **Breakable frame.** The border, background fill, and every pending `│` column continue seamlessly across page boundaries.
- **CJK-friendly.** Works out of the box with `ctex` + LuaLaTeX.
- **Zero shell-escape, no external tools, no Python helpers.**

---

## Table of contents

1. [Requirements](#1-requirements)
2. [Installation](#2-installation)
3. [Quick start](#3-quick-start)
4. [Entries: `\dir` and `\file`](#4-entries-dir-and-file)
5. [Verbatim names: `\verbdir` and `\verbfile`](#5-verbatim-names-verbdir-and-verbfile)
6. [Environment options](#6-environment-options)
   - 6.1 [Top-level keys](#61-top-level-keys)
   - 6.2 [The `box` family](#62-the-box-family)
   - 6.3 [The `pagebreak` family](#63-the-pagebreak-family)
   - 6.4 [Per-entry overrides](#64-per-entry-overrides)
7. [Cross-page behaviour](#7-cross-page-behaviour)
8. [Example gallery](#8-example-gallery)
9. [Compilation](#9-compilation)
10. [Troubleshooting](#10-troubleshooting)
11. [Limitations](#11-limitations)
12. [Project files](#12-project-files)
13. [Contact](#13-contact)
14. [License](#14-license)

---

## 1. Requirements

| Component | Notes |
| :--- | :--- |
| LuaLaTeX *or* pdfLaTeX | LuaLaTeX is required if your tree contains CJK or any non-Latin-1 text. |
| e-TeX extensions (`\numexpr`, `\dimexpr`, `\ifcsname`) | Present in every modern TeX engine (pdfTeX, XeTeX, LuaTeX) and guaranteed by the package's format requirement (`LaTeX2e` `2020/10/01` or later). |
| TikZ 3.x | The `backgrounds` library is loaded automatically. |
| `xcolor` | Both `color!mix!color` and `HTML` colour models are accepted. |
| `pgfkeys` | Option parsing. |
| `zref-abspage` | Cross-page anchoring. |
| `xparse` (auto-loaded by LaTeX2e) | `\NewDocumentEnvironment` / `\NewDocumentCommand`, plus the `v` (verbatim) argument type used by `\verbdir` / `\verbfile`. |

No `-shell-escape`, no external tools, no Python helper.

---

## 2. Installation

1. Copy `dirtreex.sty` into the same directory as your document, **or** install it under `texmf-local/tex/latex/dirtreex/` and run `mktexlsr` (TeX Live) / the MiKTeX equivalent.
2. In your preamble:

   ```latex
   \usepackage{dirtreex}
   ```

---

## 3. Quick start

The smallest possible document:

```latex
\documentclass{article}
\usepackage{dirtreex}

\begin{document}
\begin{dirtreex}
  \dir{project}{root}{
    \dir{src}{source}{
      \file{main.py}{entry point}
      \file{util.py}{helpers}
    }
    \file{README.md}{documentation}
  }
\end{dirtreex}
\end{document}
```

This produces a framed tree where each line is `<name> … <comment>` joined with a dot-leader, directory names receive a trailing `/`, and the elbow connectors (`├`, `└`, `│`) are laid out automatically.

---

## 4. Entries: `\dir` and `\file`

```latex
\dir[<entry options>]{<name>}{<comment>}{<children>}
\file[<entry options>]{<name>}{<comment>}
```

- **`<name>`** is typeset in `\ttfamily`. For `\dir`, a trailing `/` is appended automatically — write `src`, not `src/`.
- **`<comment>`** is typeset in `\rmfamily` and joined to `<name>` with a dot leader. Pass `{}` for no comment (the dot leader also disappears).
- **`<children>`** is a run of further `\dir` / `\file` calls. You do **not** supply the depth — the package tracks it from the nesting.
- **`<entry options>`** are optional and described in §6.4.

### 4.1 Multi-line comments

A comment may contain line breaks; the whole block is packed so its combined height stays rectangular, keeping the connector column straight:

```latex
\file[line color=purple]{Makefile}{
  build script\\
  (multi-line comment, stays aligned)
}
```

### 4.2 Empty subtrees and empty comments

Both are legal:

```latex
\dir{empty-dir}{}{}                % no comment, no children
\dir{has-comment}{with comment}{}  % comment but no children
```

### 4.3 Multiple trees on one page

Simply place several `dirtreex` environments back-to-back. Each environment has its own `zref` namespace, so their cross-page bookkeeping never collides.

### 4.4 Customising entry-name typesetting (`\DirtreexFormatName`)

`\DirtreexFormatName` is a public hook that controls how each entry name is typeset. The default expansion is just the stored name plus a trailing `/` for directories — exactly what every example above produces.

Override it with `\renewcommand` to inject icons, prefixes, or styling. The hook receives the 1-based entry index as `#1`, and `\DirtreexGetField{idx}{slot}` reads any stored field for that index:

- `\DirtreexGetField{#1}{n}` — the entry name (the second mandatory argument of `\dir` / `\file`).
- `\DirtreexGetField{#1}{t}` — `1` for directories, `0` for files.

**Example — tag every directory with a `[DIR]` prefix:**

```latex
\renewcommand{\DirtreexFormatName}[1]{%
  \ifnum\DirtreexGetField{#1}{t}=1 [DIR]\fi
  \DirtreexGetField{#1}{n}%
  \ifnum\DirtreexGetField{#1}{t}=1 /\fi
}
```

**Constraints.** The replacement runs inside the row's name vbox under the body's font. It must respect the row's `\hsize` and leave the caller's `\strut` intact; anything that adds vertical material (for example a `\parbox` with its own depth) will pull the entry's connector out of alignment.

**Stability.** `\DirtreexFormatName`'s single-argument convention and the `\DirtreexGetField{#1}{n}` / `\DirtreexGetField{#1}{t}` accessors are committed public surfaces — overrides built around them keep compiling across minor versions. Only slot keys `n` (entry name) and `t` (type flag: `1` for directories, `0` for files) are guaranteed stable; other slot keys exist internally but are not part of the public surface and may change.

---

## 5. Verbatim names: `\verbdir` and `\verbfile`

`\dir` and `\file` accept LaTeX-tokenised name arguments — paths containing `_`, `$`, `&`, `#`, `^`, `~`, `%`, or `\` need to be escaped (`\_`, `\$`, etc.) or wrapped in `\detokenize{}`. For paths where this is inconvenient, `dirtreex` provides two verbatim variants:

```latex
\verbdir[<entry options>]|<path>|{<comment>}{<children>}
\verbfile[<entry options>]|<path>|{<comment>}
```

The path is read with xparse's `v` (verbatim) specifier: the first non-letter, non-space character after the macro name is the opening delimiter, the matching delimiter closes the path, and every byte in between is captured at catcode 12 ("other"). Comment and children retain full LaTeX catcodes — you can still write `$x^2$`, `\textbf{...}`, `\\` inside the comment, and nested `\dir` / `\file` / `\verbdir` / `\verbfile` inside the children block work normally.

### 5.1 Example

```latex
\begin{dirtreex}
  \verbdir|src/$ENV/data_v2|{environment-keyed data root}{%
    \verbfile|users_2026-01.parquet|{snapshot}%
    \verbfile|conf{prod}.yaml|{production config}%
  }
\end{dirtreex}
```

### 5.2 Restrictions

- **The chosen delimiter cannot appear inside the path.** Pick one that doesn't collide:

  ```latex
  \verbfile|a/b|{...}        % | as delimiter
  \verbfile+a|b+{...}        % + as delimiter, | survives in the path
  \verbfile/a|b+c/{...}      % / as delimiter, | and + survive
  ```

  **Delimiter collisions corrupt SILENTLY.** Writing `\verbfile|foo|bar|{c}` makes xparse take `|foo|` as the name and `b` as the comment, leaving `ar|{c}` as stray tokens — no error fires. Pick a delimiter that does not appear in any of your paths.

- **The verbatim argument must be readable directly from source.** If you wrap `\verbfile|...|` inside another macro that captures its argument as a token list (e.g., a user-side `\newcommand` that takes `+m`), the path is tokenised at the wrapper's call site — before `\verbfile` can re-catcode it — and the verbatim semantics are lost. The children block of `\dir` and `\verbdir` does **not** suffer from this: it is a live TeX group, not a captured token list, so `\verbfile|...|` written inside `\dir{...}{...}{ ... }` works as expected.

- **Encoding.** Under T1 / TU encoding (LuaLaTeX default, or pdfLaTeX with `\usepackage[T1]{fontenc}`), every cat-12 character renders as its literal glyph in monospace. If you target legacy OT1 encoding, the special characters `_` and `&` may require explicit `\char` mapping — pick an encoding that supports them.

### 5.3 Where verbatim names are useful

- Paths with parameter substitutions (`$ENV`, `${VAR}`).
- Windows paths (`C:\Users\foo`).
- Configuration filenames (`conf{prod}.yaml`, `app_$STAGE.toml`).
- Database identifiers (`schema$ext.table_v2`).
- Log file patterns (`err_$.log`, `out_%Y-%m-%d.log`).

---

## 6. Environment options

Options go inside `[...]` on `\begin{dirtreex}` and are parsed with `pgfkeys`. Spaces around `=` are allowed.

### 6.1 Top-level keys

| Key | Default | Meaning |
| :--- | :--- | :--- |
| `fontsize` | `\small` | Size command applied to the tree body. Use any length-free size macro: `\tiny`, `\small`, `\normalsize`, …, `\Large`. |
| `line color` | `black` | Default colour for connectors and cross-page extensions. Accepts any `xcolor` expression. |
| `line width` | `0.4pt` | Default rule width for all connectors. |
| `elbow radius` | `0pt` | Elbow geometry. `0pt` (the default) gives sharp `└`/`├` right angles; any positive length gives rounded arcs of that radius. Clamped against `0.5\baselineskip` and against `line width` for legibility. |
| `box` | see §6.2 | Frame settings. |
| `pagebreak` | see §6.3 | Page-break settings. |

### 6.2 The `box` family

Pass as a sub-list: `box = { … }`.

| Subkey | Default | Meaning |
| :--- | :--- | :--- |
| `true` / `false` | `true` | Draw the frame at all. `box=false` leaves the tree bare. |
| `corners` | `0pt` | Corner radius. A single value applies to all four corners; a four-value list is TL, TR, BR, BL. |
| `border color` | `black` | |
| `border width` | `0.4pt` | |
| `background color` | `white` | Named colour, `color!mix!color`, or `HTML`. |
| `margin` | `6pt` | Padding between the border and the tree content. Single value = uniform; a four-value list is T, R, B, L (asymmetric padding is supported in both single and breakable output). |

Example:

```latex
\begin{dirtreex}[
  box = {
    true, corners = 6pt, border color = purple,
    border width = 1pt, background color = purple!5,
    margin = {2pt, 20pt, 10pt, 4pt}
  }
]
```

### 6.3 The `pagebreak` family

| Subkey | Default | Meaning |
| :--- | :--- | :--- |
| `true` / `false` | `true` | Allow the frame to break across pages. When `false`, tall trees spill past the page; they are **not** truncated. |
| `box break at` | `0pt` | Vertical gap between the frame's torn edge and the page boundary. Single value applies to both sides of every break; two values = `first-piece-bottom, next-piece-top`. |
| `tree break at` | `1em` (`0pt` when `box=false`) | Same, but applied to the tree's extension rules rather than to the border itself. Useful when the frame should reach the page edge while the internal tree lines pull back. |

### 6.4 Per-entry overrides

Any `\dir` or `\file` can take the same `line color`, `line width`, and `elbow radius` keys. They override the environment-level defaults **for that entry's connector only**:

```latex
\dir[line color = blue]{src}{source}{
  \file[line color = red, line width = 1.5pt]{old.py}{deprecated}
  \file[line color = green!60!black, elbow radius = 0pt]{new.py}{sharp}
}
```

Each entry owns its own `└`-shape. The vertical line continuing **down** from that entry's arm toward the next sibling carries the **next sibling's** colour — so two siblings with different colours share a column that changes colour at arm level (sharp) or at arc-top (rounded).

---

## 7. Cross-page behaviour

When the finished tree is taller than the space left on the current page, `dirtreex` cuts it into pieces and emits them on consecutive pages. Each piece is drawn as a self-contained TikZ `\node`, so the border, background, and all active `│` columns continue across the break.

Two compile passes are required the **first** time the break structure settles (or any time it shifts). The initial pass records absolute page numbers via `zref-abspage`; the second pass reads them so that the connector of each piece-1 entry knows it is not actually anchored to whatever sits above it in the entry list.

Concretely:

- Every piece after the first starts with a `0.5\baselineskip` leader of empty space, so the first visible entry shows a `│` above its elbow matching the inter-sibling spacing used on a single page.
- Bottom extensions of every active column continue down to the first piece's bottom edge.
- Top extensions re-appear in the second (and any subsequent) piece, matching the column colours and widths the previous piece ended with.
- The closing piece always spans the configured content width, even when the final `\vsplit` leaves a void remainder (so the bottom border never collapses to a corner sliver).

---

## 8. Example gallery

The snippets below are self-contained: drop any of them into a document with `\usepackage{dirtreex}` and they compile. For a much broader set of worked examples — every option, every combination, every edge case — see `dirtreex_examples.tex` in the repository root.

### 8.1 Defaults

```latex
\begin{dirtreex}
  \dir{project}{default settings}{
    \file{a.txt}{file A}
    \file{b.txt}{file B}
    \dir{sub}{subdirectory}{
      \file{c.txt}{file C}
    }
  }
\end{dirtreex}
```

### 8.2 Rounded elbows

```latex
\begin{dirtreex}[elbow radius = 3pt]
  \dir{round3}{rounded 3pt}{
    \file{a.txt}{}
    \dir{sub1}{subdir 1}{
      \file{b.txt}{}
      \dir{sub2}{subdir 2}{\file{c.txt}{}}
    }
    \file{d.txt}{}
  }
\end{dirtreex}
```

### 8.3 Per-branch colours

```latex
\begin{dirtreex}[
  elbow radius = 3pt,
  box = {
    true, border color = black,
    background color = white, margin = 6pt
  }]
  \dir{project}{}{
    \dir[line color = blue]{src}{blue: source code}{
      \file[line color = red]{old.py}{red: deprecated}
      \file[line color = green!60!black]{new.py}{green: new}
    }
    \dir[line color = orange]{docs}{orange: documentation}{
      \file{api.md}{}
    }
    \file[line color = purple]{Makefile}{purple}
  }
\end{dirtreex}
```

### 8.4 Thick lines

```latex
\begin{dirtreex}[
  line color = red!70!black, line width = 1pt,
  box = {
    true, border color = red!80!black,
    border width = 2pt, background color = red!5
  }]
  \dir{bold}{thick-line test}{
    \file{a.txt}{}
    \dir{sub}{}{\file{b.txt}{}}
  }
\end{dirtreex}
```

### 8.5 A tree that pages across

```latex
\begin{dirtreex}[
  elbow radius = 3pt,
  box = {
    true, border color = black,
    background color = white, margin = 6pt
  }]
  \dir{cross-page}{long tree}{
    \dir[line color = red]{red-branch}{}{
      \file{r1.txt}{}
      % ... add enough files to overflow
    }
    \dir[line color = blue]{blue-branch}{}{file{b1.txt}{}}
  }
\end{dirtreex}
```

The border, background, and all active `│` columns continue onto the next page; the first visible entry on that page shows a full `│` stem above its elbow. Colours are carried across the page break seamlessly.

### 8.6 Asymmetric margin

```latex
\begin{dirtreex}[
  box = {margin = {2pt, 20pt, 10pt, 4pt},  % T, R, B, L
         border color = teal, background color = teal!5}]
  \dir{root}{}{
    \file{a}{}
    \file{b}{}
  }
\end{dirtreex}
```

---

## 9. Compilation

```bash
lualatex -interaction=nonstopmode yourdoc.tex
lualatex -interaction=nonstopmode yourdoc.tex  # 2nd pass for zref
```

- The first pass records the absolute page number of every entry via `zref-abspage`.
- The second pass reads those labels so the first entry of each piece can distinguish "I follow an entry on the same page" (draw a long connector) from "I start a new piece" (draw a short stub and rely on the top extension to fill the column).

If you have not changed anything that moves a break point, a single pass is enough. For a fresh document, run two.

`latexmk` works: the package emits a `Package dirtreex Warning: Rerun LaTeX...` at `\end{document}` whenever any `zref` lookup was still unresolved, and `latexmk`'s default rerun detector picks that up automatically.

---

## 10. Troubleshooting

| Symptom | Likely cause | Fix |
| :--- | :--- | :--- |
| First entry on a continuation page has no `│` above its elbow | Only one compile pass has run so far | Run LaTeX again. The `Rerun LaTeX...` warning at `\end{document}` is already asking you to. |
| Vertical columns stop halfway down the last piece | Same cause — `zref` has not seen the break yet | Run LaTeX again. |
| CJK characters render as `□` or are missing | Wrong engine | Compile with LuaLaTeX (plus `ctex`). |
| `! Package dirtreex Error: \dir used outside dirtreex environment` (same for `\file`) | A stray `\dir` or `\file` that is not inside `\begin{dirtreex}…\end{dirtreex}` | Wrap the call in a `dirtreex` environment. |
| `! Package dirtreex Error: parsefour expects 1 or 4 comma-separated values` (or `parsetwo expects 1 or 2 …`) | `corners`, `margin`, `box break at`, or `tree break at` given with the wrong arity | Pass either a single value or the full set (four for `corners`/`margin`, two for the break-at keys). Remember the enclosing braces: `margin = {2pt, 4pt, 6pt, 8pt}`, not `margin = 2pt, 4pt, 6pt, 8pt`. |
| `Package dirtreex Warning: \dte@findanchor hit the recursion floor at entry N` (once per env) | The tree's first top-level entry has depth > 0, or an outer `\begingroup` shadowed `\dte@depth` and produced an inverted depth sequence | Ensure the env body starts with a depth-0 `\dir` / `\file` (or `\verbdir` / `\verbfile`). The connector for the affected entry is snapped to a cross-page-stub variant as a graceful fallback, so the build still succeeds — the warning is purely diagnostic. |

---

## 11. Limitations

- Extremely small `box.margin` combined with a very large `elbow radius` crowds the corner; the internal clamp (`connE ≤ 0.5\baselineskip`) keeps things legible but will not rescue pathological values.
- The anchor search compares `zref` page numbers as digit strings. Safe today; be aware if a future `zref` change makes that field non-numeric.
- No built-in numbering or hyperlinks. The package focuses on connector geometry; for icons or other entry-name decoration use the `\DirtreexFormatName` hook (§4.4), and wrap the tree in a `minipage` if you need decoration around the whole frame.

---

## 12. Project files

| Path | What it is |
| :--- | :--- |
| `dirtreex.sty` | The package — a single self-contained file. |
| `dirtreex_examples.tex` | Worked examples covering the full feature surface. Compile with `lualatex dirtreex_examples.tex` (twice, for `zref` to settle) to see every option in action. |
| `README.md` | This documentation. |
| `LICENSE` | The LaTeX Project Public License 1.3c. |

---

## 13. Contact

- **Maintainer:** CloudCauldron
- **Email:** <w.yizheng@qq.com>
- **Repository / issues:** <https://github.com/CloudCauldron/dirtreex>

Bug reports, feature suggestions, and patches are welcome via either channel.

---

## 14. License

Released under the [LaTeX Project Public License, version 1.3c](https://www.latex-project.org/lppl.txt) (`LPPL-1.3c`); see [`LICENSE`](LICENSE) for the full text. Maintenance status is `author-maintained`; the Current Maintainer is CloudCauldron (<w.yizheng@qq.com>).

---

## 15. About the Development

This project includes code generated with the assistance of AI tools. All such code has been reviewed and integrated by the maintainer.
