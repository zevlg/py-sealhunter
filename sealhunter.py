# Copyright (C) 2009 by Zajcev Evegny <zevlg@yandex.ru>

PROFILE=False

import sys
import os
srcdir = os.path.abspath(os.path.dirname(__file__)+'/src')
sys.path.insert(0, srcdir)

import sealhunter

if PROFILE:
    import cProfile
    cProfile.run('sealhunter.start_sealhunter()', 'profile.tmp')
else:
    sealhunter.start_sealhunter()
