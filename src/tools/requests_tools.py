"""
@Description : 网络工具
@Author      : Jason_Sam
@Time        : 2021/4/13 13:48

"""
import json

import requests

"""
:@deprecated: 获取网络数据
:@param: 
:@return: 
"""
def fetch_net_data(url: str):
    # Get方式获取网页数据
    return requests.get(url)


"""
:@deprecated: 获取网络数据
:@param: 
:@return: 
"""
def fetch_net_data_with_body(url: str, body, headers=None):
    if headers is None:
        headers = \
            {
                "Content-Type": "application/json;charset=UTF-8"
            }
    data = requests.post(url=url, data=body, headers=headers)
    if data.status_code != 200:
        raise Exception(data.text)

    return data


"""
:@deprecated: 获取网络数据
:@param: 
:@return: 
"""
def fetch_net_data_with_body_to_js(url: str, body, headers=None):
    data = fetch_net_data_with_body(url=url, body=body, headers=headers)
    text = data.text
    js = text[text.index('{'):(text.rindex('}') + 1)]
    js = json.loads(js)
    return js
