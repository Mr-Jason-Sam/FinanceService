# -*- coding: UTF-8 -*-
"""
@Description : 通用缓存
@Author      : Jason_Sam
@Time        : 2021/6/29 13:54

"""
import threading

from cacheout import Cache


class BusinessCache:
    _instance_lock = threading.Lock()
    __business_cache = Cache()

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not hasattr(BusinessCache, "_instance"):
            with BusinessCache._instance_lock:
                if not hasattr(BusinessCache, "_instance"):
                    BusinessCache._instance = object.__new__(cls)
        return BusinessCache._instance

    def get_cache(self):
        return self.__business_cache


class DatabaseCache:
    _instance_lock = threading.Lock()
    __business_cache = Cache()

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not hasattr(DatabaseCache, "_instance"):
            with DatabaseCache._instance_lock:
                if not hasattr(DatabaseCache, "_instance"):
                    DatabaseCache._instance = object.__new__(cls)
        return DatabaseCache._instance

    def get_cache(self):
        return self.__business_cache


class ApolloCache:
    _instance_lock = threading.Lock()
    __cache = Cache()

    def __init__(self):
        pass

    def __new__(cls, *args, **kwargs):
        if not hasattr(ApolloCache, "_instance"):
            with ApolloCache._instance_lock:
                if not hasattr(ApolloCache, "_instance"):
                    ApolloCache._instance = object.__new__(cls)
        return ApolloCache._instance

    def get_cache(self):
        return self.__cache
