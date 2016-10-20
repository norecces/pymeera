# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, division

import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pymeera.utils.exprparser import Expression


class TestExpressionParser(unittest.TestCase):

    def test_simple(self):
        expr = 'q1 by q2'
        parsed = Expression.parse(expression=expr)

        self.assertEqual([['q1']], parsed['rows'])
        self.assertEqual([['q2']], parsed['columns'])
        self.assertIsNone(parsed['additional_axis'])

    def test_simple_pads(self):
        expr = 'q1 by (q2)'
        parsed = Expression.parse(expression=expr)

        self.assertEqual([['q1']], parsed['rows'])
        self.assertEqual([['q2']], parsed['columns'])
        self.assertIsNone(parsed['additional_axis'])

    def test_plus(self):
        expr = 'q1 by q2 + q3'
        parsed = Expression.parse(expression=expr)

        self.assertEqual([['q1']], parsed['rows'])
        self.assertEqual([['q2'], ['q3']], parsed['columns'])
        self.assertIsNone(parsed['additional_axis'])

    def test_simple_plus_pads(self):
        expr = 'q1 by (q2 + q3)'
        parsed = Expression.parse(expression=expr)

        self.assertEqual([['q1']], parsed['rows'])
        self.assertEqual([['q2'], ['q3']], parsed['columns'])
        self.assertIsNone(parsed['additional_axis'])

    def test_simple_cross(self):
        expr = 'q1 by q2 > q3'
        parsed = Expression.parse(expression=expr)

        self.assertEqual([['q1']], parsed['rows'])
        self.assertEqual([['q2', 'q3']], parsed['columns'])
        self.assertIsNone(parsed['additional_axis'])

    def test_simple_cross_pads(self):
        expr = 'q1 by (q2 > q3)'
        parsed = Expression.parse(expression=expr)

        self.assertEqual([['q1']], parsed['rows'])
        self.assertEqual([['q2', 'q3']], parsed['columns'])
        self.assertIsNone(parsed['additional_axis'])

    def test_simple_cross_plus_pads(self):
        expr = 'q1 by (q2 + q3) > q4'
        parsed = Expression.parse(expression=expr)

        self.assertEqual([['q1']], parsed['rows'])
        self.assertEqual([['q2', 'q4'], ['q3', 'q4']], parsed['columns'])
        self.assertIsNone(parsed['additional_axis'])

    def test_stacked_cross_plus_pads(self):
        expr = 'q1 by q5 + (q2 + q3) > q4'
        parsed = Expression.parse(expression=expr)

        self.assertEqual([['q1']], parsed['rows'])
        self.assertEqual([['q5'], ['q2', 'q4'], ['q3', 'q4']], parsed['columns'])
        self.assertIsNone(parsed['additional_axis'])

    def test_multidim(self):
        expr = 'q1 by q5 + (q2 + q3) > (q4 + q5) > q6 by q7'
        parsed = Expression.parse(expression=expr)

        self.assertEqual([['q1']], parsed['rows'])
        self.assertEqual(
            [['q5'], ['q2', 'q4', 'q6'], ['q2', 'q5', 'q6'], ['q3', 'q4', 'q6'], ['q3', 'q5', 'q6']],
            parsed['columns']
        )
        self.assertEqual([['q7']], parsed['additional_axis'])
