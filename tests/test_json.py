from enum import Enum

from sr.comp.http.json_encoder import JsonEncoder


def get_encoder():
    return JsonEncoder(
        namedtuple_as_object=True,
        tuple_as_array=True,
    )


def test_simple():
    encoder = get_encoder()

    output = encoder.encode([1])

    assert "[1]" == output

    output = encoder.encode([1, 2, 3])

    assert "[1, 2, 3]" == output


def test_enum():
    encoder = get_encoder()

    val = "the-string-value"

    class Thing(Enum):
        yup = val

    output = encoder.encode(Thing.yup)
    expected = '"{}"'.format(val)

    assert output == expected
