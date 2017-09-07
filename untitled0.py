# -*- coding: utf-8 -*-
"""
Created on Thu Sep 07 09:05:09 2017

@author: Randall
"""

duplicity_check = open("duplicity_check.txt", "r")
duplicates = file.read().split(',')
duplicity_check.close()

duplicity_check = open("duplicity_check.txt", "a")
text_string = "20170907_wbb_ozone"
if text_string not in duplicates:
    duplicity_check.write(text_string + ",")

duplicity_check.close()

