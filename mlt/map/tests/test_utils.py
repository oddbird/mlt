from django.utils.unittest import TestCase



__all__ = ["LetterKeyTest"]



class LetterKeyTest(TestCase):
    @property
    def func(self):
        from mlt.map.utils import letter_key
        return letter_key


    def test_output(self):
        output = [
            (1, "A"),
            (2, "B"),
            (3, "C"),
            (25, "Y"),
            (26, "Z"),
            (27, "AA"),
            (28, "AB"),
            (29, "AC"),
            (52, "AZ"),
            (53, "BA"),
            (54, "BB"),
            (55, "BC"),
            ]
        target = [i[1] for i in output]
        actual = [self.func(i[0]) for i in output]
        self.assertEqual(target, actual)
