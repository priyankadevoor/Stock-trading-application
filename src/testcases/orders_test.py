import unittest
from http.client import HTTPConnection
import requests


class TestMyHandler(unittest.TestCase):
    #Create a mock POST request to synchronize the database of an order service which starts after a crash
    #Testcase will print the missing rows 
    def test_do_POST_sync_DB_after_crash(self):
        data={}
        data['trans_num']=160
        leader_PORT=5004
        response = requests.post('http://localhost:' + str(leader_PORT) + '/sync_database', json=data)
        miss = response.json()['missing_rows']
        print("missing rows from leader: ",response.json())
        print(miss)
        print(len(miss))

    #create a mock Get request for a valid order number
    def test_do_GET_OrderNUM(self):
        order_number=10
        QUERYORDER_ENDPOINT='/get_order_data/'+str(order_number)
        r = requests.get('http://localhost:5002' + QUERYORDER_ENDPOINT)
        res_data = r.json()
        print(res_data)
        print("\n")
        # Check that the response code is 200 and that the stock data is returned in the expected format
        self.assertEqual(r.status_code, 200)
        self.assertIsInstance(res_data, dict)
        self.assertIn("name", res_data)
        self.assertIn("transaction_number",res_data)
        self.assertIn("quantity",res_data)
        self.assertIn("type",res_data)

    #create a mock Get request for an Invalid order number
    def test_do_GET_InvalidOrderNUM(self):
        order_number=10000000
        QUERYORDER_ENDPOINT='/get_order_data/'+str(order_number)
        r = requests.get('http://localhost:5002' + QUERYORDER_ENDPOINT)
        res_data = r.json()
        print(res_data)
        print("\n")
        # Check that the response code is 200 and that the stock data is returned in the expected format
        self.assertEqual(r.status_code, 404)
        self.assertEqual("order not found",res_data)

    # TC1 - Create a mock POST request to buy a valid stock
    def test_do_POST_buy_POS(self):
        request_body={
        "name": 'GameStart',
        "quantity": 5,
        "type": "buy"
    }
        TRADE_ENDPOINT='/trade_stocks'
        r = requests.post('http://localhost:5002' + TRADE_ENDPOINT, json=request_body)
        res_data = r.json()
        print(res_data)
        print("\n")
        # Check that the response code is 200 and that the stock data is returned in the expected format
        self.assertEqual(r.status_code, 200)
        self.assertIsInstance(res_data, dict)
        self.assertIn("transaction_number", res_data)

      # TC2 - Create a mock POST request to sell a valid stock
    def test_do_POST_sell_POS(self):
        request_body={
        "name": 'FishCo',
        "quantity": 5,
        "type": "sell"
    }

        TRADE_ENDPOINT='/trade_stocks'
        r = requests.post('http://localhost:5002' + TRADE_ENDPOINT, json=request_body)
        res_data = r.json()
        print(res_data)
        print("\n")

        # Check that the response code is 200 and that the stock data is returned in the expected format
        self.assertEqual(r.status_code, 200)
        self.assertIsInstance(res_data, dict)
        self.assertIn("transaction_number", res_data)

        
      # TC3 - Create a mock POST request to buy a stock that is not present
    def test_do_POST_buy_NEG(self):
        request_body={
        "name": 'KFC',
        "quantity": 5,
        "type": "buy"
    }
        TRADE_ENDPOINT='/trade_stocks'
        r = requests.post('http://localhost:5002' + TRADE_ENDPOINT, json=request_body)
        res_data = r.json()
        print(res_data)
        print("\n")
    # Check that the response code is 404 and that the stock data is returned in the expected format
        self.assertEqual(r.status_code, 404)
        self.assertEqual(res_data,'stock not found')

    
      # TC4 - Create a mock POST request to sell a stock that is not present
    def test_do_POST_sell_NEG(self):
        request_body={
        "name": 'StartBucks',
        "quantity": 5,
        "type": "sell"
    }
        TRADE_ENDPOINT='/trade_stocks'
        r = requests.post('http://localhost:5002' + TRADE_ENDPOINT, json=request_body)
        res_data = r.json()
        print(res_data)
        print("\n")
        # Check that the response code is 404 and that the stock data is returned in the expected format
        self.assertEqual(r.status_code, 404)
        self.assertEqual(res_data,'stock not found')

    
      # TC5 - Create a mock POST request to buy a stock that exceeds the trading volume 
    def test_do_POST_buy_NEG_max(self):
        request_body={
        "name": 'GameStart',
        "quantity": 5000,
        "type": "buy"
    }
        TRADE_ENDPOINT='/trade_stocks'
        r = requests.post('http://localhost:5002' + TRADE_ENDPOINT, json=request_body)
        res_data = r.json()
        print(res_data)
        print("\n")

        # Check that the response code is 422 and that the stock data is returned in the expected format
        self.assertEqual(r.status_code, 422)
        self.assertEqual(res_data,'max trading volume exceeded')

    
      # TC6 - Create a mock POST request to sell a stock that exceeds the trading volume
    def test_do_POST_sell_NEG_max(self):
        request_body={
        "name": 'MenhirCo',
        "quantity": 5000,
        "type": "sell"
    }
        TRADE_ENDPOINT='/trade_stocks'
        r = requests.post('http://localhost:5002' + TRADE_ENDPOINT, json=request_body)
        res_data = r.json()
        print(res_data)
        print("\n")
        # Check that the response code is 422 and that the stock data is returned in the expected format
        self.assertEqual(r.status_code, 422)
        self.assertEqual(res_data,'max trading volume exceeded')

if __name__ == '__main__':
    unittest.main()
