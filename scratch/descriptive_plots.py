import matplotlib.pyplot as plt
import seaborn as sns
from datetime import date, timedelta
import numpy as np

from dateutil.parser import parse as parsedate

from ElecTweet.TweetLoader import LoadTweets, LoadUsers

from collections import Counter

twts = LoadTweets('cardump/')
usrs = LoadUsers('cardata/')
usrset = usrs[0]

cmTwts = [tw for tw in twts if tw['user']['screen_name'] in usrset]

### Weekdays
gWkdyC = Counter([parsedate(a['created_at']).weekday() for a in twts])
cmWkdyC = Counter([parsedate(a['created_at']).weekday() for a in twts if a['user']['screen_name'] in usrset])
totGt = sum(e for i,e in gWkdyC.items())
totCmt = sum(e for i,e in cmWkdyC.items())

weekdays = ['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday']

fig = plt.figure()
fig.suptitle("Distribution of tweets by weekday")
ax1 = fig.add_subplot(211)

#ax1.set_title("Brand page")
ax1.set_ylabel("Proportion(Brand page)")
sns.barplot(weekdays, [float(e)/totCmt for k,e in cmWkdyC.items()],ax=ax1)
ax1.grid(True)

ax2 = fig.add_subplot(212, sharex=ax1)
#ax2.set_title("All users")
ax2.set_ylabel("Proportion(All users)")
sns.barplot(weekdays, [float(e)/totGt for k,e in gWkdyC.items()],ax=ax2)
ax2.set_xlabel("Weekdays")

plt.show()


### Hours
timeDiff = timedelta(hours=8)
gHrC = Counter([(parsedate(a['created_at']) - timeDiff).hour for a in twts])
cmHrC = Counter([(parsedate(a['created_at']) - timeDiff).hour for a in twts if a['user']['screen_name'] in usrset])

fig = plt.figure()
fig.suptitle("Distribution of tweets by hour")
ax1 = fig.add_subplot(211)

#ax1.set_title("Brand page")
ax1.set_ylabel("Proportion(Brand page)")
sns.barplot([i for i in range(24)], [float(e)/totCmt for k,e in cmHrC.items()],ax=ax1)
ax1.grid(True)

ax2 = fig.add_subplot(212, sharex=ax1,sharey=ax1)
#ax2.set_title("All users")
ax2.set_ylabel("Proportion(All users)")
sns.barplot([i for i in range(24)], [float(e)/totGt for k,e in gHrC.items()],ax=ax2)
ax2.set_xlabel("Hours")

plt.show()

### Likes, retweets, favorites
import csv
twdta = None
with open('tweetdata_cmakers.csv') as f:
    rd = csv.DictReader(f)
    twdta = list(rd)

fig = plt.figure()
fig.suptitle("Histogram of Consumer-to-Business variables")

ax1 = fig.add_subplot(131)
ax1.set_ylabel('Frequency(log)')
ax1.set_xlabel('# of replies')

repCount = [int(rw['C2B_RE'])+1 for rw in twdta]
mybins=np.logspace(0,np.log(max(repCount)),100)

sns.distplot(repCount,hist=True,kde=False,ax=ax1,bins=mybins)
ax1.set_xscale('log')
ax1.set_yscale('log')
ax1.set_title('# of replies')
ax1.set_xlim(right=10000)

ax2 = fig.add_subplot(132)
ax2.set_ylabel('Frequency(log)')
ax2.set_xlabel('# of retweets')

rtwCount = [int(rw['C2B_RT'])+1 for rw in twdta]
mybins=np.logspace(0,np.log(max(rtwCount)),100)
sns.distplot(rtwCount,hist=True,kde=False,ax=ax2,bins=mybins)
ax2.set_yscale('log')
ax2.set_xscale('log')
ax2.set_title('# of retweets')
ax2.set_xlim(right=100000)

ax3 = fig.add_subplot(133)
ax3.set_ylabel('Frequency(log)')
ax3.set_xlabel('# of likes')

favCount = [int(rw['C2B_FAV'])+1 for rw in twdta]
mybins=np.logspace(0,np.log(max(favCount)),100)
sns.distplot(favCount,hist=True,kde=False,ax=ax3,bins=mybins)
ax3.set_yscale('log')
ax3.set_xscale('log')
ax3.set_title('# of likes')
ax3.set_xlim(right=100000)

plt.show()

### Time since tweets histograms
fig = plt.figure()
fig.suptitle("Distribution of time since previous tweets")
for i,var,labl in zip([1,2,3,4],
                 ['B2C_TTW','B2C_TNTW','B2C_RERET','B2C_RET'],
                 ['since previous tweet','since previous non-reply tweet','since previous reply tweet','it took to reply']):
    ax = fig.add_subplot(2,2,i)
    ax.set_ylabel('Frequency(log)')
    ax.set_xlabel('Minures '+labl)
    plotData = [int(float(rw[var])/60) for rw in twdta if var in rw and rw[var] not in [None,'.']]
    mybins=np.logspace(0,np.log(max(plotData)),100)
    sns.distplot(plotData,hist=True,kde=False,ax=ax,bins=mybins)
    ax.set_xscale('log')
    ax.set_yscale('log')
    ax.set_xlim(right=100000)

