import world_amazon_pb2
#!/usr/bin/env python3
from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint
import socket
import time

import sys
HOST = '0.0.0.0'  # The server's hostname or IP address
PORT = 23456        # The port used by the server

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

 

def send_to_server(msg):
    s.connect((HOST, PORT))
    print("connected to world simulator")
    _EncodeVarint(s.send, len(msg), None)
    s.sendall(msg)
    #data = s.recv(1024)
    
def receive():
    var_int_buff = []
    while True:
        buf = s.recv(1)
        var_int_buff += buf
        msg_len, new_pos = _DecodeVarint32(var_int_buff, 0)
        if new_pos != 0:
            break
    whole_message = s.recv(msg_len)
    print(str(whole_message))
    return whole_message

def create_world():
    aconnect = world_amazon_pb2.AConnect()
    aconnect.isAmazon = True
    warehouse = aconnect.initwh.add()
    warehouse.id = 1
    warehouse.x = 1
    warehouse.y = 1
    createworldmsg = aconnect.SerializeToString()
    send_to_server(createworldmsg)
    print(createworldmsg)
    aconnected = world_amazon_pb2.AConnected()
    aconnected.ParseFromString(receive())
    print("worldid:",aconnected.worldid)
    print("result:",aconnected.result)


def connect_world():
    aconnect = world_amazon_pb2.AConnect()
    aconnect.worldid = 1
    aconnect.isAmazon = True
    createworldmsg = aconnect.SerializeToString()
    send_to_server(createworldmsg)
    aconnected = world_amazon_pb2.AConnected()
    aconnected.ParseFromString(receive())
    print("worldid:",aconnected.worldid)
    print("result:",aconnected.result)
    
    
def main():
    create_world()
    #connect_world()
    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
