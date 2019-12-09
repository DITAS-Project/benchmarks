#! /usr/bin/env python3

import pandas as pd
import numpy as np


def load_monitoring(load_from_cache=False,store_cache_file=False,monitoring_cache_file=None,es=None,experiment_dates=[]):
    monitoring_data = None
    
    if load_from_cache and monitoring_cache_file is not None:
        monitoring_data = pd.read_csv(monitoring_cache_file)
    else:
        monitoring_data = collect_monitoring_data(es,"*",experiment_dates)
        if store_cache_file:
            monitoring_data.to_csv(monitoring_cache_file)
    
    return monitoring_data

def load(load_from_cache=False,store_cache_file=False,data_cache_file=None):
    data = None
    
    if load_from_cache and data_cache_file is not None:
        data = pd.read_csv(data_cache_file)
    else:
        data = __load()
        if store_cache_file:
            data.to_csv(data_cache_file)
    
   
    
    return data
    
import glob
from datetime import datetime
from dateutil.parser import parse

from elasticsearch import Elasticsearch

def __load():
    all = None
    for file in glob.glob("data/*"):
        names = file[5:-4].split("-")
        experiment=names[0]
        method=names[1]
        datetime.strptime
        timestamp=file[5+len(experiment)+1+len(method)+1:-4]
        date=timestamp[:timestamp.index("T")]
        date=datetime.strptime(date, '%Y-%m-%d')
        timestamp=parse(timestamp)
        df = pd.read_csv(file, skiprows = 0,error_bad_lines=False)
        df['experiment']=experiment
        df['method']=method
        df['startTime']=pd.Timestamp(year=timestamp.year,month=timestamp.month, day=timestamp.day, hour=timestamp.hour, minute=timestamp.minute)
        df['runDate']=pd.Timestamp(year=date.year,month=date.month, day=date.day)

        if (all is None):
            all = df
        else:
            all = pd.concat([all, df], sort=True)
        
    return all

def collect_monitoring_data(es,vdcname,dates=[]):
    all = None
    for runDate in dates:
        esAll = []
        index = "{}-{}".format(vdcname,runDate.date().strftime("%Y-%m-%d"))
        print("loading data from index",index)
        window_size = 2500
        x = es.search(index=index, 
                      body={"query": {"match_all": {}}},
                      size=window_size)

        esAll = esAll + x['hits']['hits']
        total = x['hits']['total']
        offset = window_size
        while len(esAll) < total:
            x = es.search(index=index, body={"query": {"match_all": {}}},size=window_size,from_=offset)
            offset += len(x['hits']['hits'])
            esAll = esAll + x['hits']['hits']

        esAll = list(map(lambda x:x["_source"],esAll))

        responses = filter(lambda x:'response.code' in x,esAll)
        requests = filter(lambda x:'response.code' not in x,esAll)

        responses = pd.DataFrame(responses)
        responses = responses[['request.id','response.code','response.length']]
        requests = pd.DataFrame(requests)
        requests = requests[['request.id','@timestamp','request.operationID','request.requestTime','request.client','request.method','request.path']]
        df = pd.merge(requests, responses, on='request.id')
        df['runDate'] = runDate

        if (all is None):
            all = df
        else:
            all = pd.concat([all, df], sort=True)
            
    return all

    