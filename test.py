import json

import requests


def main():
    headers = {'Content-Type': 'application/json'}
    url = 'http://{}/task/start'.format('43.33.26.148:8888')
    data = {'paths': ['/43.33.26.79/e/20180615']}
    resp = requests.post(url, data=json.dumps(data), headers=headers)
    print(resp.text)


if __name__ == '__main__':
    main()
