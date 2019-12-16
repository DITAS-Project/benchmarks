#! /usr/bin/env python3

import pandas as pd
import numpy as np

import glob
from datetime import datetime
from dateutil.parser import parse

from elasticsearch import Elasticsearch


def load_vmstat(load_from_cache=False,store_cache_file=False,cache_file=None):
    monitoring_data = None
    
    if load_from_cache and cache_file is not None:
        monitoring_data = pd.read_csv(cache_file)
    else:
        
        for file in glob.glob("vmstats/*"):
            df = pd.read_csv(file, skiprows = 0,error_bad_lines=False)
            if monitoring_data is None:
                monitoring_data = df
            else:
                monitoring_data = pd.concat([monitoring_data, df], sort=True) 
        #clean up data 
        monitoring_data["timestamp"] = pd.to_datetime(monitoring_data["timestamp"]+ 3600, unit='s')
        monitoring_data = monitoring_data.rename(columns={"r":"processes","b":"waiting","swdp":"virtual mem","free":"free","buff":"buffers","si":"mem_on_disk","so":"mem_to_disk","bi":"blockIn","bo":"blockOut","in":"interrupts","cs":"switches","us":"cpu_user","sy":"cpu_system","id":"cpu_idle","wa":"blocked"}) 
        if store_cache_file:
            monitoring_data.to_csv(cache_file)
    
    return monitoring_data

def load_elastic(load_from_cache=False,store_cache_file=False,cache_file=None,es=None,experiment_dates=[]):
    monitoring_data = None
    
    if load_from_cache and cache_file is not None:
        monitoring_data = pd.read_csv(cache_file)
    else:
        monitoring_data = collect_monitoring_data(es,"*",experiment_dates)
        if store_cache_file:
            if monitoring_data is not None:
                monitoring_data.to_csv(cache_file)
    
    return monitoring_data

def load_rmstats():
    monitoring_data = None
    
    for file in glob.glob("rmstats/*.csv"):
            df = pd.read_csv(file, skiprows = 0,error_bad_lines=False)
            if monitoring_data is None:
                monitoring_data = df
            else:
                monitoring_data = pd.concat([monitoring_data, df], sort=True) 
    
    return monitoring_data

def load_experiment(load_from_cache=False,store_cache_file=False,data_cache_file=None):
    data = None
    
    if load_from_cache and data_cache_file is not None:
        data = pd.read_csv(data_cache_file)
    else:
        data = __load()
        if store_cache_file:
            data.to_csv(data_cache_file)
    
   
    
    return data
    
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

def __collect(es,index,query):
    data = []
    page = es.search(
    index = index,
    scroll = '2m',
    size = 1000,
    body = query)
    if '_scroll_id' in page:
        
        sid = page['_scroll_id']
        scroll_size = page['hits']['total']

        data = data + page['hits']['hits']
        # Start scrolling
        while (scroll_size > 0):
            page = es.scroll(scroll_id = sid, scroll = '2m')
            # Update the scroll ID
            sid = page['_scroll_id']
            # Get the number of results that we returned in the last scroll
            scroll_size = len(page['hits']['hits'])
            data = data + page['hits']['hits']

        return data
    else:
        return data

def collect_monitoring_data(es,vdcname,dates=[]):
    all = None
    for runDate in dates:
        esAll = []
        index = "{}-{}".format(vdcname,runDate.date().strftime("%Y-%m-%d"))
        print("loading data from index",index)
        
        esAll =  __collect(es,index,{"query": {"match_all": {}}})
        
        if len(esAll) <= 0:
            continue
        

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

    