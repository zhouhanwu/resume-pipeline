#!/usr/bin/env python3
"""
gen_identity.py — turn config.json into shared/identity.tex.

    python3 pipeline/gen_identity.py

build.sh runs this before every compile, so editing config.json is enough to
change the name, email, links or per-region phone on every résumé. Nothing
about you is hardcoded in the .tex files.

What it writes:
  \\phone            the number for \\TargetRegion, set by new-company.sh
  \\regiononly{k}{}  content that appears only in a build for region k
  \\HeaderBlock      the name + contact line at the top of the page
"""

import json
import os

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
CONFIG = os.path.join(ROOT, "config.json")
OUT = os.path.join(ROOT, "shared", "identity.tex")

# LaTeX takes these literally unless they are escaped.
ESCAPES = {"&": r"\&", "%": r"\%", "$": r"\$", "#": r"\#",
           "_": r"\_", "{": r"\{", "}": r"\}", "~": r"\textasciitilde{}",
           "^": r"\textasciicircum{}"}


def tex(s):
    return "".join(ESCAPES.get(c, c) for c in str(s))


def main():
    with open(CONFIG) as fh:
        cfg = json.load(fh)

    ident = cfg["identity"]
    regions = cfg.get("regions", {})
    phones = regions.get("phones", {})
    default_region = regions.get("default") or (
        sorted(phones)[0] if phones else "uk")

    lines = [
        "% ============================================================",
        "%  IDENTITY  —  GENERATED, DO NOT EDIT",
        "% ------------------------------------------------------------",
        "%  Written by pipeline/gen_identity.py from config.json, which",
        "%  build.sh runs before every compile. Edit config.json instead;",
        "%  anything you change here is overwritten on the next build.",
        "% ============================================================",
        "",
        "%% Region -> phone. \\TargetRegion is \\def'd by the application file.",
        r"\providecommand{\TargetRegion}{%s}" % tex(default_region),
        "",
    ]

    # \phone, resolved by comparing \TargetRegion against each configured key.
    fallback = phones.get(default_region, "")
    lines.append(r"\newcommand{\phone}{%s}" % tex(fallback))
    for key, number in phones.items():
        lines += [
            r"\def\RegionKey{%s}" % tex(key),
            r"\ifx\TargetRegion\RegionKey",
            r"  \renewcommand{\phone}{%s}" % tex(number),
            r"\fi",
        ]
    lines.append("")

    # \regiononly{uk}{...} — one macro for any number of regions.
    lines += [
        r"%% \regiononly{<region>}{<content>} — shown only in that region's build.",
        r"\newcommand{\regiononly}[2]{%",
        r"  \def\RegionWanted{#1}%",
        r"  \ifx\TargetRegion\RegionWanted #2\fi}",
        "",
    ]

    # \CandidateName — the name as written, for a signature line or letterhead.
    lines += [r"\newcommand{\CandidateName}{%s}" % tex(ident["name"]), ""]

    # Header: name, email, links, phone.
    contact = [r"\href{mailto:%s}{%s}" % (ident["email"], tex(ident["email"])),
               r"\phone"]
    for link in ident.get("links", []):
        contact.append(r"\href{%s}{%s}" % (link["url"], tex(link["label"])))
    sep = r" \quad $\vert$ \quad "

    lines += [
        r"\newcommand{\HeaderBlock}{%",
        r"\begin{center}",
        r"  {\large \textbf{%s}} \\" % tex(ident["name"]).upper(),
        "  " + sep.join(contact),
        r"\end{center}",
        r"\vspace{0.2em}",
        r"}",
        "",
    ]

    with open(OUT, "w") as fh:
        fh.write("\n".join(lines))

    print("identity.tex <- config.json  (%s, regions: %s)"
          % (ident["name"], ", ".join(sorted(phones)) or "none"))


if __name__ == "__main__":
    main()
