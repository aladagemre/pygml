from pygml import *
from math import ceil, floor

def preprocessing(g):
    h = len(g.layers)
    for i in xrange(1, h-2): #i=2 to h-2
        k0 = 0
        l = 0 # OR 1 ???
        for l1 in range(0, g.layer_num_elements(i)+1):
            if l1 == g.layer_num_elements(i) or g.is_end_incident(g.get_node(i, l1)):
                k1 = g.layer_num_elements(i-1)
                if g.is_end_incident(g.get_node(i, l1-1)):
                    k1 =  g.get_node(i, l1).upper_neighbors()[0].position
                while l < l1:
                    
                    for un in g.get_node(i, l).upper_neighbors():
                        if un.position < k0 or un.position > k1:
                            g.mark_segment(un, g.get_node(i, l))
                    l += 1
                k0 = k1
        return g

def vertical_alignment(g):
    root = {}
    align = {}
    for node in g.nodes:
        root[node] = node
        align[node] = node
    
    for layer in range(len(g.layers)):
        r = 0
        for v in g.layers[layer]:
            neighbors = v.upper_neighbors()
            d = len(neighbors)

            if d > 0:
                for m in ( floor((d+1)/2), ceil((d+1)/2) ):
                    m = int(m) - 1
                    
                    if (align[v] == v):
                        
                        if not g.get_edge(neighbors[m], v).marked and r < neighbors[m].position:
                            align[neighbors[m]] = v
                            root[v] = root[neighbors[m]]
                            align[v] = root[v]
                            r = neighbors[m].position
        
    return g, align, root

def place_block(v):
    if not x.get(v):
        x[v] = 0
        w = v
        start = True
        while w!=v or start:
            start = False
            if w.position > 0:
                u = root[w.pred]
                place_block(u)
                if sink[v] == v:
                    sink[v] = sink[u]
                if sink[v] != sink[u]:
                    shift[sink[u]] = min(shift[sink[u]], x[v] - x[u] - minimum_distance)
                else:
                    x[v]  = max(x[v], x[u] + minimum_distance)
            
            w = align[w]


def horizontal_compaction():
    for v in m.nodes:
        sink[v] = v
        shift[v] = float("infinity")

    # root coordinates relative to sink
    for v in m.nodes:
        if root[v] == v:
            place_block(v)
    # absolute coordinates
    for v in m.nodes:
        x[v] = x[root[v]]
        if shift[sink[root[v]]] < float("infinity"):
            x[v] = x[v] + shift[sink[root[v]]]
m = Graph("graph_test1.gml")
sink = {}
shift = {}
x = {}
minimum_distance = 75
m = preprocessing(m)
for edge in m.edges:
    print edge.marked
    
m, align, root = vertical_alignment(m)
for key in align:
    print "%s - %s" % (key.id, align[key].id)
horizontal_compaction()
for v in x:
    v.graphics.x = float(x[v])
m.write_gml("output.gml")
