import math
import unittest

from ia_reference.numeric import cross_entropy, matmul, matvec, softmax


class NumericReferenceTests(unittest.TestCase):
    def test_matvec_reference_result(self):
        self.assertEqual(matvec([[1, 2], [3, 4]], [5, 6]), [17.0, 39.0])

    def test_matmul_reference_result(self):
        self.assertEqual(
            matmul([[1, 2, 3], [4, 5, 6]], [[7, 8], [9, 10], [11, 12]]),
            [[58.0, 64.0], [139.0, 154.0]],
        )

    def test_softmax_is_stable_and_normalized(self):
        result = softmax([1000.0, 1001.0, 999.0])
        self.assertTrue(all(math.isfinite(item) for item in result))
        self.assertAlmostEqual(sum(result), 1.0, places=12)
        self.assertGreater(result[1], result[0])

    def test_cross_entropy_matches_known_value(self):
        self.assertAlmostEqual(cross_entropy([0.0, 0.0], 0), math.log(2.0))
        self.assertGreater(cross_entropy([0.0, 2.0], 0), cross_entropy([0.0, 2.0], 1))

    def test_rejects_shape_errors(self):
        with self.assertRaisesRegex(ValueError, "columns must match vector"):
            matvec([[1, 2]], [1])
        with self.assertRaisesRegex(ValueError, "columns must match right matrix rows"):
            matmul([[1, 2]], [[1, 2]])

    def test_rejects_invalid_numeric_inputs(self):
        for bad in (True, float("nan"), float("inf"), 1_000_001):
            with self.subTest(value=bad):
                with self.assertRaises(ValueError):
                    softmax([bad, 0.0])
        with self.assertRaisesRegex(ValueError, "rectangular"):
            matmul([[1.0], [2.0, 3.0]], [[1.0], [2.0]])
        with self.assertRaisesRegex(ValueError, "target_index"):
            cross_entropy([1.0, 2.0], True)
        with self.assertRaisesRegex(ValueError, "outside"):
            cross_entropy([1.0, 2.0], 2)

    def test_bounded_large_inputs_remain_finite(self):
        result = matvec([[1_000_000.0, 1_000_000.0]], [1_000_000.0, 1_000_000.0])
        self.assertEqual(result, [2_000_000_000_000.0])
        self.assertTrue(all(math.isfinite(item) for item in result))


if __name__ == "__main__":
    unittest.main()
