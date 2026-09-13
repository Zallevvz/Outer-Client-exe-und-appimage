import unittest

import outerclient_v740_patch as p


class FakeWidget:
    def __init__(self):
        self.children = []
    def winfo_children(self):
        return self.children


class TestV740Helpers(unittest.TestCase):
    def test_easing_endpoints(self):
        self.assertEqual(p.ease_out_cubic(0), 0)
        self.assertEqual(p.ease_out_cubic(1), 1)
        self.assertEqual(p.ease_in_out_cubic(0), 0)
        self.assertEqual(p.ease_in_out_cubic(1), 1)

    def test_easing_monotonic(self):
        vals = [p.ease_out_cubic(i / 20) for i in range(21)]
        self.assertEqual(vals, sorted(vals))

    def test_mix_color(self):
        self.assertEqual(p._mix_color("#000000", "#FFFFFF", 0), "#000000")
        self.assertEqual(p._mix_color("#000000", "#FFFFFF", 1), "#FFFFFF")
        self.assertEqual(p._mix_color("#000000", "#FFFFFF", 0.5), "#808080")

    def test_hex_short_form(self):
        self.assertEqual(p._hex_to_rgb("#fff"), (255, 255, 255))
        self.assertIsNone(p._hex_to_rgb("transparent"))

    def test_walk_deduplicates(self):
        root = FakeWidget()
        child = FakeWidget()
        root.children = [child, child]
        self.assertEqual(len(list(p._walk(root))), 2)

    def test_version(self):
        self.assertEqual(p.VERSION, "7.4.0")


if __name__ == "__main__":
    unittest.main()
