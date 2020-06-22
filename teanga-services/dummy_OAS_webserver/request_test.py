from requests import Request, Session
import requests
import json

s = Session()

url = "http://localhost:8002/vocabulary/en/top/10"
req = Request('GET',url)
req.data = json.dumps({"1":"2"})

prepped = s.prepare_request(req)
words = s.send(prepped).text
words = eval(words)
print(words)
# do something with prepped.body
url = "http://localhost:8002/wordembeddings/3"
data= json.dumps(words)
req = Request('POST',  url, data=data)
prepped = s.prepare_request(req)
#prepped.body = "[1,2,3,4,5]" 
print(s.send(prepped).text)
print(requests.post)
