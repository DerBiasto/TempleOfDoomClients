from concurrent.interpreters import create
import requests
import pprint
IP = '10.255.22.214'

s = requests.Session()
#r = s.post(f'http://{IP}/lobby/new/8')
#pprint.pprint(r.json())
#print(r.status_code)
#print(r.reason)
#print(r.headers)
#print(r.text)


def create_lobby(n=5):
    r = s.post(f'http://{IP}/lobby/new/{n}')
    #pprint.pprint(r.json())
    print(r.status_code)
    print(r.reason)
    print(r.headers)
    print(r.text)
create_lobby(4)