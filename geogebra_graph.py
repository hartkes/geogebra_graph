# Helper functions that convert a GeoGebra figure into a SageMath graph, and for plotting the resulting graph.

import zipfile
import xmltodict
# Note that the Python package xmltodict needs to be installed into Sage.
# The following command will install the xmltodict package:
# sage --pip install xmltodict

import sage.all


def geogebra_to_graph(ggb_filename):
    '''
    Converts a GeoGebra file into a SageMath graph.
    The following conventions are followed:
    The GeoGebra figure should be a 2-dimensional geometry construction.
    Points become vertices.
    Line segments become edges [be careful that *lines* are not interpreted as edges, and line segments that are drawn over a point does not connect to that point.]
    
    Various attributes are also stored:
    For points/vertices: label, color, size, style.
    For line segments/edges: label, color, thickness.
    
    The position of the points is also stored in the graph's pos dictionary for later plotting.
    '''
    
    with zipfile.ZipFile(ggb_filename,'r') as f:
        d=xmltodict.parse(f.read("geogebra.xml"))

    c=d['geogebra']['construction']

    vertex_labels=[]  # vertices, as labels
    vertex_information=[]  # each vertex will have a dict of information (such as label, color, etc) about that vertex
    v=0  # current vertex number
    pos=dict()

    # interpret points as vertices
    for elt in c['element']:
        if elt['@type']=='point':
            vertex_labels.append(elt['@label'])
            pos[v]=(float(elt['coords']['@x']),float(elt['coords']['@y']))
            
            # save vertex information, such as label, color, etc, in a dict
            info=dict()
            info['label']=vertex_labels[-1]
            info['color']=(int(elt['objColor']['@r']),
                           int(elt['objColor']['@g']),
                           int(elt['objColor']['@b']),
                           float(elt['objColor']['@alpha']))
            info['size' ]=int(elt['pointSize']['@val'])
            info['style']=int(elt['pointStyle']['@val'])
            vertex_information.append(info)
            
            v+=1

    G=sage.graphs.graph.Graph()
    G.add_vertices(range(v))
    G.set_pos(pos)
    
    # store information for each vertex in the Sage graph
    for i in range(v):
        G.set_vertex(i,vertex_information[i])

    # interpret line segments as edges
    for elt in c['command']:
        if elt['@name']=='Segment':
            e=[]
            e.append(vertex_labels.index(elt['input']['@a0']))  # first endpoint of this edge
            e.append(vertex_labels.index(elt['input']['@a1']))  # second endpoint of the edge
            label=elt['output']['@a0']
            G.add_edge(e)
            G.set_edge_label(e[0],e[1],label)
    
    # we need to extract the edge properties from a different object
    for e in G.edges(sort=False):
        label=G.edge_label(e[0],e[1])
        
        for elt in c['element']:
            if elt['@type']=='segment' and elt['@label']==label:
                # save vertex information, such as label, color, etc, in a dict
                info=dict()
                info['label']=label
                info['color']=(int(elt['objColor']['@r']),
                               int(elt['objColor']['@g']),
                               int(elt['objColor']['@b']),
                               float(elt['objColor']['@alpha']))
                info['thickness']=int(elt['lineStyle']['@thickness'])
                G.set_edge_label(e[0],e[1],info)
    
    return G


def geogebra_graph_plot(G):
    '''Returns the plot of graph G, using the information retrieved from the GeoGebra file and stored in G.'''
    
    colors=dict()
    # plotted colors are named colors in matplotlib
    # https://matplotlib.org/3.1.0/gallery/color/named_colors.html
    colors[(0,255,0)]='springgreen'  # green in geogebra; vertices to extend coloring to
    colors[(255,0,0)]='salmon'  # red in geogebra; vertex and edge reducers
    colors[(0,255,255)]=other_v='skyblue'  # the rest of the vertices
    colors[(0,0,0)]=other_e='black'  # the rest of the edges
    colors[(255,0,255)]='magenta'  # magenta in geogebra; vertices to recolor
    
    vertex_colors=dict()
    for color in colors.values():
        vertex_colors[color]=[]
    for v in G.vertices(sort=False):
        color_of_v=G.get_vertex(v)['color'][:3]
        if color_of_v in colors:
            vertex_colors[colors[color_of_v]].append(v)
        else:
            vertex_colors[other_v].append(v)
    
    edge_colors=dict()
    for color in colors.values():
        edge_colors[color]=[]
    for e in G.edges(sort=False):
        color_of_e=G.edge_label(e[0],e[1])['color'][:3]
        if color_of_e in colors:
            edge_colors[colors[color_of_e]].append(e)
        else:
            edge_colors[other_e].append(e)
    
    return(G.plot(vertex_colors=vertex_colors,edge_colors=edge_colors))


