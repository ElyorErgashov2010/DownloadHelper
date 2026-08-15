"""Parser for N_m3u8DL-RE commands."""

import shlex
from dataclasses import dataclass, field


@dataclass
class ParsedCommand:
    executable: str = ""
    url: str = ""
    save_name: str = ""
    save_dir: str = ""
    headers: list[str] = field(default_factory=list)
    key: str = ""
    extra_args: list[str] = field(default_factory=list)

    def rebuild_command(self, overrides: dict[str, str] | None = None) -> list[str]:
        """Rebuild command as argument list with optional overrides."""
        overrides = overrides or {}
        parts = [self.executable]

        if self.url:
            parts.append(self.url)

        name = overrides.get("save_name", self.save_name)
        if name:
            parts.extend(["--save-name", name])

        save_dir = overrides.get("save_dir", self.save_dir)
        if save_dir:
            parts.extend(["--save-dir", save_dir])

        for h in self.headers:
            parts.extend(["-H", h])

        if self.key:
            parts.extend(["--key", self.key])

        parts.extend(self.extra_args)
        return parts


# Arguments that consume the next token as their value
_KNOWN_VALUE_ARGS = {
    "--save-name", "--save-dir", "-H", "--key",
    "--tmp-dir", "--thread-count", "--download-retry-count",
    "--base-url", "--decryption-binary-path", "--mux-after-done",
    "--select-video", "--select-audio", "--select-subtitle",
    "--header", "-M", "--muxer", "--log-level",
}


def parse_command(raw: str) -> ParsedCommand:
    """Parse a raw N_m3u8DL-RE command string into a ParsedCommand."""
    raw = raw.strip()
    # Remove leading ./ or path prefix before executable name
    tokens = shlex.split(raw)
    if not tokens:
        return ParsedCommand()

    result = ParsedCommand(executable=tokens[0])
    i = 1
    while i < len(tokens):
        tok = tokens[i]

        if tok == "--save-name" and i + 1 < len(tokens):
            result.save_name = tokens[i + 1]
            i += 2
        elif tok == "--save-dir" and i + 1 < len(tokens):
            result.save_dir = tokens[i + 1]
            i += 2
        elif tok in ("-H", "--header") and i + 1 < len(tokens):
            result.headers.append(tokens[i + 1])
            i += 2
        elif tok == "--key" and i + 1 < len(tokens):
            result.key = tokens[i + 1]
            i += 2
        elif not tok.startswith("-") and not result.url:
            result.url = tok
            i += 1
        elif tok in _KNOWN_VALUE_ARGS and i + 1 < len(tokens):
            result.extra_args.extend([tok, tokens[i + 1]])
            i += 2
        else:
            result.extra_args.append(tok)
            i += 1

    return result
