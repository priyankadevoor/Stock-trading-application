import requests,random
import time,json
import numpy as np

# Define the base URL of  Flask app
#Frontend_URL = 'http://54.226.103.56:5000'  # added public IP address 54.226.103.56 of ec instance
Frontend_URL = 'http://localhost:5000'
#initiate variable N
N=1



p=0.8                      # assign p values from 0.2 to 0.8 ,increments by 0.2
noOfTrade=0                     #count the no of trade requests

list_lookup=[]  #define lists to store the latencies of each request types
list_trade=[]
list_query=[]

# Define the trade and lookup endpoints
TRADE_ENDPOINT = '/orders'
LOOKUP_ENDPOINT = '/stocks'
QUERYORDER_ENDPOINT = '/orders'

Order_Cache=[]          #cache to store the transaction details after each trade requests

def queryOrder_Status():
    noOfMismatch=0                  #to track the no of mismatches after ordercache comparison
    for dic in Order_Cache:         # iterating through order cache
        order_num=dic['transaction_number']
        print("order_num for verifying : ",order_num)
        start_Qorder=time.perf_counter()
        response = requests.get(Frontend_URL + QUERYORDER_ENDPOINT +'/'+str(order_num))  #get Ordernum requests to frontend
        response=response.json()
        end_Qorder=time.perf_counter()  #calculating the time for each queryorder request
        timeq=end_Qorder-start_Qorder
        list_query.append(timeq)        #appending response time to the list
        print("Time taken for query order request: ",timeq)
        print(f'Order Query- {N}: {response}')
        dict1=json.dumps(response, sort_keys=True)  #sorting the response dictionary from order service for comaparison
        dict2=json.dumps(dic, sort_keys=True)      #sorting the ordercache dictionary for comaparison
        if 'error' in response:
            noOfMismatch+=1
            print("mismatch in transactions found")

        elif dict1 == dict2:            #if both responses of transactions are matching 
            print("Transaction is matching and success")
        
# Make a series of lookup and trade requests
while N<=10:
    type_of_request=random.choice(['lookup'])              # lookup request
    stock_name=random.choice(['GameStart','FishCo','MenhirCo','BoarCo','KFC','Adidas']) #'FishCo','MenhirCo','StarBucks','BoarCo','Dominos'
    print("Type of request sending: ",type_of_request)              #randomly choosing type of request to send

    if type_of_request == 'lookup':
        start_lookup=time.perf_counter()
        response = requests.get(Frontend_URL + LOOKUP_ENDPOINT+'/'+stock_name)      #get lookup requests to frontend
        end_lookup=time.perf_counter()
        timel=end_lookup-start_lookup
        print("Time taken for lookup request: ",timel)
        list_lookup.append(timel)
        response=response.json()
        print(f'Lookup- {N}: {response}')
        prob=random.uniform(0,1)                 #assigning a random proabability between 0 and 1
        print("prob assigned is:",prob)
        if 'error' not in response and response['quantity']>0:
            if prob < p :                                           #send trade request only if prob < p
                quantity=random.choice([5,13,4,3])                          #randomly choosing quantity to send
                trade_type=random.choice(['buy','sell'])                    #randomly choosing buy or sell
                request_body={
                    "name": stock_name,
                    "quantity": quantity,
                    "type": trade_type
                }
                start_trade=time.perf_counter()
                response = requests.post(Frontend_URL + TRADE_ENDPOINT, json=request_body)  #post requests to frontend
                response = response.json()
                if 'error' not in response:         # store the response only if trade is successful
                    end_trade=time.perf_counter()
                    noOfTrade+=1
                    timet=end_trade-start_trade
                    print("Time taken for trade request: ",timet)
                    print("No of trade requests:",noOfTrade)
                    list_trade.append(timet)
                    Order_Cache.append(response)    #append to the Order_Cache list
                print(f'Trade- {N}: {response}')

    N=N+1       #increment the N

print("################# queryOrder_Status ####################")
queryOrder_Status()   #to check whether the trade request was succesful by comparison


print("No of lookup requests:",N-1)
print("No of trade requests:",noOfTrade)
print(f'Lookup List time  for {p} is : {np.average(list_lookup)}') # taking the mean time to get the latency per request
print(f'Trade List time :for {p} is : {np.average(list_trade)}')
print(f'query List time :for {p} is : {np.average(list_query)}')



