import socket
import psycopg2
import calendar
import time
import threading
import os
import signal
import world_amazon_pb2
#!/usr/bin/env python3
from google.protobuf.internal.decoder import _DecodeVarint32
from google.protobuf.internal.encoder import _EncodeVarint
import socket
import amazon_ups_pb2
import time
import datetime

import sys

print("hello daemon")
HOST = "amazondaemon"
PORT = 33333

mutex_seq = threading.Lock()

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
s.bind((HOST, PORT))
s.listen(5)
try:
    db_conn = psycopg2.connect(database="postgres", user="postgres", password="123456", host="db", port="5432")
    print("Opened database successfully")
    db_conn.set_isolation_level(3)
except:
    print("open db error")

orderID = ''
user_id = ''
x_pos = ''
y_pos = ''
product_name = ''
quantity = ''
SEQNUM = 0

PORT1 = 23456        # The port used by the server

s_world = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

s_world.connect(("vcm-8131.vm.duke.edu", PORT1))
print("connected with world")


PORT2 = 22222
PORT3 = 44444
sock_ama_ups = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s_ups_ama = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

sock_ama_ups.bind(("0.0.0.0", PORT2))
s_ama_ups = 0


sock_ama_ups.listen(5)
print("listen on ups")
s_ama_ups, addr_ups = sock_ama_ups.accept()
print("accept ups")


try:
    s_ups_ama.connect(("vcm-8273.vm.duke.edu", PORT3))
    print("connected to ups")
except Exception as e:
    print("connect ups error. Exception is %s", e)


def init_db():
    try:
        cur = db_conn.cursor()
        sql = "INSERT INTO ride_share_product(name, number, warehouse_id) " \
              "SELECT 'apple', 10000, 0" \
              " WHERE NOT EXISTS (SELECT id FROM ride_share_product WHERE id = 1)"
        cur.execute(sql)
        db_conn.commit()

        sql2 = "INSERT INTO ride_share_warehouse(warehouse_id, wh_x, wh_y) " \
              "SELECT 0, 21, 21" \
              " WHERE NOT EXISTS (SELECT id FROM ride_share_warehouse WHERE id = 1)"
        cur.execute(sql2)
        db_conn.commit()
        sql3 = "TRUNCATE TABLE ride_share_ack"
        cur.execute(sql3)
        db_conn.commit()
        print("init db success")
        purchase_more(0, 1, "apple", 10000)
    except Exception as e:
        print("init product database error")
        print(e)


def check_product_exit(product_name):
    try:
        cur = db_conn.cursor()
        sql = "SELECT * FROM ride_share_product WHERE name = '{}' ".format(product_name)
        print(sql)
        cur.execute(sql)
        db_conn.commit()
        res = cur.fetchall()
        if len(res) == 0:
           cur_getMaxId = db_conn.cursor()
           sql_getMaxId = "SELECT max(id) FROM ride_share_product"
           print(sql_getMaxId)
           cur_getMaxId.execute(sql_getMaxId)
           db_conn.commit()
           res_getMaxId = cur.fetchall()
           new_item = res_getMaxId[0]
           max_id = new_item[0]
           productID = int(max_id)+1
           return False, productID
        else:
            item = res[0]
            product_id = item[0]
            return True, product_id

    except Exception as e:
        print("check product exit error")
        print(repr(e))


def search_product_db(product_name, quantity):
    try:
        cur = db_conn.cursor()
        sql = "SELECT * FROM ride_share_product WHERE name = '{}' AND number >= {}".format(product_name, quantity)
        print(sql)
        cur.execute(sql)
        db_conn.commit()
        res = cur.fetchall()
        if len(res) == 0:
            return -2
        else:

            item = res[0]
            id = item[0]
            number = item[2]
            number_update = int(number) - int(quantity)
            warehouse_id = item[3]
            print("in search product warehouse id is", warehouse_id)
            cur_update = db_conn.cursor()
            sql_update = "UPDATE ride_share_product SET number = "+str(number_update)+" WHERE id = "+str(id)+";"
            print(sql_update)
            cur_update.execute(sql_update)
            db_conn.commit()
            return warehouse_id

    except Exception as e:
        print("search product db error")
        print(repr(e))
    return -1


def update_order_status(order_id, status):
    try:
        cur = db_conn.cursor()
        sql = "UPDATE ride_share_order SET status ='{}' WHERE id={}".format(status, order_id)
        cur.execute(sql)
        db_conn.commit()
    except Exception as e:
        print("update order status error")
        print(repr(e))


