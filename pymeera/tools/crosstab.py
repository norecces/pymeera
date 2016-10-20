# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, division
import warnings

import numpy as np
import pandas as pd

from utils.exprparser import Expression
from utils.support import hash_index, unhash_index, equlize_size
import itertools


class Crosstab(object):

    def __init__(self, data, expression=None, **kwargs):

        self.rows = kwargs.pop('rows', None)
        self.columns = kwargs.pop('columns', None)
        self.additional_axis = kwargs.pop('additional_axis', None)

        if self.additional_axis:
            warnings.warn('Additional axis is not supported now')

        self.column_total = kwargs.pop('column_total', True)

        self.result = None
        self._crosstab = None

        if expression is not None:
            parsed = Expression.parse(expression=expression)
            self.rows = parsed['rows']
            self.columns = parsed['columns']
            self.additional_axis = parsed['additional_axis']

        self._check(data)

        self.title = kwargs.pop('title', '')
        self.subtitle = kwargs.pop('subtitle', '')
        self.footer = kwargs.pop('footer', '')
        self.corner = kwargs.pop('corner', '')

        self.weight = kwargs.pop('weight', None)  # weight is variable

        self.data = data[self._flat_variables()].copy()

        self._evaluated_columns = None
        self._evaluated_index = None

        self._evaluate()

    def _flat_variables(self):
        flat_rows = [item for sublist in self.rows for item in sublist]
        flat_columns = [item for sublist in self.columns for item in sublist]
        flat_3rd_axis = None if not self.additional_axis else [item for sublist in self.additional_axis for item in sublist]

        all_variables = flat_rows
        all_variables.extend(flat_columns)
        if flat_3rd_axis is not None:
            all_variables.extend(flat_3rd_axis)

        all_variables = list(set(all_variables))
        return all_variables

    def _check(self, data):

        if self.rows is None or self.columns is None:
            raise Exception('Rows are empty')

        if not len(self.rows) or not len(self.columns):
            raise Exception('Columns are empty')

        self._check_variable_existence(data)

    def _check_variable_existence(self, data):

        all_variables = self._flat_variables()

        for variable in all_variables:
            if variable not in data.columns:
                raise Exception('Variable "%s" is not defined in columns' % (variable, ))

    def _compute_total_and_weights(self):
        """
            Adds __Total__ column to dataframe based on specific columns:
            If Respondent has at least one answer in specified columns - than percentage
            will be evaluated including this respondent in base. It is needed to correctly
            compute percentage in checkbox(multi) questions.
        """
        self.data.loc[:, '__TOTAL__'] = None
        self.data.loc[:, '__WEIGHT__'] = None

        flat_rows = list(set([item for sublist in self.rows for item in sublist]))

        self.data.loc[df[flat_rows].count(axis=1).apply(lambda x: x > 0), '__TOTAL__'] = 1
        self.data.loc[df[flat_rows].count(axis=1).apply(lambda x: x > 0), '__WEIGHT__'] = 1

        if self.weight:
            self.data.loc[df[flat_rows].count(axis=1).apply(lambda x: x > 0), '__WEIGHT__'] = self.data.loc[df[flat_rows].count(axis=1).apply(lambda x: x > 0), self.weight]

    def _compute_base(self, columns):

        base_total, base_row = None, None

        # if self.column_total:
        #     base_total = pd.crosstab(self.data['__TOTAL__'], self.data['__WEIGHT__'])

        if self.columns is not None:
            base_row = pd.crosstab(index=self.data['__TOTAL__'],
                                   columns=list(map(lambda v: self.data[v], columns)),
                                   values=self.data['__WEIGHT__'],
                                   aggfunc=np.sum
                                   )
            base_row.columns = list(
                map(lambda v: hash_index(v, columns), base_row.columns.values)
            )

            base_row.index = pd.MultiIndex.from_tuples((('$BASE$', '$COUNT$'), ))
            base_row.index.names = ['__DESCRIPTION__', '__STATISTICS__TYPE__']

        # if base_total is None and base_column is None:
        #     return pd.crosstab(self.data['__TOTAL__'], self.data['__WEIGHT__'])
        #
        # if base_total is not None and base_column is not None:
        #     return pd.concat([base_total, base_column], axis=1)

        if base_row is not None:
            return base_row

        return base_total

    def _compute_index_shape(self):

        def _shape_of_group(gr):
            if isinstance(gr, (str, bytes, bool)):
                return 1
            return len(gr)

        return (
            max(map(lambda x: _shape_of_group(x), self.rows)),
            max(map(lambda x: _shape_of_group(x), self.columns))
        )

    def _evaluate(self):

        self._compute_total_and_weights()

        row_result = None

        for row_group_idx, row_group in enumerate(self.rows):
            col_result = None
            for column_group in self.columns:

                ct = pd.crosstab(index=list(map(lambda v: self.data[v], row_group)),
                                 columns=list(map(lambda v: self.data[v], column_group)),
                                 values=self.data['__WEIGHT__'],
                                 aggfunc=np.sum)

                ct.index = list(
                    map(lambda v: hash_index(v, row_group), ct.index.values)
                )
                ct.index.name = '__DESCRIPTION__'

                # append more info about cross
                ct['__STATISTICS__TYPE__'] = '$COUNT$'
                ct = ct.set_index('__STATISTICS__TYPE__', append=True)

                ct.columns = list(
                    map(lambda v: hash_index(v, column_group), ct.columns.values)
                )

                if row_group_idx == len(self.rows) - 1:
                    # if last one iteration lets append base row
                    base = self._compute_base(columns=column_group)
                    ct = pd.concat([ct, base], axis=0)
                col_result = pd.concat([col_result, ct], axis=1)

            #  without reindex column order will be lost
            row_result = pd.concat([row_result, col_result], axis=0).reindex(columns=col_result.columns)

        self._crosstab = row_result.copy()
        del row_result, col_result

        self._evaluated_columns = self._crosstab.columns.copy()
        self._evaluated_index = self._crosstab.index.copy()

        self._map_names()

    def _map_names(self):
        unhashed_columns = list(map(lambda x: unhash_index(x), self._evaluated_columns))
        cols = equlize_size(unhashed_columns)
        # TODO: map labels to variables and values
        cols = tuple(map(lambda x: tuple(itertools.chain(*x)), cols))
        self._crosstab.columns = pd.MultiIndex.from_tuples(cols)

        unhashed_index = list(map(lambda x: unhash_index(x[0]), self._evaluated_index))
        idx = equlize_size(unhashed_index)
        # TODO: map labels to variables and values
        idx = tuple(map(lambda x: tuple(itertools.chain(*x)), idx))
        self._crosstab.index = pd.MultiIndex.from_tuples(idx)

    def __repr__(self):
        return self._crosstab.__repr__()

    def as_cpct(self):
        self._crosstab.iloc[:-1, :] = self._crosstab.iloc[:-1, :] / self._crosstab.iloc[-1, :]


if __name__ == '__main__':
    import pandas as pd
    df = pd.DataFrame(
        [[1, 2, 1, 2], [None, 2, 1, 2], [1, 2, 1, 4], [None, None, 1, 4]],
        columns=['q1', 'q2', 'Всего', 'q3']
    )

    df.loc[[0, 2], 'r1'] = 2
    df.loc[[1, 3], 'r1'] = 3
    df.loc[[0, 2], 'r2'] = 2
    df.loc[[1, 3], 'r2'] = 3
    cross = Crosstab(data=df, rows=[['q1'], ['q2', 'q3']], columns=[['Всего'], ['r1', 'r2']])

    cross.as_cpct()

    print(cross)




