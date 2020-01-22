import unittest
import random
from apachescan.guard import Guard
from apachescan.guard import WrongArguments


class TestGuard(unittest.TestCase):

    def test_guard_wrong_arguments(self):
        self.assertRaises(WrongArguments, Guard, -1, 10, "")
        self.assertRaises(WrongArguments, Guard, 0, 10, "")
        self.assertRaises(WrongArguments, Guard, None, 10, "")
        self.assertRaises(WrongArguments, Guard, 1, None, "")

    def test_guard_negative_threshold(self):
        key = "value"
        guard = Guard(1, -1, key)
        self.assertTrue(guard.is_threshold_reach())
        self.assertEqual(guard.get_key(), key)

    def test_guard_array(self):
        key = "short_array"
        threshold = 10
        guard = Guard(20, threshold, key)
        self.assertFalse(guard.is_threshold_reach())
        self.assertEqual(guard.get_key(), key)
        random_numbers = []

        # with double number some variation occurs because of rounding error
        for i in range(10):
            random_numbers.append(int(random.random() * 10))

        accumulated_value = 0
        for value in random.sample(random_numbers, 10):
            accumulated_value += value
            guard.append(value)
            self.assertEqual(guard.get_value(),
                             accumulated_value)
            self.assertEqual(guard.is_threshold_reach(),
                             accumulated_value > threshold)

        self.assertEqual(guard.get_key(), key)

        new_accumulated_value = 0
        for value in random.sample(random_numbers, 10):
            accumulated_value += value
            new_accumulated_value += value
            guard.append(value)
            self.assertEqual(guard.is_threshold_reach(),
                             accumulated_value > threshold)
            self.assertEqual(guard.get_value(),
                             accumulated_value)

        for value in random.sample(random_numbers, 10):
            new_accumulated_value += value
            guard.append(value)

        self.assertEqual(guard.is_threshold_reach(),
                         new_accumulated_value > threshold)
        self.assertEqual(guard.get_value(),
                         new_accumulated_value)

        self.assertEqual(guard.get_key(), key)
        self.assertIsNotNone(str(guard))


if __name__ == "__main__":
    unittest.main()
