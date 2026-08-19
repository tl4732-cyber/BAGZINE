import unittest

from bags.product_linking import is_likely_accessory, should_drop_listing, should_link_listing
from bags.title_parser import ParsedProduct, parse_title


class ProductLinkingTest(unittest.TestCase):
    def test_organizer_is_dropped(self):
        title = "Zoomoni Bag Organizer for Hermes Kelly 32 (Premium/20 Color Options)"
        self.assertTrue(should_drop_listing(title))

    def test_real_bag_not_dropped(self):
        title = "Hermes Kelly 32 Epsom Vert Anglais Sellier"
        self.assertFalse(should_drop_listing(title, 6000.0))

    def test_accessory_charm(self):
        title = "Hermes Birkin Bag Charm New"
        self.assertTrue(is_likely_accessory(title))
        self.assertTrue(should_drop_listing(title))
        self.assertFalse(should_link_listing(title, 4000.0))

    def test_accessory_silicone_cover(self):
        title = "Clear Silicone Protective cover for handbag stud feet for hermes Birkin 25, 30"
        self.assertTrue(is_likely_accessory(title))
        self.assertTrue(should_drop_listing(title))
        self.assertFalse(should_link_listing(title, 29.99))

    def test_accessory_gift_box(self):
        title = "HERMES Birkin 30 empty Gift Box 36×38×15.5cm"
        self.assertTrue(is_likely_accessory(title))
        self.assertTrue(should_drop_listing(title))
        self.assertFalse(should_link_listing(title, 382.0))

    def test_clochette_dropped(self):
        title = "Hermes Kelly 28/32/35 Clochette & Tirette Noir Matte Alligator Chèvre Lined"
        self.assertTrue(should_drop_listing(title))

    def test_unparseable_title_dropped(self):
        title = "Luxury designer handbag authentic pre-owned"
        self.assertTrue(should_drop_listing(title))

    def test_bag_with_dust_bag_not_accessory(self):
        title = "CHANEL Black Quilted CC Flap Turn Lock Gold Chain Crossbody Bag Dust Bag"
        self.assertFalse(is_likely_accessory(title))
        parsed = parse_title(title)
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.model, "Classic Flap")
        self.assertFalse(should_drop_listing(title, 5000.0))

    def test_birkin_under_floor_not_linked(self):
        title = "Hermes Birkin 35 Taurillon Clemence White Hand Bag"
        parsed = parse_title(title)
        self.assertFalse(should_link_listing(title, 7500.0, parsed))
        self.assertTrue(should_drop_listing(title, 7500.0))

    def test_birkin_at_floor_linked(self):
        title = "Hermes Birkin 30 Togo Gold"
        parsed = parse_title(title)
        self.assertTrue(should_link_listing(title, 8000.0, parsed))
        self.assertFalse(should_drop_listing(title, 8000.0))

    def test_kelly_under_floor_not_linked(self):
        title = "Hermes Kelly 32 Epsom Vert Anglais Sellier"
        parsed = parse_title(title)
        self.assertFalse(should_link_listing(title, 4500.0, parsed))
        self.assertTrue(should_drop_listing(title, 4500.0))

    def test_vinyl_kelly_not_subject_to_leather_kelly_floor(self):
        title = "HERMES Vinyl Kelly Hand Bag Vinyl Clear Gold Auth 188256"
        parsed = parse_title(title)
        self.assertEqual(parsed.model, "Vinyl Kelly")
        self.assertTrue(should_link_listing(title, 413.60, parsed))

    def test_kelly_at_floor_linked(self):
        title = "Hermes Kelly 32 Epsom Vert Anglais Sellier"
        parsed = parse_title(title)
        self.assertTrue(should_link_listing(title, 5000.0, parsed))
        self.assertFalse(should_drop_listing(title, 5000.0))

    def test_kelly_quartz_watch_not_linked(self):
        title = "[Exc+5] HERMES Kelly 20mm White Dial Burgundy band Quartz Women's Watch with bag"
        self.assertTrue(is_likely_accessory(title))
        self.assertFalse(should_link_listing(title, 469.99))

    def test_birkin_without_variant_not_linked(self):
        title = "Hermes Birkin authentic handbag"
        parsed = parse_title(title)
        self.assertIsNotNone(parsed)
        self.assertFalse(should_link_listing(title, 8000.0, parsed))

    def test_real_birkin_linked(self):
        title = "Hermes Birkin 30 Authentic Etoupe/Beige"
        parsed = parse_title(title)
        self.assertTrue(should_link_listing(title, 14600.0, parsed))

    def test_hac_not_subject_to_birkin_floor(self):
        title = "Authentic HERMES Haut à Courroies 32 HAC Birkin red Box leather vintage 1995"
        parsed = parse_title(title)
        self.assertEqual(parsed.model, "Haut à Courroies")
        self.assertTrue(should_link_listing(title, 7999.0, parsed))


if __name__ == "__main__":
    unittest.main()
