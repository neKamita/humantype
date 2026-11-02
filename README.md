# humantype

Types prepared text into the focused window the way a person would: uneven rhythm,
pauses after punctuation and new lines, and occasional mistakes that are noticed a
few characters later, erased with Backspace, and retyped.

Works in any text input: web page fields, Google Docs, LibreOffice Writer, messengers.
Spaces, tabs, and line breaks are preserved; rich formatting (bold, italic, lists) is not.

## Requirements

- Linux with a Wayland compositor that supports the virtual keyboard protocol
  (Hyprland, Sway, niri and other wlroots-based compositors)
- Python 3.10+ (standard library only)
- [`wtype`](https://github.com/atx/wtype) - sends the keystrokes
- `wl-clipboard` (`wl-paste`) - reads the clipboard
- `zenity` - the window for pasting text
- `notify-send` (libnotify) - the start notification

On Arch Linux:

```bash
sudo pacman -S wtype wl-clipboard zenity libnotify
```

## Usage

```bash
./humantype.py              # opens a window prefilled with the clipboard text
./humantype.py text.txt     # types the contents of a UTF-8 file
```

1. Copy the text or prepare a file.
2. Run the script. Without a file argument a window opens with the clipboard
   contents; edit or replace the text and press the start button.
3. You have 5 seconds to click into the target text field.
4. To stop typing, switch back to the terminal and press `Ctrl+C`.

Keystrokes always go to the window that has focus, so do not switch windows while
the script is typing.

## Options

| Option | Default | Meaning |
|---|---|---|
| `--wpm` | `120` | Typing speed in words per minute (a word is 5 characters). Pauses scale with it. |
| `--typos` | `0.03` | Chance of a mistake per letter, from `0` (none) to `1`. |
| `--delay` | `5` | Seconds to wait before typing starts. |

Example: slower typing without mistakes:

```bash
./humantype.py text.txt --wpm 60 --typos 0
```

## How it works

`plan()` turns the text into a sequence of steps: type a character or press a key,
each with a pause before it. Pauses follow a log-normal distribution around the
target speed, with extra time after `.!?`, `,;:`, new lines, and occasionally
before a word.

When a mistake happens, `mistake()` picks one of three kinds: a neighbouring key on
the QWERTY or JCUKEN row, two swapped letters, or a doubled letter. Up to three
correct characters may follow before the mistake is "noticed"; then everything since
the mistake is erased and retyped.

`main()` sends each step to `wtype`.

## Known limitations

- Editor features such as autocorrect, smart quotes, or auto-closing brackets can
  change the typed text. Turn them off if the result must match exactly.
- Slow pages (for example, fields with live suggestions) may drop characters at high
  speed; lower `--wpm`.
- `wtype` swaps the keyboard layout to type non-ASCII characters; some browsers keep
  the wrong layout afterwards. Switching the layout back and forth fixes it.
- Trailing blank lines in the pasted text are dropped.

## Tests

```bash
python3 -m unittest -v test_humantype
```

The tests check that the typed result always equals the input text after all
corrections, that mistakes happen and are sometimes noticed late, and that the speed
matches `--wpm`.
