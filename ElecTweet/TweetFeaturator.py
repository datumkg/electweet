import datetime as dt
import re
from dateutil.parser import parse as parsedate
from collections import defaultdict
from statistics import mean,stdev
from textblob import TextBlob


def is_outlier(elm,m,sd):
    return abs(elm - m) <= 3*sd

def outlier_count(elms):
    mn = mean(elms)
    sd = stdev(elms)
    return sum(1 if is_outlier(e,mn,sd) else 0 for e in elms)

def mean_minus_outliers(elms):
    mn = mean(elms)
    sd = stdev(elms)
    return sum(e if not is_outlier(e,mn,sd) else 0 for e in elms) / (len(elms) - outlier_count(elms))
    pass

twPCount = defaultdict(lambda :0)

def twitterPolarity(txt):
    keyWords = {'l-)':1,':-}':1,';;-)':1,'=]':1,':)':1,':-)':1,
                '[-(':-1,':-((':-1,':(':-1,'T T':-1,':-[':-1,'T_T':-1,
                """
                'lol':1,'dbeyr':-1,'ilum':1,'iwiam':-1,'x-d':1,'iyqkewl':1,'nfs':-1,'iwalu':1,
                'h8ttu':-1,'koc':1,'gtfo': -1,'#cold': -0.282,'#fab': 0.812,'#ffoe': -0.25,'#leadership': 0.484,'#whoops': 0.188,
                '-.-': 0.0,
                '-_-': 0.062,
                ":'(": -0.562,
                ":')": 0.218,
                ':(': -0.454,
                ':-d': -0.156,
                ':/': -0.374,
                ':]': 0.422,
                ':d': -0.078,
                ':o': 0.032,
                ':p': 0.344,
                ':s': -0.094,
                ':|': -0.062,
                ';)': 0.312,
                ';d': -0.266,
                '<33': 0.626,
                '!':0.5,
                '???':-0.2,
                'plz':0.2,
                'aww': 0.454,
                'bitches': -0.984,
                'cant waitt': 0.516,
                'chillin': 0.532,
                'd:': -0.172,
                'ew': -0.296,
                'eww': -0.484,
                'fml': -0.468,
                "g'morning": 0.656,
                'gooood': 0.718,
                'heey': 0.046,
                'hi-5': 0.75,
                'n00b': -0.766,
                'no biggie': 0.376,
                """:1,
                '<3': 0.626,
                '=(': -0.5,
                '😄':0.5, '😃':0.5, '😀':0.5,'😊':0.5,'☺':0.5,
                '😉':0.5,'😍':0.5,'😘':0.5,'😚':0.5,'😗':0.5,'😙':0.5,'😜':0.5,
                '😝':0.5,'😛':0.5,'😂':0.5,'😆':0.5,'😋':0.5,'💛':0.5,'💙':0.5,
                '💜':0.5,'💚':0.5,'💗':0.5,'💓':0.5,'💕':0.5,'💖':0.5,'💞':0.5,'👍':0.5,
                '😒':-0.5,'😞':-0.5,'😣':-0.5,'😥':-0.5,'😠':-0.5,'😡':-0.5,'😟':-0.5,
                '😕':-0.5,'😬':-0.5,'👎':-0.5,'😰':-0.5,
                """'no mms': -0.124,
                'ouch': -0.344,
                'promoz': 0.406,
                'smexy': 0.36,
                'smfh': -0.406,
                'smilin': 0.688,
                'teehee': 0.328,
                'th*nks': 0.438,
                'twitterverse': 0.39,
                'wanna': 0.266,
                'woo': 0.578,
                'woohoo': 0.796,
                'wtf': -0.532,
                'xxx': 0.078,""":1,
                '💖':0.5,'👍':0.5,'#love':0.5,'❤':0.5,'😍':0.8,'😂':0.7,'😎':0.6,
                '😭':-0.5,'😔':-0.3,'😩':-0.4,
                """'luv':0.5,'thang':0.5,
                'yaaay': 0.672,
                'yay': 0.672,
                'yaay': 0.766,
                #'yo': -0.046,
                'yuck': -0.704""":1}
    sum = 0
    for k,e in keyWords.items():
        if k in txt.lower(): 
            sum += 1 if e > 0 else -1
            twPCount[k] += 1
    return sum #/len(keyWords)