plt.show()

### Business reply tweets
bizReplies = [tw for tw in twts 
              if 'in_reply_to_user_id' in tw and 
              tw['in_reply_to_user_id'] is not None and 
              tw['user']['screen_name'] in usrset]
allReplies = [tw for tw in twts 
              if 'in_reply_to_user_id' in tw and 
              tw['in_reply_to_user_id'] is not None]

def is_image(tw=None,usrset=None):
    if usrset is not None and tw['user']['screen_name'] not in usrset: return 0
    if 'media' in tw['entities']:
        types = set(et['type'] for et in tw['entities']['media'])
    else: types = set()
    if 'extended_entities' in tw:
        types = types.union(set(et['type'] for et in tw['extended_entities']['media']))
    if 'photo' in types:
        return 1
    return 0

def is_video(tw=None,usrset=None):
    if usrset is not None and tw['user']['screen_name'] not in usrset: return 0
    if 'extended_entities' not in tw: return 0
    types = set(et['type'] for et in tw['extended_entities']['media'])
    if 'video' not in types and 'animated_gif' not in types: return 0
    return 1

def is_link(tw=None,usrset=None):
    if usrset is not None and tw['user']['screen_name'] not in usrset: return 0
    if tw['entities']['urls'] is None or len(tw['entities']['urls']) == 0: return 0
    return 1

def is_text(tw=None,usrset=None):
    is_l = is_link(tw,usrset)
    is_i = is_image(tw,usrset)
    is_v = is_video(tw,usrset)
    return 1 if is_l + is_i + is_v == 0 else 0

cmNonRepTwts = [tw for tw in twts if 'in_reply_to_user_id' not in tw or tw['in_reply_to_user_id'] is None and
                tw['user']['screen_name'] in usrset]

cmReplyCounts = {'is_link':sum(is_link(tw) for tw in bizReplies)/len(bizReplies),
          'is_image':sum(is_image(tw) for tw in bizReplies)/len(bizReplies),
          'is_video':sum(is_video(tw) for tw in bizReplies)/len(bizReplies)}
allReplyCounts = {'is_link':sum(is_link(tw) for tw in allReplies)/len(allReplies),
          'is_image':sum(is_image(tw) for tw in allReplies)/len(allReplies),
          'is_video':sum(is_video(tw) for tw in allReplies)/len(allReplies)}

allCounts = {'is_link':sum(is_link(tw) for tw in twts)/len(twts),
             'is_image':sum(is_image(tw) for tw in twts)/len(twts),
             'is_video':sum(is_video(tw) for tw in twts)/len(twts)}
cmCounts = {'is_link':sum(is_link(tw) for tw in cmTwts)/len(cmTwts),
             'is_image':sum(is_image(tw) for tw in cmTwts)/len(cmTwts),
             'is_video':sum(is_video(tw) for tw in cmTwts)/len(cmTwts)}


cmNonRepCounts = {'is_link':sum(is_link(tw) for tw in cmNonRepTwts)/len(cmNonRepTwts),
                  'is_image':sum(is_image(tw) for tw in cmNonRepTwts)/len(cmNonRepTwts),
                  'is_video':sum(is_video(tw) for tw in cmNonRepTwts)/len(cmNonRepTwts),
                  'is_text':sum(is_text(tw) for tw in cmNonRepTwts)/len(cmNonRepTwts)}

#### Followers per carmaker
carmakers = len(usrset)
followers = {}
cnt = 0
for tw in reversed(cmTwts):
    if tw['user']['screen_name'] in followers: continue
    followers[tw['user']['screen_name']] = tw['user']['followers_count']
    cnt += 1
    if cnt == carmakers: break


##### 
from statistics import mean,stdev
avgFavs = {us:mean(tw['favorite_count'] for tw in twts if tw['user']['screen_name'] == us) for us in usrset}
avgRTs = {us:mean(tw['retweet_count'] for tw in twts if tw['user']['screen_name'] == us) for us in usrset}

sdFavs = {us:stdev(tw['favorite_count'] for tw in twts if tw['user']['screen_name'] == us) for us in usrset}
sdRTs = {us:stdev(tw['retweet_count'] for tw in twts if tw['user']['screen_name'] == us) for us in usrset}

cmMeanFavs = mean(tw['favorite_count'] for tw in twts if tw['user']['screen_name'] in usrset)
cmSDFavs = stdev(tw['favorite_count'] for tw in twts if tw['user']['screen_name'] in usrset)

cmMeanRTs = mean(tw['retweet_count'] for tw in twts if tw['user']['screen_name'] in usrset)
cmSDRTs = stdev(tw['retweet_count'] for tw in twts if tw['user']['screen_name'] in usrset)

cmMeanRes = mean(int(rw['C2B_RE']) for rw in twdta)
cmSDRes = stdev(int(rw['C2B_RE']) for rw in twdta)