def query_ack(ack_num, type):
    try:
        cur = db_conn.cursor()
        sql = "SELECT * FROM ride_share_ack WHERE ack_num={} AND type = '{}'".format(ack_num, type)
        cur.execute(sql)
        res = cur.fetchall()
        if len(res) ==0:
            return False
        else:
            return True
    except Exception as e:
        print("query ack db error")
        print(repr(e))


def insert_ack(ack_num, type):
    try:
        cur = db_conn.cursor()
        sql = "INSERT INTO ride_share_ack(ack_num, type) VALUES({}, '{}')".format(ack_num, type)
        cur.execute(sql)
        db_conn.commit()
    except Exception as e:
        print("update ack db error")
        print(repr(e))


def send_world_ack(ack):
    acommand = world_amazon_pb2.ACommands()
    acommand.acks.append(ack)
    msg = acommand.SerializeToString()
    send_to_server_init(msg)

def send_ups_444_ack(ack):
    a2urequest = amazon_ups_pb2.A2URequest()
    a2urequest.ack.append(ack)
    msg = a2urequest.SerializeToString()
    _EncodeVarint(s_ups_ama.send, len(msg), None)
    s_ups_ama.sendall(msg)

def send_ups_222_ack(ack):
    a2uresponse = amazon_ups_pb2.A2UResponse()
    a2uresponse.ack.append(ack)
    msg = a2uresponse.SerializeToString()
    _EncodeVarint(s_ama_ups.send, len(msg), None)
    s_ama_ups.sendall(msg)


def handle_ack(seq_num, ack_num, type):
    if seq_num == ack_num:
        #send_world_ack(ack_num)
        print("in handle ack, match, send back to world")
    # else:
    #     ack_exist = query_ack(ack_num, type)
    #
    #     if ack_exist == False:
    #         insert_ack(ack_num, type)
    #
    #     seq_exist = query_ack(seq_num, type)
    #     if seq_exist == False:
    #         print("in handle ack, still need recving")
    #         return True
    return False


def recv_world_resp(seq_num):
    return_res = "res"
    while True:
        response = world_amazon_pb2.AResponses()
        response.ParseFromString(receive())
        print("received response from world")

        for purchasearrive in response.arrived:
            print("product arrived at warehouse id:", purchasearrive.whnum)
            for thing in purchasearrive.things:
                curarrive = db_conn.cursor()
                sql = "INSERT INTO ride_share_ack(ack_num, type, status) VALUES({}, 'W2A', 'arrived')".format(seq_num)
                curarrive.execute(sql)
                db_conn.commit()
                print("product id:", thing.id)
                print("description", thing.description)
                print("count:", thing.count)

                send_world_ack(thing.seqnum)
            return_res = "arrived"
        for error in response.error:
            print("error:", error.err)
            send_world_ack(error.seqnum)
            curerr = db_conn.cursor()
            sql = "INSERT INTO ride_share_ack(ack_num, type, status) VALUES({}, 'W2A', 'error')".format(seq_num)
            curerr.execute(sql)
            db_conn.commit()
            return_res = "error"
        for packed in response.ready:
            send_world_ack(packed.seqnum)
            curpacked = db_conn.cursor()
            sql = "INSERT INTO ride_share_ack(ack_num, type, status) VALUES({}, 'W2A', 'packed')".format(seq_num)
            curpacked.execute(sql)
            db_conn.commit()
            print("packed ship id:", packed.shipid)
            cur1 = db_conn.cursor()
            sql1 = "UPDATE ride_share_order SET status = '{}' WHERE id = {}".format("PACKED", packed.shipid)
            cur1.execute(sql1)
            db_conn.commit()
            sq11_insert = "INSERT INTO ride_share_messageworld(order_id, message, type) " \
                          "VALUES({}, '{}', '{}')".format(packed.shipid, "PACKED", "PACKED")
            cur1.execute(sq11_insert)
            db_conn.commit()
            return_res = "packed"
        for loaded in response.loaded:
            curloaded = db_conn.cursor()
            sql = "INSERT INTO ride_share_ack(ack_num, type, status) VALUES({}, 'W2A', 'loaded')".format(seq_num)
            curloaded.execute(sql)
            db_conn.commit()
            print("loaded ", loaded)
            send_world_ack(loaded.seqnum)
            cur2 = db_conn.cursor()
            sql2 = "UPDATE ride_share_order SET status = 'LOADED' WHERE id = {}".format(loaded.shipid)
            cur2.execute(sql2)
            db_conn.commit()

            sq12_insert = "INSERT INTO ride_share_messageworld(order_id, message, type) " \
                          "VALUES({}, '{}', '{}')".format(loaded.shipid, "LOADED", "LOADED")
            cur2.execute(sq12_insert)
            db_conn.commit()
            return_res = "loaded"
        for packagestatus in response.packagestatus:
            curquery = db_conn.cursor()
            sql = "INSERT INTO ride_share_ack(ack_num, type, status) VALUES({}, 'W2A', 'packagestatus')".format(seq_num)
            curquery.execute(sql)
            db_conn.commit()
            send_world_ack(packagestatus.seqnum)
            print("packageid: ", packagestatus.packageid)
            print("status: ", packagestatus.status)
            update_order_status(packagestatus.packageid, packagestatus.status)
            return_res = "packagestatus"

        res_set = []
        for ack in response.acks:
            print("ack:", ack)
            handle_res = handle_ack(int(seq_num), int(ack), "W2A")
            res_set.append(handle_res)
        mark_keep_recv = False
        for res in res_set:
            if res == True:
                mark_keep_recv = True
        curack = db_conn.cursor()
        sql = "SELECT status FROM ride_share_ack WHERE ack_num =  {}".format(seq_num)
        curack.execute(sql)
        ackres = curack.fetchall()

        if mark_keep_recv == False and len(ackres) != 0:
            print("breaking while 1 recving from world")
            break
    return return_res


