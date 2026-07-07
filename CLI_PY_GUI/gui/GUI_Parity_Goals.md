# GUI Parity Goals (v1)

**Hard requirements**
- True PTY backend (ConPTY on Windows, pty on *nix) with isatty behavior.
- No hidden flags; show exact command preview string.
- Ctrl‑C / EOF / Kill buttons that send correct signals.
- Resize-aware (cols×rows) and status strip showing CWD | Shell | Venv | rows×cols | Exit.
- ANSI essentials: carriage return `\r`, backspace `\b`, CSI K.

**Parity tests**
- CR overwrite visible (`printf 'abc\rABCD\n'` → shows `ABCD`).
- Unicode I/O OK (e.g., `π≈3.14`).
- Exit codes propagated; Ctrl‑C leads to signal exit code.
- Stderr interleave visible; no line reordering.

**Nice-to-haves**
- History & search; Copy-on-select; Bracketed paste.
- Artifacts pane (watch CWD for new files).
- Session recorder (.cast).

