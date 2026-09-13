import unittest
import outerclient_v741_patch as p


class FakeWidget:
    def __init__(self, manager="grid", fg="#202020"):
        self._manager = manager
        self.opts = {
            "fg_color": fg,
            "corner_radius": 12,
            "border_width": 0,
            "border_color": "#303030",
            "text": "",
        }
        self._children = []
        self.master = None
        self.scheduled = []

    def winfo_children(self): return list(self._children)
    def winfo_exists(self): return True
    def winfo_manager(self): return self._manager
    def grid_info(self): return {"padx": 4, "pady": 2}
    def pack_info(self): return {"padx": 4, "pady": 2}
    def place_info(self): return {"rely": 0.2}
    def grid_configure(self, **kw): self.grid_cfg = kw
    def pack_configure(self, **kw): self.pack_cfg = kw
    def place_configure(self, **kw): self.place_cfg = kw
    def cget(self, key): return self.opts.get(key)
    def configure(self, **kw): self.opts.update(kw)
    def after(self, delay, fn):
        self.scheduled.append((delay, fn))
        if delay == 0:
            fn()
        return f"a{len(self.scheduled)}"
    def after_cancel(self, _ident): pass
    def bind(self, *_args, **_kwargs): pass


class Tests(unittest.TestCase):
    def test_pad(self):
        self.assertEqual(p.pad(5), (5, 5))
        self.assertEqual(p.pad("3 9"), (3, 9))
        self.assertEqual(p.pad((4, 7)), (4, 7))

    def test_loading_detection(self):
        self.assertEqual(p.loading_base("Ładowanie..."), "Ładowanie")
        self.assertEqual(p.loading_base("Loading …"), "Loading")
        self.assertIsNone(p.loading_base("Gotowe"))

    def test_reveal_only_once(self):
        app = type("A", (), {"cfg": {"ui_animations": True}})()
        widget = FakeWidget()
        self.assertTrue(p.reveal(app, widget, delay=5))
        self.assertTrue(widget._v741_revealed)
        self.assertFalse(p.reveal(app, widget))

    def test_card_detection(self):
        class Frame(FakeWidget): pass
        class Ctk: CTkFrame = Frame
        widget = Frame()
        widget._children.append(FakeWidget())
        self.assertTrue(p.cardlike(Ctk, widget))
        widget.opts["corner_radius"] = 0
        self.assertFalse(p.cardlike(Ctk, widget))

    def test_install_sets_version_and_helpers(self):
        class Ctk:
            class CTkProgressBar: pass
            class CTkScrollableFrame: pass
        class OC:
            def __init__(self): pass
            def set_active_page(self, *_args, **_kwargs): pass
        mod = type("M", (), {})()
        mod.OuterClient = OC
        mod.ctk = Ctk
        mod.TEXTS = {"pl": {}, "en": {}}
        mod.BG = "#101010"
        mod.SURFACE_3 = "#202020"
        mod.BORDER = "#303030"
        p.install(mod)
        self.assertEqual(mod.APP_VERSION, "7.4.1")
        self.assertTrue(callable(OC.stagger_page_v741))
        self.assertTrue(callable(OC.scan_rich_motion_v741))
        self.assertTrue(callable(OC.decorate_card_v741))
        self.assertTrue(callable(OC.animate_loading_label_v741))

    def test_color_mix(self):
        self.assertEqual(p.mix("#000000", "#FFFFFF", .5), "#808080")


if __name__ == "__main__":
    unittest.main()
