# Copyright (C) 2009-2011 by Zajcev Evegny <zevlg@yandex.ru>

import sys, os, getopt
import os
srcdir = os.path.abspath(os.path.dirname(__file__)+'/src')
sys.path.insert(0, srcdir)

import sealhunter
from constants import DEBUG_TYPES

def usage():
   print "usage: %s [-c <cfg>] [-d <type,type,..>] [-p <file>]"%sys.argv[0]
   print
   print "  -c <cfg>     Execute config file <cfg> on start."
   print "               Option NOT available with -p."
   print "  -d <types>   Enable debug mode with <type>"
   print "               Available types: all, %s"%", ".join(DEBUG_TYPES)
   print "  -p <file>    Write profiling info to <file>"
   print "               Examine it with $ python -m pstats <file>"
   sys.exit(0)

def main():
   try:
      opts, args = getopt.getopt(sys.argv[1:], "c:d:p:")
   except getopt.GetoptError, err:
      print str(err)
      usage()

   opts = dict(opts)

   # Enable debug mode
   if '-d' in opts:
      import misc
      misc.options_load()
      shopts = misc.options()
      if opts['-d'] == 'all':
         shopts["debug"] = DEBUG_TYPES
      else:
         shopts["debug"] = opts['-d'].split(",")

   if '-p' in opts:
      import cProfile
      cProfile.run('sealhunter.start_sealhunter()', opts['-p'])
   else:
      config = None
      if '-c' in opts:
         config = opts['-c']

      sealhunter.start_sealhunter(config)

if __name__ == "__main__":
   import psyco
   psyco.full()

   main()
