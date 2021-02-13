# -*- coding: utf-8 -*-
"""
Created on Sat Aug 22 12:14:32 2020

@author: ASUS
"""
import unittest
from ChipConsole import Console

class TestStringMethods(unittest.TestCase):

    def test_load(self):
        self.C = Console()
        self.assertTrue(True)
    
    def test_display(self):
        self.C = Console()
        self.C.display
        self.assertTrue(True)
    
    def test_opcodes(self):
        self.C = Console()





unittest.main()