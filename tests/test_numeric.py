import math
import unittest

from ia_reference.numeric import cross_entropy, matmul, matvec, softmax


class NumericReferenceTests(unittest.TestCase):
    def test_matvec_and_matmul(self):
        self.assertEqual(matvec([[1, 2], [3, 4]], [2, 1]), [4.0, 10.0])
        self.assertEqual(matmul([[1, 2], [3, 4]], [[2, 0], [1, 2]]), [[4.0, 4.0], [10.0, 8.0]])

    def test_softmax_is_stable_and_normalized(self):
        result = softmax([1000.0, 1001.0, 999.0])
        self.assertTrue(all(math.isfinite(x) for x in result))
        self.assertAlmostEqual(sum(result), 1.0)
        self.assertGreater(result[1], result[0])
        self.assertGreater(result[0], result[2])

    def test_cross_entropy_matches_known_value(self):
        self.assertAlmostEqual(cross_entropy([0.0, 0.0], 0), math.log(2.0))
        self.assertAlmostEqual(cross_entropy([0.0, 4.0], 1), math.log1p(math.exp(-4.0)))

    def test_rejects_oversized_vectors_and_matrices(self):
        with self.assertRaisesRegex(ValueError, "vector length limit"):
            softmax([0.0] * 100_001)
        with self.assertRaisesRegex(ValueError, "column limit"):
            matvec([[0.0] * 4097], [0.0] * 4097)

    def test_rejects_excessive_matrix_multiplication_work(self):
        left = [[1.0] * 200 for _ in range(250)]
        right = [[1.0] * 250 for _ in range(200)]
        with self.assertRaisesRegex(ValueError, "operation budget"):
            matmul(left, right)

    def test_rejects_shape_errors(self):
        with self.assertRaisesRegex(ValueError, "columns"):
            matvec([[1.0, 2.0]], [1.0])
        with self.assertRaisesRegex(ValueError, "rows"):
            matmul([[1.0, 2.0]], [[1.0, 2.0]])

    def test_rejects_boolean_nonfinite_and_extreme_values(self):
        with self.assertRaisesRegex(ValueError, "finite numbers"):
            softmax([True, 0.0])
        with self.assertRaisesRegex(ValueError, "finite numbers"):
            matvec([[float("inf")]], [1.0])
        with self.assertRaisesRegex(ValueError, "magnitude bound"):
            softmax([1_000_001.0])
        with self.assertRaisesRegex(ValueError, "integer"):
            cross_entropy([1.0, 2.0], True)

    def test_rejects_invalid_target_index(self):
        for index in (-1, 2):
            with self.subTest(index=index), self.assertRaisesRegex(ValueError, "outside"):
                cross_entropy([1.0, 2.0], index)


if __name__ == "__main__":
    unittest.main()
