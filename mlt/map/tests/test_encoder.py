import json
from django.test import TestCase



__all__ = ["IterEncoderTest"]



class IterEncoderTest(TestCase):
    @property
    def encoder(self):
        from mlt.map.encoder import IterEncoder
        return IterEncoder


    def test_generator(self):
        def g():
            for i in range(2):
                yield i

        self.assertEqual(json.dumps(g(), cls=self.encoder), "[0, 1]")


    def test_listiterator(self):
        self.assertEqual(json.dumps(iter([1, 2]), cls=self.encoder), "[1, 2]")


    def test_list(self):
        self.assertEqual(json.dumps([2, 3], cls=self.encoder), "[2, 3]")


    def test_dict(self):
        self.assertEqual(json.dumps({3: 4}, cls=self.encoder), '{"3": 4}')


    def test_unknown(self):
        class Something(object):
            pass

        with self.assertRaises(TypeError):
            json.dumps(Something(), cls=self.encoder)
