import socket
import requests,os,csv
from flask import Flask, request,jsonify
from Read_Write_Lock import ReadWriteLock
app=Flask(__name__)

rwlock=ReadWriteLock()  #read write lock for synchronization

#server details
CatalogServer='http://localhost:5001'
OrderServer='http://localhost:5002'
server=socket.gethostname()
FrontendServer = f'http://{server}:5000'

def update_csv(stock_name,quantity):                #function to update csv
    if os.path.exists("Backend/stocks_DB.csv"):
        rwlock.acquire_write()
        with open("Backend/stocks_DB.csv") as f:
            reader = csv.reader(f)  #reading the data from csv
            rows=[]
            for row in reader :
                if stock_name in row:   
                    print(row)
                    row[2]=quantity     #updating the row with the updated quantity 
                    print("after updating row ",row)
                rows.append(row)
        with open("Backend/stocks_DB.csv", 'w', newline='') as file:    # Write the updated contents to the new file
            writer = csv.writer(file)
            writer.writerows(rows)
        rwlock.release_write() #releasing the write lock after updating

def update_InmemCache(stock_name):          #fucntion to update inmemcache request to frontend
    print("Inside Updat InMem Cache")
    response=requests.post(FrontendServer+'/invalidate_MemCache',json=stock_name)    #response from frontend after invalidating
    print("response_data from frontend after Invalidating",response.json())


#end point to lookup csv for a stockname
@app.route('/Lookup_csv/<stock_name>', methods=['GET'])
def lookup_csv(stock_name):
    print("inside lookup csv")
    if os.path.exists("Backend/stocks_DB.csv"):       #open the stocks DB for reading the stockdata
        rwlock.acquire_read()                           #acquiring read lock before reading the stocks_DB
        print("lock acquired")
        with open("Backend/stocks_DB.csv") as f:
            print("inside stocks_DB ")
            reader = csv.reader(f)
            for row in reader :            #read line by line through csv and check
                if stock_name in row:      #if stockname is present in lookup
                    print(row)
                    keys = ['name', 'price', 'quantity', 'max_trade']
                    result = dict(zip(keys, row))   #reading out the data from csv into a dictionary
                    result['price'] = float(result['price'])
                    result['quantity'] = int(result['quantity'])
                    result['max_trade']=int(result['max_trade'])
                    print(result)
                    rwlock.release_read()       #releasing read lock after reading the stocks_DB
                    return result
            rwlock.release_read()
            response='stock not found' #if no stock_name in row, return stock not found
            return jsonify(response),404


#end point for updating csv after trade is successful
@app.route('/Update_csv/<stock_name>',methods=['POST'])
def updatelookup(stock_name):
    post_data=request.json
    if post_data is None or post_data == {}:        #if data passed is empty
        response={"Error": "Please provide correct type to buy or sell"}
        return jsonify(response),400

    else:
        stock_name=post_data['name']
        quantity=post_data['quantity']
        update_csv(stock_name,quantity)             #update the lookup with latest data
        print("sending invalidate request to frontend for",stock_name)
        update_InmemCache(stock_name)               # send invalidate requests to frontend after each trade
        data={'success':'data updated successfully'}
        return jsonify(data),200  #sending data back to order service


if __name__ == '__main__':
    app.run(debug=True, port=5001, host='localhost')