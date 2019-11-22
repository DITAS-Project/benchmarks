#! /usr/bin/env python3

import pandas as pd
import numpy as np

def load(store_cache_file=False,cache_file=None):
    if not store_cache_file and cache_file:
        return pd.load(cache_file)
    else:
        #TODO load your data into a DataFrame
        result = __load()
        
        if store_cache_file and cache_file:
            result.to_csv(cache_file)
        
        return result
    
import glob
from datetime import datetime
from dateutil.parser import parse
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
        df['startTime']=timestamp
        df['runDate']=date

        if (all is None):
            all = df
        else:
            all = pd.concat([all, df], sort=True)
        
        return all

    