"""
Interesting fields of the Tweet object:
 - 'id', 'id_str'
 - 'scopes' (k-v pairs) - Context in which Tweet is promoted
 - 'place' (somewhat GeoJSON with [long,lat])
 - 'retweet_count' (int)
 - 'favorite_count' (int)
 - 'text' (str)
 - 'created_at' (str)
 - entities (Entities object)
"""

"""
Interesting fields of the User object: 
 - 'id', 'id_str'
 - 'screen_name' (str)
 - 'statuses_count' (int)
 - 'verified' (bool)
 - 'time_zone' (str)
 - "followers_count" (int)
 - "friends_count" (int) - Number of followees
"""

"""
Interesting fields of the Entities object:
 - "hashtags" (Array of object):
    [{"text":"lol"},{"text":"itsforoil"},..]

 - "urls" (Array of object):
    [{"url":"http://lol"},{"url":"http://hanja.me"},..]

 - "user_mentions" (Array of object):
    [{'screen_name':'polecitoem', 'id':125, 'id_str':'125'},...]
"""

import glob
import json
import csv
from collections import Counter
from explore_helper import *
import datetime as dt

files = glob.glob('./cardump/*json')
twts = [a for fl in files for a in json.load(open(fl))]
twts.sort(key=lambda x: x['id'] if 'id' in x else int(x['id_str']) if 'id_str' in x else 0)
twts = [a for a in twts if 'id' in a or 'str_id' in a]
twts = [a for a in twts 
        if (('id' in a and a['id'] >= 656971539691257900) or 
            ('id_str' in a and int(a['id_str']) >= 656971539691257900))]

usrfiles = glob.glob('./cardata/*txt')
users = [a.strip("@") # Removing the @
         for fl in usrfiles
         for nms in open(fl)
         for a in nms.strip().split(",")]
usrset = set(users)

# At this point we have all tweets that are common. We will now build conversations

for tw in twts:
    if 'id' not in tw: tw['id'] = int(tw['id_str'])
    if 'id_str' not in tw: tw['id_str'] = str(tw['id'])
    pass
"""
mentions = get_mentions(twts)

mentions_by_carmaker = get_mentions(twts,users)
"""
""" Ways in which tweets can indicate being quotes or replies:

- 'quoted_status_id' (int)
- 'quoted_status_id_str' (str)

- 'in_reply_to_screen_name' (str)
- 'in_reply_to_user_id' (int)
- 'in_reply_to_status_id'(int)
- 'in_reply_to_status_id_str'(str)

- 'retweeted_status' (Tweet)
"""

### In this section, we will build the conversations that occurred

convoDic = get_convos(twts,users)

(convos, absences, 
 carmakerConvos, carmakerFirstTweet) = (convoDic['list'], convoDic['missing_tweets'],
                                        convoDic['convos_with_carmaker'], convoDic['frst_tweet_by_carmaker'])

print("Absent tweets: "+str(len(absences)))
print("Conversations: "+str(len(convos)))
print("Carmaker convos: "+str(sum(len(e) for k,e in carmakerConvos.items())))

# Now we find percentage of conversations that start with a tweet from a NORMAL user,
# and then answered by a carmaker
print("Proportion of conversations with carmaker that were started by carmaker,\n and answered by someone else:")
prop_convos_carmaker = {a:float(carmakerFirstTweet[a])/len(carmakerConvos[a]) for a in carmakerConvos}
print_sorted(prop_convos_carmaker)

auth_cnt = authored_count(twts,users)
reply_cnt = reply_count(twts,users)
print("Proportion of tweets of a carmaker that are a response to another tweet:")
prop_reply_tweets = {a:float(reply_cnt[a])/auth_cnt[a] for a in auth_cnt}
print_sorted(prop_reply_tweets)

print("Number of tweets by each carmaker:")
print_sorted(auth_cnt)

followers = get_followers(twts,users)
print("Number of followers by each carmaker:")
print_sorted(followers)

followees = get_followees(twts,users)
print("Number of followees by each carmaker:")
print_sorted(followees)

avg_secs = get_time_between_tweets(twts,users)
print("Average seconds between tweets by each carmaker:")
print_sorted(avg_secs)

print("Average seconds between Non-reply tweets by each carmaker:")
avg_secs_non_reply = get_time_between_tweets(twts,users,lambda x: x['in_reply_to_status_id'] is None)
print_sorted(avg_secs_non_reply)

print("Average seconds between reply tweets by each carmaker:")
avg_secs_reply = get_time_between_tweets(twts,users,lambda x: x['in_reply_to_status_id'] is not None)
print_sorted(avg_secs_reply)

print("Average seconds between a user being mentioned:")
avg_secs_mention = get_time_between_mentions(twts,users)
print_sorted(avg_secs_mention)

#f = open('needed_tweets.json','w')
#json.dump([a['id'] for a in absences],f)
#f.close()

f = open("data.csv",'w')
wr = csv.writer(f)
wr.writerow(["Screen name", "Conversations CM-USR", "Conversations USR-CM", "% tweets by CM that are replies",
             "Tweets by CM", "Followers","Followees","Time between tweets","Time between non-reply tweets",
             "Time between reply tweets", "Time between mentions"])
for usr in users:
    wr.writerow([usr,prop_convos_carmaker[usr],1 - prop_convos_carmaker[usr], 
                 prop_reply_tweets[usr],auth_cnt[usr],
                 followers[usr],followees[usr],avg_secs[usr],avg_secs_non_reply[usr],
                 avg_secs_reply[usr], avg_secs_mention[usr]])

f.close()
