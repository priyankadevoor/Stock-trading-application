import requests
from flask import Flask, request, json, Response, jsonify
import os,csv,sys
from Read_Write_Lock import ReadWriteLock

app=Flask(__name__)

#Variables to store the order replicas ID,PORT and DB path.
self_ID=int(sys.argv[1])
PORT=sys.argv[2]
DB_path=sys.argv[3]
leader_ID=None

#Variables to store all servers link
CatalogServer='http://localhost:5001'
OrderServer_prefix='http://localhost:'
FrontendServer = 'http://localhost:5000'

rwlock=ReadWriteLock()

LOOKUP_ENDPOINT = '/Lookup_csv/'

#To read config data of all the replicas from config file and store it in a dictionary
f = open("config.json","r")
json_data = f.read()
config_data = json.loads(json_data)

#If the passed transaction number exists in the DB entire row from the csv file is returned as a dictionary else order not found.
def get_order_data(order_number):
    if os.path.exists(DB_path):
        rwlock.acquire_read()   #Take a read lock before accessing the db file.
        with open(DB_path) as f:
            reader = csv.reader(f)
            next(reader)
            for row in reader:
                if int(order_number)==int(row[0]):
                    data_dict={}   #If the given order exists putting the details to a dictionary
                    data_dict['number']=row[0]
                    data_dict={}
                    data_dict['transaction_number']=row[0]
                    data_dict['name']=row[1]
                    data_dict['type']=row[2]
                    data_dict['quantity']=row[3]
                    print("data_dict in get_order_data: ",data_dict)
                    rwlock.release_read()
                    return data_dict
    rwlock.release_read() #Release the lock after reading is done
    return 'order not found'

#To fetch the last transaction number inorder to update the recent transaction, lock is acquired before accessing the file
def getlatestTransactioNum():
    if os.path.exists(DB_path):
        rwlock.acquire_read() #Take a read lock before accessing the db file.
        with open(DB_path) as f:
            reader = csv.reader(f)
            rows=0          #Logic to get the last transaction number
            for row in reader:
                rows+=1
            if rows==1:
                transaction_number=0
            else:
                transaction_number=int(row[0])
        rwlock.release_read()  #Release the lock after reading is done
        return transaction_number

#Function which will return the missing rows when sync db is called
def get_missing_transaction_data(req_last_trans_num):
    #Current replica will send its last  transaction number to the leader,
    #if the leader has made more transaction than the replica the missing rows are sent.
    missing_rows=[]
    if os.path.exists(DB_path):
        rwlock.acquire_read()
        with open(DB_path) as f:
            reader = csv.reader(f)
            rows=0
            for row in reader:
                if rows==0:
                    rows+=1
                elif rows>=1 and int(row[0])>int(req_last_trans_num):  #Appending the missing rows to list
                    missing_rows.append(row)
        rwlock.release_read()
        return missing_rows

#On startup sync DB of all the replicas
def sync_db():
    print("in sync db")
    unique_missing_rows=[]
    current_last_transaction_number = getlatestTransactioNum() #On startup get the last transaction number
    data={}
    data['trans_num']=current_last_transaction_number
    print(data)
    try:
        respone_leader = requests.get(FrontendServer + '/getleaderID') #Getting the eader ID from the front-end server
        leader_data = respone_leader.json()
        leader_PORT = leader_data['leader_PORT']
        print("leader ID is: ",leader_data['leader_ID'])
        print("leader PORT is: ",leader_PORT)
        #Sending a POST req to the leader to get the missing transaction data
        response = requests.post(OrderServer_prefix + str(leader_PORT) + '/sync_database', json=data)
        miss = response.json()['missing_rows']
        print("missing rows from leader: ",response.json())
        print(miss)
        print(len(miss))
        #Once the leader sends missing rows, updating its database
        if len(miss)!=0:
            for i in range(len(miss)):
                rwlock.acquire_write()
                with open(DB_path, 'a', newline= '') as file:  # Write the updated contents to the new file
                    # Write the updated contents to the new file
                    writer = csv.writer(file)
                    writer.writerow(miss[i])
                rwlock.release_write()

    except requests.exceptions.ConnectionError:
        print("inside exception")
        pass

#Method to inform front-end that replica with self_ID is UP.
def send_update_status_to_frontend():
    try:
        response = requests.get(FrontendServer + '/update_order_replica_status' + '/' + str(self_ID))
        print(response.status_code)
    except:
        pass

#Endpoint to the leader, if alive will respond OK
@app.route('/health')
def health_check():
    return jsonify({"status":"OK"}),200

#Endpoint for query order
@app.route('/get_order_data/<order_number>', methods=['GET'])
def order_query(order_number):
    orderdata=get_order_data(order_number) #If requested order is present forward the response to front-end
    print("orderdata :",orderdata)
    if orderdata=='order not found': #If requested order not present send order not found
        return jsonify(orderdata),404
    else:
        return jsonify(orderdata),200

