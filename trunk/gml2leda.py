"""
Converts a graph gml to its generating LEDA code.
"""
from pygml import *
from random import randint, choice, sample

import sys

if len(sys.argv) < 3:
    print "python %s inputfile outputfile" % sys.argv[0]
    sys.exit(-1)

inputfile = sys.argv[1]
outputfile = sys.argv[2]
g = Graph(inputfile)
f = open(outputfile,"w")

# Write nodes
node_decleration = "node "
node_decleration += ", ". join([("n%d" % i) for i in range(len(g.nodes))])
    

f.write(node_decleration + ";\n")
for node in g.nodes:
    string="""n%(id)d = G.new_node();
G [ n%(id)d ] = %(id)d;
""" % {'id': node.id }

    f.write(string)

# Write edges
f.write("\n\nedge e;\n");
for edge in g.edges:
    string="""e = G.new_edge( n%(source)d, n%(target)d, %(weight)d );
""" % {'source':edge.u.id, 'target': edge.v.id, 'weight':int(edge.parameter) }

    f.write(string)
    
# Close the file
f.close()