def query(orderid):
    acommands = world_amazon_pb2.ACommands()
    acommands.simspeed = 100000
    aquery = acommands.queries.add()
    aquery.packageid = orderid
    global SEQNUM
    mutex_seq.acquire()
    SEQNUM += 1
    mutex_seq.release()
    aquery.seqnum = SEQNUM
    msg = acommands.SerializeToString()
    print("query seqnum: ", aquery.seqnum)
    send_to_server(msg, SEQNUM)


def to_pack(whnum, productid, description, count, orderid):
    print("in to pack function")
    acommands = world_amazon_pb2.ACommands()
    acommands.simspeed = 100000
    apack = acommands.topack.add()
    apack.whnum = whnum
    product = apack.things.add()
    product.id = productid
    product.description = description
    product.count = count
    apack.shipid = orderid
    global SEQNUM
    mutex_seq.acquire()
    SEQNUM += 1
    mutex_seq.release()
    apack.seqnum = SEQNUM
    print("topack seqnum: ", apack.seqnum)
    msg = acommands.SerializeToString()
    res = send_to_server(msg, SEQNUM)

    return res


def query_order(order_id):
    query(order_id)


def purchase_more(whnum, product_id, description, count):
    acommands = world_amazon_pb2.ACommands()
    acommands.simspeed = 1000
    purchasemore = acommands.buy.add()
    purchasemore.whnum = whnum
    global SEQNUM
    mutex_seq.acquire()
    SEQNUM += 1
    mutex_seq.release()
    purchasemore.seqnum = SEQNUM

    product = purchasemore.things.add()
    product.id = product_id
    product.description = description
    product.count = count
    msg = acommands.SerializeToString()
    send_to_server(msg, SEQNUM)


def receive_u2a_response():
    var_int_buff = []
    while True:
        buf = s_ups_ama.recv(1)
        var_int_buff += buf
        msg_len, new_pos = _DecodeVarint32(var_int_buff, 0)
        if new_pos != 0:
            break
    whole_message = s_ups_ama.recv(msg_len)
    print(str(whole_message))
    return whole_message


def pickup_request(order_id, product_name, whid, wh_x, wh_y, dest_x, dest_y, ups_acc):
    a2urequest = amazon_ups_pb2.A2URequest()
    pickup = a2urequest.pickup.add()
    global SEQNUM
    mutex_seq.acquire()
    SEQNUM += 1
    mutex_seq.release()
    pickup.seqnum = SEQNUM
    pickup.orderid = order_id
    pickup.productName = product_name
    pickup.whid = whid
    pickup.wh_x = wh_x
    pickup.wh_y = wh_y
    pickup.dest_x = dest_x
    pickup.dest_y = dest_y
    if ups_acc != '':
        pickup.upsAccount = ups_acc
    msg = a2urequest.SerializeToString()
    _EncodeVarint(s_ups_ama.send, len(msg), None)
    s_ups_ama.sendall(msg)


