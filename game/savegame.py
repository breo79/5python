from pathlib import Path

SAVE_PATH = Path(__file__).resolve().parent / "assets" / "leveldata" / "saves" / "savefile.txt"
END_MARKER = "00000"

STATE_KEYS = {
    "green": "BeatenLevels",
    "yellow": "BeatenLVLSnoWt",
    "reached": "Unbeaten"
}


def format_numbers(numbers):
    return ",".join(str(n) for n in numbers)


def parse_numbers(text):
    numbers = []
    for part in text.replace(";", "").split(","):
        part = part.strip()
        if part.isdigit():
            numbers.append(int(part))
    return numbers


def write_save(progress, time_spent, path=SAVE_PATH):
    by_state = {state: sorted(i + 1 for i, s in progress.items() if s == state) for state in STATE_KEYS}
    lines = [
        f"BeatenLevels {format_numbers(by_state['green'])};",
        f"BeatenLVLSnoWt {format_numbers(by_state['yellow'])}",
        f"Unbeaten {format_numbers(by_state['reached'])}",
        f"WinTokenAmount {len(by_state['green'])}",
        f"TimeSpentPlaying {time_spent:.1f}",
        END_MARKER
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def load_save(path=SAVE_PATH):
    if not path.exists():
        return None
    lines = [line.strip() for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    if not lines or not lines[0].startswith("BeatenLevels"):
        return None

    fields = {}
    for line in lines:
        if line == END_MARKER:
            break
        key, _, value = line.partition(" ")
        fields[key] = value

    progress = {}
    for state, key in reversed(list(STATE_KEYS.items())):
        for number in parse_numbers(fields.get(key, "")):
            if number >= 1:
                progress[number - 1] = state
    if not progress:
        progress[0] = "reached"

    try:
        time_spent = float(fields.get("TimeSpentPlaying", "0").replace(";", ""))
    except ValueError:
        time_spent = 0.0

    return {"progress": progress, "time_spent": time_spent}


def has_save(path=SAVE_PATH):
    return load_save(path) is not None


def format_time(seconds):
    hours, rest = divmod(seconds, 3600)
    minutes, secs = divmod(rest, 60)
    return f"{int(hours):02d}:{int(minutes):02d}:{secs:04.1f}"
