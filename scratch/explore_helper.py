from collections import Counter,defaultdict
from dateutil.parser import parse as parsedate

def get_followers(twts,usrlst):
    res = {}
    usrset = set(usrlst)
    for tw in reversed(twts):
        if tw['user']['screen_name'] in usrset:
            user = tw['user']['screen_name']
            res[user] = tw['user']['followers_count']
            usrset.remove(user)
        if len(usrset) == 0: break
    return res

def get_followees(twts, usrlst):
    res = {}
    usrset = set(usrlst)
    for tw in reversed(twts):
        if tw['user']['screen_name'] in usrset:
            user = tw['user']['screen_name']
            res[user] = tw['user']['friends_count']
            usrset.remove(user)
        if len(usrset) == 0: break
    return res

def get_time_between_mentions(twts,usrlst):
    tweetTimes = {usr:[] for usr in usrlst}
    lastTwts = {usr: None for usr in usrlst}
    usrset = set(usrlst)
    for tw in twts:
        ments = set(usr['screen_name'] for usr in tw['entities']['user_mentions'])
        mentIusrs = ments.intersection(usrset)
        for cmaker in mentIusrs:
            lastTwt = lastTwts[cmaker]
            lastTwts[cmaker] = tw
            if lastTwt is None: continue
            oldDate = parsedate(lastTwt['created_at'])
            nwDate = parsedate(tw['created_at'])
            diff = nwDate - oldDate
            tweetTimes[cmaker].append(diff.total_seconds())
        pass
    res = {usr:0 if len(tweetTimes[usr]) == 0 else sum(tweetTimes[usr])/len(tweetTimes[usr]) 
           for usr in usrlst}
    return res

def get_time_between_tweets(twts,usrlst,condition=lambda x: True):
    tweetTimes = {usr:[] for usr in usrlst}
    lastTwts = {usr: None for usr in usrlst}
    usrset = set(usrlst)
    for tw in twts:
        if tw['user']['screen_name'] not in usrset: continue
        if not condition(tw): continue
        user = tw['user']['screen_name']
        lastTwt = lastTwts[user]
        lastTwts[user] = tw
        if lastTwt is None: continue
        oldDate = parsedate(lastTwt['created_at'])
        nwDate = parsedate(tw['created_at'])
        diff = nwDate - oldDate
        tweetTimes[user].append(diff.total_seconds())

    res = {usr:0 if len(tweetTimes[usr]) == 0 else sum(tweetTimes[usr])/len(tweetTimes[usr]) 
           for usr in usrlst}
    return res

def get_mentions(twts,usrlst = []):
    usrset = set(usrlst)
    return Counter([len(tw['entities']['user_mentions']) 
            for tw in twts 
            if 'entities' in tw and 'user_mentions' in tw['entities'] and 
            (len(usrset) == 0 or tw['user']['screen_name'] in usrset)])

def authored_count(twts,usrlst):
    usrset = set(usrlst)
    return _count_tweets(twts,lambda tw: tw['user']['screen_name'] in usrset)

def reply_count(twts,usrlst):
    usrset = set(usrlst)
    return _count_tweets(twts,lambda tw: (tw['user']['screen_name'] in usrset and 
                                          ('in_reply_to_status_id' not in tw or 
                                           tw['in_reply_to_status_id'] is not None)))

def _count_tweets(twts,condition):
    res = defaultdict(lambda : 0)
    for tw in twts:
        if condition(tw): res[tw['user']['screen_name']] += 1
    return res

def print_sorted(dic):
    for k, e in sorted(list(dic.items()),key=lambda x:x[1]):
        print(k+"\t\t"+str(e))
    print("")


def get_convos(twts,usrlst):
    twts_dic = {tw['id']:tw for tw in twts} # Building an id-index
    usrset = set(usrlst)
    convos = []
    absences = []
    added = set()
    carmakerConvos = {a:[] for a in usrset}
    carmakerTweets = {a:0 for a in usrset}
    carmakerFirstTweet = {a:0 for a in usrset}
    starterTweets = set()
    for tw in reversed(twts):
        if tw['user']['screen_name'] in usrset:
            carmakerTweets[tw['user']['screen_name']] += 1
            if ('in_reply_to_status_id' not in tw or tw['in_reply_to_status_id'] is None):
                continue # Not a reply to another tweet
                if tw['id'] in added: continue

        convo = []
        explorer = tw
        while explorer is not None:
            convo.append(explorer)
            added.add(explorer['id'])
            if explorer['user']['screen_name'] in usrset:
                carmakerConvos[explorer['user']['screen_name']].append(len(convos))
            if 'in_reply_to_status_id' not in explorer or explorer['in_reply_to_status_id'] is None: 
                starterTweets.add(explorer['id'])
                if explorer['user']['screen_name'] in usrset: 
                    carmakerFirstTweet[explorer['user']['screen_name']] += 1
                break # Done going backwards
            next_twt = explorer['in_reply_to_status_id']
            if  next_twt not in twts_dic:
                #print("Tweet "+str(next_twt)+" not in dictionary.")
                absence = {'id':next_twt,'user':{'screen_name':explorer.get('in_reply_to_screen_name'),
                                                 'id':explorer.get('in_reply_to_user_id')}}
                absences.append(absence)
                convo.append(absence)
                break
            explorer = twts_dic[explorer['in_reply_to_status_id']]
        convos.append(list(reversed(convo)))

    return {'list':convos, 'frst_tweet_by_carmaker':carmakerFirstTweet,
            'convos_with_carmaker':carmakerConvos, 'missing_tweets':absences,
            'tweets_in_conversation':added}
