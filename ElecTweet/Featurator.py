import datetime as dt
import re
from random import choice
from dateutil.parser import parse as parsedate
from collections import defaultdict
from statistics import mean,stdev

def is_outlier(elm,m,sd):
    return abs(elm - m) <= 3*sd

def outlier_count(elms):
    mn = mean(elms)
    sd = stdev(elms)
    return sum(1 if is_outlier(e,mn,sd) else 0 for e in elms)

def mean_minus_outliers(elms):
    #mn = mean(elms)
    #sd = stdev(elms)
    return choice([sum(choice(elms) for e in elms) for _ in range(5)]) / len(elms)
    pass

mean = mean_minus_outliers

class Featurator():
    def __init__(self,usrset):
        self._usrset = usrset
        self._per_tweet_features = {}
        self._user_features = {}
        self._convo_features = {}
        self.set_state()
        self.configure_features()
        pass

    def set_state(self,state='start'):
        self._state = state
        
    def get_state(self):
        return self._state

    def finalize(self):
        if self.get_state() != 'end':
            raise Exception("To finalize must be in 'end' state")
        res = {}
        for key, feat in self._user_features.items():
            res[key] = feat()
        for key, feat in self._convo_features.items():
            res[key] = feat()
        for key, feat in self._per_tweet_features.items():
            res[key] = feat()

        return res

    def build_convos(self,twts):
        self.__twts_dic = {tw['id']:tw for tw in twts} # id-index
        twts_dic = self.__twts_dic
        usrset = self._usrset
        self._convos = []
        absent_twts = []
        added = set()
        self._carmakerConvoReps = {us:defaultdict(lambda:0.0) for us in usrset}
        for tw in reversed(twts):
            if tw['id'] in added: continue
            if 'in_reply_to_status_id' not in tw or tw['in_reply_to_status_id'] is None: continue
            convo = []
            pnt = tw
            while pnt is not None:
                convo.append(pnt)
                added.add(pnt['id'])
                if pnt['user']['screen_name'] in usrset:
                    self._carmakerConvoReps[pnt['user']['screen_name']][len(self._convos)] += 1
                if 'in_reply_to_status_id' not in pnt or pnt['in_reply_to_status_id'] is None:
                    break
                next_twt = twts_dic.get(pnt['in_reply_to_status_id'])
                if next_twt is None:
                    absence = {'id':next_twt,'user':{'screen_name':pnt.get('in_reply_to_screen_name'),
                                                     'id':pnt.get('in_reply_to_user_id')}}
                    absent_twts.append(absence)
                    convo.append(absence)
                    break
                pnt = next_twt
            self._convos.append(list(reversed(convo)))

    def tweet_features(self,tw):
        if self.get_state() != 'running':
            raise Exception("To initialize must be in 'start' state")
        if tw['user']['screen_name'] in self._usrset:
            self.__tweet_count[tw['user']['screen_name']] += 1

        for key,feat in self._per_tweet_features.items():
            feat(tw)

    def initialize(self,twts):
        if self.get_state() != 'start':
            raise Exception("To initialize must be in 'start' state")
        self.__tweet_count = {us:0 for us in self._usrset}
        for key, feat in self._per_tweet_features.items():
            feat(None)
        self.build_convos(twts)
        self.set_state('running')
    
    def configure_features(self):
        self._per_tweet_features['MT_V'] = self._VV_Video
        self._per_tweet_features['MT_I'] = self._VV_Image
        self._per_tweet_features['MT_L'] = self._VV_Link
        self._per_tweet_features['MT_T'] = self._VV_Text
        self._per_tweet_features['C2B_RTT'] = self._VV_TextRetweets
        self._per_tweet_features['C2B_RTV'] = self._VV_VidRetweets
        self._per_tweet_features['C2B_RTI'] = self._VV_ImgRetweets
        self._per_tweet_features['C2B_RTL'] = self._VV_LinkRetweets
        self._per_tweet_features['T_D'] = self._PT_Weekday
        self._per_tweet_features['T_H'] = self._PT_PeakHour
        self._per_tweet_features['C2B_FAV'] = self._EG_Favs
        self._per_tweet_features['C2B_FAVV'] = self._EG_FavVid
        self._per_tweet_features['C2B_FAVI'] = self._EG_FavImg
        self._per_tweet_features['C2B_FAVL'] = self._EG_FavLink
        self._per_tweet_features['C2B_FAVT'] = self._EG_FavText
        self._per_tweet_features['C2B_RT'] = self._EG_Retweets
        self._per_tweet_features['B2C_REP'] = self._OEG_ReProp
        self._per_tweet_features['B2C_TTW'] = self._UI_TimeTweet
        self._per_tweet_features['B2C_TNTW'] = self._UI_TimeNonReply
        self._per_tweet_features['B2C_RERET'] = self._MX_TimeReplies
        self._per_tweet_features['B2C_RT'] = self._OEG_Retweet
        self._per_tweet_features['C2B_MT'] = self._EG_MentionTime
        self._per_tweet_features['C2B_REV'] = self._VV_VideoReplies
        self._per_tweet_features['C2B_REI'] = self._VV_ImageReplies
        self._per_tweet_features['C2B_REL'] = self._VV_LinkReplies
        self._per_tweet_features['C2B_RET'] = self._VV_TextReplies
        #self._per_tweet_features['MT-Inter'] = self._MT_Inter
        self._per_tweet_features['C2B_RE'] = self._MX_Replies
        self._per_tweet_features['MT_HI'] = self._IT_HighInteract
        self._per_tweet_features['MT_LI'] = self._IT_LowInteract
        self._per_tweet_features['C2B_FAVHI'] = self._IT_FavHighInt
        self._per_tweet_features['C2B_FAVLI'] = self._IT_FavLowInt
        self._per_tweet_features['C2B_RTLI'] = self._VV_RTLowInteract
        self._per_tweet_features['C2B_RTHI'] = self._VV_RTHiInteract

        #self._per_tweet_features['C2B_RELI'] = self._VV_RELowInteract
        #self._per_tweet_features['C2B_REHI'] = self._VV_REHiInteract

        self._per_tweet_features['CT_I'] = self._CT_Info
        self._per_tweet_features['CT_E'] = self._CT_Enter

        self._user_features['B2C_FL'] = self._OEG_Followees
        self._user_features['C2B_FL'] = self._EG_Followers
        self._user_features['B2C_TW'] = self._UI_NumTweets
        self._user_features['B2C_FAV'] = self._OEG_FavsByUs

        self._convo_features['B2C_CL'] = self._MX_ConvoLen
        self._convo_features['B2C_REC'] = self._MX_ConvoReps
        self._convo_features['B2C_RED'] = self._MX_RepDiff
        self._convo_features['B2C_RET'] = self._MX_RepTime

    def _CT_Enter(self,tw=None):
        if self._state != 'end': return
        iT = self.__info_tweets
        tC = self.__tweet_count
        return {us:(1.0 - float(iT[us])/tC[us]) if tC[us] > 0 else 1 for us in self._usrset}

    def _CT_Info(self,tw=None):
        if self._state == 'start':
            self.___info_regexp = re.compile('.*[Tt]he (new )?[#@]?[A-Z0-9]')
            self.___info_keywords = ['Toyota','VW','Mercedes-Benz','Volvo','Lexus','Infiniti','BMW','Audi',
                                     'Ford','MB','Hyundai','Nissan','MINI','Jeep','FIAT','Volkswagen']
            self.__info_tweets = {us:0 for us in self._usrset}
            return
        if self._state == 'end':
            iT = self.__info_tweets
            tC = self.__tweet_count
            return {us:float(iT[us])/tC[us] if tC[us] > 0 else 0 for us in self._usrset}
        if tw['user']['screen_name'] not in self._usrset: return
        if 'in_reply_to_status_id' in tw and tw['in_reply_to_status_id'] is not None: return
        rex = self.___info_regexp
        kwds = self.___info_keywords
        iT = self.__info_tweets
        score = 0
        if rex.match(tw['text']) is not None: score += 1
        if any(kw in tw['text'] for kw in kwds): score += 1
        if score < 1: return
        iT[tw['user']['screen_name']] += 1

    def _PT_PeakHour(self,tw=None):
        if self._state == 'start':
            self.__peakhr_tweets = {us:0 for us in self._usrset}
            self.___peakhrs = set([16,17,18,19])
            return
        if self._state == 'end':
            tC = self.__tweet_count
            fC = self.__peakhr_tweets
            return {us:float(fC[us])/tC[us] if tC[us] > 0 else 0 for us in self._usrset}
        if tw['user']['screen_name'] not in self._usrset: return
        if parsedate(tw['created_at']).time().hour in self.___peakhrs:
            us = tw['user']['screen_name']
            self.__peakhr_tweets[us] += 1

    def _VV_RTLowInteract(self,tw=None):
        if self._state == 'start':
            self.__rtlowinter_count = {us:[] for us in self._usrset}
            return
        if self._state == 'end':
            fC = self.__rtlowinter_count
            tC = self.__lowinter_count
            return {us:(mean(fC[us]) if len(fC[us]) > 0 else 0) for us in self._usrset}

    def _VV_RTHiInteract(self,tw=None):
        if self._state == 'start':
            self.__rthiinter_count = {us:[] for us in self._usrset}
            return
        if self._state == 'end':
            fC = self.__rthiinter_count
            tC = self.__hiinter_count
            return {us:(mean(fC[us]) if len(fC[us]) > 0 else 0) for us in self._usrset}

    def _IT_HighInteract(self,tw=None):
        if self._state != 'end': return
        fC = self.__hiinter_count
        tC = self.__tweet_count
        return {us:float(fC[us])/tC[us]  if tC[us] > 0 else 0 for us in self._usrset}

    def _IT_FavLowInt(self,tw=None):
        if self._state != 'end': return
        fC = self.__lowinter_favs
        tC = self.__lowinter_count
        return {us:float(fC[us])/tC[us]  if tC[us] > 0 else 0 for us in self._usrset}

    def _IT_FavHighInt(self,tw=None):
        if self._state != 'end': return
        fC = self.__hiinter_favs
        tC = self.__hiinter_count
        return {us:float(fC[us])/tC[us] if tC[us] > 0 else 0 for us in self._usrset}

    def _IT_FavLowhInt(self,tw=None):
        if self._state != 'end': return
        fC = self.__lowinter_favs
        tC = self.__tweet_count
        return {us:float(fC[us])/tC[us] if tC[us] > 0 else 0 for us in self._usrset}

    def _IT_LowInteract(self,tw=None):
        if self._state == 'start':
            self.___hi_keywords = ['contest','sweepstakes','chance to win','gift','quiz','dm ']
            self.___li_keywords = ['visit ','follow us','vote','poll','tell us','check out']
            self.__lowinter_count = {us:0 for us in self._usrset}
            self.__lowinter_favs = {us:0 for us in self._usrset}
            self.__hiinter_count = {us:0 for us in self._usrset}
            self.__hiinter_favs = {us:0 for us in self._usrset}
            return
        if self._state == 'end':
            fC = self.__lowinter_count
            tC = self.__tweet_count
            return {us:float(fC[us])/tC[us] if tC[us] > 0 else 0 for us in self._usrset}
        if tw['user']['screen_name'] not in self._usrset: return
        lwCase = tw['text'].lower()
        usr = tw['user']['screen_name']
        if any(kw in lwCase for kw in self.___hi_keywords):
            self.__rthiinter_count[usr].append(tw['retweet_count'])
            self.__hiinter_count[usr] += 1
            favs = 0 if 'favorite_count' not in tw or tw['favorite_count'] is None else int(tw['favorite_count'])
            self.__hiinter_favs[usr] += favs
            return
        if any(kw in lwCase for kw in self.___li_keywords) or ('?' in lwCase and tw['in_reply_to_user_id'] is None):
            self.__lowinter_count[usr] += 1
            self.__rtlowinter_count[usr].append(tw['retweet_count'])
            favs = 0 if 'favorite_count' not in tw or tw['favorite_count'] is None else int(tw['favorite_count'])
            self.__lowinter_favs[usr] += favs
            return

    def _VV_TextReplies(self,tw=None):
        if self._state == 'start':
            self.__textreplies_count = {us:defaultdict(lambda : 0) for us in self._usrset}
            return
        if self._state == 'end':
            res = {}
            vR = self.__textreplies_count
            for us, rCounts in vR.items():
                res[us] = float(sum(cnt for twId,cnt in rCounts.items()))/(len(rCounts) if len(rCounts) > 0 else 1)
            return res
        if 'in_reply_to_status_id' not in tw or tw['in_reply_to_status_id'] is None: return
        if tw['in_reply_to_status_id'] not in self.__twts_dic: return
        oldTw = self.__twts_dic[tw['in_reply_to_status_id']]
        if oldTw['entities']['urls'] is not None and len(oldTw['entities']['urls']) > 0: return
        if oldTw['user']['screen_name'] not in self._usrset: return
        if ('media' in oldTw['entities'] and 
            oldTw['entities']['media'] is not None and 
            len(oldTw['entities']['media']) > 0): 
            return
        if 'extended_entities' in tw and len(tw['extended_entities']['media']) > 0: return
        us = tw['in_reply_to_screen_name']
        twId = tw['in_reply_to_status_id']
        self.__textreplies_count[us][twId] += 1
        

    def _VV_LinkReplies(self,tw=None):
        if self._state == 'start':
            self.__linkreplies_count = {us:defaultdict(lambda : 0) for us in self._usrset}
            return
        if self._state == 'end':
            res = {}
            vR = self.__linkreplies_count
            for us, rCounts in vR.items():
                res[us] = float(sum(cnt for twId,cnt in rCounts.items()))/(len(rCounts) if len(rCounts) > 0 else 1)
            return res
        if 'in_reply_to_status_id' not in tw or tw['in_reply_to_status_id'] is None: return
        if tw['in_reply_to_status_id'] not in self.__twts_dic: return
        oldTw = self.__twts_dic[tw['in_reply_to_status_id']]
        if oldTw['user']['screen_name'] not in self._usrset: return
        if oldTw['entities']['urls'] is None or len(tw['entities']['urls']) == 0: return
        us = tw['in_reply_to_screen_name']
        twId = tw['in_reply_to_status_id']
        self.__linkreplies_count[us][twId] += 1

    def _VV_ImageReplies(self,tw=None):
        if self._state == 'start':
            self.__imgreplies_count = {us:defaultdict(lambda : 0) for us in self._usrset}
            return
        if self._state == 'end':
            res = {}
            vR = self.__imgreplies_count
            for us, rCounts in vR.items():
                res[us] = float(sum(cnt for twId,cnt in rCounts.items()))/(len(rCounts) if len(rCounts) > 0 else 1)
            return res
        if 'in_reply_to_status_id' not in tw or tw['in_reply_to_status_id'] is None: return
        if tw['in_reply_to_status_id'] not in self.__twts_dic: return
        oldTw = self.__twts_dic[tw['in_reply_to_status_id']]
        if oldTw['user']['screen_name'] not in self._usrset: return
        if 'media' in oldTw['entities']:
            types = set(et['type'] for et in oldTw['entities']['media'])
        else: types = set()
        if 'extended_entities' in oldTw:
            types = types.union(set(et['type'] for et in oldTw['extended_entities']['media']))
        if 'photo' not in types: return
        us = tw['in_reply_to_screen_name']
        twId = tw['in_reply_to_status_id']
        self.__imgreplies_count[us][twId] += 1

    def _VV_VideoReplies(self,tw=None):
        if self._state == 'start':
            self.__vidreplies_count = {us:defaultdict(lambda : 0) for us in self._usrset}
            return
        if self._state == 'end':
            res = {}
            vR = self.__vidreplies_count
            for us, rCounts in vR.items():
                res[us] = float(sum(cnt for twId,cnt in rCounts.items()))/(len(rCounts) if len(rCounts) > 0 else 1)
            return res
        if 'in_reply_to_status_id' not in tw or tw['in_reply_to_status_id'] is None: return
        if tw['in_reply_to_status_id'] not in self.__twts_dic: return
        oldTw = self.__twts_dic[tw['in_reply_to_status_id']]
        if oldTw['user']['screen_name'] not in self._usrset: return
        if 'extended_entities' not in oldTw: return
        types = set(et['type'] for et in oldTw['extended_entities']['media'])
        if 'video' not in types: return
        us = tw['in_reply_to_screen_name']
        twId = tw['in_reply_to_status_id']
        self.__vidreplies_count[us][twId] += 1
        

    def _MX_Replies(self,tw=None):
        if self._state == 'start':
            self.__replies_count = {us:defaultdict(lambda : 0) for us in self._usrset}
            return
        if self._state == 'end':
            res = {}
            vR = self.__replies_count
            for us, rCounts in vR.items():
                lVrUs = len(vR[us]) if len(vR[us]) > 0 else 1
                res[us] = float(sum(cnt for twId,cnt in rCounts.items()))/lVrUs
            return res
        if 'in_reply_to_status_id' not in tw or tw['in_reply_to_status_id'] is None: return
        if tw['in_reply_to_screen_name'] not in self._usrset: return
        us = tw['in_reply_to_screen_name']
        twId = tw['in_reply_to_status_id']
        self.__replies_count[us][twId] += 1
        
    def _MX_RepDiff(self):
        res = {}
        for us in self._usrset:
            convoReps = self._carmakerConvoReps[us]
            convoCount = len(convoReps) if len(convoReps) > 0 else 1
            diffSum = sum([2*reps - len(self._convos[conv]) for conv,reps in convoReps.items()])
            res[us] = float(diffSum)/convoCount
        return res

    def _MX_RepTime(self):
        res = {}
        self.__rep_timediffs = {}
        for us in self._usrset:
            convoReps = self._carmakerConvoReps[us]
            timeDiffs = []
            self.__rep_timediffs[us] = timeDiffs
            for cvId, reps in convoReps.items():
                convo = self._convos[cvId]
                mentionTw = None
                for i, tw in enumerate(convo):
                    if 'created_at' not in tw: continue
                    if tw['user']['screen_name'] == us and i == 0: continue
                    if tw['user']['screen_name'] != us: 
                        mentionTw = tw
                        continue
                    if mentionTw is None: continue
                    st = parsedate(mentionTw['created_at'])
                    end = parsedate(tw['created_at'])
                    delta = end - st
                    timeDiffs.append(delta.total_seconds())
                    mentionTw = None
                    reps -= 1
                    if reps == 0: break # Go to the next conversation
            res[us] = 0
            if len(timeDiffs) > 0: res[us] = mean(timeDiffs)
        return res

    def _MX_ConvoLen(self):
        res = {}
        for us in self._usrset:
            convoReps = self._carmakerConvoReps[us]
            convoCount = len(convoReps) if len(convoReps) > 0 else 1
            lenSum = sum([len(self._convos[conv]) for conv,reps in convoReps.items()])
            res[us] = float(lenSum)/convoCount
        return res

    def _MX_ConvoReps(self):
        cR = self._carmakerConvoReps
        res = {us:sum(reps/len(cR[us]) for conv,reps in cR[us].items()) for us in self._usrset}
        return res

    def _MT_Inter(self,tw=None):
        if self._state == "start": return
        if self._state == "end":
            vC = self.__video_count
            lC = self.__link_count
            tC = self.__tweet_count
            res = {us:float(vC[us]+lC[us])/float(tC[us])  if tC[us] > 0 else 0 for us in self._usrset}
            return res

    def _OEG_Followees(self):
        if self.get_state() != "end":
            raise Exception("User features can only be computed after tweet features are done computing")
        lT = self.__last_tweet
        usrs = self._usrset
        return {us:lT[us]['user']['friends_count'] if lT[us] is not None else 0 for us in usrs}

    def _OEG_FavsByUs(self):
        if self.get_state() != "end":
            raise Exception("User features can only be computed after tweet features are done computing")
        lt = self.__last_tweet
        usrs = self._usrset
        return {us:lt[us]['user']['favourites_count'] if lt[us] is not None else 0 for us in usrs}

    def _EG_Followers(self):
        if self.get_state() != "end":
            raise Exception("User features can only be computed after tweet features are done computing")
        lt = self.__last_tweet
        usrs = self._usrset
        self.__follower_count = {us:lt[us]['user']['followers_count'] if lt[us] is not None else 0 for us in usrs}
        return self.__follower_count

    def _EG_MentionTime(self,tw=None):
        if self._state == "start":
            self.__last_mention = {us:None for us in self._usrset}
            self.__mention_times = {us:[] for us in self._usrset}
            return
        if self._state == "end":
            oC = self.__mention_times
            res = {us:float(sum(oC[us]))/len(oC[us]) if len(oC[us]) > 0 else 0 for us in self._usrset}
            return res
        mentioned = set([mn['screen_name'] for mn in tw['entities']['user_mentions']])
        carMakerMentions = self._usrset.intersection(mentioned)
        if len(carMakerMentions) == 0: return
        latter = parsedate(tw['created_at'])
        for cmaker in carMakerMentions:
            first = self.__last_mention[cmaker]
            self.__last_mention[cmaker] = tw
            if first is None: continue
            first = parsedate(first['created_at'])
            diff = latter - first
            self.__mention_times[cmaker].append(diff.total_seconds())

    def _VV_VidRetweets(self,tw=None):
        if self._state == 'start':
            self.__vidretweet_count = {us:0 for us in self._usrset}
            return
        if self._state == 'end':
            rC = self.__vidretweet_count
            tC = self.__video_count
            return {us:float(rC[us])/tC[us] if tC[us] > 0 else 0 for us in self._usrset}
        if tw['user']['screen_name'] not in self._usrset: return
        if 'extended_entities' not in tw: return
        types = set(et['type'] for et in tw['extended_entities']['media'])
        if 'video' not in types: return
        us = tw['user']['screen_name']
        self.__vidretweet_count[us] += tw['retweet_count']

    def _VV_ImgRetweets(self,tw=None):
        if self._state == 'start':
            self.__imgretweet_count = {us:0 for us in self._usrset}
            return
        if self._state == 'end':
            rC = self.__imgretweet_count
            tC = self.__image_count
            return {us:float(rC[us])/tC[us] if tC[us] > 0 else 0 for us in self._usrset}
        if tw['user']['screen_name'] not in self._usrset: return
        if 'media' in tw['entities']:
            types = set(et['type'] for et in tw['entities']['media'])
        else: types = set()
        if 'extended_entities' in tw:
            types = types.union(set(et['type'] for et in tw['extended_entities']['media']))
        if 'photo' not in types: return
        us = tw['user']['screen_name']
        self.__imgretweet_count[us] += tw['retweet_count']

    def _VV_LinkRetweets(self,tw=None):
        if self._state == 'start':
            self.__linkretweet_count = {us:0 for us in self._usrset}
            return
        if self._state == 'end':
            rC = self.__linkretweet_count
            tC = self.__link_count
            return {us:float(rC[us])/tC[us] if tC[us] > 0 else 0 for us in self._usrset}
        if tw['user']['screen_name'] not in self._usrset: return
        if tw['entities']['urls'] is None or len(tw['entities']['urls']) == 0: return
        us = tw['user']['screen_name']
        self.__linkretweet_count[us] += tw['retweet_count']

    def _VV_TextRetweets(self,tw=None):
        if self._state == 'start':
            self.__textretweet_count = {us:0 for us in self._usrset}
            return
        if self._state == 'end':
            rC = self.__textretweet_count
            tC = self.__text_count
            return {us:float(rC[us])/tC[us] if tC[us] > 0 else 0 for us in self._usrset}
        if tw['user']['screen_name'] not in self._usrset: return
        if tw['entities']['urls'] is not None and len(tw['entities']['urls']) > 0: return
        if 'media' in tw['entities'] and tw['entities']['media'] is not None and len(tw['entities']['media']) > 0: return
        if 'extended_entities' in tw and len(tw['extended_entities']['media']) > 0: return
        us = tw['user']['screen_name']
        self.__textretweet_count[us] += tw['retweet_count']

    def _OEG_Retweet(self,tw=None):
        if self._state == "start":
            self.__retweet_count = {us:0 for us in self._usrset}
            return
        if self._state == "end":
            oC = self.__retweet_count
            tC = self.__tweet_count
            res = {us:float(oC[us])/float(tC[us]) if tC[us] > 0 else 0 for us in self._usrset}
            return res
        if tw['user']['screen_name'] not in self._usrset: return
        if 'retweeted_status' not in tw or tw['retweeted_status'] is None: return
        usr = tw['user']['screen_name']
        self.__retweet_count[usr] += 1

    def _MX_TimeReplies(self,tw=None):
        if self._state == "start":
            self.__last_yesreply = {us:None for us in self._usrset}
            self.__yesreply_times = {us:[] for us in self._usrset}
            return
        if self._state == "end":
            oC = self.__yesreply_times
            res = {us:float(sum(oC[us]))/len(oC[us]) if len(oC[us]) > 0 else 0 for us in self._usrset}
            return res
        if tw['user']['screen_name'] not in self._usrset: return
        if (not (('quoted_status_id_str' in tw and tw['quoted_status_id_str'] is not None) or
                 ('in_reply_to_screen_name' in tw and tw['in_reply_to_screen_name'] is not None) or
                 ('in_reply_to_status_id' in tw and tw['in_reply_to_status_id'] is not None))):
            return
        oC = self.__last_yesreply
        usr = tw['user']['screen_name']
        lTw = oC[usr]
        oC[usr] = tw
        if lTw is None: return
        prev = parsedate(lTw['created_at'])
        latt = parsedate(tw['created_at'])
        delta = latt - prev
        self.__yesreply_times[usr].append(delta.total_seconds())

    def _UI_TimeNonReply(self,tw=None):
        if self._state == "start":
            self.__last_nonreply = {us:None for us in self._usrset}
            self.__nonreply_times = {us:[] for us in self._usrset}
            return
        if self._state == "end":
            oC = self.__nonreply_times
            res = {us:float(sum(oC[us]))/len(oC[us]) if len(oC[us]) > 0 else 0  for us in self._usrset}
            return res
        if tw['user']['screen_name'] not in self._usrset: return
        if (('quoted_status_id_str' in tw and tw['quoted_status_id_str'] is not None) or
            ('in_reply_to_screen_name' in tw and tw['in_reply_to_screen_name'] is not None) or
            ('in_reply_to_status_id' in tw and tw['in_reply_to_status_id'] is not None)):
            return
        oC = self.__last_nonreply
        usr = tw['user']['screen_name']
        lTw = oC[usr]
        oC[usr] = tw
        if lTw is None: return
        prev = parsedate(lTw['created_at'])
        latt = parsedate(tw['created_at'])
        delta = latt - prev
        self.__nonreply_times[usr].append(delta.total_seconds())

    def _UI_NumTweets(self,tw=None):
        if self._state != "end": return
        tC = self.__tweet_count
        res = {us:tC[us]  if tC[us] > 0 else 0 for us in self._usrset}
        return res

    def _UI_TimeTweet(self,tw=None):
        if self._state == "start":
            self.__last_tweet = {us:None for us in self._usrset}
            self.__tweet_times = {us:[] for us in self._usrset}
            return
        if self._state == "end":
            oC = self.__tweet_times
            res = {us:(0 if len(oC[us]) == 0 else float(mean(oC[us]))) for us in self._usrset}
            return res
        if tw['user']['screen_name'] not in self._usrset: return
        oC = self.__last_tweet
        usr = tw['user']['screen_name']
        lTw = oC[usr]
        oC[usr] = tw
        if lTw is None: return
        prev = parsedate(lTw['created_at'])
        latt = parsedate(tw['created_at'])
        delta = latt - prev
        self.__tweet_times[usr].append(delta.total_seconds())
        

    def _OEG_ReProp(self,tw=None):
        if self._state == "start":
            self.__reply_count = {us:0 for us in self._usrset}
            return
        if self._state == "end":
            oC = self.__reply_count
            tC = self.__tweet_count
            res = {us:float(oC[us])/float(tC[us]) if tC[us] > 0 else 0 for us in self._usrset}
            return res
        if tw['user']['screen_name'] not in self._usrset: return
        if (not (('quoted_status_id_str' in tw and tw['quoted_status_id_str'] is not None) or
                 ('in_reply_to_screen_name' in tw and tw['in_reply_to_screen_name'] is not None) or
                 ('in_reply_to_status_id' in tw and tw['in_reply_to_status_id'] is not None))):
            return
        usr = tw['user']['screen_name']
        self.__reply_count[usr] += 1
    

    def _EG_Favs(self,tw=None):
        if self._state == "start":
            self.__favs_count = {us:0 for us in self._usrset}
            return
        if self._state == "end":
            oC = self.__favs_count
            tC = self.__tweet_count
            res = {us:float(oC[us])/float(tC[us]) if tC[us] > 0 else 0 for us in self._usrset}
            return res
        if tw['user']['screen_name'] not in self._usrset: return
        favs = 0 if 'favorite_count' not in tw or tw['favorite_count'] is None else int(tw['favorite_count'])
        usr = tw['user']['screen_name']
        self.__favs_count[usr] += favs

    def _EG_FavVid(self,tw=None):
        if self._state == "start":
            self.__favvid_count = {us:0 for us in self._usrset}
            self.__vid_count = {us:0 for us in self._usrset}
            return
        if self._state == "end":
            oC = self.__favvid_count
            tC = self.__vid_count
            res = {us:float(oC[us])/float(tC[us]) if tC[us] != 0 else 0 for us in self._usrset}
            return res
        if tw['user']['screen_name'] not in self._usrset: return
        if 'extended_entities' not in tw: return
        types = set(et['type'] for et in tw['extended_entities']['media'])
        if 'video' not in types: return
        favs = 0 if 'favorite_count' not in tw or tw['favorite_count'] is None else int(tw['favorite_count'])
        usr = tw['user']['screen_name']
        self.__vid_count[usr] += 1
        self.__favvid_count[usr] += favs

    def _EG_FavText(self,tw=None):
        if self._state == "start":
            self.__favtext_count = {us:0 for us in self._usrset}
            self.__text_count = {us:0 for us in self._usrset}
            return
        if self._state == "end":
            oC = self.__favtext_count
            tC = self.__text_count
            res = {us:float(oC[us])/float(tC[us]) if tC[us] > 0 else 0 for us in self._usrset}
            return res
        if tw['user']['screen_name'] not in self._usrset: return
        if tw['entities']['urls'] is not None and len(tw['entities']['urls']) > 0: return
        if 'media' in tw['entities'] and tw['entities']['media'] is not None and len(tw['entities']['media']) > 0: return
        if 'extended_entities' in tw and len(tw['extended_entities']['media']) > 0: return
        favs = 0 if 'favorite_count' not in tw or tw['favorite_count'] is None else int(tw['favorite_count'])
        usr = tw['user']['screen_name']
        self.__favtext_count[usr] += favs
        self.__text_count[usr] += 1

    def _EG_FavImg(self,tw=None):
        if self._state == "start":
            self.__favimg_count = {us:0 for us in self._usrset}
            self.__img_count = {us:0 for us in self._usrset}
            return
        if self._state == "end":
            oC = self.__favimg_count
            tC = self.__img_count
            res = {us:float(oC[us])/float(tC[us]) if tC[us] > 0 else 0 for us in self._usrset}
            return res
        if tw['user']['screen_name'] not in self._usrset: return
        ## Here we check video!
        if 'media' in tw['entities']:
            types = set(et['type'] for et in tw['entities']['media'])
        else: types = set()
        if 'extended_entities' in tw and 'media' in tw['extended_entities']:
            types = types.union(set(et['type'] for et in tw['extended_entities']['media']))
        if 'photo' in types:
            favs = 0 if 'favorite_count' not in tw or tw['favorite_count'] is None else int(tw['favorite_count'])
            self.__favimg_count[tw['user']['screen_name']] += favs
            self.__img_count[tw['user']['screen_name']] += 1

    def _EG_FavLink(self,tw=None):
        if self._state == "start":
            self.__favlink_count = {us:0 for us in self._usrset}
            self.__link_count = {us:0 for us in self._usrset}
            return
        if self._state == "end":
            oC = self.__favlink_count
            tC = self.__link_count
            res = {us:float(oC[us])/float(tC[us]) if tC[us] > 0 else 0 for us in self._usrset}
            return res
        if tw['user']['screen_name'] not in self._usrset: return
        ## Here we check video!
        if tw['entities']['urls'] is None or len(tw['entities']['urls']) == 0: return
        favs = 0 if 'favorite_count' not in tw or tw['favorite_count'] is None else int(tw['favorite_count'])
        self.__favlink_count[tw['user']['screen_name']] += favs
        self.__link_count[tw['user']['screen_name']] += 1

    def _EG_Retweets(self,tw=None):
        if self._state == "start":
            self.__share_count = {us:0 for us in self._usrset}
            return
        if self._state == "end":
            oC = self.__share_count
            tC = self.__tweet_count
            res = {us:float(oC[us])/float(tC[us]) if tC[us] > 0 else 0 for us in self._usrset}
            return res
        if tw['user']['screen_name'] not in self._usrset: return
        shares = 0 if 'retweet_count' not in tw or tw['retweet_count'] is None else int(tw['retweet_count'])
        usr = tw['user']['screen_name']
        self.__share_count[usr] += shares

    def _PT_Weekday(self,tw=None):
        if self._state == "start":
            self.__weekday_count = {us:0 for us in self._usrset}
            return
        if self._state == "end":
            oC = self.__weekday_count
            tC = self.__tweet_count
            res = {us:float(oC[us])/float(tC[us]) if tC[us] > 0 else 0 for us in self._usrset}
            return res
        if tw['user']['screen_name'] not in self._usrset: return
        twDate = parsedate(tw['created_at'])
        if twDate.weekday() >= 5: return # 5 and 6 are Saturday Sunday
        self.__weekday_count[tw['user']['screen_name']] += 1
        
    def _VV_Image(self,tw=None):
        """ Requires a tweet count dictionary somewhere """
        if self._state == "start":
            self.__image_count = {us:0 for us in self._usrset}
            return
        if self._state == "end":
            vC = self.__image_count
            tC = self.__tweet_count
            res = {us:float(vC[us])/float(tC[us]) if tC[us] > 0 else 0 for us in self._usrset}
            return res
        if tw['user']['screen_name'] not in self._usrset: return
        ## Here we check video!
        if 'media' in tw['entities']:
            types = set(et['type'] for et in tw['entities']['media'])
        else: types = set()
        if 'extended_entities' in tw:
            types = types.union(set(et['type'] for et in tw['extended_entities']['media']))
        if 'photo' in types:
            self.__image_count[tw['user']['screen_name']] += 1

    def _VV_Video(self,tw=None):
        """ Requires a tweet count dictionary somewhere """
        if self._state == "start":
            self.__video_count = {us:0 for us in self._usrset}
            return
        if self._state == "end":
            vC = self.__video_count
            tC = self.__tweet_count
            res = {us:float(vC[us])/float(tC[us]) if tC[us] > 0 else 0 for us in self._usrset}
            return res
        if tw['user']['screen_name'] not in self._usrset: return
        ## Here we check video!
        if 'extended_entities' not in tw: return
        types = set(et['type'] for et in tw['extended_entities']['media'])
        if 'video' not in types and 'animated_gif' not in types: return
        self.__video_count[tw['user']['screen_name']] += 1

    def _VV_Link(self,tw=None):
        """ Requires a tweet count dictionary somewhere """
        if self._state == "start":
            self.__link_count = {us:0 for us in self._usrset}
            return
        if self._state == "end":
            lC = self.__link_count
            tC = self.__tweet_count
            res = {us:float(lC[us])/float(tC[us]) if tC[us] > 0 else 0 for us in self._usrset}
            return res
        if tw['user']['screen_name'] not in self._usrset: return
        if tw['entities']['urls'] is None or len(tw['entities']['urls']) == 0: return
        self.__link_count[tw['user']['screen_name']] += 1

    def _VV_Text(self,tw=None):
        if self._state == "start":
            self.__text_count = {us:0 for us in self._usrset}
            return
        if self._state == "end":
            txC = self.__text_count
            tC = self.__tweet_count
            res = {us:float(txC[us])/float(tC[us]) if tC[us] > 0 else 0 for us in self._usrset}
            return res
        if tw['user']['screen_name'] not in self._usrset: return
        if tw['entities']['urls'] is not None and len(tw['entities']['urls']) > 0: return
        if 'media' in tw['entities'] and tw['entities']['media'] is not None and len(tw['entities']['media']) > 0: return
        if 'extended_entities' in tw and len(tw['extended_entities']['media']) > 0: return
        self.__text_count[tw['user']['screen_name']] += 1
