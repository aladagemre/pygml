"""
Gives random weights to the graph given.
"""
from pygml import *
from random import randint, choice, sample

import sys

if len(sys.argv) < 3:
    print "python %s inputfile outputfile" % sys.argv[0]
    sys.exit(-1)

inputfile = sys.argv[1]
outputfile = sys.argv[2]

g = Graph(sys.argv[1])

for edge in g.edges:   
    edge.parameter = str(choice((1,2)))

l = sample(g.edges, int(len(g.edges)*0.3))
for e in l:
    e.parameter = str(choice((50, 100)))

g.write_gml(sys.argv[2])