def put_on_truck(whnum,truckid,orderid):
    acommand = world_amazon_pb2.ACommands()
    load = acommand.load.add()
    load.whnum = whnum
    load.truckid = truckid
    load.shipid = orderid
    global SEQNUM
    mutex_seq.acquire()
    SEQNUM += 1
    mutex_seq.release()
    load.seqnum = SEQNUM
    msg = acommand.SerializeToString()
    res = send_to_server(msg, SEQNUM)
    return res


def recv_pickup_resp():

    while True:

        u2aresponse = amazon_ups_pb2.U2AResponse()
        print("in receive pickup response while")
        u2aresponse.ParseFromString(receive_u2a_response())
        truckid = -1
        ups_ack = -1
        for ack in u2aresponse.ack:
            print("pickup response ack: ", ack)
            ups_ack = ack
        for pickup in u2aresponse.pickup:
            truckid = pickup.truckid
        if truckid != -1:
            print("jump out of truck id while")
            print("truck id:", truckid)
            send_ups_444_ack(ups_ack)
            break

    return truckid


def delivery_request(tracknum):
    a2urequest = amazon_ups_pb2.A2URequest()
    delivery = a2urequest.delivery.add()
    global SEQNUM
    mutex_seq.acquire()
    SEQNUM += 1
    mutex_seq.release()
    delivery.seqnum = SEQNUM
    delivery.tracknum = tracknum
    msg = a2urequest.SerializeToString()
    _EncodeVarint(s_ups_ama.send, len(msg), None)
    s_ups_ama.sendall(msg)


def recv_deliver_resp():
    u2aresponse = amazon_ups_pb2.U2AResponse()
    while True:
        u2aresponse.ParseFromString(receive_u2a_response())
        tracknum = -1
        for ack in u2aresponse.ack:
            print("deliver response ack:", ack)
        for delivery in u2aresponse.delivery:
            tracknum = delivery.tracknum
        if tracknum != -1:
            break
    update_delivery(tracknum)


def update_delivery(tracknum):
    try:
        cur = db_conn.cursor()
        sql = "UPDATE ride_share_order SET status = 'DELIVERED' WHERE id = {}".format(int(tracknum))
        cur.execute(sql)
        db_conn.commit()
    except Exception as e:
        print("update delivery status db error")


def pickup_handler(order_id, product_name, whid, wh_x, wh_y, dest_x, dest_y, ups_acc):
    print("in pickup handler function")
    while True:
        cur = db_conn.cursor()
        sql = "SELECT status FROM ride_share_order WHERE id ={}".format(order_id)
        cur.execute(sql)
        res = cur.fetchall()
        item = res[0]
        status = str(item[0])
        if status == "PACKED":
            break
    # send pickup to ups
    print("in pick up handler, ready to send pickup request")
    pickup_request(order_id, product_name, whid, wh_x, wh_y, dest_x, dest_y, ups_acc)
    # get response from ups
    print("after send pick up")
    truck_id = recv_pickup_resp()
    print("received in pick up is ", truck_id)
    if truck_id != -1:
        # send load to warehouse
        # get response from warehouse
        res_load = put_on_truck(0, truck_id, order_id)
        while True:
            cur_check_load = db_conn.cursor()
            sql_load = "SELECT status FROM ride_share_order WHERE id = {} AND status = 'LOADED'".format(order_id)
            cur_check_load.execute(sql_load)
            res_load_db = cur_check_load.fetchall()
            if len(res_load_db) !=0:
                print("now we are loaded and can send delivery")
                break

        # send deliver to ups
        print("sending deliver to ups")
        delivery_request(order_id)
        print("recving response for ups deliver")
        recv_deliver_resp()


