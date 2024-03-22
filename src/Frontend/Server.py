import json
import socket

import requests
from flask import Flask, request,jsonify

app=Flask(__name__)

inMemCacheDict={}


#end points defined
TRADE_ENDPOINT = '/trade_stocks'
LOOKUP_ENDPOINT = '/Lookup_csv/'
QUERYORDER_ENDPOINT = '/get_order_data'
HEALTH_CHECK_ENDPOINT = '/health'

CatalogServer='http://localhost:5001'
OrderServer_prefix='http://localhost:'

CacheFlag=False  #switch to turn ON and OFF the cache


order_replicas_status = {'1':False,'2':False,'3':False}     #Dict to maintain status of all the replicas

#To read config data of all the replicas from config file
f = open("config.json","r")
json_data = f.read()
config_data = json.loads(json_data)

#To find leader
def leader_election(unresponsive_node=1000,config_data=config_data):
    leader_ID=0
    for i in range(len(config_data)):
        print("unresponsive node: ",unresponsive_node)
        if config_data[i]["ID"]>leader_ID and unresponsive_node>config_data[i]['ID']:
            leader_ID=config_data[i]["ID"]      #retrieving leader ID
            leader_PORT=config_data[i]["PORT"] #retrieving leader Port
    print(leader_ID,leader_PORT)
    return leader_ID,leader_PORT

#Send health check req to leader and if up broadcast leader to all replicas
def health_check_to_leader(leader_ID,leader_PORT):
    try:
        health_check_response=requests.get(OrderServer_prefix + str(leader_PORT) + HEALTH_CHECK_ENDPOINT) #send requests for health check
        health_check_resp=health_check_response.json()
        print("Health check response from leader: ",health_check_resp)
        if health_check_response.status_code == 200:
            print('Server is healthy')
            order_replicas_status[str(leader_ID)]=True      #set the status of Leader node to True in order_replicas_status
            print(order_replicas_status)
            return 'OK',leader_ID,leader_PORT
    except requests.exceptions.ConnectionError:     #if there is a connection error during health check
        print('Leader is unresponsive hence re-doing the election for a new leader')
        new_leader_ID,new_leader_PORT=leader_election(unresponsive_node=leader_ID) #call for leader election
        return health_check_to_leader(new_leader_ID,new_leader_PORT)


#Broadcast leader to all the replicas
def broadcast_leader(leader_ID,config_data):
    ENDPOINT='/leader_broadcast'
    payload = {'leader_ID': leader_ID}
    for i in range(len(config_data)):
        PORT=config_data[i]['PORT']
        try:
            response = requests.post('http://localhost:' + str(PORT) + ENDPOINT, json=payload)  #broadcast request to all replicas
            print(response.status_code)
            if response.status_code == 200:
                print('leader value received by the replica hence updating they are alive')
                order_replicas_status[str(config_data[i]['ID'])]=True   #leader value received by the replica hence updating they are alive by setting True
                print(order_replicas_status)
        except requests.exceptions.ConnectionError:  #in case of connection error, node is unresponsive
            print('Error sending/receiving leader value by the replica as it is unresponsive node')

leader_ID,leader_PORT = leader_election()  #startup leader election function call
health_response,leader_ID,leader_PORT = health_check_to_leader(leader_ID,leader_PORT) #startup health check
print(health_response,leader_ID,leader_PORT)
broadcast_leader(leader_ID,config_data) #broadcasting leader during startup


#health check function for each order service node
@app.route('/health_check',methods=['GET'])
def health_check():
    result=dict()
    leader_ID,leader_PORT = leader_election()
    res,ID,PORT = health_check_to_leader(leader_ID,leader_PORT) #health check response from leader
    result['leader_response']=res
    result['leader_ID']=ID
    result['leader_PORT']=PORT
    return jsonify(result)


@app.route('/update_order_replica_status/<replica_ID>',methods=['GET'])
def update_order_replica_status(replica_ID):
    order_replicas_status[replica_ID]=True    #set the replica status to True
    print("updated replicas status: ",order_replicas_status)
    leader_ID,leader_PORT = leader_election()   #Re-do leader election bcz a new order server is UP
    print("new leader is:",leader_ID,leader_PORT)
    return jsonify({'status':'OK'})


#endpoint for getting leader_ID
@app.route('/getleaderID', methods=['GET'])
def getleaderID():
    return jsonify({'leader_ID':leader_ID,'leader_PORT':leader_PORT}),200

