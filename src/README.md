
## catalog service 
Service to lookup the stocks_DB.csv for stock name and return the response. Also handle the lookup and update requests from the Order service to modify the stock_DB.csv
cd to src folder
Run the catalog service   :python3 back-end/catalog_service.py
 
## Frontend Service

The clients can communicate with the front-end service using the below 3 HTTP-based REST APIs. It will forward the requests based on lookup or trade to catalog or order server.
Front end server does the leader election, health check to leader ad broadcast to all the replicas
1.GET /stocks/<stock_name>
2.POST /orders
3.GET /orders/<order_number>

cd to src folder
Run the server  :python3 front-end/server.py

## order service

The order service supports replication hence have to provide replica ID, PORT number and specific db path.

cd to src folder
Run the orders service :
To start replica with ID 1 -  python3 Backend/orders_service.py 1 5002 "Backend/orders_DB1.csv"
To start replica with ID 2 -  python3 Backend/orders_service.py 2 5003 "Backend/orders_DB2.csv"
To start replica with ID 3 -  python3 Backend/orders_service.py 3 5004 "Backend/orders_DB3.csv"

## Client
Once all servers are up and running ,execute the client :

cd to src folder
1. Run the client application on your machine : python3 client.py

Work Division:

Priyanka V devoor :
1. Query order
2. Replication
3. Fault tolerance
4. Design document and output files
5. testcases
6. in-line comments

Femimol Joseph:
1. Caching
2. Switching to Flask Framework
3. AWS deployment
4. Evaluation doc
5. testcases
6. in-line comments





