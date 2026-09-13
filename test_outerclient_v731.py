import unittest

from outerclient_v731_patch import VERSION, cleanup_launch_footer, contains_launch_text


class Widget:
    def __init__(self, text="", master=None, image=None):
        self._text = text
        self.master = master
        self._children = []
        self._image = image
        if master is not None:
            master._children.append(self)

    def winfo_children(self):
        return list(self._children)

    def cget(self, key):
        if key == "text":
            return self._text
        if key == "image":
            return self._image
        raise KeyError(key)

    def configure(self, **kwargs):
        if "text" in kwargs:
            self._text = kwargs["text"]
        if "image" in kwargs:
            self._image = kwargs["image"]


class CTkProgressBar(Widget):
    def __init__(self, master=None, value=1.0):
        super().__init__(master=master)
        self.value = value

    def set(self, value):
        self.value = value


class App(Widget):
    def __init__(self):
        super().__init__()
        self._v731_launch_generation = 1
        self._v731_launch_active = False


class V731Tests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(VERSION, "7.3.1")

    def test_launch_text_nested(self):
        self.assertTrue(contains_launch_text({"bar": ["Uruchamianie Minecrafta...", 0.8]}))
        self.assertFalse(contains_launch_text({"bar": ["Pobieranie Sodium", 0.8]}))

    def test_cleanup_clears_finished_launch_footer(self):
        app = App()
        footer = Widget(master=app)
        label = Widget("Uruchamianie Minecrafta...", footer)
        right = Widget("Minecraft", footer)
        bar = CTkProgressBar(footer, 0.75)
        changed = cleanup_launch_footer(app, 1)
        self.assertTrue(changed)
        self.assertEqual(label._text, "")
        self.assertEqual(right._text, "")
        self.assertEqual(bar.value, 0)

    def test_cleanup_does_not_touch_download_footer(self):
        app = App()
        footer = Widget(master=app)
        label = Widget("Pobieranie Sodium", footer)
        bar = CTkProgressBar(footer, 0.4)
        changed = cleanup_launch_footer(app, 1)
        self.assertFalse(changed)
        self.assertEqual(label._text, "Pobieranie Sodium")
        self.assertEqual(bar.value, 0.4)

    def test_old_generation_cannot_clear_new_launch(self):
        app = App()
        app._v731_launch_generation = 2
        footer = Widget(master=app)
        label = Widget("Uruchamianie Minecrafta...", footer)
        bar = CTkProgressBar(footer, 0.2)
        self.assertFalse(cleanup_launch_footer(app, 1))
        self.assertEqual(label._text, "Uruchamianie Minecrafta...")
        self.assertEqual(bar.value, 0.2)

    def test_active_launch_is_not_cleared(self):
        app = App()
        app._v731_launch_active = True
        footer = Widget(master=app)
        label = Widget("Uruchamianie Minecrafta...", footer)
        self.assertFalse(cleanup_launch_footer(app, 1))
        self.assertEqual(label._text, "Uruchamianie Minecrafta...")


if __name__ == "__main__":
    unittest.main()
