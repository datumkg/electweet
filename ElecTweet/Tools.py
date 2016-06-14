import datetime as dt
from dateutil.parser import parse as parsedate

def CutSeconds(twts,seconds):
    start = parsedate(twts[0]['created_at'])
    startI = 0
    endI = len(twts) - 1
    for i, tw in enumerate(twts):
        if i == 0: continue
        end = parsedate(tw['created_at'])
        delta = end - start
        if delta.total_seconds() >= seconds:
            endI = i
            break
    return (startI, endI)

def GetAll(twts):
    return (0,len(twts))

def GetMonth(twts):
    monthSeconds = 30*24*60*60 # 30 days, 24 hours, 60 mins, 60 secs
    return CutSeconds(twts,monthSeconds)

def GetWeek(twts):
    weekSeconds = 7*24*60*60 # 7 days, 24 hours, 60 mins, 60 secs
    return CutSeconds(twts,weekSeconds)

def GetDay(twts):
    daySeconds = 24*60*60 # 24 hours, 60 minutes, 60 seconds
    return CutSeconds(twts,daySeconds)

def GetCut(twts,period):
    calls = {'day':GetDay,
             'week':GetWeek,
             'month':GetMonth,
             'all':GetAll}
    return calls[period](twts)
