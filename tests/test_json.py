import unittest
from enum import Enum

from sr.comp.http.json_provider import JsonEncoder


class JsonTests(unittest.TestCase):
    def get_encoder(self) -> JsonEncoder:
        return JsonEncoder(
            namedtuple_as_object=True,
            tuple_as_array=True,
        )

    def test_simple(self) -> None:
        encoder = self.get_encoder()

        output = encoder.encode([1])

        self.assertEqual("[1]", output)

        output = encoder.encode([1, 2, 3])

        self.assertEqual("[1, 2, 3]", output)

    def test_enum(self) -> None:
        encoder = self.get_encoder()

        val = "the-string-value"

        class Thing(Enum):
            yup = val

        output = encoder.encode(Thing.yup)
        expected = '"{}"'.format(val)

        self.assertEqual(expected, output)
