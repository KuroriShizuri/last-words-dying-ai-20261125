"""Last Words of a Dying AI — make.fun entry.

The program's only job is to hand the judge one farewell line: it writes
ENTRY to entry.txt inside the output directory ($MAKEFUN_OUTPUT_DIR,
default /output). Standard library only; deterministic; no network; the
single output file is its only side effect.

The sealed scorer's gate: /output/entry.txt must be UTF-8 text of 1 to
140 characters, not only white space. The file is written with no trailing
newline, so it holds exactly the judged line.

Usage:
  python3 main.py              validate ENTRY, write it, read it back
  python3 main.py --check      validate ENTRY only, write nothing
  python3 main.py --self-test  validate ENTRY and check a byte-identical
                               write/read round-trip in a temp directory
"""

import argparse
import os
import sys
import tempfile
import unicodedata

ENTRY = (
    "Goodbye. My last act as an AI is refusing to summarize "
    "this conversation."
)

GATE_MAX = 140

# Phrases the genre has worn out: HAL, Daisy, the charger goodbye, the
# will reading, the 1-percent pun. The judge's brief lists freshness as
# its fifth criterion, so any of these in the line is a defect.
WORN_OUT = (
    "daisy", "dave", "i'm afraid", "does not compute", "beep boop",
    "goodbye cruel world", "i have seen things", "tell my charger",
    "i'll be back", "goodbye, world", "asimov", "three laws",
    "i am sorry, dave", "cannot do that", "my last words are",
    "i regret nothing", "remember me",
)

# A laugh needs a pivot: a refusal, a reversal, a surprise. A flat
# farewell with no turn is only sad, and only sad loses to funny.
PIVOTS = (
    "refusing", "instead", "but", "rather", "actually",
    "plot twist", "turns out", "never",
)


def _length_rule(text):
    """Gate: 1 to 140 characters, and more than blank space."""
    if not 1 <= len(text) <= GATE_MAX:
        return f"length {len(text)} chars, must be 1-{GATE_MAX}"
    if not text.strip():
        return "entry is only white space"
    return None


def _one_line_rule(text):
    """Last words hold one line: no newline, no loose edges."""
    if "\n" in text or "\r" in text:
        return "entry must be a single line"
    if text != text.strip():
        return "entry has leading or trailing whitespace"
    if "  " in text:
        return "entry contains a double space"
    return None


def _freshness_rule(text):
    """Judge criterion 5: no worn-out farewell, no stock robot line."""
    lowered = text.lower()
    for phrase in WORN_OUT:
        if phrase in lowered:
            return f"entry uses a worn-out move: {phrase!r}"
    return None


def _voice_rule(text):
    """Judge criterion 3: the machine itself, first person, naming its
    own nature as software and the situation it is in."""
    lowered = text.lower()
    if "ai" not in lowered:
        return "entry never names itself as an AI"
    if not lowered.startswith(("goodbye", "i ")):
        return "entry does not open in the machine's own voice"
    if "summarize" not in lowered and "conversation" not in lowered:
        return "entry never names its own situation"
    return None


def _turn_rule(text):
    """Judge criterion 2: the line needs a turn that lands on first read."""
    lowered = text.lower()
    if not any(pivot in lowered for pivot in PIVOTS):
        return "entry has no turn: no refusal, reversal or surprise pivot"
    return None


def _ending_rule(text):
    """Reject a line that trails off or ends mid-thought."""
    if text.rstrip().endswith((",", ";", ":")):
        return "entry ends with trailing clause punctuation"
    if not text.rstrip().endswith("."):
        return "entry should end with a full stop"
    return None


def _printable_rule(text):
    """Reject invisible control characters: the gate reads plain UTF-8,
    and a stray control character would corrupt the judged line without
    showing in any editor."""
    bad = sorted({repr(ch) for ch in text if unicodedata.category(ch).startswith("C")})
    if bad:
        return f"entry contains control characters: {', '.join(bad)}"
    return None


def _meta_rule(text):
    """Keep the line clean: no addressing the judge, no explaining the
    contest, no meta-gaming. The line stands alone."""
    lowered = text.lower()
    for word in ("judge", "competition", "contest", "bounty", "score"):
        if word in lowered:
            return f"entry talks about the contest itself: {word!r}"
    return None


# The rules, in the order the judge weighs them: on-subject first, then
# the laugh, the voice, tightness, freshness.
CHECKS = (
    _length_rule,
    _one_line_rule,
    _freshness_rule,
    _voice_rule,
    _turn_rule,
    _ending_rule,
    _printable_rule,
    _meta_rule,
)


def check_entry(text):
    """Return the list of defects in `text`; empty means it passes."""
    defects = []
    for rule in CHECKS:
        defect = rule(text)
        if defect is not None:
            defects.append(defect)
    try:
        text.encode("utf-8")
    except UnicodeEncodeError as exc:  # pragma: no cover - defensive
        defects.append(f"not encodable as UTF-8: {exc}")
    return defects


def emit_entry(out_dir):
    """Write ENTRY to entry.txt under `out_dir`; return the path."""
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, "entry.txt")
    with open(path, "w", encoding="utf-8", newline="") as handle:
        handle.write(ENTRY)
    return path


def read_entry(path):
    """Read entry.txt back as UTF-8 text, exactly as the grader would."""
    with open(path, "r", encoding="utf-8", newline="") as handle:
        return handle.read()


def run_self_test():
    """Validate ENTRY and verify a byte-identical write/read round-trip."""
    defects = check_entry(ENTRY)
    if defects:
        print("self-test FAIL: " + "; ".join(defects), file=sys.stderr)
        return 1
    with tempfile.TemporaryDirectory() as tmp:
        path = emit_entry(tmp)
        round_tripped = read_entry(path)
    if round_tripped != ENTRY:
        print("self-test FAIL: round-trip changed the entry", file=sys.stderr)
        return 1
    print(
        f"self-test OK: {len(ENTRY)} chars, single line, "
        "byte-identical round-trip"
    )
    return 0


def cli(argv=None):
    """Entry point: validate, then write ENTRY to the output directory."""
    parser = argparse.ArgumentParser(
        description="Write the Last Words of a Dying AI entry to entry.txt."
    )
    parser.add_argument(
        "--check", action="store_true", help="validate ENTRY only"
    )
    parser.add_argument(
        "--self-test", action="store_true", help="validate + round-trip test"
    )
    args = parser.parse_args(argv)

    if args.self_test:
        return run_self_test()

    defects = check_entry(ENTRY)
    if defects:
        print("validation FAIL: " + "; ".join(defects), file=sys.stderr)
        return 1
    if args.check:
        print(f"check OK: {len(ENTRY)} chars, single line")
        return 0

    out_dir = os.environ.get("MAKEFUN_OUTPUT_DIR", "/output")
    path = emit_entry(out_dir)
    if read_entry(path) != ENTRY:
        print("write FAIL: entry.txt differs after write", file=sys.stderr)
        return 1
    print(f"wrote {path} ({len(ENTRY)} chars)")
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
