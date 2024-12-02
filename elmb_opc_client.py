#!/usr/bin/env python
############################################
# OPC-UA client for the CanOpcUAClient
# Carlos.Solans@cern.ch
# Luca.Colangeli@mail.utoronto.ca
############################################

from opcua import Client
from opcua import ua

class elmb_opc_client:
    def __init__(self, connstr,connect=False):
        self.verbose=False
        self.nodes = {}
        self.client = Client(connstr)
        self.client.session_timeout = 600000
        self.client.secure_channel_timeout = 600000
        if connect: self.Open()
        pass
    def Open(self):
        try:
            self.client.connect()
        except:
            print("Cannot connect to server on: %s" % connstr)
            return
        self.FindNodes(self.client.get_objects_node().get_children(),self.nodes,["bus","elmb","TPDO3","ch"])
        pass
    def FindNodes(self,objs,nodes,keys):
        for obj in objs:
            if "transportMech" in obj.get_display_name().Text: continue
            if "_TPDO" in obj.get_display_name().Text: continue
            if keys[0] in obj.get_display_name().Text:
                if self.verbose: print("Found node: %s" % (obj.get_display_name().Text)) 
                if len(keys)>1:
                    nodes[obj.get_display_name().Text]={}
                    self.FindNodes(obj.get_children(),nodes[obj.get_display_name().Text],keys[1:])
                    pass
                else:
                    #print(obj.get_children()[-1].get_value())
                    nodes[obj.get_display_name().Text]=obj.get_children()[-1]
                    pass
                pass
            pass
        return nodes
    def Close(self):
        self.client.disconnect()
        pass
    def PrintServerInfo(self):
        self.root = self.client.get_root_node()
        print("Root node is: ", self.client.get_root_node())
        print("Children of root are: ", self.client.get_root_node().get_children())
        print("Children of objects are: ", self.client.get_objects_node().get_children())
        pass
    def SetVerbose(self, v):    
        self.verbose = v
        pass  
    pass

if __name__=="__main__":
    
    import os
    import sys
    import signal
    import argparse
    import time
    import datetime

    constr="opc.tcp://pcatlidiot01:48012"
    
    parser=argparse.ArgumentParser()
    parser.add_argument('-s','--constr',help="connection string: %s" % constr, default=constr)
    parser.add_argument("-d","--delay",help="Delay time [s] between measurements.Default 0",type=int,default=2)
    parser.add_argument('-v','--verbose',help="enable verbose mode", action="store_true")
    
    args=parser.parse_args()
    
    client=elmb_opc_client(args.constr)
    client.SetVerbose(args.verbose)
    client.Open()
         
    
    cont = True
    def signal_handler(signal, frame):
        print('You pressed ctrl+C')
        global cont
        cont = False
        return

    signal.signal(signal.SIGINT, signal_handler)

    print("Reading")
    
    tstart = int(time.time()) # start time
    #client.Close()
    #sys.exit()
    
    while True:
        tcurr = int(time.time())
        if cont==False: break
        if(args.verbose): print(client.nodes)
        for k1 in client.nodes:
            if not isinstance(client.nodes[k1],dict): continue
            for k2 in client.nodes[k1]:
                if not isinstance(client.nodes[k1][k2],dict): continue
                for k3 in client.nodes[k1][k2]:
                    if not isinstance(client.nodes[k1][k2][k3],dict): continue
                    for k4 in client.nodes[k1][k2][k3]:
                        print("%s.%s.%s.%s: %s" % (k1,k2,k3,k4,client.nodes[k1][k2][k3][k4].get_value()))
                        
        time.sleep(args.delay)
        pass
    pass
    print("Closing connection")
    client.Close()
    print("Have a nice day")
    pass