def graph_to_geogebra(G,ggb_filename):
    '''
    Converts a SageMath graph into a GeoGebra file, where vertices become points and edges become line segments.
    Vertex labels become vertex labels.
    The graph's pos dictionary is used for the position of the points.
    '''
    with open("geogebra.xml","wt") as f:
        f.write(r'<?xml version="1.0" encoding="utf-8"?>' +"\n")
        f.write(r'<geogebra format="5.0">' +"\n")
        
        f.write(r'<euclidianView>' +"\n")
        f.write(r'<viewNumber viewNo="1"/>' +"\n")
        #f.write(r'<size width="2339" height="1196"/>' +"\n")
        #f.write(r'<coordSystem xZero="888.4649186451074" yZero="465.3980334757529" scale="653.3442584680625" yscale="653.3442584680623"/>' +"\n")
        f.write(r'<evSettings axes="false" grid="false" gridIsBold="false" pointCapturing="3" rightAngleStyle="1" checkboxSize="26" gridType="3"/>' +"\n")
        f.write(r'<bgColor r="255" g="255" b="255"/>' +"\n")
        f.write(r'<axesColor r="0" g="0" b="0"/>' +"\n")
        f.write(r'<gridColor r="192" g="192" b="192"/>' +"\n")
        f.write(r'<lineStyle axes="1" grid="0"/>' +"\n")
        f.write(r'<axis id="0" show="true" label="" unitLabel="" tickStyle="1" showNumbers="true"/>' +"\n")
        f.write(r'<axis id="1" show="true" label="" unitLabel="" tickStyle="1" showNumbers="true"/>' +"\n")
        f.write(r'</euclidianView>' +"\n")
        
        f.write(r'<construction>' +"\n")
        
        pos=G.get_pos()
        for v in G.vertices(sort=False):
            f.write(f'<element type="point" label="{v}">' +"\n")
            f.write(r'<show object="true" label="true"/>' +"\n")
            f.write(r'<objColor r="77" g="77" b="255" alpha="0"/>' +"\n")
            f.write(r'<layer val="0"/>' +"\n")
            f.write(r'<labelMode val="0"/>' +"\n")
            f.write(f'<coords x="{pos[v][0]}" y="{pos[v][1]}" z="1"/>' +"\n")
            f.write(r'<pointSize val="5"/>' +"\n")
            f.write(r'<pointStyle val="0"/>' +"\n")
            f.write(r'</element>' +"\n")
        
        for e in G.edges(sort=False):
            label=f"edge_{e[0]}_{e[1]}"
            f.write(r'<command name="Segment">' +"\n")
            f.write(f'<input a0="{e[0]}" a1="{e[1]}"/>' + "\n")
            f.write(f'<output a0="{label}"/>' +"\n")
            f.write(r'</command>' +"\n")
            f.write(f'<element type="segment" label="{label}">' +"\n")
            f.write(r'<show object="true" label="false"/>' +"\n")  # do not show edge label
            f.write(r'<objColor r="0" g="0" b="0" alpha="0"/>' +"\n")
            f.write(r'<layer val="0"/>' +"\n")
            f.write(r'<labelMode val="0"/>' +"\n")
            #f.write(r'<coords x="-0.8400000000000001" y="1.2800000000000002" z="4.5984"/>' +"\n")
            f.write(r'<lineStyle thickness="5" type="0" typeHidden="1" opacity="178"/>' +"\n")
            #f.write(r'<outlyingIntersections val="false"/>' +"\n")
            #f.write(r'<keepTypeOnTransform val="true"/>' +"\n")
            f.write(r'</element>' +"\n")
        
        f.write(r'' +"\n")
        f.write(r'</construction>' +"\n")
        f.write(r'</geogebra>' +"\n")
        # f.write(r'' +"\n")
    
    with zipfile.ZipFile(ggb_filename,'w') as f:
        f.write("geogebra.xml")
    

if __name__=="__main__":
    
    # Demonstration code
    filename="3vert_on_3face_4verts.ggb"
    G=geogebra_to_graph(filename)
    p=geogebra_graph_plot(G)
    p.save(filename+".pdf")
    
    pos=G.get_pos()
    print("vertices:")
    for v in G.vertices(sort=False):
        info=G.get_vertex(v)
        print(v,info,pos[v])
    print("edges:")
    for e in G.edges(sort=False):
        print(e,G.edge_label(e[0],e[1]))
    
    import sage.graphs.generators.smallgraphs
    G=sage.graphs.generators.smallgraphs.PetersenGraph()
    graph_to_geogebra(G,"petersen.ggb")
    
