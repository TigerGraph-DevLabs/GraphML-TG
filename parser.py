import xml.etree.ElementTree as ET
import re
import pyTigerGraph as tg

# DEBUG MODE :1
# NORMAL MODE : 0
DEBUG = 0


# GraphML Related 
fileGraphML = "sample.graphml"
EDGE_NAME = "EDGE_NAME"
NODE_NAME = "GraphMLNode"


# TigerGraph related
host        =  "http://127.0.0.1"
username    =  "tigergraph"
password    =  "tigergraph"
tg_version  =  "3.1.0"

    

nodes = []
edges = []

edgedefault = ""
graphname = ""


node_keys = []
edge_keys = []

node_data = []
edge_data = []

node_default = []
edge_default = []





try:
    conn = tg.TigerGraphConnection(host=host,username=username,password=password,version=tg_version)
    res = conn.gsql("ls")
except:
    print("Connection can't be established to TigerGraph Exititng")
    exit(0)


def getChild(root,level):
    global edgedefault
    global graphname
    global node_keys
    global edge_keys
    for child in root:
        
        ee = re.sub('{.*?}', '', child.tag)
        if level == 0 and re.sub('{.*?}', '', root.tag) == "graphml" and ee == "key":
            if child.attrib["for"] == "node":
                node_keys.append(child.attrib)
            if child.attrib["for"] == "edge":
                edge_keys.append(child.attrib)
        if level == 0 and ee == "graph":
            edgedefault = child.attrib["edgedefault"]
            try:
                graphname = child.attrib["id"]
            except:
                graphname = "G"
        if ee == "node":
            nodes.append(child.attrib)
        if ee == "edge":
            edges.append(child.attrib)
        getChild(child,level+1)

def graphmlParser(GraphMLFile):
    TigerTree = ET.parse(GraphMLFile)
    root = TigerTree.getroot()   
    getChild(root,0)

def result():
    if DEBUG:
        print("----------------nodes----------------")
        print(nodes)
        print("----------------edges----------------")
        print(edges)
        print("----------------node_keys----------------")
        print(node_keys)
        print("----------------edge_keys----------------")
        print(edge_keys)
        print("----------------edgedefault----------------")
        print(edgedefault)
        print("----------------graphname----------------")
        print(graphname)
        print("----------------Nodes----------------")
    create_statement = ""
    for element in node_keys:
        create_statement += ", {} {}".format(element['attr.name'],str(element['attr.type']).upper())

    final_statement_node = 'ADD VERTEX GraphMLNode (PRIMARY_ID id UINT{}) WITH primary_id_as_attribute="TRUE";'.format(create_statement)

    create_statement_edge = ""
    for element in edge_keys:
        create_statement_edge += ", {} {}".format(element['attr.name'],str(element['attr.type']).upper())

    final_statement_edge = 'ADD {} EDGE CONTAINER_OF (FROM {}, TO {} {});'.format(edgedefault.upper(),"GraphMLNode","GraphMLNode",create_statement_edge)

    print(final_statement_node)
    print(final_statement_edge)
    return final_statement_node,final_statement_edge


def schema(graphname,final_statement_nodes,final_statement_edges):
    gsql = """
    CREATE  GRAPH {0} ()
    USE GRAPH {0}
    CREATE SCHEMA_CHANGE JOB schema_change_job_{0} FOR GRAPH {0} {{ 
        {1}
        {2}
    }}
    RUN SCHEMA_CHANGE JOB schema_change_job_{0}
    DROP JOB schema_change_job_{0}

    """.format(graphname,final_statement_nodes,final_statement_edges)
    print(gsql)
    res = conn.gsql(gsql)
    print(res)

def insert_nodes(nodes):
    for node in nodes:
        conn.upsertVertex(NODE_NAME,node["id"])

def insert_edges(edges):
    for edge in edges:
        conn.upsertEdge(NODE_NAME,edge["source"],EDGE_NAME,NODE_NAME,edge["target"])

graphmlParser(fileGraphML)
a,b = result()
schema(graphname,a,b)
conn.graphname = graphname
conn.apiToken = conn.getToken(conn.createSecret())
insert_nodes(nodes)
insert_edges(edges)