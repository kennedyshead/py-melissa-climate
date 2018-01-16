#!/usr/bin/env python
# -*- coding: utf-8 -*-
__author__ = 'magnusknutas'


def load_fixture(name):
    file_object = open("fixtures/%s" % name, 'r')
    ret = file_object.read()
    file_object.close()
    return ret
