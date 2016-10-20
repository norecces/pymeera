# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, division
import warnings
from pyparsing import (Literal, CaselessLiteral, Word, Group, ungroup,
                       ZeroOrMore, Forward, alphanums, ParseResults)

from itertools import product


class Expression(object):

    def __init__(self):

        _by = CaselessLiteral('by')
        _add = Literal('+').suppress()
        _nest = Literal('>').suppress()
        _lpar = Literal('(').suppress()
        _rpar = Literal(')').suppress()
        _variable = ~_by + Word(alphanums + '_' + '.')

        def _p_act(s, l , t):
            # dirty hack to unpack group permutations
            # if has lists in result than it is multidimension cross
            levels_array = list(map(lambda v: isinstance(v, ParseResults), t))
            if sum(levels_array):
                # find where second level of cross starts
                first_cross_starts_at = levels_array.index(True)
                t = t.asList()
                levels = [t[:first_cross_starts_at]]
                levels.extend(t[first_cross_starts_at:])
                return list(map(lambda v: list(v), product(*levels)))
            return t

        self.expr = Forward()
        atom = _variable | (_lpar + ungroup(self.expr) + _rpar)
        cross = Forward()
        cross << (atom + ZeroOrMore(Group(_nest + atom))).setParseAction(_p_act)
        add = Forward()
        add << cross + ZeroOrMore(_add + cross)
        self.expr << Group(add + ZeroOrMore(add))

    @classmethod
    def parse(cls, expression):
        """
        Parses string tables description
        Allows only 3 nested levels (defined by "by" keyword)
        First nested level - rows,
        Second - columns
        Third - dimension (optional, is used for pandas.Panel creation)

        :param expression: string
        :return: list, structure that defines how to cross variables

        Example:
             ExpressionParser.parse('q1 by q2 + (q3 + q4) > q5 > q6 + q6 > q7 by q8')
             {
                rows: [['q1']],
                columns: [
                    ['q2'],
                    ['q3', 'q5', 'q6'],
                    ['q4', 'q5', 'q6'],
                    ['q6', 'q7']
                ],
                additional_axis: [['q8']]
             }

        """
        parser = cls()

        parts = expression.split(' by ')

        if len(parts) < 2:
            raise Exception('You have defined less than 2 dimensions')
        if len(parts) > 3:
            warnings.warn('You have defined more than 3 dimensions')

        rows = parser._parse_part(part=parts[0]).asList()
        columns = parser._parse_part(part=parts[1]).asList()
        additional_axis = None if len(parts) < 3 else parser._parse_part(part=parts[2]).asList()

        def _to_one_depth_list(item):
            if isinstance(item, (list, tuple)):
                return item
            else:
                return [item]

        return {
            'rows': list(map(_to_one_depth_list, rows)),
            'columns': list(map(_to_one_depth_list, columns)),
            'additional_axis': list(map(_to_one_depth_list, additional_axis)) if additional_axis else None
        }

    def _parse_part(self, part):
        banner = self.expr.parseString(part)
        return banner[0]


if __name__ == '__main__':
    print(Expression.parse('q1+q2 by q2 + (q3 + q4) > q5 > q6 + q6 > q7'))