import unittest
import requests,json

# import the MyHandler class from the main script

class TestCatalogService(unittest.TestCase):
    # TC1 - Create a mock GET request to retrieve stock data for a known stock
    def test_do_GET_POS(self):
        LOOKUP_ENDPOINT="/Lookup_csv/GameStart"
        r =requests.get('http://localhost:5001' + LOOKUP_ENDPOINT)
        print("Request sending is: GET /Lookup_csv/GameStart")
        print("r.status",r.status_code)
        res_data=r.json()
        print("result data",res_data)
        # Check that the response code is 200 and that the stock data is returned in the expected format
        self.assertEqual(r.status_code, 200)
        self.assertIsInstance(res_data, dict)
        self.assertIn("name", res_data)
        self.assertIn("price", res_data)
        self.assertIn("quantity", res_data)
        del res_data['max_trade']
        print("\n")

    # TC2 - Create a mock GET request to retrieve stock data for an unknown stock
    def test_do_GET_NEG(self):
        LOOKUP_ENDPOINT="/Lookup_csv/KFC"
        r =requests.get('http://localhost:5001' + LOOKUP_ENDPOINT)
        print("Request sending is: GET /Lookup_csv/KFC")
        res_data =r.json()
        self.assertEqual(res_data,'stock not found')
        print("result data",res_data)
        print("res.status",r.status_code)


        # Check that the response code is 404 when the stock is not found
        self.assertEqual(r.status_code, 404,"Got {} but expected 200".format(
            r.status_code))


if __name__ == '__main__':
    unittest.main()
