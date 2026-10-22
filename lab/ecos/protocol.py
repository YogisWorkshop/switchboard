from dataclasses import dataclass, field


def split_outside_quotes(text, separator):
    parts = []
    current = ""
    in_quotes = False
    depth = 0
    for char in text:
        if char == '"':
            in_quotes = not in_quotes
        elif not in_quotes:
            if char == "[":
                depth += 1
            elif char == "]":
                depth -= 1
            elif char == separator and depth == 0:
                parts.append(current)
                current = ""
                continue
        current += char
    parts.append(current)
    return [part.strip() for part in parts if part.strip()]


def unquote(value):
    if len(value) >= 2 and value.startswith('"') and value.endswith('"'):
        return value[1:-1].replace('""', '"')
    return value


def parse_option(token):
    if "[" not in token:
        return token, []
    name, rest = token.split("[", 1)
    inside = rest[:-1]
    args = [unquote(arg) for arg in split_outside_quotes(inside, ",")]
    return name, args


def parse_entry(line):
    tokens = split_outside_quotes(line, " ")
    obj_id = int(tokens[0])
    options = {}
    for token in tokens[1:]:
        name, args = parse_option(token)
        options[name] = args
    return obj_id, options


def parse_end(line):
    inner = line[len("<END "):-1]
    code, _, text = inner.partition(" ")
    return int(code), text.strip("()")

@dataclass
class Message:
    kind: str
    header: str
    entries: list = field(default_factory=list)
    code: int = 0
    text: str = ""

    @property
    def ok(self):
        return self.code == 0

def parse_message(lines):
    first = lines[0]
    if not (first.startswith("<REPLY ") or first.startswith("<EVENT ")):
        raise ValueError(f"not a REPLY or EVENT: {first!r}")
    kind, header = first[1:-1].split(" ", 1)
    entries = [parse_entry(line) for line in lines[1:-1]]
    code, text = parse_end(lines[-1])
    return Message(kind, header, entries, code, text)

