import json
import unittest
from pathlib import Path

from bags.title_parser import match_product, parse_title


FIXTURES = Path(__file__).parent / "fixtures" / "matching_cases.json"


class TitleParserTest(unittest.TestCase):
    def test_hermes_birkin_full_title(self):
        parsed = parse_title("Hermès Togo Birkin 30 Gold")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.brand, "Hermès")
        self.assertEqual(parsed.model, "Birkin")
        self.assertEqual(parsed.size, "30")
        self.assertEqual(parsed.leather, "Togo")
        self.assertEqual(parsed.color, "Gold")

    def test_chanel_classic_flap(self):
        parsed = parse_title("Chanel Lambskin Quilted Classic Double Flap Bag")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.brand, "Chanel")
        self.assertEqual(parsed.model, "Classic Double Flap")
        self.assertEqual(parsed.leather, "Lambskin")

    def test_lv_damier_ebene_canvas_detected_as_leather(self):
        parsed = parse_title("Louis Vuitton Damier Ebene Alma BB")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.model, "Alma")
        self.assertEqual(parsed.leather, "Damier Ebene")

    def test_lv_monogram_empreinte_detected_as_leather(self):
        parsed = parse_title("Louis Vuitton Monogram Empreinte Braided Pochette Metis Shoulder Bag")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.model, "Pochette Métis")
        self.assertEqual(parsed.leather, "Monogram Empreinte")

    def test_saint_laurent_velvet_detected_as_leather(self):
        parsed = parse_title("Saint Laurent LouLou Velvet w/ Strap & Dust Bag")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.model, "Loulou")
        self.assertEqual(parsed.leather, "Velvet")

    def test_ebay_birkin_title(self):
        parsed = parse_title("Hermes Birkin 30 Authentic Etoupe/Beige")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.brand, "Hermès")
        self.assertEqual(parsed.model, "Birkin")
        self.assertEqual(parsed.size, "30")
        self.assertEqual(parsed.color, "Etoupe")

    def test_hac_title(self):
        parsed = parse_title("Authentic HERMES Birkin HAC Haut à Courroies 32 brown courchevel leather bag")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.model, "Haut à Courroies")
        self.assertEqual(parsed.size, "32")
        self.assertEqual(parsed.leather, "Courchevel")
        self.assertEqual(parsed.color, "Brown")

    def test_accessory_without_model_returns_none(self):
        parsed = parse_title("Clear Silicone Protective cover for handbag stud feet")
        self.assertIsNone(parsed)

    def test_gift_box_does_not_match_box_leather(self):
        parsed = parse_title("HERMES Birkin 30 empty Gift Box 36×38×15.5cm")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.model, "Birkin")
        self.assertIsNone(parsed.leather)

    def test_hardware_not_parsed_as_color(self):
        parsed = parse_title(
            "Hermes Birkin 30 Tanzanite BlueTogo Leather Bag Gold Tone D Stamp 2019"
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.color, "Tanzanite Blue")
        self.assertEqual(parsed.leather, "Togo")

    def test_vert_anglais_kelly(self):
        parsed = parse_title(
            "Hermes Vert Anglais Epsom Kelly 32 Sellier 2way Handbag"
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.model, "Kelly")
        self.assertEqual(parsed.color, "Vert Anglais")
        self.assertEqual(parsed.leather, "Epsom")

    def test_trench_birkin(self):
        parsed = parse_title(
            "HERMES Birkin 30 Togo Leather Trench Hand Bag Purse 90303158"
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.model, "Birkin")
        self.assertEqual(parsed.size, "30")
        self.assertEqual(parsed.color, "Trench")
        self.assertEqual(parsed.leather, "Togo")

    def test_cascade_tricolor_birkin(self):
        parsed = parse_title(
            "Authentic Hermes Birkin 35 Limited edition Cascade Tricolor Clemence Swift"
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.model, "Birkin")
        self.assertEqual(parsed.size, "35")
        self.assertEqual(parsed.color, "Cascade Tricolor")
        self.assertEqual(parsed.leather, "Clemence")

    def test_vert_vertigo_birkin(self):
        parsed = parse_title(
            "Authentic Hermès Birkin 30 Vert Vertigo Togo Palladium Hardware (PHW) - Pre-love"
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.model, "Birkin")
        self.assertEqual(parsed.size, "30")
        self.assertEqual(parsed.color, "Vert Vertigo")
        self.assertEqual(parsed.leather, "Togo")

    def test_chanel_cc_flap(self):
        parsed = parse_title(
            "CHANEL Black Quilted CC Flap Turn Lock Gold Chain Crossbody Bag Dust Bag"
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.brand, "Chanel")
        self.assertEqual(parsed.model, "Classic Flap")
        self.assertEqual(parsed.color, "Black")

    def test_chanel_single_flap_maxi(self):
        parsed = parse_title(
            "Chanel Maxi Single Flap Black Caviar Leather Silver Hardware Classic Quilted Bag"
        )
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.model, "Classic Flap")
        self.assertEqual(parsed.size, "Maxi")
        self.assertEqual(parsed.leather, "Caviar")

    def test_celine_luggage(self):
        parsed = parse_title("Celine Nano Luggage Tote Black Calfskin")
        self.assertEqual(parsed.brand, "Celine")
        self.assertEqual(parsed.model, "Luggage")

    def test_dior_lady_dior(self):
        parsed = parse_title("Christian Dior Lady Dior Medium Black Cannage Lambskin")
        self.assertEqual(parsed.brand, "Dior")
        self.assertEqual(parsed.model, "Lady Dior")

    def test_prada_galleria(self):
        parsed = parse_title("Prada Galleria Saffiano Black Bag")
        self.assertEqual(parsed.brand, "Prada")
        self.assertEqual(parsed.model, "Galleria")

    def test_saint_laurent_loulou(self):
        parsed = parse_title("Saint Laurent Loulou Medium Black Matelasse")
        self.assertEqual(parsed.brand, "Saint Laurent")
        self.assertEqual(parsed.model, "Loulou")

    def test_generic_saddle_word_rejected_for_unsupported_brand(self):
        # "Saddle" is a Dior model name but also a generic bag-shape term;
        # a brand we don't track must never inherit the Dior model gate.
        self.assertIsNone(parse_title("Coach Saddle Bag Tan Leather"))

    def test_chanel_reissue_double_flap(self):
        parsed = parse_title("CHANEL Reissue 2.55 Double Flap Chain Shoulder Bag Genuine")
        self.assertIsNotNone(parsed)
        self.assertEqual(parsed.model, "Classic Double Flap")

    def test_labelled_matching_fixture(self):
        cases = json.loads(FIXTURES.read_text())
        checked_fields = 0
        correct_fields = 0
        for case in cases:
            with self.subTest(title=case["title"]):
                parsed = parse_title(case["title"])
                expected = case["expected"]
                if expected is None:
                    self.assertIsNone(parsed)
                    continue
                self.assertIsNotNone(parsed)
                for field, value in expected.items():
                    checked_fields += 1
                    if getattr(parsed, field) == value:
                        correct_fields += 1
                    self.assertEqual(getattr(parsed, field), value)
        self.assertGreaterEqual(correct_fields / checked_fields, 0.95)

    def test_structured_aspects_override_title_fallback(self):
        result = match_product(
            "Hermes Birkin handbag",
            {
                "Brand": "Hermes",
                "Model": "Birkin",
                "Size": "30",
                "Exterior Color": "Noir",
                "Exterior Material": "Togo leather",
            },
        )
        self.assertIsNotNone(result.product)
        self.assertEqual(result.product.size, "30")
        self.assertEqual(result.product.color, "Black")
        self.assertEqual(result.product.leather, "Togo")
        self.assertEqual(result.method, "structured")
        self.assertGreaterEqual(result.confidence, 0.95)


if __name__ == "__main__":
    unittest.main()
