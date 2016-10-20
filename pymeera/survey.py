# -*- coding: utf-8 -*-
from __future__ import print_function, unicode_literals, division
from copy import deepcopy
from collections import OrderedDict

import warnings

__author__ = 'norecces'
__contact__ = 'https://github.com/norecces'


class VariableStructure(object):
    __slots__ = ['variable_id', 'variable_type', 'variable_label', 'variable_children',
                 'variable_survey_type', 'variable_values']

    def __init__(self, variable_id, variable_type=None, variable_label='',
                 variable_children=None, variable_survey_type=None, variable_values=None):
        """

        :param variable_id: str, name of varible
        :param variable_type: str, type of variable one_of basic types, e.g. int, float, boolean ...
        :param variable_label: str
        :param variable_children: list of variable_ids
        :param variable_survey_type: str, survey type, e.g. checkbox, radio ...
        :param variable_values: dict or OrderDict of values and labels, {value_id_1: value_label_1, value_id_2: ....}
        :return:
        """

        self.variable_id = variable_id
        self.variable_type = variable_type
        self.variable_label = variable_label
        self.variable_children = variable_children if variable_children else []
        self.variable_survey_type = variable_survey_type
        self.variable_values = variable_values if variable_values else OrderedDict()

    def __repr__(self):
        return '%s' % (self.variable_id, )


class SurveyStructure(object):
    """
        Structure that describes survey variables and their relations
    """

    def __init__(self, is_hierarchical=False, multiple_choice_separator='_'):

        self._variables_list = OrderedDict()
        self.is_hierarchical = is_hierarchical
        self.multiple_choices_separator = multiple_choice_separator

    def __contains__(self, key):
        return key in self._variables_list.keys()

    @classmethod
    def from_list(cls, lst):
        survey_structure = cls()
        for item in lst:
            if isinstance(item, (dict, OrderedDict, VariableStructure)):
                survey_structure.add_variable(item)
            else:
                raise TypeError('item type %s is not instance of dict' % (type(item), ))
        return survey_structure

    def add_variable(self, variable):
        if isinstance(variable, (dict, OrderedDict)):
            variable = VariableStructure(**variable)

        if not isinstance(variable, VariableStructure):
            raise Exception('Variable object must be instance of VariableStructure or dict not %s' % (type(variable),))

        if variable.variable_id in self._variables_list:
            # overwrite existing variable
            warnings.warn('Variable %s was overwritten' % (variable.variable_id, ))
            self.remove(variable.variable_id)

        self._variables_list[variable.variable_id] = variable

    def get_variable_by_id(self, variable_id):
        return self._variables_list[variable_id]

    def get_all_variables_ids(self):
        return list(self._variables_list.keys())

    def remove(self, variable_id):
        self._variables_list.pop(variable_id)

    def to_hierarchical(self, convert_exceptions=None):
        """
        Construct hierarchical structure from plain based on multiple choice separator
        Example:

        Got one Single Question and one Multiple Question (with 3 choices)  in survey with column ids in database:
            single@q1, multiple@q2choice_1, multiple@q2choice_2, multiple@q2choice_3
        This structure will be converted to:
            single@q1, multiple@q2choice{1,2,3}

        Variable values will be updated during merge.

        :param convert_exceptions: list of variables
        :return: new instance of SurveyStructure
        """

        if self.is_hierarchical:
            return deepcopy(self)

        if convert_exceptions and not isinstance(convert_exceptions, (list, set)):
            raise Exception('convert_exceptions must be iterable got instead %s' % (type(convert_exceptions),))

        # question_id is more powerful thing that may contains more than one variable
        # basic example – multiple choice question, which consist of number of variables - maximum
        # number of choices respondent could made in question
        question_ids = []
        for variable_id in self._variables_list:
            if convert_exceptions:
                if variable_id in convert_exceptions:
                    # if variable is in exceptions than it is independent variable
                    question_ids.append(variable_id)
                    continue

            question_ids.append(variable_id.split(self.multiple_choices_separator)[0])

        temp_structure = OrderedDict()

        for variable_id_idx, question_id in enumerate(question_ids):
            if question_id in temp_structure:
                temp_structure[question_id].append(list(self._variables_list.values())[variable_id_idx])
            else:
                temp_structure[question_id] = [list(self._variables_list.values())[variable_id_idx]]

        new_survey_structure = SurveyStructure(is_hierarchical=True)
        for question_id in temp_structure:

            variable_structure = temp_structure[question_id][0]

            question_structure = VariableStructure(
                variable_id=question_id,
                variable_type=variable_structure.variable_type,
                variable_label=variable_structure.variable_label,
                variable_children=deepcopy(variable_structure.variable_children),
                variable_survey_type=variable_structure.variable_survey_type,
                variable_values=deepcopy(variable_structure.variable_values)
            )

            for variable in temp_structure[question_id]:
                question_structure.variable_children.append(variable)
                question_structure.variable_values.update(
                    variable.variable_values
                )

            new_survey_structure.add_variable(question_structure)

        return new_survey_structure


class SurveyData(object):
    """
        sd = SurveyData(data=pd.DataFrame, var_labs, val_labs)
        tab1 = sd.cross('q1 by q2 + q3>q4')
        tab1 = sd.cross(rows='q1',
                        columns=pd.MultiIndex(q2).union(pd.MultiIndex(q3, q4))
        tab1 = sd.cross('q1 by q2 + q3>q4',
                        weight='w'
                        show_counts=True,
                        show_column_percentage=True,
                        show_row_percentage=True,
                        show_table_percentage=True,
                        show_mean=True,
                        show_median=True,
                        show_std=True,
                        show_variance=True,
                        show_sampling_error=True)
    """

    def __init__(self, data, variable_labels=None, value_labels=None):
        """

        :param data: pd.DataFrame
        :param variable_labels: dict, {variable_id: variable_label}
        :param value_labels: nested dict, {variable_id: {value_id: value_label}}
        :return: instance of SurveyData
        """
        self.data = data

        if variable_labels is not None:
            self._variable_labels = variable_labels
        if value_labels is not None:
            self._value_labels = value_labels

        self.data_transformation_history = []

    @property
    def variable_labels(self):
        return self._variable_labels

    @variable_labels.setter
    def variable_labels(self, var_labs):
        self._variable_labels = var_labs

    @property
    def value_labels(self):
        return self._value_labels

    @value_labels.setter
    def value_labels(self, val_labs):
        self._value_labels = val_labs

    def rename_variable(self, prev_variable_id, next_variable_id):
        raise NotImplementedError

    def rename_variable_label(self, variable_id, variable_label):
        raise NotImplementedError

    def rename_variable_value_label(self, variable_id, value_id, value_label):
        raise NotImplementedError

    def cross(self, expression=None, **kwargs):
        raise NotImplementedError

    def melt(self, **kwargs):
        raise NotImplementedError

    def vars_to_cases(self, **kwargs):
        return self.melt(**kwargs)

    def pivot(self, **kwargs):
        raise NotImplementedError

    def cases_to_vars(self, **kwargs):
        return self.pivot(**kwargs)

    def recode(self, **kwargs):
        raise NotImplementedError


