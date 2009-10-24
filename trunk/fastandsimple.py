from pygml import *
from math import ceil, floor
import sys
import cProfile

class FastAndSimple:
    
    def __init__(self, input_file, output_file, minimum_distance, vstart, hstart, layersorpositions='layers'):
        self.sink = {}
        self.shift = {}
        self.x = {}
        self.align={}
        self.minimum_distance = int(minimum_distance)
        
        if isinstance(input_file, Graph):
            self.g = input_file
        else:
            self.g = Graph(input_file)

        if not (vstart and hstart):
            return
        
           
        #if self.detect_type2():
        #print "Because of the type 2 crossings, there might be problems."
            
        print "Preprocessing..."
        self.preprocessing()
        # Mark type 1 crossing edges with red.
        """for edge in self.g.edges:
            if edge.marked:
                edge.graphics.fill = "#FF0000"
        """
        
        if vstart == "up":
            if hstart == "left":
                self.vertical_alignment_up_left()
                self.horizontal_compaction_left()
            else:
                self.vertical_alignment_up_right()
                self.horizontal_compaction_right()
        else:
            if hstart == "left":
                self.vertical_alignment_down_left()
                self.horizontal_compaction_left()
            else:
                self.vertical_alignment_down_right()
                self.horizontal_compaction_right()
             
        # Assign the computed coordinates
        for v in self.x:
            v.graphics.x = float(self.x[v])
        
        print "Weighted y coordinates..."
        self.weighted_y_coordinates(100)
        #self.debug()
        #self.adjustments()
        #self.g.write_gml(output_file)
        self.straighten_bends()
        if layersorpositions == 'layers':
            self.write_layers()
        elif layersorpositions == 'positions':
            self.post_adjustments()
            self.write_positions()
            
            
    def detect_type2(self):
        detected = False
        for layer in self.g.layers:
            for u in self.g.layers[layer]:
                if u.virtual:
                    uoe = u.outgoing_edges
                    for out_edge in uoe:
                        if out_edge.v.virtual:
                            for i in range(u.position + 1, len(self.g.layers[layer])):
                                v = self.g.layers[layer][i]
                                for edge in v.outgoing_edges:
                                    if edge.u.virtual and edge.v.virtual and edge.v.position < out_edge.v.position:
                                        print "(%d, %d) and (%d, %d) are type 2 crossing." % (out_edge.u.id, out_edge.v.id, edge.u.id, edge.v.id)
                                        detected = True
        return detected
            
    def weighted_y_coordinates(self, base_height):
        
        total_sum = 0.0
        layer_sums = {}
        for layer in self.g.layers:
            layer_sum = 0.0
            for node in self.g.layers[layer]:
                edges = node.outgoing_edges
                for edge in edges:
                    if not "parameter" in edge.__dict__:
                        edge.parameter = 2.0
                    layer_sum += float(edge.parameter)
                    
                        
            layer_sums[layer] = layer_sum
            total_sum += layer_sum


        
        last_y = 0
        for layer in self.g.layers:
            layer_sums[layer]/=total_sum
            if layer > 0:
                    last_y += base_height/4 + base_height * len(self.g.layers)* layer_sums[layer-1]
            for node in self.g.layers[layer]:                
                    node.graphics.y = last_y
            
    def post_adjustments(self):
        """Some post adjustments after balancing. (terrible)"""
        # Shifts the overlapping nodes by half of their widths.
        print "Post ad"
        
        layer_overlaps = {0: 1}
        tour = 0
        while sum(layer_overlaps.values()) != 0:
            print "New tour"
            tour += 1
            
            for layer in self.g.layers:
                layer_overlaps[layer] = 0
                for u in self.g.layers[layer]:
                    for v in self.g.layers[layer]:
                        if u!=v and abs(u.graphics.x - v.graphics.x) < (u.graphics.w + v.graphics.w)/2 :
                            if tour > 15:
                                print u.id,":",u.graphics.x,"---",v.id,":", v.graphics.x
                                print "-------------------------------------------------"*10
                                return
                            
                            
                            print "Adjusting %d and %d" % (u.id, v.id)
                            if u.position < v.position:
                                if u.pred:
                                    prev_x = u.pred.graphics.x
                                else:
                                    prev_x = u.graphics.x - self.minimum_distance
                                if prev_x + self.minimum_distance not in [node.graphics.x for node in self.g.layers[layer]]:
                                    u.graphics.x = prev_x + self.minimum_distance
                                else:
                                    u.graphics.x = prev_x + self.minimum_distance/2
                            else:
                                if v.pred:
                                    prev_x = v.pred.graphics.x
                                else:
                                    prev_x = v.graphics.x - self.minimum_distance
                                    
                                if prev_x + self.minimum_distance not in [node.graphics.x for node in self.g.layers[layer]]:
                                    v.graphics.x = prev_x + self.minimum_distance
                                else:
                                    v.graphics.x = prev_x + self.minimum_distance/2
                            layer_overlaps[layer] = 1
    def straighten_bends(self):
        """
            from top to bottom
          from left to right
               if x is dummy move x left OR right as much as possible
               (without molesting any left/right neighbors on the same
               layer ) so that the slope of segment (x,y) is maximized,
               where y is the neighbor of x in the following layer.
               """
        for layer in self.g.layers:
            for u in self.g.layers[layer]:
                if len(u.outgoing_edges) == 0:
                    continue
                v = u.outgoing_edges[0].v
                if u.virtual and v.virtual:
                    
                    
                    dx = u.graphics.x - v.graphics.x
                    if dx == 0:
                        continue
                    if dx < 0:
                        # If u is on the upper left of v,
                        if v.pred:
                            # If a preceding node exists
                            if u.graphics.x - v.pred.graphics.x - self.minimum_distance > 0:
                                # If it is feasible to move y left, do it.
                                v.graphics.x = u.graphics.x
                            else:
                                # If it is not, then move x right.
                                if u.succ:
                                    # If a successor node exists,
                                    if u.succ.graphics.x - v.graphics.x - self.minimum_distance > 0:
                                        # If it is feasible to move x right, do it.
                                        u.graphics.x = v.graphics.x
                                else:
                                    # If no preceding node, move freely.
                                    u.graphics.x = v.graphics.x
                                
                        else:
                            v.graphics.x = u.graphics.x
                    
                    elif dx > 0:
                        # If u is on the upper right side of v,
                        if v.succ:
                            if v.succ.graphics.x - u.graphics.x - self.minimum_distance > 0:
                                v.graphics.x = u.graphics.x
                            else:
                                if u.pred:
                                    # If it is feasible to move u left, do it.
                                    if v.graphics.x - u.pred.graphics.x - self.minimum_distance > 0:
                                        u.graphics.x = v.graphics.x
                                else:
                                    u.graphics.x = v.graphics.x
    def hide_dummy_nodes(self):
        """Hides dummy nodes in the graph"""
        print self.g.virtual_nodes
        for node in self.g.virtual_nodes:
            node.graphics.w = 0.01
            node.graphics.h = 0.01
            node.graphics.fill = "#FFFFFF"
            for edge in self.g.edges:
                if edge.v.virtual:
                    edge.graphics.arrow = "none"
                    
    def adjustments(self):
        """Some adjustments for the bug of the algorithm. Seperates overlapping nodes."""
        
        
        # Aligns the false-ordered nodes to their root.        
        for layer in self.g.layers:
            for i in range(len(self.g.layers[layer])):
                current_layer = self.g.layers[layer]
                if i>0 and i<len(current_layer) and current_layer[i].graphics.x <= current_layer[i-1].graphics.x:
                    current_layer[i].graphics.x = self.root[current_layer[i]].graphics.x
                    #current_layer[i].graphics.x = (current_layer[i-1].graphics.x + current_layer[i+1].graphics.x)/2
        
        """
        # Shifts the overlapping nodes by half of their widths.
        for u in self.g.nodes:
            for v in self.g.nodes:
                if u != v and u.graphics.x == v.graphics.x and u.graphics.y == v.graphics.y:
                    if self.align[u].graphics.x > self.align[v].graphics.x:
                        u.graphics.x += u.graphics.w/2+3
                        v.graphics.x -= v.graphics.w/2+3
                    else:
                        u.graphics.x -= u.graphics.w/2+3
                        v.graphics.x += v.graphics.w/2+3
        """
        layer_overlaps = {0: 1}
        while sum(layer_overlaps.values()) != 0:
            for layer in self.g.layers:
                layer_overlaps[layer] = 0
                for u in self.g.layers[layer]:
                    v = u.succ
                    if v!=None and abs(u.graphics.x - v.graphics.x) < (u.graphics.w + v.graphics.w)/2:
                            u.graphics.x -= u.graphics.w/2
                            v.graphics.x += v.graphics.w/2
                            layer_overlaps[layer] = 1
        
    
    def debug(self):
        """

        """
        print "Checking for overlaps..."
        # Print the nodes that are overlapping
        #print "Checking overlapping nodes."
        for layer in self.g.layers:
            #print "Layer %d" % layer
            #print_list(self.g.layers[layer])
            for u in self.g.layers[layer]:    
                for v in self.g.layers[layer]:
                    if u!=v and u.graphics.x == v.graphics.x and u.graphics.y == v.graphics.y:
                        print "%s (%0.0f, %0.0f) , %s (%0.0f, %0.0f)" % (u.id, u.graphics.x, u.graphics.y, v.id, v.graphics.x, v.graphics.y)
                        
            
        
        """for layer in self.g.layers:
        print "Layer " + str(layer)
        for node in self.g.layers[layer]:
            print "%.1f" % (node.graphics.x / 100),
            
        print
        """     
        """
        # Print x coordinates of all nodes
        for node in self.g.nodes:
            print node.graphics.x
        """
                
        """
        # Prints the x coordinates of the nodes layer by layer
        for layer in self.g.layers:
            print "Layer " + str(layer)
            for node in self.g.layers[layer]:
                print "%.1f" % (node.graphics.x / 100),
                
            print
        """
        
    def preprocessing(self):
        """Marks the edges with type 1 crossing."""
        h = len(self.g.layers)
        for i in xrange(1, h-2): #i=2 to h-2
            k0 = 0
            l = 0
            for l1 in range(0, self.g.layer_num_elements(i+1)):
                if l1 == self.g.layer_num_elements(i+1) or self.g.is_end_incident(self.g.get_node(i+1, l1)): #incident means target v(i+1, l1) should be real and source is virtual?
                    k1 = self.g.layer_num_elements(i)
                    if self.g.is_end_incident(self.g.get_node(i+1, l1)):
                        k1 = self.g.get_node(i+1, l1).upper_neighbors()[0].position
                    while l < l1:
                        
                        for un in self.g.get_node(i+1, l).upper_neighbors():
                            if un.position < k0 or un.position > k1:
                                self.g.mark_segment(un, self.g.get_node(i+1, l))
                        l += 1
                    k0 = k1
    
    def vertical_alignment_up_left(self):
        print "Vertical Alignment Up left..."
        self.root = {}
        self.align = {}
        for node in self.g.nodes:
            self.root[node] = node
            self.align[node] = node
        
        for layer in range(len(self.g.layers)):
            #print "Layer %d" % layer
            r = -1
            for v in self.g.layers[layer]:
                neighbors = v.upper_neighbors()
                d = float(len(neighbors))
                
                if d > 0:
                    for m in ( floor((d+1)/2), ceil((d+1)/2) ):
                        m = int(m) - 1
                        if (self.align[v] == v):
                            if not self.g.get_edge(neighbors[m], v).marked and r < neighbors[m].position:
                                self.align[neighbors[m]] = v
                                self.root[v] = self.root[neighbors[m]]    
                                self.align[v] = self.root[v]
                                r = neighbors[m].position
                
    def vertical_alignment_up_right(self):
        print "Vertical Alignment Up Right..."
        self.root = {}
        self.align = {}
        for node in self.g.nodes:
            self.root[node] = node
            self.align[node] = node
        
        for layer in range(len(self.g.layers)):
            r = len(self.g.layers[layer]) # Changed 0 to last index for right
            
            for v in self.g.layers[layer][::-1]: # Changed order for right
                neighbors = v.upper_neighbors()
                d = float(len(neighbors))
                if d > 0:
                    for m in ( ceil((d+1)/2), floor((d+1)/2) ): #changed order for right
                        m = int(m) - 1
                        
                        if (self.align[v] == v):
                            
                            if not self.g.get_edge(neighbors[m], v).marked and r > neighbors[m].position: # Changed < to > for right
                                self.align[neighbors[m]] = v
                                self.root[v] = self.root[neighbors[m]]
                                self.align[v] = self.root[v]
                                r = neighbors[m].position
                                
    def vertical_alignment_down_right(self):
        print "Vertical Alignment Down Right..."
        self.root = {}
        self.align = {}
        for node in self.g.nodes:
            self.root[node] = node
            self.align[node] = node
        
        for layer in range(len(self.g.layers))[::-1]:
            r = len(self.g.layers[layer]) # Changed 0 to last index for right
            for v in self.g.layers[layer][::-1]: # Changed order for right
                neighbors = v.lower_neighbors()
                neighbors.reverse()
                d = float(len(neighbors))
                if d > 0:
                    for m in ( floor((d+1)/2), ceil((d+1)/2) ): #changed order for right
                        m = int(m) - 1
                        if (self.align[v] == v):
                            if not self.g.get_edge(v, neighbors[m]).marked and r > neighbors[m].position: # Changed < to > for right
                
                                self.align[neighbors[m]] = v
                                self.root[v] = self.root[neighbors[m]]
                                self.align[v] = self.root[v]
                                r = neighbors[m].position
                                
                                
    def vertical_alignment_down_left(self):
        print "Vertical Alignment Down left..."
        self.root = {}
        self.align = {}
        for node in self.g.nodes:
            self.root[node] = node
            self.align[node] = node
        
        for layer in range(len(self.g.layers))[::-1]:
            r = -1
            for v in self.g.layers[layer]:
                neighbors = v.lower_neighbors()
                d = float(len(neighbors))
    
                if d > 0:
                    for m in ( floor((d+1)/2), ceil((d+1)/2) ):
                        m = int(m) - 1
                        
                        if (self.align[v] == v):
                            if not self.g.get_edge(v, neighbors[m]).marked and r < neighbors[m].position: # Changed (n,v) to (v, neighbors[m])
                                self.align[neighbors[m]] = v
                                self.root[v] = self.root[neighbors[m]]
                                self.align[v] = self.root[v]
                                r = neighbors[m].position

    def place_block_left(self, v):
        if not self.x.get(v):
            self.x[v] = 0
            w = v
            start = True
            while w!=v or start:
                start = False
                if w.position > 0:
                    u = self.root[w.pred]
                    self.place_block_left(u)
                    if self.sink[v] == v:
                        self.sink[v] = self.sink[u]
                    if self.sink[v] != self.sink[u]:                                               
                        self.shift[self.sink[u]] = min(self.shift[self.sink[u]], self.x[v] - self.x[u] - self.minimum_distance)
                    else:
                        self.x[v]  = max(self.x[v], self.x[u] + self.minimum_distance)
                        
                w = self.align[w]
    def place_block_right(self, v):
        if not self.x.get(v):
            self.x[v] = 0
            w = v
            start = True
            while w!=v or start:
                start = False
                if w.position < len(self.g.layers[w.layer])-1:
                    u = self.root[w.succ]
                    self.place_block_right(u)
                    if self.sink[v] == v:
                        self.sink[v] = self.sink[u]
                    if self.sink[v] != self.sink[u]:                                               
                        self.shift[self.sink[u]] = min(self.shift[self.sink[u]], self.x[v] - self.x[u] - self.minimum_distance)
                    else:
                        self.x[v]  = min(self.x[v], self.x[u] - self.minimum_distance)
                
                w = self.align[w]
    
    
    
    def horizontal_compaction_left(self):
        print "Horizontal Compaction left..."
        for v in self.g.nodes:
            self.sink[v] = v
            self.shift[v] = float("infinity")
    
        # root coordinates relative to self.sink
        for layer in self.g.layers:
            for v in self.g.layers[layer]:
                if self.root[v] == v:
                    self.place_block_left(v)
                
        # absolute coordinates
        #for v in self.g.nodes:
        for layer in self.g.layers:
            for v in self.g.layers[layer]:
                self.x[v] = self.x[self.root[v]]
                if v==self.root[v] and self.shift[self.sink[v]] < float("infinity"):
                    self.x[v] = self.x[v] + self.shift[self.sink[v]]
                    
        
            
    def horizontal_compaction_right(self):
        print "Horizontal Compaction right..."
        for v in self.g.nodes:
            self.sink[v] = v
            self.shift[v] = float("infinity")
    
        # root coordinates relative to self.sink
        for v in self.g.nodes:
            if self.root[v] == v:
                self.place_block_right(v)
        # absolute coordinates
        for v in self.g.nodes:
            self.x[v] = self.x[self.root[v]]
            if v==self.root[v] and self.shift[self.sink[v]] < float("infinity"):
                self.x[v] = self.x[v] - self.shift[self.sink[v]]
    
    def write_positions(self):
        f = open("positions.txt", "w")
        f.write("%d\n" % len(self.g.nodes))
        for layer in self.g.layers:
            this_layer = self.g.layers[layer]
            f.write("%d " % len(this_layer) + " ".join(["%f %f" % (node.graphics.x, -1.0*node.graphics.y) for node in this_layer]) + "\n")
        f.close()
                
                
    def write_layers(self):
        f = open("layers.txt", "w")
        l = len(self.g.nodes)
        f.write("%d\n" % l)
        f.write(" ".join([str(node.layer) for node in self.g.nodes]))
        f.close()

