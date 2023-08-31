from unittest import TestCase

from discarding_queue import DiscardingQueue


class TestDiscardingQueue(TestCase):
    def test_create_simple(self):
        q = DiscardingQueue()
        self.assertIsNotNone(q)

    def test_create(self):
        q = DiscardingQueue((1, 2, 3, 4), max_len=5)
        self.assertEqual(4, len(q))
        self.assertEqual(5, q.max_len)

    def test_append(self):
        q = DiscardingQueue((1, 2, 3), max_len=4)
        q.append(4)
        self.assertEqual(4, len(q))
        self.assertListEqual([1, 2, 3, 4], list(q))

    def test_append_with_discard(self):
        q = DiscardingQueue((1, 2, 3), max_len=3)
        q.append(4)
        self.assertEqual(3, len(q))
        self.assertListEqual([2, 3, 4], list(q))

    def test_pop(self):
        q = DiscardingQueue((1, 2, 3), max_len=4)
        self.assertEqual(1, q.pop())
        self.assertEqual(2, len(q))

    def test_index(self):
        q = DiscardingQueue((1, 2, 3), max_len=4)
        self.assertEqual(2, q[1])
        self.assertEqual(3, len(q))
