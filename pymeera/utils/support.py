# -*- coding: utf-8 -*-

from __future__ import print_function, unicode_literals, division


def hash_index(v, group):
    """
    Hash values to store hierarchical index

    :param v: index value
    :param group: variables from which index was derived
    :return: str

    v = [1, 2]
    group = ['q1', 'q2]

    return 'q1::1__q2::2'
    """
    if not isinstance(v, (list, tuple)):
        _hash = list(zip(group, [v]))
    else:
        _hash = list(zip(group, v))
    return '__'.join(list(map(lambda x: '%s::%s' % (x[0], x[1]), _hash)))


def unhash_index(_hash):
    """
    Decode hased value to tuple

    :param _hash: str, hash_index result
    :return: tuple of tuples

    hash = 'q1::1__q2::2'
    return ((q1, 1), (q2, 2))
    """
    try:
        return tuple(map(lambda x: tuple(x.split('::')), _hash.split('__')))
    except:
        print(_hash)


def equlize_size(lst):
    """
    Equalize size of incoming iterables

    :param args: 2-dimensional iterables
    :return: tuple of tuples
    """

    max_size = max(map(lambda x: len(x), lst))
    ret = []

    for v in lst:
        ret.append(tuple(v) + (('', ''),) * (max_size - len(v)))

    return tuple(ret)



