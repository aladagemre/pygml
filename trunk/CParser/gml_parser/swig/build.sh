swig -python -llibc.i -lgml_scanner.i gml_parser.i 
gcc -c gml_scanner.c gml_parser.c gml_parser_wrap.c -I/usr/include/python2.6
ld -shared gml_scanner.o gml_parser.o gml_parser_wrap.o -o _gml_parser.so