class Aligner:
    """Utilities for aligning the 4 candidate graphs."""
    def __init__(self, graphs):
        print "Combiner..."
        # Store x values
        x_ul = {}
        x_dl = {}
        x_ur = {}
        x_dr = {}
        
        names = ["ul","ur","dl","dr"]
        # Find the reference graph.
        min_width = float("infinity")
        for graph in graphs:
            w = graph.get_width()
            #print "Width of %s : %f" % (names[graphs.index(graph)], w)
            if  w < min_width:
                min_width = w
                reference_graph = graph
        #print "Minimum width :", names[graphs.index(reference_graph)], min_width
        
        (ul, ur, dl, dr) = graphs
        
        min_ref = reference_graph.min_x()        
        max_ref = reference_graph.max_x()
        #print "min_ref", min_ref
        #print "max_ref", max_ref

        # Shift left
        min_ul = ul.min_x()
        min_dl = dl.min_x()
        #print "min_ul = ",min_ul
        #print "min_dl = ",min_dl
    
        difference = min_ul - min_ref
        #print "difference = ",difference
        for node in ul.nodes:
            if reference_graph != ul:
                node.graphics.x -= difference
            x_ul[node.id] = node.graphics.x
            
            
    
        difference = min_dl - min_ref
        #print "min_dl - min_ref = %d - %d = %d" % (min_dl, min_ref, difference)
        for node in dl.nodes:
            if reference_graph != dl:
                #if node.id == 10: print "Before: ", node.graphics.x
                node.graphics.x -= difference
                #if node.id == 10: print "After: ", node.graphics.x
            x_dl[node.id] = node.graphics.x
        # Shift right
        
        max_ur = ur.max_x()
        max_dr = dr.max_x()
        #print "max_ur = ", max_ur
        #print "max_dr = ", max_dr
    
        difference = max_ur - max_ref
        for node in ur.nodes:
            if reference_graph != ur:        
                node.graphics.x -= difference
            x_ur[node.id] = node.graphics.x
    
        difference = max_dr - max_ref
        for node in dr.nodes:
            if reference_graph != dr:
                node.graphics.x -= difference
            x_dr[node.id] = node.graphics.x
    
        
        # Average of median
        for node_id in x_ul.keys(): # Not particularly x_ul. As ids are all the same.
            x_list = [ x_ul[node_id], x_ur[node_id], x_dl[node_id], x_dr[node_id] ]
            #if node_id == 10:
                #print x_list            
            x_list.sort()
            
            average = (x_list[1] + x_list[2])/2
            reference_graph.get_node_by_id(node_id).graphics.x = average
            #if node_id == 10:
                #print "10 - ", average
        
        
        self.result = reference_graph
    
    def get_result(self):
        return self.result
            

