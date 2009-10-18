from pygml import *
from math import ceil, floor
import sys

class FastAndSimple:
    def __init__(self, input_file, output_file):
        self.sink = {}
        self.shift = {}
        self.x = {}
        self.align={}
        self.minimum_distance = 75
        self.g = Graph(input_file)
        
        """self.preprocessing()
        for edge in self.g.edges:
            if edge.marked:
                edge.graphics.fill = "#FF0000"
                #print "(%s, %s) - %s" % (edge.source, edge.target,  edge.marked)
        self.g.write_gml("pre_" + output_file)
        """
        self.vertical_alignment()
        self.horizontal_compaction()
        
        for v in self.x:
            v.graphics.x = float(self.x[v])
        self.g.write_gml(output_file)
        self.write_layers()
    def preprocessing(self):
        h = len(self.g.layers)
        for i in xrange(1, h-2): #i=2 to h-2
            k0 = 0
            l = 0 # OR 1 ???
            for l1 in range(0, self.g.layer_num_elements(i)+1):
                if l1 == self.g.layer_num_elements(i) or self.g.is_end_incident(self.g.get_node(i, l1)):
                    k1 = self.g.layer_num_elements(i-1)
                    if self.g.is_end_incident(self.g.get_node(i, l1-1)):
                        k1 =  self.g.get_node(i, l1).upper_neighbors()[0].position
                    while l < l1:
                        
                        for un in self.g.get_node(i, l).upper_neighbors():
                            if un.position < k0 or un.position > k1:
                                self.g.mark_segment(un, self.g.get_node(i, l))
                        l += 1
                    k0 = k1
    
    def vertical_alignment(self):
        self.root = {}
        self.align = {}
        for node in self.g.nodes:
            self.root[node] = node
            self.align[node] = node
        
        for layer in range(len(self.g.layers)):
            r = 0
            for v in self.g.layers[layer]:
                neighbors = v.upper_neighbors()
                d = len(neighbors)
    
                if d > 0:
                    for m in ( floor((d+1)/2), ceil((d+1)/2) ):
                        m = int(m) - 1
                        
                        if (self.align[v] == v):
                            
                            if not self.g.get_edge(neighbors[m], v).marked and r < neighbors[m].position:
                                self.align[neighbors[m]] = v
                                self.root[v] = self.root[neighbors[m]]
                                self.align[v] = self.root[v]
                                r = neighbors[m].position
    
    def place_block(self, v):
        if not self.x.get(v):
            self.x[v] = 0
            w = v
            start = True
            while w!=v or start:
                start = False
                if w.position > 0:
                    u = self.root[w.pred]
                    self.place_block(u)
                    if self.sink[v] == v:
                        self.sink[v] = self.sink[u]
                    if self.sink[v] != self.sink[u]:
                        self.shift[self.sink[u]] = min(self.shift[self.sink[u]], self.x[v] - self.x[u] - self.minimum_distance)
                    else:
                        self.x[v]  = max(self.x[v], self.x[u] + self.minimum_distance)
                
                w = self.align[w]
    
    
    def horizontal_compaction(self):
        for v in self.g.nodes:
            self.sink[v] = v
            self.shift[v] = float("infinity")
    
        # root coordinates relative to self.sink
        for v in self.g.nodes:
            if self.root[v] == v:
                self.place_block(v)
        # absolute coordinates
        for v in self.g.nodes:
            self.x[v] = self.x[self.root[v]]
            if self.shift[self.sink[self.root[v]]] < float("infinity"):
                self.x[v] = self.x[v] + self.shift[self.sink[self.root[v]]]
        
    def write_layers(self):
        f = open("layers.txt", "w")
        l = len(self.g.nodes)
        f.write("%d\n" % l)
        f.write(" ".join([str(node.layer) for node in self.g.nodes]))
        f.close()
            
if __name__ == "__main__":
    if len(sys.argv) > 2:
        fs = FastAndSimple(sys.argv[1], sys.argv[2])
    else:
        print "Insufficient parameters"
        print "Usage: python %s <input file> <output file>" % sys.argv[0]