def operation(order_id, conn):
    print("in operation")
    cur = db_conn.cursor()
    sql = "SELECT id, user_id, x_pos, y_pos, product_name, quantity, ups_acc FROM ride_share_order WHERE id = {};".format(order_id)
    time.sleep(3)
    cur.execute(sql)
    db_conn.commit()
    res = cur.fetchall()
    if len(res) == 0:

        # msg = 'error'
        print("OrderID does not exits:", order_id)
        # conn.send(msg.encode())
        # print("send back to web with error")


    else:
        # msg = 'success'
        # print('before send success to web')
        # conn.send(msg.encode())
        # print("send back to web with success")
        for item in res:
            orderID = str(item[0])
            user_id = str(item[1])
            x_pos = str(item[2])
            y_pos = str(item[3])
            product_name = str(item[4])
            quantity = str(item[5])
            ups_acc = str(item[6])

        print(orderID)
        print(user_id)
        print(x_pos)
        print(y_pos)
        print(product_name)
        print(quantity)
        print(ups_acc)
        search_product = search_product_db(product_name, quantity)
        exist, product_id = check_product_exit(product_name)
        if search_product == -2:
            #not enough produce, contact with warehouse
            print("contact to warehouse to get more products")
            purchase_more(1, product_id, product_name, 2*int(quantity))
            if exist == True:
                #update
                try:
                    cur = db_conn.cursor()
                    sql1 = "SELECT number FROM ride_share_order WHERE id = "+str(product_id)+";"
                    cur.execute(sql1)
                    res = cur.fetchall()
                    number_set = res[0]
                    num_old = number_set[0]
                    num_new = int(quantity) + int(num_old)
                    sql2 = "UPDATE ride_share_order SET number = "+ num_new + ";"
                    cur.execute(sql2)
                    db_conn.commit()
                except Exception as e:
                    print("update product db error")
                    print(repr(e))

            if exist==False:
                #insert
                try:
                    new_num = int(quantity)
                    cur = db_conn.cursor()
                    sql = "INSERT INTO ride_share_product(name, number, warehouse_id) " \
                          "VALUES('{}', {}, 1 )".format(product_name, new_num)
                    cur.execute(sql)
                    db_conn.commit()
                except Exception as e:
                    print("update product db error")
                    print(repr(e))
        elif search_product == -1:
            print("something error in search product")
        else:
            print("found enough product in db")
            # send two packs to warehouse
            print(search_product)
            print("warehouse id is ")
            print(search_product)
        cur = db_conn.cursor()
        sql = "SELECT * FROM ride_share_warehouse WHERE warehouse_id = 0"
        cur.execute(sql)
        res = cur.fetchall()
        print("in test out of range, length is ", len(res))
        item = res[0]
        wh_x = item[2]
        wh_y = item[3]
        print(wh_x)
        print(wh_y)
        two_threads = []
        t1 = threading.Thread(target=to_pack, args=(0, int(product_id), product_name, int(quantity), int(order_id),))
        t1.start()
        two_threads.append(t1)

        print("sending to pack in operation func")
        #pickup_request(int(order_id), product_name, 0, 21, 21, int(x_pos), int(y_pos))
        t2 = threading.Thread(target=pickup_handler, args=(int(order_id),product_name, 0, 21, 21, int(x_pos), int(y_pos), ups_acc, ))
        t2.start()
        two_threads.append(t2)

        print("sending pickup in operation func")


# def handler_time(signum, frame):
#     print("Forever is over!")
#     raise Exception("end of time")



def send_to_server(msg, seq_num):
    # signal.signal(signal.SIGALRM, handler_time)
    # signal.alarm(15)
    while True:
        res = ""
        print("in send_to_server outer loop")
        _EncodeVarint(s_world.send, len(msg), None)
        s_world.sendall(msg)
        try:
            starttime = time.time()
            res = recv_world_resp(seq_num)
            endtime = time.time()
            print("res is:", res)
            if res != "":
                if int((endtime-starttime)) < 200:
                    break
        except Exception as exc:
           continue
    print("breaking out of outer loop")
    # signal.alarm(0)
    return res


def receive():
    var_int_buff = []
    while True:
        buf = s_world.recv(1)
        var_int_buff += buf
        msg_len, new_pos = _DecodeVarint32(var_int_buff, 0)
        if new_pos != 0:
            break
    whole_message = s_world.recv(msg_len)
    print(str(whole_message))
    return whole_message


def send_to_server_init(msg):
    _EncodeVarint(s_world.send, len(msg), None)
    s_world.sendall(msg)


def create_world():
    aconnect = world_amazon_pb2.AConnect()
    aconnect.isAmazon = True
    warehouse = aconnect.initwh.add()
    warehouse.id = 0
    warehouse.x = 21
    warehouse.y = 21
    createworldmsg = aconnect.SerializeToString()
    print('createworldmsg',createworldmsg)
    send_to_server_init(createworldmsg)
    aconnected = world_amazon_pb2.AConnected()
    aconnected.ParseFromString(receive())
    print("worldid:", aconnected.worldid)
    print("result:", aconnected.result)


def connect_world(word_id):
    aconnect = world_amazon_pb2.AConnect()
    aconnect.worldid = word_id
    aconnect.isAmazon = True
    warehouse = aconnect.initwh.add()
    warehouse.id = 0
    warehouse.x = 21
    warehouse.y = 21
    createworldmsg = aconnect.SerializeToString()
    send_to_server_init(createworldmsg)
    aconnected = world_amazon_pb2.AConnected()
    aconnected.ParseFromString(receive())
    print("connect worldid:", aconnected.worldid)
    print("connect result:", aconnected.result)


