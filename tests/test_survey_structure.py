# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, division

import unittest
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from pymeera.survey import SurveyStructure, VariableStructure


class TestSurveyStructures(unittest.TestCase):

    def test_create_variable(self):
        vs = VariableStructure(
            variable_id='a1',
            variable_label='q2@3_label',
            variable_values={11: 'a1_a'}
        )

        self.assertEqual(vs.variable_id, 'a1')
        self.assertEqual(vs.variable_label, 'q2@3_label')

    def test_add_variable(self):
        ss = SurveyStructure()
        vs = VariableStructure(
            variable_id='a1',
            variable_label='q2@3_label',
            variable_values={11: 'a1_a'}
        )
        ss.add_variable(vs)

        self.assertEqual(ss.get_variable_by_id('a1').variable_label, 'q2@3_label')

    def test_to_hierarchical(self):

        ss = SurveyStructure()

        ss.add_variable(VariableStructure(
            variable_id='a1_1',
            variable_label='q2@1_label',
            variable_values={11: 'a1_a'}
        ))

        ss.add_variable(VariableStructure(
            variable_id='a1_2',
            variable_label='q2@2_label',
            variable_values={12: 'a1_b'}
        ))

        ss.add_variable(VariableStructure(
            variable_id='a2_1',
            variable_label='q2@3_label',
            variable_values={13: 'a1_c'}
        ))

        ss.add_variable(VariableStructure(
            variable_id='a2_2',
            variable_label='q2@4_label',
            variable_values={14: 'a1_d'}
        ))

        ss = ss.to_hierarchical()
        children = ss.get_variable_by_id('a1').variable_children
        vals = ss.get_variable_by_id('a1').variable_values

        self.assertEqual(len(children), 2)
        self.assertEqual(list(map(lambda x: x.variable_id, children)), ['a1_1', 'a1_2'])
        self.assertEqual(vals, {11: 'a1_a', 12: 'a1_b'})

