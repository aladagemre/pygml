
format_value = lambda value: '"%s"'%value if isinstance(value, str) else value
def print_list(l):
    """Prints the contents of a list"""
    print "{",
    print ", ".join([e.__unicode__() for e in l]),
    print "}"

def print_dict(d):
    """Prints the contents of a dict"""
    for key in d:
        print "%s: " % key,
        print_list(d[key])

class Graphics:
    pass
class LabelGraphics:
    pass
class Line:
    pass
class Point:
    pass

class BaseClass:
    """Base class for Node and Edge. Includes some printing methods."""
    def print_subsection(self, name, fields):
        """Prints the subsection of Node/Edge."""
        output = ""
        try:			

            output += "\t\t%s [\n" % name
            for field in fields:
                if field != "Line":
                    output += "\t\t\t%s %s\n" % (field, format_value(fields[field]))

            if fields.get("Line"): output += self.print_line(fields["Line"].__dict__)

            output += "\t\t]\n"
        except:
            print "No %s section for node, passing." % name
        return output

    def print_line(self, fields):
        """Prints the Line subsubsection of Edge."""
        output = ""
        points =  fields["points"][:]
        output += "\t\t\tLine [\n"
        for point in points:
            output += "\t\t\t\tpoint [\n"
            for key in point.__dict__:
                output += "\t\t\t\t\t%s %s\n" % (key, format_value(point.__dict__[key]))
            output += "\t\t\t\t]\n"
        output += "\t\t\t]\n"
        return output		

    def print_header(self, name, fields):
        """Prints the primitive attributes of the object like "label","directed","id","parameter","labelAnchor", "source","target"."""
        output = "\t%s [\n" % name

        try:
            del fields["LabelGraphics"]
            del fields["graphics"]
        except:
            pass

        # Primitive fields:
        for field in filter(lambda f: f in ("label","directed","id","parameter","labelAnchor", "source","target"), fields):
            output += "\t\t%s %s\n" % (field, format_value(fields[field]))

        return output

    def print_footer(self):
        """Prints the closing bracket ]"""
        return "\t]\n\n"


class Edge(BaseClass):
    """Essential data structure and methods for edges."""
    def __unicode__(self):
        return "(%s, %s)" % (self.source, self.target)

    def __init__(self):
        self.marked = False
        
    def as_gml(self):
        """Returns GML string representation of the edge."""
        fields  = self.__dict__.copy()
        output  = self.print_header("edge", fields)
        output += self.print_subsection("graphics", self.graphics.__dict__)
        if "LabelGraphics" in self.__dict__:
            output += self.print_subsection("LabelGraphics", self.LabelGraphics.__dict__)
        output += self.print_footer()
        return output

    def is_short(self):
        """Checks if the edge is short (1 segment)."""
        return (self.u.layer - self.v.layer == 1)

class Node(BaseClass):
    """Essential data structure and methods for nodes."""
    def __init__(self):
        self.incoming_edges = []
        self.outgoing_edges = []
        self.outgoing_dict = {}

    def __unicode__(self):
        #fields = filter(lambda x: isinstance(self.__dict__[x], str) or isinstance(self.__dict__[x], int), self.__dict__)
        #return "[" + "/".join(map(str, map(self.__dict__.get, fields))) + "]"
        #return "[%s/%s/%s]" % (self.id, self.parameter, self.label)
        return "<%s>" % self.id

    def as_gml(self):
        """Returns GML string representation of the node."""
        fields  = self.__dict__.copy()
        output  = self.print_header("node", fields)
        output += self.print_subsection("graphics", self.graphics.__dict__)
        output += self.print_subsection("LabelGraphics", self.LabelGraphics.__dict__)
        output += self.print_footer()
        return output

    def upper_neighbors(self):
        """Returns the upper neighbor nodes (from which incoming edges exist) of the node."""
        return filter(lambda un: un.layer < self.layer, [edge.u for edge in self.incoming_edges])

    def lower_neighbors(self):
        """Returns the lower neighbor nodes (to which outgoing edges exist) of the node."""
        return filter(lambda ln: ln.layer > self.layer, [edge.v for edge in self.outgoing_edges])

    def upper_degree(self):
        """Returns the number of upper neighbors."""
        return len(self.upper_neighbors())

    def lower_degree(self):
        """Returns the number of upper neighbors."""
        return len(self.lower_neighbors())

    def get_position(self):
        """Returns the position of a node in the format (layer, index)"""
        return (self.layer, self.position)

