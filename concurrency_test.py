import threading
import requests

URL = "http://127.0.0.1:5000/withdraw"

def make_request(thread_name, amount):
    print(f"{thread_name} sending request...")
    try:
        response = requests.post(URL, json={"amount": amount})
        print(f"{thread_name} finished. Status: {response.status_code} | Data: {response.json()}")
    except Exception as e:
        print(f"{thread_name} failed: {e}")

t1 = threading.Thread(target=make_request, args=("device 1", 60))
t2 = threading.Thread(target=make_request, args=("device 2", 60))

t1.start()
t2.start()

t1.join()
t2.join()
