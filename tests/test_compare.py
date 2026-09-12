from __future__ import annotations

import unittest

from compare_local import exact_mcnemar_p


class CompareTests(unittest.TestCase):
    def test_exact_mcnemar_without_discordance(self) -> None:
        self.assertEqual(exact_mcnemar_p(0, 0), 1.0)

    def test_exact_mcnemar_one_sided_discordance(self) -> None:
        self.assertAlmostEqual(exact_mcnemar_p(5, 0), 0.0625)


if __name__ == "__main__":
    unittest.main()