class Graph:
    """Essential data structure and methods for graphs."""
    def __init__(self, filename=None):
        self.nodes = []
        self.edges = []
        self.virtual_nodes = []
        self.real_nodes = []
        
        self.node_dict = {}
        self.layers = {}
        
        if filename:
            self.read_gml(filename)

        self.find_vertical_layers()
        self.find_virtual_vertices()
        self.setup_edges()

    # I/O Methods	
    def as_gml(self):
        """Returns the string GML representation of the graph."""
        output = "graph [\n"

        for attribute in self.__dict__:
            a = self.__dict__[attribute]

            if isinstance(a, str) or isinstance(a, int) or isinstance(a, float):
                if isinstance(a, str) and len(a) == 0: a='""'
                output += "\t%s %s\n" % (attribute, a)

        for node in self.nodes:
            output+=node.as_gml()
        for edge in self.edges:
            output+=edge.as_gml()

        output += "]"
        return output

    def read_gml(self, filename):
        """Reads from the GML file with the filename specified. Data is injected
        to the graph object."""
        f = open(filename)
        in_graph = False
        in_node = False
        in_edge = False

        in_graphics = False
        in_label_graphics = False
        in_line = False
        in_point = False


        for line in f:
            line = line.strip("\n").strip(" ").strip("\r")
            parts = line.split(" ")

            # HEADER PARSING
            if parts[0] == "graph" and parts[1] == "[":
                # Starting a new graph
                in_graph = True

            elif parts[0] == "node" and parts[1] == "[":
                # Starting a new node
                in_graph = False
                in_edge = False
                in_node = True
                n = Node()
                self.nodes.append(n)

            elif parts[0] == "edge" and parts[1] == "[":
                # Starting a new edge
                in_node = False
                in_edge = True
                e = Edge()
                self.edges.append(e)

            elif parts[0] == "graphics" and parts[1] == "[":
                # Starting a new graphics subsection.
                #in_node = False
                in_label_graphics = False
                in_graphics = True
                g = Graphics()
                if in_node:
                    n.__dict__["graphics"] = g
                elif in_edge:
                    e.__dict__["graphics"] = g
                elif in_graph:
                    self.__dict__["graphics"] = g
                else:
                    print "Ooops! Where to put the graphics? Edge/node?"
                    break					

            elif parts[0] == "LabelGraphics" and parts[1] == "[":
                # Starting a new LabelGraphics subsection.
                #in_node = False
                in_graphics = False
                in_label_graphics = True

                lg = LabelGraphics()
                if in_node:
                    n.__dict__["LabelGraphics"] = lg
                elif in_edge:
                    e.__dict__["LabelGraphics"] = lg
                elif in_graph:
                    self.__dict__["LabelGraphics"] = lg
                else:
                    print "Ooops! Where to put the LabelGraphics? Edge/node?"
                    break

            elif parts[0] == "Line" and parts[1] == "[":
                in_line = True

                line = Line()
                e.graphics.__dict__["Line"] = line

            elif parts[0] == "point" and parts[1] == "[":
                in_point = True

                point = Point()
                # Create an initial point and put it into the newly created list.
                # We will access the last point by index -1.
                if not e.graphics.Line.__dict__.get("points"):
                    e.graphics.Line.__dict__["points"] = []
                e.graphics.Line.points.append(point)




            elif parts[0] == "]":
                # End of the section
                if in_label_graphics:
                    in_label_graphics = False
                elif in_point:
                    in_point = False

                elif in_line:
                    in_line = False

                elif in_graphics:
                    in_graphics = False

                elif in_node:
                    in_node = False

                elif in_edge:
                    in_edge = False


            else:
                # CONTENT PARSING
                # If the line and the value is not empty.
                if line and parts[1]!="":
                    # Set the types
                    if '"' in parts[1]:
                        # If contains ", then clear it and set type to str.
                        parts[1] = str(parts[1].replace('"',''))

                    elif '.' in parts[1]:
                        # If contains ., then set the type to float
                        # TODO: Other fields might contain . too!
                        parts[1] = float(parts[1])
                    else:
                        parts[1] = int(parts[1])

                    # Set the attributes

                    if in_point:
                        e.graphics.Line.points[-1].__dict__[parts[0]] = parts[1]

                    elif in_line:
                        e.graphics.Line.__dict__[parts[0]] = parts[1]

                    elif in_graphics:
                        g.__dict__[parts[0]] = parts[1]
                    elif in_label_graphics:
                        lg.__dict__[parts[0]] = parts[1]
                    # graphics and label_graphics should be above node and edge. (more priority)
                    elif in_node:
                        n.__dict__[parts[0]] = parts[1]
                    elif in_edge:
                        e.__dict__[parts[0]] = parts[1]

                    elif in_graph:
                        self.__dict__[parts[0]] = parts[1]	

    def write_gml(self, filename):
        """Writes the GML Representation of the graph to the file with the filename given."""
        f = open(filename, "w")
        f.write(self.as_gml())
        f.close()


    # Preprocessing methods
    def find_vertical_layers(self):
        """Determines the vertical layers by dividing y coordinate to 100.
        Then it sorts each layer according to the x coordinate and
        Assigns the position attribute to each node."""

        for node in self.nodes:
            node.layer = int(round(node.graphics.y / 100))
            if not self.layers.get(node.layer):
                self.layers[node.layer] = []
            self.layers[node.layer].append(node)

        for layer in self.layers:
            self.layers[layer].sort(lambda u,v: cmp(int(u.graphics.x), int(v.graphics.x)))
            # Now set the position info into the nodes
            for node in self.layers[layer]:
                node.position = self.layers[layer].index(node)
                if node.position > 0:
                    node.pred = self.layers[layer][node.position - 1]
                else:
                    node.pred = None
                    
                if node.position < len(self.layers[layer])-1:
                    node.succ = self.layers[layer][node.position + 1]
                else:
                    node.succ = None

    def find_virtual_vertices(self, color='#FF8000'):
        """Determines the virtual vertices. Sets boolean "virtual" attribute for node,
        adds the node to virtual_nodes or real_nodes lists of the graph."""

        for node in self.nodes:
            if node.graphics.fill == color: # in (color, '#FF8C00'):
                node.virtual = True
                self.virtual_nodes.append(node)
            else:
                node.virtual = False
                self.real_nodes.append(node)

    def setup_edges(self):
        """Sets u and v attributes as node objects.
        Appends the edge to the incoming and outgoing edge lists
        of the corresponding nodes."""
        
        for edge in self.edges:
            edge.u = self.nodes[edge.source]	
            edge.v = self.nodes[edge.target]

            edge.u.outgoing_edges.append(edge)
            edge.v.incoming_edges.append(edge)
            
            
            for e in edge.u.outgoing_edges:
                edge.u.outgoing_dict[e.v] = e
            
        for node in self.nodes:
            node.incoming_edges.sort(lambda e1,e2: cmp(float(e1.u.graphics.x), int(e2.u.graphics.x)))
            node.outgoing_edges.sort(lambda e1,e2: cmp(float(e1.v.graphics.x), int(e2.v.graphics.x)))
            
            self.node_dict[node.id] = node
            #node.incoming_edges.sort(lambda u,v: cmp(float(u.graphics.x), float(v.graphics.x)))
            #node.outgoing_edges.sort(lambda u,v: cmp(float(u.graphics.x), float(v.graphics.x)))
    # Service methods
    def get_node(self, layer, position):
        """Returns the requested node with layer and position number given.

        @return Node
        """
        return self.layers[layer][position]

    def get_node_by_id(self, id):
        """Returns the node with the given id."""
        return self.node_dict.get(id)

    def get_edge(self, u, v):
        """Returns the edge with the given source and target nodes."""
        return u.outgoing_dict.get(v)
    
    def get_double_edge(self, u, v):
        """Returns the edge with the given or reverse source and target nodes."""
        a = self.get_edge(u,v)
        if a:
            return a
        else:
            return self.get_edge(v,u)
        
    def get_edge_by_id(self, id):
        """Returns the edge with the given id."""
        for edge in self.edges:
            if edge.id == id:
                return edge
        return None

    def is_crossing(self, edge1, edge2):
        """Checks if two edges provided are crossing"""
        return (edge1.u < edge2.u and edge2.v < edge1.v) or (edge2.u < edge1.u and edge1.v < edge2.v)
    def layer_num_elements(self, i):
        return len(self.layers[i])
    def is_end_incident(self, node):
        """Checks if the node is on the last point of the long edge.
        i.e. has incoming edge from a virtual node but itself is real."""
        """for edge in node.incoming_edges:
            if edge.u.virtual and not edge.v.virtual:
                return True
        return False
        """
        if node.virtual:
            if len(node.incoming_edges) > 1:
                print "len(inc_edge) = %d!!!" % len(node.incoming_edges)
            
            e = node.incoming_edges[0]
            
            return e.u.virtual
        else:
            return False

    def is_start_incident(self, node):
        """Checks if the node is on the starting point of the long edge.
        i.e. has outgoing edge from itself (real) to a virtual node."""
        for edge in node.outgoing_edges:
            if not edge.u.virtual and edge.v.virtual:
                return True
        return False

    def mark_segment(self, u, v):
        """Marks the edge as type 1 crossing."""
        e = self.get_edge(u,v)
        e.marked = True
    def min_x(self):
        """Returns the minimum x value among the nodes of the graph."""
        min_x = float("infinity")
        for node in self.nodes:
            x = node.graphics.x
            if x < min_x:
                min_x = x
        return min_x
                
    def max_x(self):
        """Returns the maximum x value among the nodes of the graph."""
        max_x = float("-infinity")
        
        for node in self.nodes:
            x = node.graphics.x
            if x > max_x:
                max_x = x
                
        return max_x
                                
            
    def get_width(self):
        """Returns the width of the graph."""
        return self.max_x() - self.min_x()
    