# dirtreex

A self-contained LaTeX package for rendering directory trees inside an optionally breakable, fully styleable frame. Built directly on TikZ and `zref` — no `tcolorbox` or classic `dirtree` underneath.

## Features

- **Auto-tracked depth.** Nest `\dir`, `\file`, and `\archive` as deeply as you want; the package derives the depth from the nesting — no per-entry depth argument.
- **Sharp or rounded elbows**, configurable per tree or per entry via a single `elbow radius` key (`0pt` = sharp, any positive length = rounded arc).
- **Per-entry overrides** for icons, line colour, line width, line style, and elbow radius.
- **Breakable frame.** The border, background fill, and every pending `│` column continue seamlessly across page boundaries.
- **CJK-friendly.** Works out of the box with `ctex` + LuaLaTeX.
- **Zero shell-escape, no external tools, no Python helpers.**

---

## Table of contents

1. [Requirements](#1-requirements)
2. [Installation](#2-installation)
3. [Quick start](#3-quick-start)
4. [Entries: `\dir`, `\file`, and `\archive`](#4-entries-dir-file-and-archive)
5. [Verbatim names: `\verbdir`, `\verbfile`, and `\verbarchive`](#5-verbatim-names-verbdir-verbfile-and-verbarchive)
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
| LuaLaTeX, pdfLaTeX or XeLaTeX | For CJK, use a suitable font setup, such as `ctex` with LuaLaTeX. |
| e-TeX extensions (`\numexpr`, `\dimexpr`, `\ifcsname`) | Present in every modern TeX engine (pdfTeX, XeTeX, LuaTeX) and guaranteed by the package's format requirement (`LaTeX2e` `2020/10/01` or later). |
| TikZ 3.x | The `backgrounds` library is loaded automatically. |
| `xcolor` | Use colour names or expressions such as `blue!50!black`. Define HTML colours first, for example `\definecolor{accent}{HTML}{336699}`. |
| `pgfkeys` | Option parsing. |
| `zref-abspage` | Absolute page tracking; PGF positions distinguish standard two-column output. |
| Document commands (LaTeX kernel) | `\NewDocumentEnvironment` / `\NewDocumentCommand`, plus the `v` (verbatim) argument type used by `\verbdir` / `\verbfile` / `\verbarchive`. |

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

## 4. Entries: `\dir`, `\file`, and `\archive`

```latex
\dir    [<entry options>]{<name>}{<comment>}{<children>}
\file   [<entry options>]{<name>}{<comment>}
\archive[<entry options>]{<name>}{<comment>}{<children>}
```

- **`<name>`** is typeset in `\ttfamily`. For `\dir`, a trailing `/` is appended automatically — write `src`, not `src/`. `\file` and `\archive` render the name as-is.
- **`<comment>`** is typeset in `\rmfamily` and joined to `<name>` with a dot leader. Pass `{}` for no comment (the dot leader also disappears).
- **`<children>`** is a run of further `\dir` / `\file` / `\archive` calls. `\file` has no children block. You do **not** supply the depth — the package tracks it from the nesting.
- **`<entry options>`** are optional and described in §6.4.

`\archive` is a container entry: it accepts a children block, so its contents indent and connect inside the tree, and its name is rendered as-is (no path separator appended). Use it for archive-like containers (`.tar.gz`, `.zip`, `.jar`, …) or for any container whose name should not carry a trailing `/`. Set `icon={...}` (§6.4) to choose an icon for an individual entry. For automatic formatting by entry type, override `\DirtreexFormatName` (§4.4) and dispatch on the entry's `t` slot.

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

`\DirtreexFormatName` is a public hook that controls how each entry name is typeset. The default formatter prints the optional icon with a nonbreaking `0.5em` gap, then the stored name plus a trailing `/` for directories. An omitted or empty `icon={}` adds no prefix or gap.

Override it with `\renewcommand` to inject icons, prefixes, or styling. The hook receives the 1-based entry index as `#1`, and `\DirtreexGetField{idx}{slot}` reads any stored field for that index:

- `\DirtreexGetField{#1}{n}` — the entry name (the first mandatory argument of `\dir` / `\file` / `\archive`).
- `\DirtreexGetField{#1}{t}` — `1` for directories, `0` for files, `2` for archives.
- `\DirtreexGetField{#1}{i}` — the raw icon code, empty when omitted; the name field stays unchanged.

A replacement hook controls the entire name, including icon rendering. Save and call the original formatter to retain its icon handling, gap, and directory slash when adding your own decoration.

**Example — tag every directory with a `[DIR]` prefix while keeping the default formatter:**

```latex
\let\OriginalDirtreexFormatName\DirtreexFormatName
\renewcommand{\DirtreexFormatName}[1]{%
  \ifnum\DirtreexGetField{#1}{t}=1 [DIR]\fi
  \OriginalDirtreexFormatName{#1}%
}
```

**Example — three-way icon dispatch on `t`:**

```latex
\renewcommand{\DirtreexFormatName}[1]{%
  \ifcase\DirtreexGetField{#1}{t}%
    [F]\space\DirtreexGetField{#1}{n}%             % t=0 file
  \or
    [D]\space\DirtreexGetField{#1}{n}/%            % t=1 directory
  \or
    [A]\space\DirtreexGetField{#1}{n}%             % t=2 archive
  \fi
}
```

Swap the bracketed tags for icons from your icon package of choice (`\faFolder`, `\faFile`, `\faFileArchive`, …) to get the same dispatch with glyphs.

**Constraints.** The replacement runs inside the row's name vbox under the body's font. It must respect the row's `\hsize` and leave the caller's `\strut` intact; anything that adds vertical material (for example a `\parbox` with its own depth) will pull the entry's connector out of alignment.

**Stability.** `\DirtreexFormatName`'s single-argument convention and the `\DirtreexGetField` accessors for `n` (entry name), `t` (type flag), and `i` (icon code) are committed public surfaces — overrides built around them keep compiling across minor versions. Other slot keys exist internally but are not part of the public surface and may change.

---

## 5. Verbatim names: `\verbdir`, `\verbfile`, and `\verbarchive`

`\dir`, `\file`, and `\archive` accept LaTeX-tokenised name arguments — paths containing `_`, `$`, `&`, `#`, `^`, `~`, `%`, or `\` need to be escaped (`\_`, `\$`, etc.) or wrapped in `\detokenize{}`. For paths where this is inconvenient, `dirtreex` provides three verbatim variants:

```latex
\verbdir    [<entry options>]|<path>|{<comment>}{<children>}
\verbfile   [<entry options>]|<path>|{<comment>}
\verbarchive[<entry options>]|<path>|{<comment>}{<children>}
```

Each verbatim variant pairs with the same-shape regular command: `\verbdir` mirrors `\dir` (children block, trailing `/`), `\verbfile` mirrors `\file` (no children), and `\verbarchive` mirrors `\archive` (children block, no trailing `/`).

The path uses the LaTeX kernel's `v` (verbatim) argument type. It accepts two matching delimiters other than `%`, `\`, `#`, braces or a space, or a braced form such as `\verbfile{path.txt}{comment}`. ASCII letters retain their category; the usual special characters become literal characters, while spaces and tabs remain active tokens. Non-ASCII character categories depend on the engine: active in 8-bit engines, letter or other in Unicode engines.

Comment and children retain full LaTeX catcodes — you can still write `$x^2$`, `\textbf{...}` and `\\` inside the comment, and nested `\dir` / `\file` / `\archive` / `\verbdir` / `\verbfile` / `\verbarchive` inside the children block work normally.

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

  **Delimiter collisions corrupt SILENTLY.** Writing `\verbfile|foo|bar|{c}` makes the verbatim scanner take `|foo|` as the name and `b` as the comment, leaving `ar|{c}` as stray tokens — no error fires. Pick a delimiter that does not appear in any of your paths.

- **The verbatim argument must be readable directly from source.** If you wrap `\verbfile|...|` inside another macro that captures its argument as a token list (e.g., a user-side `\NewDocumentCommand` with an `m` or `+m` argument), the path is tokenised at the wrapper's call site — before `\verbfile` can re-catcode it — and the verbatim semantics are lost. The children block of `\dir` and `\verbdir` does **not** suffer from this: it is a live TeX group, not a captured token list, so `\verbfile|...|` written inside `\dir{...}{...}{ ... }` works as expected.

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
| `dotfill color` | inherited | Colour of the leader between an entry name and its comment. Accepts an `xcolor` expression; inherits the current text colour when omitted. |
| `dotfill command` | `\dotfill` | TeX code that fills the gap before a comment. Use `\hrulefill` for a solid rule, `\hfill` for a blank gap, or a custom leader with `\hfill` stretch. |
| `line color` | `black` | Default colour for connectors and cross-page extensions. Accepts any `xcolor` expression. |
| `line width` | `0.4pt` | Default rule width for all connectors. |
| `line style` | `solid` | Dash pattern for every connector segment styled by this entry. Accepts any TikZ line-style token — `solid`, `dashed`, `dotted`, `densely dashed`, `loosely dashed`, `densely dotted`, `loosely dotted`, `dash dot`, `dash dot dot`, … — or a comma-separated TikZ option list such as `dash pattern={on 3pt off 2pt},dash phase=1pt`. `solid` keeps the primitive `\vrule` fast path; any other value routes that segment through TikZ. Propagates to the entry's own elbow, the upper-half of its own-depth pass-through column, and (for the next sibling at each active depth) the lower-half pass-through and full pure-pass-through trunks, plus the matching cross-page extension rules. |
| `elbow radius` | `0pt` | Elbow geometry. `0pt` (the default) gives sharp `└`/`├` right angles; any positive length gives rounded arcs of that radius. Clamped against `0.5\baselineskip` and the horizontal connector arm length for legibility. |
| `box` | see §6.2 | Frame settings. |
| `pagebreak` | see §6.3 | Page-break settings. |

Enclose comma-separated `line style` options in braces. A macro may supply the list; conditional selection of key–value lists must finish before returning the selected keys. The stored keys are applied in normal TikZ order; per-entry styles retain capture-time expansion.

The dotfill options apply to all nonempty comments in that environment. The leader's colour and any declarations in its command are local to the leader; names and comments retain their own formatting. Explicit `\\` continuations keep their right alignment, with a leader only before the first line.

```latex
\begin{dirtreex}[dotfill color=blue!60!black,
                dotfill command=\hrulefill]
  \dir{project}{root}{
    \file{main.py}{entry point}
    \file{LICENSE}{}
  }
\end{dirtreex}
```

Custom leader commands are evaluated in the tree's font at rendering time. Use `\hfill` stretch to preserve comment alignment, and keep the leader within the normal text height. See the comment-leader section of `dirtreex_examples.tex` for a custom dashed pattern.

### 6.2 The `box` family

Pass as a sub-list: `box = { … }`.

| Subkey | Default | Meaning |
| :--- | :--- | :--- |
| `true` / `false` | `true` | Draw the frame at all. `box=false` leaves the tree bare. |
| `corners` | `0pt` | Corner radius. A single value applies to all four corners; a four-value list is TL, TR, BR, BL. |
| `border color` | `black` | |
| `border width` | `0.4pt` | |
| `background color` | `white` | Colour name or `xcolor` expression; define HTML colours first (see §1). |
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

All six entry commands accept `icon={...}` to print inline TeX content before that entry's name using the default name formatter. Icons are specific to each entry: children and siblings start without an icon. The code is stored unexpanded and rendered in a local horizontal box, so ordinary font and colour declarations affect only the icon. A nonbreaking `0.5em` gap follows a nonempty icon; omitting the option or using `icon={}` adds no gap.

```latex
\begin{dirtreex}
  \verbdir[icon={[D]}]|src_code|{sources}{
    \verbfile[icon={\textcolor{blue}{[F]}}]|main_app.py|{entry point}
    \file{LICENSE}{}
  }
\end{dirtreex}
```

Use a glyph command or a text-sized `\includegraphics` for an image icon. Keep its height and depth within the normal text row to preserve baseline and frame alignment; standard `\raisebox` can adjust its vertical position. The item-icon section in `dirtreex_examples.tex` shows images scaled to `0.9em` high and lowered by `0.15em`. Custom `\DirtreexFormatName` hooks control whether and how the icon is rendered (§4.4).

Any `\dir`, `\file`, `\archive` (or their verbatim siblings `\verbdir` / `\verbfile` / `\verbarchive`) can take the same `line color`, `line width`, `line style`, and `elbow radius` keys. They override the environment-level defaults **for connector segments owned by that entry**:

```latex
\dir[line color = blue]{src}{source}{
  \file[line color = red, line width = 1.5pt]{old.py}{deprecated}
  \file[line color = green!60!black, elbow radius = 0pt]{new.py}{sharp}
  \archive{vendor.zip}{bundled}{
    \file[line style = dashed]{numpy.py}{}
    \file[line style = dashed]{pandas.py}{}
  }
}
```

Each entry owns its own `└`-shape. The vertical line continuing **down** from that entry's arm toward the next sibling carries the **next sibling's** colour — so two siblings with different colours share a column that changes colour at arm level (sharp) or at arc-top (rounded).

---

## 7. Cross-page behaviour

When a tree needs splitting, `dirtreex` emits pieces on consecutive pages or standard LaTeX columns, accounting for current float reservations and rendered frame dimensions. Each piece contains a TikZ content node, with its frame and active `│` columns drawn around it. Bare trees use the same splitting machinery without a frame.

The initial pass records absolute page numbers via `zref-abspage` and, in standard two-column mode, horizontal row origins via PGF. Later passes use these locations to distinguish a predecessor on the same piece from one across a page or column break. Recompile until the auxiliary files settle; the isolated regression cases settle within two passes, and the gallery with its table of contents within three.

Concretely:

- Every piece after the first starts with a `0.5\baselineskip` leader of empty space, so the first visible entry shows a `│` above its elbow matching the inter-sibling spacing used on a single page.
- Bottom extensions of every active column continue down to the first piece's bottom edge.
- Top extensions re-appear in the second (and any subsequent) piece, matching the column colours and widths the previous piece ended with.
- The closing piece retains the configured content width. If first-piece fitting consumes the entire tree, it produces a complete tree without an empty trailing closing piece.

---

## 8. Example gallery

The snippets below are self-contained: drop any of them into a document with `\usepackage{dirtreex}` and they compile. For more worked examples of the supported options, see `dirtreex_examples.tex` in the repository root.

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
    \dir[line color = blue]{blue-branch}{}{\file{b1.txt}{}}
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

- The first pass records absolute pages and any required column positions.
- Subsequent passes read those locations to choose connector anchors and cross-break extensions.

For a fresh document, start with two passes and rerun if labels or the table of contents still change. The gallery requires three passes. A document with unchanged, settled auxiliary files generally needs only one.

The package emits `Package dirtreex Warning: Rerun LaTeX...` at `\end{document}` when required page or column data is missing. This is a rerun request, not a complete auxiliary-stability check; also heed LaTeX's changed-label warnings or use `latexmk`.

---

## 10. Troubleshooting

| Symptom | Likely cause | Fix |
| :--- | :--- | :--- |
| First entry on a continuation page has no `│` above its elbow | Only one compile pass has run so far | Run LaTeX again. The `Rerun LaTeX...` warning at `\end{document}` is already asking you to. |
| Vertical columns stop halfway down the last piece | Same cause — `zref` has not seen the break yet | Run LaTeX again. |
| CJK characters render as `□` or are missing | Missing glyphs or font setup | Use a suitable Unicode engine and fonts, for example LuaLaTeX with `ctex`. |
| `! Package dirtreex Error: \dir used outside dirtreex environment` (same for `\file`, `\archive`, and their verbatim siblings) | A stray entry command that is not inside `\begin{dirtreex}…\end{dirtreex}` | Wrap the call in a `dirtreex` environment. |
| `! Package dirtreex Error: parsefour expects 1 or 4 comma-separated values` (or `parsetwo expects 1 or 2 …`) | `corners`, `margin`, `box break at`, or `tree break at` given with the wrong arity | Pass either a single value or the full set (four for `corners`/`margin`, two for the break-at keys). Remember the enclosing braces: `margin = {2pt, 4pt, 6pt, 8pt}`, not `margin = 2pt, 4pt, 6pt, 8pt`. |
| `Package dirtreex Warning: \dte@findanchor hit the recursion floor at entry N` (once per env) | The tree's first top-level entry has depth > 0, or an outer `\begingroup` shadowed `\dte@depth` and produced an inverted depth sequence | Ensure the env body starts with a depth-0 `\dir` / `\file` / `\archive` (or `\verbdir` / `\verbfile` / `\verbarchive`). The connector for the affected entry is snapped to a cross-page-stub variant as a graceful fallback, so the build still succeeds — the warning is purely diagnostic. |

---

## 11. Limitations

- Nested directory/archive entries are supported; nested `dirtreex` environments and entry constructors invoked from rendering hooks are unsupported. Keep entry capture in the environment body.
- Pagination assumes standard LaTeX page/column and float accounting. Arbitrary replacement output routines or balancing-column packages are not qualified.
- Entry formatting runs once per entry, but picture hooks can run during rejected fitting trials. Keep their global or immediate side effects in mind; grouping cannot roll them back.
- A row or frame padding too large for any column can still produce a finite overflow diagnostic. Repeated unconsumed deferral stops at the twentieth attempt; reduce recurring paragraph/header material or clear pending floats.
- Extremely small `box.margin` combined with a very large `elbow radius` crowds the corner; the internal clamp (`connE ≤ 0.5\baselineskip`) keeps things legible but will not rescue pathological values.
- No built-in numbering or hyperlinks. Use `icon={...}` (§6.4) for per-entry icons and the `\DirtreexFormatName` hook (§4.4) for custom name formatting; wrap the tree in a `minipage` if you need decoration around the whole frame.

---

## 12. Project files

| Path | What it is |
| :--- | :--- |
| `dirtreex.sty` | The package — a single self-contained file. |
| `dirtreex_examples.tex` | Worked examples covering the full feature surface. Compile with `lualatex dirtreex_examples.tex` three times to settle tree locations and the table of contents. |
| `assets/` | PNG glyphs (`directory.png`, `python.png`, `zip_file.png`) used by the icon examples in `dirtreex_examples.tex`. |
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