# -----------------------------------------


def main():
    if sys.argv[4] == "combined":
        print "Up Left"
        ul = FastAndSimple(sys.argv[1], sys.argv[2], sys.argv[3], "up", "left", sys.argv[6])
        print
        print "Up Right"
        ur = FastAndSimple(sys.argv[1], sys.argv[2], sys.argv[3], "up", "right", sys.argv[6])
        print
        print "Down Left"
        dl = FastAndSimple(sys.argv[1], sys.argv[2], sys.argv[3], "down", "left", sys.argv[6])
        print
        print "Down Right"
        dr = FastAndSimple(sys.argv[1], sys.argv[2], sys.argv[3], "down", "right", sys.argv[6])
        
        #print "x(10)=", dl.g.get_node_by_id(10).graphics.x
        
        aligner = Aligner((ul.g, ur.g, dl.g, dr.g))
        result = aligner.get_result()
        fs = FastAndSimple(result, sys.argv[2], 100, None, None)
        fs.hide_dummy_nodes()
        #fs.post_adjustments()
        #fs.debug()
        fs.g.write_gml(sys.argv[2])
        fs.write_layers()
    else:
        fs = FastAndSimple(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4], sys.argv[5], sys.argv[6])
        #fs.post_adjustments()
        fs.g.write_gml(sys.argv[2])
    
    #import os
    #os.system("./graphwin %s &" % sys.argv[2])

    
    
if __name__ == "__main__":
    if len(sys.argv) > 4:
        #cProfile.run('main()')
        main()
    else:
        print "Insufficient parameters"
        print "Usage: python %s <input file> <output file> <minimum distance> <combined/up/down> [left/right] [layers/positions]" % sys.argv[0]