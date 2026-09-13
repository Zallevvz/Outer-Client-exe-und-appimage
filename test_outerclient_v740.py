import os
import unittest
from unittest.mock import patch

import outerclient_v740_motion_core as core
import outerclient_v740_motion_widgets as widgets


class Node:
    def __init__(self, children=None):
        self._children = list(children or [])

    def winfo_children(self):
        return list(self._children)


class App:
    def __init__(self, cfg=None):
        self.cfg = dict(cfg or {})


class MotionCoreTests(unittest.TestCase):
    def test_blend_color_midpoint(self):
        self.assertEqual(core.blend_color("#000000", "#FFFFFF", 0.5), "#808080")
        self.assertEqual(core.blend_color("#123456", "#123456", 0.7), "#123456")
        self.assertIsNone(core.blend_color("transparent", "#FFFFFF", 0.5))

    def test_easing_boundaries_and_monotonicity(self):
        values = [core.ease_out_cubic(i / 20) for i in range(21)]
        self.assertEqual(values[0], 0.0)
        self.assertEqual(values[-1], 1.0)
        self.assertEqual(values, sorted(values))

    def test_reduced_motion_switches(self):
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("OUTERCLIENT_REDUCED_MOTION", None)
            self.assertTrue(core.motion_enabled(App()))
            self.assertFalse(core.motion_enabled(App({"ui_animations": False})))
            self.assertFalse(core.motion_enabled(App({"reduce_motion": True})))
        with patch.dict(os.environ, {"OUTERCLIENT_REDUCED_MOTION": "1"}):
            self.assertFalse(core.motion_enabled(App()))

    def test_loading_detection_is_bilingual(self):
        self.assertTrue(widgets.is_loading_text("Pobieranie moda…"))
        self.assertTrue(widgets.is_loading_text("Refreshing versions…"))
        self.assertTrue(widgets.is_loading_text("Uruchamianie Minecrafta…"))
        self.assertFalse(widgets.is_loading_text("Gotowy"))

    def test_widget_walk_is_deduplicated(self):
        shared = Node()
        root = Node([Node([shared]), Node([shared])])
        found = list(core.walk_widgets(root))
        self.assertEqual(len(found), 4)
        self.assertEqual(len({id(w) for w in found}), 4)

    def test_clamp_guards_animation_inputs(self):
        self.assertEqual(core.clamp(-5), 0.0)
        self.assertEqual(core.clamp(5), 1.0)
        self.assertAlmostEqual(core.clamp(0.42), 0.42)


if __name__ == "__main__":
    unittest.main()
