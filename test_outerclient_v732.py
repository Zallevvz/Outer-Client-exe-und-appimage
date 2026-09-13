import unittest

from outerclient_v732_patch import VERSION, _find_account_card, _find_avatar


class Widget:
    def __init__(self, text="", master=None, column=None):
        self.text = text
        self.master = master
        self.children = []
        self.column = column
        if master is not None:
            master.children.append(self)

    def winfo_children(self):
        return list(self.children)

    def cget(self, key):
        if key == "text":
            return self.text
        raise KeyError(key)

    def grid_info(self):
        return {} if self.column is None else {"column": self.column}


class V732Tests(unittest.TestCase):
    def test_version(self):
        self.assertEqual(VERSION, "7.3.2")

    def test_finds_account_card_without_fixed_row(self):
        root = Widget()
        unrelated = Widget(master=root)
        Widget("Other", unrelated)
        card = Widget(master=root)
        Widget("Zallev", card)
        Widget("Aktywne konto", card)
        Widget("Wyloguj", card)
        self.assertIs(_find_account_card(root, "Zallev", "Wyloguj"), card)

    def test_account_names_are_matched_exactly(self):
        root = Widget()
        card_a = Widget(master=root)
        Widget("Zallev", card_a)
        Widget("Wyloguj", card_a)
        card_b = Widget(master=root)
        Widget("Zallev2", card_b)
        Widget("Wyloguj", card_b)
        self.assertIs(_find_account_card(root, "Zallev2", "Wyloguj"), card_b)

    def test_avatar_prefers_column_zero_initial(self):
        card = Widget()
        avatar = Widget("Z", card, column=0)
        Widget("Zallev", card, column=1)
        self.assertIs(_find_avatar(card, "Zallev"), avatar)

    def test_missing_account_returns_none(self):
        root = Widget()
        card = Widget(master=root)
        Widget("Someone", card)
        Widget("Wyloguj", card)
        self.assertIsNone(_find_account_card(root, "Zallev", "Wyloguj"))


if __name__ == "__main__":
    unittest.main()
