import random
import unittest

from humantype import plan


def replay(steps):
    """Apply planned steps to a buffer the way the target text field would."""
    buf = []
    for kind, value, _ in steps:
        if kind == "text":
            buf.append(value)
        elif value == "BackSpace":
            buf.pop()
        else:
            buf.append({"Return": "\n", "Tab": "\t"}[value])
    return "".join(buf)


class PlanTest(unittest.TestCase):
    TEXT = "Привет, мир! Hello World.\n\tВторая строка - с дефисом и цифрами 123."

    def test_result_matches_text_even_with_many_typos(self):
        for seed in range(50):
            steps = list(plan(self.TEXT, typo_rate=0.5, rng=random.Random(seed)))
            self.assertEqual(replay(steps), self.TEXT)

    def test_typos_happen_and_pauses_are_positive(self):
        steps = list(plan(self.TEXT, typo_rate=0.5, rng=random.Random(1)))
        self.assertIn(("key", "BackSpace"), [(k, v) for k, v, _ in steps])
        self.assertTrue(all(p > 0 for _, _, p in steps))

    def test_no_typos_when_rate_is_zero(self):
        steps = list(plan(self.TEXT, typo_rate=0, rng=random.Random(1)))
        self.assertEqual(len(steps), len(self.TEXT))

    def test_mistakes_are_sometimes_noticed_late(self):
        steps = list(plan(self.TEXT * 5, typo_rate=0.3, rng=random.Random(2)))
        values = [v for _, v, _ in steps]
        # Two or more Backspaces in a row: extra characters were typed after the mistake.
        self.assertTrue(any(values[j:j + 2] == ["BackSpace"] * 2 for j in range(len(values))))

    def test_speed_roughly_matches_wpm(self):
        text = "word " * 400
        default = sum(p for _, _, p in plan(text, typo_rate=0, rng=random.Random(1)))
        slow = sum(p for _, _, p in plan(text, wpm=60, typo_rate=0, rng=random.Random(1)))
        # 400 words: ~200 s at the default 120 wpm, ~400 s at 60 wpm; thinking pauses add a bit.
        self.assertTrue(175 < default < 300, default)
        self.assertTrue(350 < slow < 600, slow)


if __name__ == "__main__":
    unittest.main()
