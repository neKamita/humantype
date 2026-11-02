#!/usr/bin/env python3
"""Type text into the focused window with human-like rhythm and typos (Wayland, via wtype)."""
import argparse
import random
import subprocess
import sys
import time

# Keyboard rows: a typo hits a horizontal neighbour of the intended key.
ROWS = ["qwertyuiop", "asdfghjkl", "zxcvbnm", "йцукенгшщзхъ", "фывапролджэ", "ячсмитьбю"]
NEIGHBORS = {ch: row[max(i - 1, 0):i] + row[i + 1:i + 2] for row in ROWS for i, ch in enumerate(row)}
KEYS = {"\n": "Return", "\t": "Tab"}


def mistake(text, i, rng):
    """Return (wrong, n): what gets typed instead of the correct text[i:i + n]."""
    ch = text[i]
    nxt = text[i + 1] if i + 1 < len(text) else ""
    kind = rng.random()
    if kind < 0.25 and nxt.isalpha() and nxt != ch:
        return nxt + ch, 2  # swapped letters
    if kind < 0.4:
        return ch + ch, 1  # doubled letter
    wrong = rng.choice(NEIGHBORS[ch.lower()])
    return (wrong.upper() if ch.isupper() else wrong), 1  # neighbouring key


def plan(text, wpm=120, typo_rate=0.03, rng=random):
    """Yield (kind, value, pause_before) steps; kind is 'text' or 'key'."""
    base = 60 / (wpm * 5)  # seconds per character, a "word" is 5 characters
    scale = 60 / wpm  # thinking pauses shrink as typing speeds up
    last = ""

    def type_out(s):
        nonlocal last
        for c in s:
            pause = base * rng.lognormvariate(0, 0.4)
            if last in ".!?":
                pause += scale * rng.uniform(0.4, 1.2)
            elif last in ",;:":
                pause += scale * rng.uniform(0.1, 0.4)
            elif last == "\n":
                pause += scale * rng.uniform(0.8, 2.0)
            elif last == " " and rng.random() < 0.05:
                pause += scale * rng.uniform(0.3, 1.0)  # thinking about the next word
            yield ("key", KEYS[c], pause) if c in KEYS else ("text", c, pause)
            last = c

    i = 0
    while i < len(text):
        if text[i].lower() not in NEIGHBORS or rng.random() >= typo_rate:
            yield from type_out(text[i])
            i += 1
            continue
        wrong, n = mistake(text, i, rng)
        # A few correct characters slip out before the mistake is noticed.
        tail = text[i + n:i + n + rng.randint(0, 3)]
        tail = tail[:next((j for j, c in enumerate(tail) if c in KEYS), len(tail))]
        yield from type_out(wrong + tail)
        yield "key", "BackSpace", scale * rng.uniform(0.3, 0.8)  # noticing the mistake
        for _ in range(len(wrong + tail) - 1):
            yield "key", "BackSpace", base * rng.uniform(0.5, 1.0)
        yield from type_out(text[i:i + n + len(tail)])
        i += n + len(tail)


def send(kind, value):
    subprocess.run(["wtype", "-k", value] if kind == "key" else ["wtype", "--", value], check=True)


def main():
    p = argparse.ArgumentParser(description="Печатает текст в активное окно, как живой человек.")
    p.add_argument("file", nargs="?", help="текстовый файл (UTF-8); без него откроется окно для вставки текста")
    p.add_argument("--wpm", type=float, default=120, help="скорость, слов в минуту (по умолчанию 120)")
    p.add_argument("--typos", type=float, default=0.03, help="вероятность ошибки на букву (по умолчанию 0.03)")
    p.add_argument("--delay", type=float, default=5, help="секунд до начала печати (по умолчанию 5)")
    a = p.parse_args()
    if a.wpm <= 0 or not 0 <= a.typos <= 1:
        p.error("--wpm должен быть > 0, --typos от 0 до 1")

    if a.file:
        with open(a.file, encoding="utf-8") as f:
            text = f.read()
    else:
        clipboard = subprocess.run(["wl-paste", "--no-newline"], capture_output=True, text=True).stdout
        # The window starts with the clipboard text; the user can edit or replace it.
        win = subprocess.run(
            ["zenity", "--text-info", "--editable", "--width=700", "--height=500",
             "--title=Вставьте текст и нажмите OK", "--ok-label=Начать", "--cancel-label=Отмена"],
            input=clipboard, capture_output=True, text=True)
        if win.returncode != 0:
            sys.exit("Отменено.")
        text = win.stdout.rstrip("\n")  # zenity appends a trailing newline
    text = text.replace("\r\n", "\n")
    if not text:
        sys.exit("Нет текста: передайте файл или скопируйте текст в буфер обмена.")

    hint = f"{len(text)} символов. Через {a.delay:g} с щёлкните в поле ввода."
    print(hint, "Остановка: Ctrl+C в этом терминале.")
    subprocess.run(["notify-send", "Печать текста", hint])
    try:
        time.sleep(a.delay)
        for kind, value, pause in plan(text, a.wpm, a.typos):
            time.sleep(pause)
            send(kind, value)
    except KeyboardInterrupt:
        sys.exit("\nОстановлено.")
    print("Готово.")


if __name__ == "__main__":
    main()
