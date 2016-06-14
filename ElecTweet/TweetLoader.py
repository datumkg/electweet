import glob
import json

def LoadTweets(directory):
    directory = directory +"/*json"
    files = glob.glob(directory)[:100]
    twts = [a for fl in files for a in json.load(open(fl))]
    twts.sort(key=lambda x: x['id'] if 'id' in x else int(x['id_str']) if 'id_str' in x else 0)
    twts = [a for a in twts if 'id' in a or 'str_id' in a]
    twts = [a for a in twts 
            if (('id' in a and a['id'] >= 656971539691257900) or 
                ('id_str' in a and int(a['id_str']) >= 656971539691257900))]
    res = []
    prev_id = 0
    for tw in twts:
        if 'id' not in tw: tw['id'] = int(tw['id_str'])
        if 'id_str' not in tw: tw['id_str'] = str(tw['id'])
        if tw['id'] != prev_id: res.append(tw)
        prev_id = tw['id']

    return res

def LoadUsers(directory):
    directory = directory + "/*txt"
    usrfiles = glob.glob(directory)
    users = [(a.strip("@"),fl) # Removing the @
             for fl in usrfiles
             for nms in open(fl)
             for a in nms.strip().split(",")]
    usrset = set([a[0] for a in users])
    return usrset, users
