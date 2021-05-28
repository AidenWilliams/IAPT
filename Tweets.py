import tweepy
import json
from string import punctuation
import re
from nltk.corpus import stopwords
from nltk.tokenize import TweetTokenizer
import six
from google.cloud import translate_v2 as translate

"""
['arabic',
 'azerbaijani',
 'danish',
 'dutch',
 'english',
 'finnish',
 'french',
 'german',
 'greek',
 'hungarian',
 'indonesian',
 'italian',
 'kazakh',
 'nepali',
 'norwegian',
 'portuguese',
 'romanian',
 'russian',
 'spanish',
 'swedish',
 'turkish']
"""


class Tweets:
    def __init__(self, consumer_key, consumer_secret, access_token, access_token_secret):
        auth = tweepy.OAuthHandler(consumer_key, consumer_secret)
        auth.set_access_token(access_token, access_token_secret)
        self.api = tweepy.API(auth)
        self.translate_client = translate.Client.from_service_account_json('service_account.json')
        self.tweets = {}
        # dictionary of sets, very fast indeed
        self.stopwords = {
            "en": set(stopwords.words('english')),
            "fr": set(stopwords.words('french')),
            "de": set(stopwords.words('german')),
            "es": set(stopwords.words('spanish')),
            "nl": set(stopwords.words('dutch')),
            "it": set(stopwords.words('italian'))
        }
        self.punctuation = punctuation + '΄´’…“”–—―»«'

        # Tokenize: Change to lowercase, reduce length and remove handles
        self.tknzr = TweetTokenizer(preserve_case=False, reduce_len=True,
                                    strip_handles=True)  # reduce_len changes, for example, waaaaaayyyy to waaayyy.

    def reset(self):
        self.tweets = {}

    def addTweets(self, ids: list):
        tweets = self.api.statuses_lookup(ids)
        for t in tweets:
            self.tweets[str(t.id)] = t.text

    def removeTweets(self, ids: list):
        for id in ids:
            if str(id) in self:
                self.tweets.pop(str(id))

    def saveJSON(self, file_name):
        if '.json' not in file_name:
            file_name += '.json'
        to_save = {}
        for i, tweet in enumerate(self):
            to_save[i] = {'id': tweet, 'text': self[tweet]}
        json.dump(to_save, open(file_name, 'w+'))

    def loadJSON(self, file_name):
        if '.json' not in file_name:
            file_name += '.json'
        jsontweets = json.load(open(file_name))
        tweets = {jsontweets[id]['id']: jsontweets[id]['text'] for id in jsontweets}
        self.tweets.update(tweets)

    def _pp(self, tweet, lang):
        # Remove HTML special entities (e.g. &amp;)
        tweet_no_special_entities = re.sub(r'&\w*;', '', tweet)
        # Remove tickers
        tweet_no_tickers = re.sub(r'\$\w*', '', tweet_no_special_entities)
        # Remove hyperlinks
        tweet_no_hyperlinks = re.sub(r'https?://.*/\w*', '', tweet_no_tickers)
        # Remove Punctuation and split 's, 't, 've with a space for filter
        tweet_no_punctuation = re.sub(r'[' + punctuation.replace('@', '') + ']+', ' ', tweet_no_hyperlinks)
        # Remove words with 2 or fewer letters
        tweet_no_small_words = re.sub(r'\b\w{1,2}\b', '', tweet_no_punctuation)
        # Remove whitespace (including new line characters)
        tweet_no_whitespace = re.sub(r'\s\s+', ' ', tweet_no_small_words)
        # Remove single space remaining at the front of the tweet.
        tweet_no_whitespace = tweet_no_whitespace.lstrip(' ')
        tw_list = self.tknzr.tokenize(tweet_no_whitespace)
        # Remove stopwords
        list_no_stopwords = [i for i in tw_list if i not in self.stopwords[lang]]
        # Final filtered tweet
        tweet_filtered = ' '.join(list_no_stopwords)
        '''
        _pp(tweet='    RT @Amila #Test\nTom\'s newly listed Co. &amp; Mary\'s unlisted     Group to supply tech for nlTK.\nh.. $TSLA $AAPL https:// t.co/x34afsfQsh', lang='en')
        '''

        return tweet_filtered

    def preProcess(self, language):
        temp_tweets = {id: self._pp(tweet=self[id], lang=language) for id in self}
        self.tweets = temp_tweets
        return self.tweets

    def _translate(self, tweet, source_language):
        """Translates text into the target language.

        Make sure your project is allowlisted.

        source_language must be an ISO 639-1 language code.
        See https://g.co/cloud/translate/v2/translate-reference#supported_languages
        """
        if isinstance(tweet, six.binary_type):
            tweet = tweet.decode("utf-8")

        # Text can also be a sequence of strings, in which case this method
        # will return a sequence of results for each text.
        return self.translate_client.translate(tweet, target_language='en', source_language=source_language)[
            "translatedText"]

    def translate(self, language):
        temp_tweets = {id: self._translate(tweet=self[id], source_language=language) for id in self}
        self.tweets = temp_tweets
        return self.tweets

    def __repr__(self):
        """Allows the representation of Tweets as the tweets dict

        Returns
        -------
        tweets
        """
        return self.tweets

    def __iter__(self):
        """Gives functionality to iterate over tweets
        """
        for tweet in self.tweets:
            yield tweet

    def __getitem__(self, item):
        """
        Returns
        -------
        item in item at index
        """
        return self.tweets[item]

    def values(self):
        """
        Returns
        -------
        item' values
        """
        return self.tweets.values()


if __name__ == '__main__':
    from decouple import config

    tweets = Tweets(config('TWITTER_API_KEY'),
                    config('TWITTER_API_SECRET'),
                    config('TWITTER_ACCESS_TOKEN_KEY'),
                    config('TWITTER_ACCESS_TOKEN_SECRET'))
    # tweet ids taken from 2021-01-01_clean-dataset.tsv
    tweets.addTweets(['1344871397026361345', '1344871397286359041', '1344871407654731777'])
    print('Added')
    for t in tweets:
        print(t, ' ', tweets[t])
    tweets.removeTweets(['1344871397026361345', '1344871397286359041'])
    print('After removal')
    for t in tweets:
        print(t, ' ', tweets[t])

    tweets.saveJSON('test')

    print('After Saving')
    for t in tweets:
        print(t, ' ', tweets[t])
    tweets.addTweets(['1344871397026361345', '1344871397286359041'])
    print('After Adding')
    for t in tweets:
        print(t, ' ', tweets[t])

    tweets.loadJSON('test.json')
    print('After Loading')
    for t in tweets:
        print(t, ' ', tweets[t])

    tweets.preProcess('en')
    for t in tweets:
        print(t, ' ', tweets[t])
