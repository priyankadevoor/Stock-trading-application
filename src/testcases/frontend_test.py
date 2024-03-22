import json
import unittest,requests

class TestFrontendService(unittest.TestCase):

    #Create a mock POST request to check invalidate memcache - if the stock value has c
    def test_do_POST_memcache(self):
        END_POINT = '/invalidate_MemCache'
        request_body='GameStart'
        r = requests.post('http://localhost:5000' + END_POINT, json=request_body)
        res_data=r.json()
        print(res_data)
        print("\n")
        self.assertIsInstance(res_data, dict)
        self.assertEqual('Not Applicable',res_data['Invalidation Request'])

    #create a mock get request for getting the leader ID
    def test_do_GET_Leader_ID(self):
        QUERY_Leader_ENDPOINT='/getleaderID'
        r = requests.get('http://localhost:5000' + QUERY_Leader_ENDPOINT)
        res_data=r.json()
        print("response data :",res_data)
        # Check that the response code is 200 and that the leader_ID is 3 when all order replicas of IDs 1,2 and 3 are UP.
        self.assertEqual(r.status_code, 200)
        self.assertIsInstance(res_data, dict)
        self.assertEqual(3,res_data['leader_ID'])
        self.assertEqual(5004,res_data['leader_PORT'])

    #Create mock GET request to do a health check to the leader after election
    def test_do_GET_health_check_to_leader(self):
        ENDPOINT = '/health_check'
        r = requests.get('http://localhost:5000' + ENDPOINT)
        res_data = r.json()
        print("health check response from leader: ",res_data)
        # Check that the response code is 200 and leader return OK if it is UP and sends its ID and PORT.
        self.assertEqual(r.status_code, 200)
        self.assertIsInstance(res_data, dict)
        self.assertEqual('OK',res_data['leader_response'])
        self.assertEqual(3,res_data['leader_ID'])
        self.assertEqual(5004,res_data['leader_PORT'])


    #create a mock Get request for a valid order number to frontend
    def test_Application_GetOrderNUM(self):
        order_number=10
        QUERYORDER_ENDPOINT='/queryOrder/'+str(order_number)
        r = requests.get('http://localhost:5000' + QUERYORDER_ENDPOINT)
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

    #create a mock Get request for an Ivalid order number to frontend
    def test_Application_GetInvalidOrderNUM(self):
        order_number=10000
        QUERYORDER_ENDPOINT='/queryOrder/'+str(order_number)
        r = requests.get('http://localhost:5000' + QUERYORDER_ENDPOINT)
        res_data = r.json()
        print(res_data)
        print("\n")
        # Check that the response code is 404 and that the error message is returned in the expected format
        self.assertEqual(r.status_code, 404)
        self.assertIsInstance(res_data, dict)
        self.assertIn("error", res_data)
        self.assertIn("code",res_data['error'])
        self.assertIn("message",res_data['error'])


    #create a mock POST request to sell a stock which exceeds the max trade volume
    def test_sell_highstocks(self):
        type_of_request='trade'
        stock_name='FishCo'
        quantity=500
        trade_type='sell'
        request_body={
            "name": stock_name,
            "quantity": quantity,
            "type": trade_type
        }
        TRADE_ENDPOINT='/orders'
        r = requests.post('http://localhost:5000' + TRADE_ENDPOINT, json=request_body)
        print("Type of request sending: ",type_of_request,trade_type)
        res_data=r.json()
        print(res_data)
        print("\n")
        self.assertIsInstance(res_data, dict)
        self.assertIn("error", res_data)

    #create a mock POST request to buy a stock which exceeds the max trade volume
    def test_buy_highstocks(self):
        type_of_request='trade'
        stock_name='FishCo'
        quantity=500
        trade_type='buy'
        request_body={
            "name": stock_name,
            "quantity": quantity,
            "type": trade_type
        }
        TRADE_ENDPOINT='/orders'
        r = requests.post('http://localhost:5000' + TRADE_ENDPOINT, json=request_body)
        print("Type of request sending: ",type_of_request,trade_type)
        res_data=r.json()
        print(res_data)
        print("\n")
        self.assertIsInstance(res_data, dict)
        self.assertIn("error", res_data)

if __name__ == '__main__':
    unittest.main()