def send_u2aconnected(world_id):
    u2aconnected = amazon_ups_pb2.U2AConnected()
    u2aconnected.worldid = world_id
    u2aconnected.result = "connected!"
    msg = u2aconnected.SerializeToString()
    _EncodeVarint(s_ama_ups.send, len(msg), None)
    s_ama_ups.sendall(msg)


def receive_u2a_request():
    var_int_buff = []
    print("enter receiveUPS")
    while True:
        try:
            buf = s_ama_ups.recv(1)
            print("in receive ups:", buf)
        except Exception as e:
            print(e)
        var_int_buff += buf
        msg_len, new_pos = _DecodeVarint32(var_int_buff, 0)
        if new_pos != 0:
            break
    whole_message = s_ama_ups.recv(msg_len)
    print(str(whole_message))
    return whole_message


def recv_u2aconnect(from_ups):
    u2aconnect = amazon_ups_pb2.U2AConnect()
    u2aconnect.ParseFromString(from_ups)
    return u2aconnect.worldid


def handlerOrder(conn, addr):
    print("in handle order function")
    from_client = ''
    while True:

        data = conn.recv(1024)
        print("accepted")
        if not data:
            break
        from_client += data.decode('ascii')

    print("received from the web ")
    print(from_client)
    if from_client.find("query") == -1:
        print("when buy order")

        operation(from_client, conn)

    else:
        pos = from_client.find(" ")
        order_id = int(from_client[pos + 1:])
        print("when query order")
        print(order_id)
        query_order(order_id)
    conn.close()


# def receive_u2a_request():
#     var_int_buff = []
#     while True:
#         buf = s_ama_ups.recv(1)
#         var_int_buff += buf
#         msg_len, new_pos = _DecodeVarint32(var_int_buff, 0)
#         if new_pos != 0:
#             break
#     whole_message = s_ama_ups.recv(msg_len)
#     print(str(whole_message))
#     return whole_message


def update_dest(id, new_x, new_y):
    try:
        cur = db_conn.cursor()
        sql = "UPDATE ride_share_order SET x_pos = {}, y_pos = {} WHERE id = {}".format(int(new_x),
                                                                                                 int(new_y),int(id))
        cur.execute(sql)
        db_conn.commit()
    except Exception as e:
        print(e)
        return "error"


def send_ups_error(originseq, seqnum):
    a2uresponse = amazon_ups_pb2.A2UResponse()
    a2uresponse.ack.append(originseq)
    error = a2uresponse.error.add()
    error.originseqnum = originseq
    error.seqnum = seqnum
    error.err = "update destination error: tracknum does not exist"
    msg = a2uresponse.SerializeToString()
    _EncodeVarint(s_ama_ups.send, len(msg), None)
    s_ama_ups.sendall(msg)


def receive_update_des():
    u2arequest = amazon_ups_pb2.U2ARequest()
    u2arequest.ParseFromString(receive_u2a_request())
    seqnum = 0
    tracknum = 0
    new_x = 0
    new_y = 0
    for dest in u2arequest.dest:
        seqnum = dest.seqnum
        tracknum = dest.tracknum
        new_x = dest.new_x
        new_y = dest.new_y
    res = update_dest(tracknum,new_x,new_y)
    if res == "error":
        global SEQNUM
        SEQNUM += 1
        send_ups_error(seqnum, SEQNUM)
    else:
        send_ups_222_ack(seqnum)


threads = []


def main():
    buy_order_id = 0
    print("hello daemon main")
    while True:
        from_ups = receive_u2a_request()
        if from_ups != '':
            break
    world_id = recv_u2aconnect(from_ups)
    print("received world id from ups", world_id)
    connect_world(world_id)
    # create_world()
    send_u2aconnected(world_id)
    print("send world id to ups")

    init_db()

    while True:
        conn, addr = s.accept()
        # handlerOrder(conn, addr)
        t = threading.Thread(target=handlerOrder, args=(conn, addr, ))
        t.start()
        threads.append(t)
        print("in main, after call handlerorder")
        t2 = threading.Thread(target=receive_update_des, args=())
        t2.start()
        threads.append(t2)

    db_conn.close()
    s_ama_ups.close()
    sock_ama_ups.close()
    s_ups_ama.close()


for t in threads:
    t.join()


if __name__ == "__main__":
    main()


