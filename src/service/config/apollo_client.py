# -*- coding: UTF-8 -*-
"""
@Description : Apollo配置的连接
@Author      : Jason_Sam
@Time        : 2021/9/15 13:42

"""
import threading

from py_openapi_apollo_client.apollo_client import PrivateApolloClient


from src.cache.cache import ApolloCache
from src.config.dev.apollo_config import ApolloConfig
from src.constants import cache_constants


class ApolloClient:
    _instance_lock = threading.Lock()
    __client = PrivateApolloClient(app_id=ApolloConfig.app_id,
                                   env=ApolloConfig.env,
                                   portal_address=ApolloConfig.portal_address,
                                   authorization=ApolloConfig.authorization)
    __cache = ApolloCache().get_cache()

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not hasattr(ApolloClient, "_instance"):
            with ApolloClient._instance_lock:
                if not hasattr(ApolloClient, "_instance"):
                    ApolloClient._instance = object.__new__(cls)
        return ApolloClient._instance

    """
    :@deprecated: 获取连接
    :@param: 
    :@return: 
    """
    def get_client(self):
        return self.__client

    """
    :@deprecated: 获取value
    :@param: 
    :@return: 
    """
    def get_namespace_items_value_by_key(self, key, namespaceName='application'):
        cache_key = cache_constants.APOLLO_CLIENT_CACHE + key + namespaceName

        value = self.__cache.get(cache_key)

        if value is not None:
            return value

        value = self.__client.get_namespace_items_key(key, namespaceName)['value']

        self.__cache.set(cache_key, value)

        return value


"""
:@deprecated: 获取namespace为Strategy.core的value
:@param: 
:@return: 
"""
def get_core_namespace(key):
    return ApolloClient().get_namespace_items_value_by_key(key, ApolloConfig.core)


"""
:@deprecated: 获取namespace为Strategy.business的value
:@param: 
:@return: 
"""
def get_business_namespace(key):
    return ApolloClient().get_namespace_items_value_by_key(key, ApolloConfig.business)


"""
:@deprecated: 获取namespace为Strategy.datasource的value
:@param: 
:@return: 
"""
def get_datasource_namespace(key):
    return ApolloClient().get_namespace_items_value_by_key(key, ApolloConfig.datasource)

