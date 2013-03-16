C-Compiler
==========

written by python


usage:

run  ./parser.py source_file_path  (tested in 12.04 64bit ubuntu)
e.g. : ./parser.py test2.c
then the executable file will be runable and test2.s is the assembling file

explanation about the source code file:

 ./raw_cfg.py :contains the  C grammer this compiler support

actionTable and gotoTable: is intermediate result based on the C grammer and will be used in the parseing process. remove either one of them, it will take about 30s to regenerate both.

./test2.c is a test file
