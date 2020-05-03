import unittest

from sr.comp.http.query_utils import parse_difference_string


class ParseDifferenceStringTests(unittest.TestCase):
    def test_exact_equal(self) -> None:
        self.assertTrue(
            parse_difference_string('4')(4),
        )

    def test_exact_gt(self) -> None:
        self.assertFalse(
            parse_difference_string('4')(6),
        )

    def test_exact_lt(self) -> None:
        self.assertFalse(
            parse_difference_string('4')(2),
        )

    def test_parse_failure(self) -> None:
        with self.assertRaises(ValueError):
            parse_difference_string('cheese', int)

    def test_upper_equal(self) -> None:
        self.assertTrue(
            parse_difference_string('..4')(4),
        )

    def test_upper_gt(self) -> None:
        self.assertFalse(
            parse_difference_string('..4')(6),
        )

    def test_upper_lt(self) -> None:
        self.assertTrue(
            parse_difference_string('..4')(2),
        )

    def test_lower_equal(self) -> None:
        self.assertTrue(
            parse_difference_string('4..')(4),
        )

    def test_lower_gt(self) -> None:
        self.assertTrue(
            parse_difference_string('4..')(6),
        )

    def test_lower_lt(self) -> None:
        self.assertFalse(
            parse_difference_string('4..')(2),
        )

    def test_bounds_lt(self) -> None:
        self.assertFalse(
            parse_difference_string('4..6')(2),
        )

    def test_bounds_lower(self) -> None:
        self.assertTrue(
            parse_difference_string('4..6')(4),
        )

    def test_bounds_mid(self) -> None:
        self.assertTrue(
            parse_difference_string('4..6')(5),
        )

    def test_bounds_upper(self) -> None:
        self.assertTrue(
            parse_difference_string('4..6')(6),
        )

    def test_bounds_gt(self) -> None:
        self.assertFalse(
            parse_difference_string('4..6')(8),
        )

    def test_other_types(self) -> None:
        self.assertTrue(
            parse_difference_string('cheese..', str)('cheese'),
        )

    def test_other_types_negative(self) -> None:
        self.assertFalse(
            parse_difference_string('cheese..', str)(''),
        )

    def test_invalid_ds(self) -> None:
        with self.assertRaises(ValueError):
            parse_difference_string('1..2..3')

    def test_inverted_bounds(self) -> None:
        with self.assertRaises(ValueError):
            parse_difference_string('3..2')

    def test_double_open(self) -> None:
        with self.assertRaises(ValueError):
            parse_difference_string('..', str)
