"""Analytical examples, boundary cases, and mathematical invariants."""

import math
import random
import unittest

from checker.similarity import cosine_similarity, normalize_text, similarity


class NormalizationTests(unittest.TestCase):
    def test_chinese_punctuation_and_whitespace(self):
        self.assertEqual(normalize_text("你好，世界！\n 测试\t"), "你好世界测试")

    def test_fullwidth_case_and_numbers(self):
        self.assertEqual(normalize_text("ＡＢＣ１２３ Straße"), "abc123strasse")

    def test_unicode_composed_and_decomposed(self):
        self.assertEqual(normalize_text("Café"), normalize_text("Cafe\u0301"))

    def test_only_punctuation_and_emoji(self):
        self.assertEqual(normalize_text("，。！\n 😀"), "")


class CosineTests(unittest.TestCase):
    def test_analytical_value(self):
        self.assertAlmostEqual(cosine_similarity({"a": 3, "b": 4}, {"a": 1}), 0.6)

    def test_disjoint_vectors(self):
        self.assertEqual(cosine_similarity({"甲": 2}, {"乙": 3}), 0.0)

    def test_zero_left_norm(self):
        self.assertEqual(cosine_similarity({}, {"a": 2}), 0.0)

    def test_zero_right_norm(self):
        self.assertEqual(cosine_similarity({"a": 2}, {}), 0.0)

    def test_both_zero_norms(self):
        self.assertEqual(cosine_similarity({"a": 0}, {"b": 0}), 0.0)

    def test_proportional_vectors(self):
        self.assertAlmostEqual(cosine_similarity({"a": 1, "b": 2}, {"a": 2, "b": 4}), 1)

    def test_sparse_optimization_matches_dense_reference(self):
        rng = random.Random(12345)
        for _ in range(100):
            left = {
                str(key): rng.randrange(1, 20) for key in rng.sample(range(60), rng.randrange(40))
            }
            right = {
                str(key): rng.randrange(1, 20) for key in rng.sample(range(60), rng.randrange(40))
            }
            keys = sorted(set(left) | set(right))
            a = [left.get(key, 0) for key in keys]
            b = [right.get(key, 0) for key in keys]
            denominator = math.sqrt(sum(x * x for x in a) * sum(y * y for y in b))
            expected = sum(x * y for x, y in zip(a, b)) / denominator if denominator else 0.0
            self.assertAlmostEqual(cosine_similarity(left, right), expected, places=12)


class SimilarityTests(unittest.TestCase):
    def test_identical_chinese(self):
        self.assertEqual(similarity("软件工程与测试", "软件工程与测试"), 1.0)

    def test_formatting_changes_are_ignored(self):
        self.assertEqual(similarity("今天，天气晴。ABC １２３", "今天 天气晴 abc123"), 1.0)

    def test_disjoint_text(self):
        self.assertEqual(similarity("甲乙丙丁", "戊己庚辛"), 0.0)

    def test_hand_calculated_weighted_score(self):
        # Unigram = 2/3; bigram = 1/2; 0.3*(2/3) + 0.7*(1/2) = 0.55.
        self.assertAlmostEqual(similarity("abc", "abd"), 0.55)

    def test_empty_original(self):
        self.assertEqual(similarity("", "文字"), 0.0)

    def test_empty_candidate(self):
        self.assertEqual(similarity("文字", ""), 0.0)

    def test_both_empty(self):
        self.assertEqual(similarity("", ""), 0.0)

    def test_no_usable_characters(self):
        self.assertEqual(similarity("\n，。", "！😀"), 0.0)

    def test_single_character_equal(self):
        self.assertEqual(similarity("甲", "甲"), 1.0)

    def test_single_character_unequal(self):
        self.assertEqual(similarity("甲", "乙"), 0.0)

    def test_single_character_fallback(self):
        self.assertAlmostEqual(similarity("甲", "甲乙"), 1 / math.sqrt(2))

    def test_append_changes_score(self):
        self.assertGreater(similarity("今天晚上去看电影", "今天晚上去看电影然后吃饭"), 0.7)
        self.assertLess(similarity("今天晚上去看电影", "今天晚上去看电影然后吃饭"), 1.0)

    def test_delete_changes_score(self):
        self.assertGreater(similarity("今天晚上去看电影", "今天去看电影"), 0.6)
        self.assertLess(similarity("今天晚上去看电影", "今天去看电影"), 1.0)

    def test_order_matters(self):
        self.assertAlmostEqual(similarity("甲乙丙丁", "丁丙乙甲"), 0.3)

    def test_symmetry_and_bounds_on_seeded_random_text(self):
        rng = random.Random(3224004157)
        for _ in range(150):
            left = "".join(rng.choices("论文查重ABC１２，。", k=rng.randrange(50)))
            right = "".join(rng.choices("论文查重ABC１２，。", k=rng.randrange(50)))
            with self.subTest(left=left, right=right):
                score = similarity(left, right)
                self.assertGreaterEqual(score, 0.0)
                self.assertLessEqual(score, 1.0)
                self.assertAlmostEqual(score, similarity(right, left))

    def test_long_repetitive_input(self):
        score = similarity("软件测试" * 25000, "软件测试" * 24999 + "数据分析")
        self.assertGreater(score, 0.99)
