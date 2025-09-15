#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os

__author__ = "magnusknutas"

path = os.path.dirname(os.path.realpath(__file__))


def load_fixture(name):
    file_object = open("".join([path, "/fixtures/%s" % name]), "r")
    ret = file_object.read()
    file_object.close()
    return ret
