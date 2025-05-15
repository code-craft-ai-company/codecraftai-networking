
"""
.. module:: bosefeatureversion
    :platform: Darwin, Linux, Unix, Windows
    :synopsis: Module containing the BoseFeatureVersion class.

.. moduleauthor:: Myron Walker <myron.walker@gmail.com>
"""

__author__ = "Myron Walker"
__copyright__ = "Copyright 2024, Myron W Walker"
__credits__ = []


class BoseFeatureVersion:

    def __init__(self, major: int, minor: int):
        self._major = major
        self._minor = minor
        return