#End point to sync db after a crash or on startup with the leader, will only return missing rows, helper function sync_db will actually update the database
@app.route('/sync_database', methods=['POST'])
def sync_database():
    req = request.get_json()
    req_last_trans_num=req['trans_num']
    current_replica_last_trans_num = getlatestTransactioNum() #Calling function to get current replica last transaction number
    print(current_replica_last_trans_num)
    if req_last_trans_num<current_replica_last_trans_num:
        missing_rows = get_missing_transaction_data(req_last_trans_num) #Calling method to get the missing data from the leader
    else:
        missing_rows = []
    return jsonify({'missing_rows':missing_rows}),200

#Endpoint which the front-end will use to broadcast the leader. Leader is maintained in variable leader_ID
@app.route('/leader_broadcast', methods=['POST'])
def leader_broadcast():
    data = request.get_json()
    leader_ID = data['leader_ID']
    print("Leader is: ",leader_ID)
    return jsonify({"status":"OK"}),200

#Called after a successful transaction in order to update the database
@app.route('/update_order_db', methods=['POST'])
def update_order_db():
    add_new_transaction = request.get_json()
    print(add_new_transaction)
    rwlock.acquire_write()
    with open(DB_path, 'a', newline= '') as file:  # Write the updated contents to the new file
        # Write the updated contents to the new file
        writer = csv.writer(file)
        writer.writerow(add_new_transaction['data'])
    rwlock.release_write()
    return jsonify({"status":"OK"}),200


@app.route('/trade_stocks', methods=['POST'])
def trade_stocks():
    postdata = request.get_json()
    print("post data:",postdata)
    print("type of post data:",type(postdata))
    # Handle the post data here add or subtract the trade volume
    if postdata['name']:
        #forward lookup request to catalog
        response = requests.get(CatalogServer + LOOKUP_ENDPOINT+'/'+postdata['name'])
        response=response.json()
        print("response from Catalog service : ",response)
        if response=='stock not found':  #If the catalog does not have the requested stock send stock not found with 404 code
            return jsonify(response),404

        else:
            stock_name=response['name'] #if the stock is available from lookup in catlog server check for the maximum trading limit condition
            print("stock name:",stock_name)
            present_quantity=response['quantity']
            max_trade_possible=response['max_trade']
            if postdata['name'] == stock_name :
                num_of_stocks=postdata['quantity']
                print("num_of_stocks:",num_of_stocks)

                if (postdata['type']=='buy' or postdata['type']=='sell') and (num_of_stocks>max_trade_possible or  num_of_stocks>present_quantity):
                    print("1")
                    response= "max trading volume exceeded" # if num_of_stocks > max_trade_possible throw error
                    return jsonify(response),422

                elif postdata['type']=='buy' and num_of_stocks<=max_trade_possible and num_of_stocks<=present_quantity:
                    print("2")
                    response['quantity']=response['quantity'] - postdata['quantity']


                elif postdata['type']=='sell' and num_of_stocks<=max_trade_possible and num_of_stocks<=present_quantity:
                    print("3")
                    response['quantity']=response['quantity'] + postdata['quantity'] #increase the quantity of the stock after selling

                #connect to catalog server for updating the modified data
                datatocat=response
                print("datatocat:",datatocat)
                catpostresponse=requests.post(CatalogServer + '/Update_csv/'+postdata['name'],json=datatocat) #response for buying trade from catalog
                catpostresponse=catpostresponse.json()
                print("resonse from catalog after updating :",catpostresponse)
                transaction_number=getlatestTransactioNum() #get latest transaction number
                catpostresponse['transaction_number']=transaction_number+1 #increase the transaction number after trade
                del catpostresponse['success']
                catpostresponse.update(postdata)
                print("catpostresponse :",catpostresponse)
                add_new_transaction=[transaction_number+1,postdata['name'],postdata['type'],postdata['quantity']]
                #Update current DB
                rwlock.acquire_write()
                print(self_ID,add_new_transaction)
                with open(DB_path, 'a', newline= '') as file:  # Write the updated contents to the new file
                    # Write the updated contents to the new file
                    writer = csv.writer(file)
                    writer.writerow(add_new_transaction)
                rwlock.release_write()
                data={}
                data['data']=add_new_transaction
                #Calling method to update other replicas DB
                for i in range(len(config_data)):
                    if self_ID!=int(config_data[i]['ID']):
                        try:
                            update_response = requests.post(OrderServer_prefix + str(config_data[i]['PORT']) + '/update_order_db', json=data)
                            print(update_response.status_code)
                        except requests.exceptions.ConnectionError:
                            pass
                return jsonify(catpostresponse),200


if __name__ == '__main__':
    sync_db() #On startup sync db with the leader
    send_update_status_to_frontend() #Send UP status to the front-end
    app.run(debug=True, port=PORT, host='localhost')
    