#endpoint for looking up stocks
@app.route('/stocks/<stock_name>', methods=['GET'])
def lookup(stock_name):

    if stock_name in inMemCacheDict and CacheFlag==True:       #only check stockname in cache if CacheFlag is set to True
        print("############## Pulling from In-memmory Cache #################")
        data_dict= {}
        data_dict['name']=stock_name
        data_dict2=inMemCacheDict[stock_name]
        data_dict.update(data_dict2)    #updating the response to send back frontend
        print("final data_dict :",data_dict)
        return jsonify(data_dict)

    else:           #if not in inMemCacheDict GET request to catalog server
        lookupResponse=requests.get(CatalogServer + LOOKUP_ENDPOINT+'/'+stock_name)
        lookupResponse=lookupResponse.json()
        print("type of lookupresponse",type(lookupResponse))
        print("lookupResponse before :",lookupResponse)
        if type(lookupResponse) == dict:   #cleaning up the response by removing 'max_trade'
            if 'max_trade' in lookupResponse.keys():
                del lookupResponse['max_trade']
        print("lookupResponse:",lookupResponse)
        if lookupResponse != "stock not found" and CacheFlag==True :    #only push response to cache if CacheFlag is set to True
            print("############## Pushing to In-memmory Cache #################")
            dict_copy=lookupResponse.copy()
            del dict_copy['name']  #cleaning the dict_copy to delete the 'name'
            inMemCacheDict[stock_name]=dict_copy
            print("inMemCacheDict: ",inMemCacheDict)

        elif lookupResponse == "stock not found":  #if stock not found return error message
            #creating the error body message
            print("############## Error : No stock found  #################")
            message={"error": {"code": 404,
                               "message": "stock not found"}}
            return jsonify(message),404
        return jsonify(lookupResponse),200

#end point to trade requests buy or sell
@app.route('/orders', methods=['POST'])
def trade():
    data = request.json
    print("data to post :",data)
    leader_ID,leader_PORT = leader_election() #get the leader info from leader election
    health_response,leader_ID,leader_PORT = health_check_to_leader(leader_ID,leader_PORT)  #health check response from leader
    print(health_response,leader_ID,leader_PORT)
    if health_response=='OK':    #if leader health is OK
        traderesponse = requests.post(OrderServer_prefix + str(leader_PORT) + TRADE_ENDPOINT, json=data)
        traderesponse=traderesponse.json()      #response from Orders service
        print("response from Orders service : ",traderesponse)
        if traderesponse == "max trading volume exceeded":      #when the quantity exceeds the max trade limit throw error
            #creating the error body message
            print("############## Error : Max Trading volume exceeded  #################")
            message={"error": {"code": 422,
                               "message": "Max Trading volume exceeded"}}
            return jsonify(message),422
        return jsonify(traderesponse),200



#end point for Ordernumber enquiry from client
@app.route('/orders/<order_number>',methods=['GET'])
def queryOrder(order_number):
    print("order_number",order_number)
    leader_ID,leader_PORT = leader_election()
    health_response,leader_ID,leader_PORT = health_check_to_leader(leader_ID,leader_PORT)  #health check response from leader
    print(health_response,leader_ID,leader_PORT)
    broadcast_leader(leader_ID,config_data) #broadcast leader to all replicas
    if health_response=='OK':
        querOrderResponse=requests.get(OrderServer_prefix + str(leader_PORT) +QUERYORDER_ENDPOINT+'/'+order_number)
        querOrderResponse=querOrderResponse.json() #response from Order service
        print(querOrderResponse)
        if querOrderResponse=='order not found':  #if no order exists
            message={"error": {"code": 404,
                               "message": "order number doesn't exist"}}
            return jsonify(message),404
        return jsonify(querOrderResponse)


#api for invalidate memcache
@app.route('/invalidate_MemCache', methods=['POST'])
def invalidate_MemCache():
    stock_name = request.json
    if stock_name in inMemCacheDict:    #if stockname available in  inMemCache,delete the entry
        del inMemCacheDict[stock_name]
        print("Updated In-Mem Cache :",inMemCacheDict)
        response={'Invalidation Request' : 'Success'}
    else:
        response={'Invalidation Request' : 'Not Applicable'} # if teh stockname not available, not applicable response
    return jsonify(response)



if __name__ == '__main__':
    app.run(debug=True, port=5000, host=socket.gethostname())  #localhost