class Featurator():
    def __init__(self,usrset,mainCmakers=None):
        #self._main_carmakers = ['Audi','Toyota','BMWUSA','VolvoCarUSA','NissanUSA','Jeep']
        self._main_carmakers = []
        if mainCmakers is not None:
            self._main_carmakers = mainCmakers
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
        self.__rep_count = defaultdict(lambda:0)
        self.__rep_polarity = defaultdict(lambda:0)
        self.__tw_polarity = defaultdict(lambda:0)
        self.__rep_subjectiv = defaultdict(lambda:0)
        twts_dic = self.__twts_dic
        usrset = self._usrset
        self._convos = []
        absent_twts = []
        added = set()
        for tw in reversed(twts):
            if ('in_reply_to_status_id' in tw and tw['in_reply_to_status_id'] is not None and
                tw['in_reply_to_screen_name'] in usrset):
                self.__rep_count[tw['in_reply_to_status_id']] += 1
                tPol = twitterPolarity(tw['text'])
                tb = TextBlob(tw['text'])
                self.__rep_polarity[tw['in_reply_to_status_id']] += tb.sentiment.polarity
                self.__rep_subjectiv[tw['in_reply_to_status_id']] += tb.sentiment.subjectivity
                self.__tw_polarity[tw['in_reply_to_status_id']] += tPol

    def feature_names(self):
        return list(self._per_tweet_features.keys())+self._main_carmakers

    def tweet_features(self,tw):
        if self.get_state() != 'running':
            raise Exception("To initialize must be in 'start' state")
        if tw['user']['screen_name'] in self._usrset:
            self.__tweet_count[tw['user']['screen_name']] += 1
        else:
            return

        res = {}
        for key,feat in self._per_tweet_features.items():
            res[key] = feat(tw)
        for cmaker in self._main_carmakers:
            res[cmaker] = 0
            if tw['user']['screen_name'] == cmaker: res[cmaker] = 1
        return res

    def initialize(self,twts):
        if self.get_state() != 'start':
            raise Exception("To initialize must be in 'start' state")
        self.__tweet_count = {us:0 for us in self._usrset}
        for key, feat in self._per_tweet_features.items():
            feat(None)
        self.build_convos(twts)
        self.set_state('running')
    
    def configure_features(self):
        #self._per_tweet_features['MT_V'] = self._VV_Video #
        #self._per_tweet_features['MT_I'] = self._VV_Image # 
        #self._per_tweet_features['MT_L'] = self._VV_Link #
        #self._per_tweet_features['MT_T'] = self._VV_Text #

        self._per_tweet_features['T_D'] = self._PT_Weekday #
        self._per_tweet_features['T_H'] = self._PT_PeakHour #
        #self._per_tweet_features['T_PK'] = self._PT_MixPeak #
        self._per_tweet_features['C2B_FAV'] = self._EG_Favs #

        self._per_tweet_features['C2B_RT'] = self._EG_Retweets #
        self._per_tweet_features['B2C_REP'] = self._OEG_ReProp #
        self._per_tweet_features['B2C_TTW'] = self._UI_TimeTweet #
        self._per_tweet_features['B2C_TNTW'] = self._UI_TimeNonReply #
        self._per_tweet_features['B2C_RERET'] = self._MX_TimeReplies #
        #self._per_tweet_features['B2C_RT'] = self._OEG_Retweet #
        self._per_tweet_features['B2C_VV'] = self._B2C_Vividness
        self._per_tweet_features['B2C_IT'] = self._B2C_Interactivity

        #self._per_tweet_features['B2C_HT'] = self._B2C_Hashtags
        self._per_tweet_features['B2C_MT'] = self._B2C_Mentions

        #self._per_tweet_features['MT-Inter'] = self._MT_Inter
        #self._per_tweet_features['MT_HI'] = self._IT_HighInteract #
        #self._per_tweet_features['MT_LI'] = self._IT_LowInteract #

        #self._per_tweet_features['C2B_RELI'] = self._VV_RELowInteract
        #self._per_tweet_features['C2B_REHI'] = self._VV_REHiInteract

        #self._per_tweet_features['CT_I'] = self._CT_Info #
        #self._per_tweet_features['CT_E'] = self._CT_Enter #

        #self._per_tweet_features['TW_ID'] = self._TW_ID

        #self._user_features['B2C_FL'] = self._OEG_Followees #
        #self._user_features['C2B_FL'] = self._EG_Followers #
        #self._user_features['B2C_TW'] = self._UI_NumTweets #

        self._per_tweet_features['B2C_RET'] = self._MX_RepTime # 

        self._per_tweet_features['U_CM'] = self._U_carmaker
        #self._per_tweet_features['T_SP'] = self._T_SentimentP
        #self._per_tweet_features['T_SS'] = self._T_SentimentS

        self._per_tweet_features['C2B_RE'] = self._MX_Replies #### TODOOOO
        #self._per_tweet_features['C2B_SS'] = self._C2B_SSubject #### TODOOOO
        #self._per_tweet_features['C2B_SP'] = self._C2B_SPolar #### TODOOOO
        #self._per_tweet_features['C2B_STP'] = self._C2B_TWPolar
        #self._per_tweet_features['C2B_PTS'] = self._C2B_PTSubjectivity
        #self._per_tweet_features['C2B_PTP'] = self._C2B_PTPolarity
        #self._per_tweet_features['C2B_PTTP'] = self._C2B_PTTWPolar
        #self._per_tweet_features['C2B_DRE'] = self._MX_GotReply #### TODOOOO
        """
        self._convo_features['B2C_CL'] = self._MX_ConvoLen
        self._convo_features['B2C_REC'] = self._MX_ConvoReps
        self._convo_features['B2C_RED'] = self._MX_RepDiff
        """

    def _TW_ID(self,tw=None):
        if tw is None: return "."
        return tw['id']

    def _C2B_PTTWPolar(self,tw=None):
        if tw is None: return "."
        if 'in_reply_to_status_id' not in tw or tw['in_reply_to_status_id'] is None: return "."
        pId = tw['in_reply_to_status_id']
        if pId not in self.__twts_dic: return "."
        pTw = self.__twts_dic[pId]
        return twitterPolarity(pTw['text'])

    def _C2B_PTPolarity(self,tw=None):
        if tw is None: return "."
        if 'in_reply_to_status_id' not in tw or tw['in_reply_to_status_id'] is None: return "."
        pId = tw['in_reply_to_status_id']
        if pId not in self.__twts_dic: return "."
        pTw = self.__twts_dic[pId]
        tb = TextBlob(pTw['text'])
        return tb.sentiment.polarity

    def _C2B_PTSubjectivity(self,tw=None):
        if tw is None: return "."
        if 'in_reply_to_status_id' not in tw or tw['in_reply_to_status_id'] is None: return "."
        pId = tw['in_reply_to_status_id']
        if pId not in self.__twts_dic: return "."
        pTw = self.__twts_dic[pId]
        tb = TextBlob(pTw['text'])
        return tb.sentiment.subjectivity

        """
    def _B2C_Interactivity(self,tw=None):
        if self._state == 'start':
            self.___hi_keywords = ['contest','sweepstakes','chance to win','gift','quiz','prize']
            self.___li_keywords = ['visit ','share','reply','call us','call our','customer service',
                                   'follow us','vote','poll','tell us','check out','dm ']
            return
        if tw is None: return "."
        hiSc = self._IT_HighInteract(tw)
        liSc = self._IT_LowInteract(tw)
        lnkSc = self._VV_Link(tw)
        if hiSc == 1: return 3
        if liSc == 1: return 2
        if lnkSc == 1: return 1
        return 0
        """

    def _B2C_Interactivity(self,tw=None):
        if self._state == 'start':
            self.___hi_keywords = ['contest','sweepstakes','chance to win','gift','quiz','prize']
            self.___li_keywords = ['visit ','share','reply','call us','call our','customer service',
                                   'follow us','vote','poll','tell us','check out','dm ']
            return
        if tw is None: return "."
        is_txt = self._VV_Text(tw)
        is_lnk = self._VV_Link(tw)
        is_vid = self._VV_Video(tw)
        is_img = self._VV_Image(tw)
        #htgs = self._per_tweet_features['B2C_HT'](tw)
        liSc = self._IT_LowInteract(tw)
        hiSc = self._IT_HighInteract(tw)
        if is_vid == 1: return 2
        if is_lnk == 1: return 2
        if hiSc == 1: return 2
        if liSc == 1: return 1
        #if htgs > 0: return 1
        if is_img == 1: return 0
        if is_txt == 1: return 0
        return "."

    def _B2C_Vividness(self,tw=None):
        if tw is None: return "."
        is_txt = self._VV_Text(tw)
        is_lnk = self._VV_Link(tw)
        is_vid = self._VV_Video(tw)
        is_img = self._VV_Image(tw)
        if is_vid == 1: return 3
        if is_lnk == 1: return 2
        if is_img == 1: return 1
        if is_txt == 1: return 0
        return "."

    def _T_SentimentP(self,tw=None):
        if self._state == 'start' or self._state == 'end': return
        tb = TextBlob(tw['text'])
        return tb.sentiment.polarity

    def _T_SentimentS(self,tw=None):
        if self._state == 'start' or self._state == 'end': return
        tb = TextBlob(tw['text'])
        return tb.sentiment.subjectivity

    def _U_carmaker(self,tw=None):
        if self._state == 'start' or self._state == 'end': return
        return tw['user']['screen_name']

    def _B2C_Hashtags(self,tw=None):
        if tw is None: return None
        return len(tw['entities']['hashtags']) if 'hashtags' in tw['entities'] else 0

    def _B2C_Mentions(self,tw=None):
        if tw is None: return None
        #return len(tw['entities']['user_mentions']) if 'user_mentions' in tw['entities'] else 0
        mentions = len(tw['entities']['user_mentions']) if 'user_mentions' in tw['entities'] else 0
        return  1 if mentions > 0 else 0

    def _CT_Enter(self,tw=None):
        if self._state == 'start': return
        if self._state == 'end': return
        if tw['user']['screen_name'] not in self._usrset: return
        if 'in_reply_to_status_id' in tw and tw['in_reply_to_status_id'] is not None: return 1
        rex = self.___info_regexp
        kwds = self.___info_keywords
        score = 0
        if rex.match(tw['text']) is not None: score += 1
        if any(kw.lower() in tw['text'].lower() for kw in kwds): score += 1
        if score < 1: return 1
        return 0

    def _CT_Info(self,tw=None):
        if self._state == 'start':
            self.___info_regexp = re.compile('.*[Tt]he (new )?[#@]?[A-Z0-9]')
            self.___info_keywords = ['Toyota','VW','Mercedes-Benz','Volvo','Lexus','Infiniti','BMW','Audi',
                                     'Ford','MB','Hyundai','Nissan','MINI','Jeep','FIAT','Volkswagen']
            return
        if self._state == 'end':
            return
        if tw['user']['screen_name'] not in self._usrset: return
        if 'in_reply_to_status_id' in tw and tw['in_reply_to_status_id'] is not None: return 0
        rex = self.___info_regexp
        kwds = self.___info_keywords
        score = 0
        if rex.match(tw['text']) is not None: score += 1
        if any(kw in tw['text'].lower() for kw in kwds): score += 1
        if score < 1: return 0
        return 1

    def _PT_MixPeak(self,tw=None):
        if self._state == 'start': return
        if self._state == 'end': return
        pkHr = self._PT_PeakHour(tw)
        wkDy = self._PT_Weekday(tw)
        res = 0
        #if (pkHr, wkDy) == (2, 2): res = 3
        #if (pkHr,wkDy) == (2,1): res = 2
        #if (pkHr,wkDy) == (1,2): res = 1
        #return res

    def _PT_PeakHour(self,tw=None):
        if self._state == 'start':
            hrRank = [9, 10, 8, 7, 11, 6, 5, 12, 4, 3, 2, 13, 1,
                      0, 14, 23, 15, 22, 21, 20, 19, 16, 18, 17]
            self.___hrsRanks = {e:int(i*2/len(hrRank)) for i,e in enumerate(hrRank)}
            #self.___peakhrs = set([15,16,17,18,19,20])
            self.___peakhrs = set(range(8,18))
            return
        if self._state == 'end':
            return
        if tw['user']['screen_name'] not in self._usrset: return "."
        #twTime = parsedate(tw['created_at']).time().hour
        hour = parsedate(tw['created_at']).time().hour
        return 1 if hour in self.___peakhrs else 0
        #if twTime in self.___peakhrs: return 1
        #return self.___hrsRanks[twTime]

    def _IT_HighInteract(self,tw=None):
        if self._state == 'end' or self._state == 'start': return

        if tw['user']['screen_name'] not in self._usrset: return 0
        lwCase = tw['text'].lower()
        usr = tw['user']['screen_name']
        if any(kw in lwCase for kw in self.___hi_keywords):
            return 1 # High interactive
        return 0

    def _IT_LowInteract(self,tw=None):
        if self._state == 'start':
            return
        if self._state == 'end':
            return
        if tw['user']['screen_name'] not in self._usrset: return 0
        lwCase = tw['text'].lower()
        usr = tw['user']['screen_name']
        if any(kw in lwCase for kw in self.___li_keywords) or ('?' in lwCase and tw['in_reply_to_user_id'] is None):
            return 1 # Low interactive
        return 0

    def _MX_Replies(self,tw=None):
        if self._state == 'start':
            return
        if self._state == 'end':
            return
        if tw['user']['screen_name'] not in self._usrset: return 0
        if tw['id'] in self.__rep_count: return self.__rep_count[tw['id']]
        return 0

    def _C2B_SSubject(self,tw=None):
        if self._state == 'start':
            return
        if self._state == 'end':
            return
        if tw['user']['screen_name'] not in self._usrset: return "."
        if tw['id'] not in self.__rep_count: return "."
        reps = self.__rep_count[tw['id']]
        tSubject = self.__rep_subjectiv[tw['id']]
        return tSubject/reps

    def _C2B_SPolar(self,tw=None):
        if self._state == 'start':
            return
        if self._state == 'end':
            return
        if tw['user']['screen_name'] not in self._usrset: return "."
        if tw['id'] not in self.__rep_count: return "."
        reps = self.__rep_count[tw['id']]
        tPolar = self.__rep_polarity[tw['id']]
        return tPolar/reps

    def _C2B_TWPolar(self,tw=None):
        if self._state == 'start':
            return
        if self._state == 'end':
            return
        if tw['user']['screen_name'] not in self._usrset: return "."
        if tw['id'] not in self.__rep_count: return "."
        reps = self.__rep_count[tw['id']]
        tPolar = self.__tw_polarity[tw['id']]
        return tPolar/reps

    def _MX_GotReply(self,tw=None):
        if self._state == 'start':
            return
        if self._state == 'end':
            return
        return 0 if self._MX_Replies(tw) == 0 else 1
        
    def _MX_RepTime(self,tw=None):
        if self._state == 'start':
            return
        if self._state == 'end':
            return
        if 'in_reply_to_status_id' not in tw or tw['in_reply_to_status_id'] is None: return "."
        end = parsedate(tw['created_at'])
        startw = self.__twts_dic.get(tw['in_reply_to_status_id'])
        if startw is None: return "."
        start = parsedate(startw['created_at'])
        dif = end - start
        return dif.total_seconds()

    def _MT_Inter(self,tw=None):
        if self._state == "start": return
        if self._state == "end":
            return

    def _OEG_Followees(self,tw=None):
        if self.get_state() in ["start","end"]:
            return
        if tw['user']['screen_name'] not in self._usrset: return 0
        usrs = self._usrset
        return tw['user']['friends_count']

    def _EG_Followers(self):
        if self.get_state() in ["start","end"]:
            return
        if tw['user']['screen_name'] not in self._usrset: return 0
        usrs = self._usrset
        return tw['user']['followers_count']

    def _OEG_Retweet(self,tw=None):
        if self._state == "start":
            return
        if self._state == "end":
            return
        #if tw['user']['screen_name'] not in self._usrset: return 0
        if 'retweeted_status' not in tw or tw['retweeted_status'] is None: return 0
        return 1

    def _MX_TimeReplies(self,tw=None):
        if self._state == "start":
            self.__last_yesreply = {us:None for us in self._usrset}
            return
        if self._state == "end":
            return
        if tw['user']['screen_name'] not in self._usrset: return
        oC = self.__last_yesreply
        usr = tw['user']['screen_name']
        lTw = oC[usr]
        if (('quoted_status_id_str' in tw and tw['quoted_status_id_str'] is not None) or
            ('in_reply_to_screen_name' in tw and tw['in_reply_to_screen_name'] is not None) or
            ('in_reply_to_status_id' in tw and tw['in_reply_to_status_id'] is not None)):
            oC[usr] = tw
        if lTw is None: return "."
        if lTw['id'] == tw['id']: return "."
        prev = parsedate(lTw['created_at'])
        latt = parsedate(tw['created_at'])
        delta = latt - prev
        if delta.total_seconds() == 0 and tw['text'] == lTw['text']: return "."
        return delta.total_seconds()

    def _UI_TimeNonReply(self,tw=None):
        if self._state == "start":
            self.__last_nonreply = {us:None for us in self._usrset}
            self.__nonreply_times = {us:[] for us in self._usrset}
            return
        if self._state == "end":
            return
        if tw['user']['screen_name'] not in self._usrset: return
        oC = self.__last_nonreply
        usr = tw['user']['screen_name']
        lTw = oC[usr]
        if (not (('quoted_status_id_str' in tw and tw['quoted_status_id_str'] is not None) or
                 ('in_reply_to_screen_name' in tw and tw['in_reply_to_screen_name'] is not None) or
                 ('in_reply_to_status_id' in tw and tw['in_reply_to_status_id'] is not None))):
            oC[usr] = tw
        if lTw is None: return "."
        if lTw['id'] == tw['id']: return "."
        prev = parsedate(lTw['created_at'])
        latt = parsedate(tw['created_at'])
        delta = latt - prev
        if delta.total_seconds() == 0 and tw['text'] == lTw['text']: return "."
        return delta.total_seconds()

    def _UI_NumTweets(self,tw=None):
        if self._state in ["start","end"]: return
        if tw['user']['screen_name'] not in self._usrset: return 0
        return tw['user']['statuses_count']

    def _UI_TimeTweet(self,tw=None):
        if self._state == "start":
            self.__last_tweet = {us:None for us in self._usrset}
            return
        if self._state == "end":
            return
        if tw['user']['screen_name'] not in self._usrset: return "."
        oC = self.__last_tweet
        usr = tw['user']['screen_name']
        lTw = oC[usr]
        oC[usr] = tw
        if lTw is None: return "."
        if lTw['id'] == tw['id']: return "."
        prev = parsedate(lTw['created_at'])
        latt = parsedate(tw['created_at'])
        delta = latt - prev
        if delta.total_seconds() == 0 and tw['text'] == lTw['text']: return "."
        return delta.total_seconds()
        

    def _OEG_ReProp(self,tw=None):
        if self._state == "start":
            return
        if self._state == "end": return
        if tw['user']['screen_name'] not in self._usrset: return
        if (not (('quoted_status_id_str' in tw and tw['quoted_status_id_str'] is not None) or
                 ('in_reply_to_screen_name' in tw and tw['in_reply_to_screen_name'] is not None) or
                 ('in_reply_to_status_id' in tw and tw['in_reply_to_status_id'] is not None))):
            return 0
        return 1
    

    def _EG_Favs(self,tw=None):
        if self._state == "start": return
        if self._state == "end": return
        if tw['user']['screen_name'] not in self._usrset: return 0
        favs = 0 if 'favorite_count' not in tw or tw['favorite_count'] is None else int(tw['favorite_count'])
        return favs

    def _EG_Retweets(self,tw=None):
        if self._state == "start":
            return
        if self._state == "end":
            return
        if tw['user']['screen_name'] not in self._usrset: return 0
        shares = 0 if 'retweet_count' not in tw or tw['retweet_count'] is None else int(tw['retweet_count'])
        usr = tw['user']['screen_name']
        return shares 

    def _PT_Weekday(self,tw=None):
        if self._state == "start":
            #self.__dayRank = {e:i for i,e in enumerate([6,5,0,3,4,2,1])}
            rankWeek = [5, 6, 4, 3, 2, 1, 0]
            self.__dayRank = {e:int(i*3/len(rankWeek)) for i,e in enumerate(rankWeek)}
            return
        if self._state == "end":
            return
        if tw['user']['screen_name'] not in self._usrset: return "."
        twDate = parsedate(tw['created_at'])
        if twDate.weekday() >= 5: return 0 # 5 and 6 are Saturday Sunday
        return 1
        #return twDate.weekday()
        #return self.__dayRank[twDate.weekday()]
        
    def _VV_Image(self,tw=None):
        """ Requires a tweet count dictionary somewhere """
        if self._state == "start":
            return
        if self._state == "end":
            return 
        if tw['user']['screen_name'] not in self._usrset: return 0
        ## Here we check video!
        if 'media' in tw['entities']:
            types = set(et['type'] for et in tw['entities']['media'])
        else: types = set()
        if 'extended_entities' in tw:
            types = types.union(set(et['type'] for et in tw['extended_entities']['media']))
        if 'photo' in types:
            return 1
        return 0

    def _VV_Video(self,tw=None):
        """ Requires a tweet count dictionary somewhere """
        if self._state == "start":
            return
        if self._state == "end":
            return
        if tw['user']['screen_name'] not in self._usrset: return 0
        ## Here we check video!
        if 'extended_entities' not in tw: return 0
        types = set(et['type'] for et in tw['extended_entities']['media'])
        if 'video' not in types and 'animated_gif' not in types: return 0
        return 1

    def _VV_Link(self,tw=None):
        """ Requires a tweet count dictionary somewhere """
        if self._state == "start":
            return
        if self._state == "end":
            return
        if tw['user']['screen_name'] not in self._usrset: return 0
        if tw['entities']['urls'] is None or len(tw['entities']['urls']) == 0: return 0
        return 1

    def _VV_Text(self,tw=None):
        if self._state == "start":
            return
        if self._state == "end":
            return
        if tw['user']['screen_name'] not in self._usrset: return 0
        if tw['entities']['urls'] is not None and len(tw['entities']['urls']) > 0: return 0
        if 'media' in tw['entities'] and tw['entities']['media'] is not None and len(tw['entities']['media']) > 0: return 0
        if 'extended_entities' in tw and len(tw['extended_entities']['media']) > 0: return 0
        return 1
