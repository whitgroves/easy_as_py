from nltk.tokenize import sent_tokenize, word_tokenize
from nltk.corpus import stopwords
from string import punctuation
from collections import defaultdict
from heapq import nlargest
import urllib.request as urlreq
from bs4 import BeautifulSoup

class FreqeuencySummarizer:
	
	# Works with a frequency outside of min_cut and max_cut are ignored.
	def __init__(self, min_cut=0.1, max_cut=0.9):
		self._min_cut = min_cut
		self._max_cut = max_cut
		self._stopwords = set(stopwords.words('english') + list(punctuation))
	
	# Input: A list of sentences.
	# Output: A dictionary of {word:frequency} pairs.
	def _compute_frequencies(self, word_sent):
		freq = defaultdict(int)
		for sent in word_sent:
			for word in sent:
				if word not in self._stopwords:
					freq[word] += 1
		
		# Normalize frequencies to the largest value so they fall between 0-1.
		# Words outside of the max and min cut are also removed in this step.
		max_n = float(max(freq.values()))
		for word in list(freq.keys()):
			freq[word] = freq[word]/max_n
			if freq[word] >= self._max_cut or freq[word] <= self._min_cut:
				del freq[word]
		
		return freq
		
	# Input: Text and the number of sentences the summary should contain.
	# Output: A summary of the text with the specified number of sentences.
	def summarize(self, text, n):
		sentences = sent_tokenize(text)
		assert n <= len(sentences) # Sanity check.
		word_sent = [word_tokenize(sentence.lower()) for sentence in sentences]
		self._freq = self._compute_frequencies(word_sent)
		
		# Calculate the rankings based on word frequencies.
		rankings = defaultdict(int)
		for i, sent in enumerate(word_sent):
			for word in sent:
				if word in self._freq:
					rankings[i] += self._freq[word]
					
		# Find the n most important sentences based on the ranking above.
		sent_idx = nlargest(n, rankings, key=rankings.get)
		
		return [sentences[j] for j in sent_idx]

# Input: A WaPo article url.
# Output: A (title, body) tuple with only text from the article.
def get_wapo_text(url):
	print('Fetching article from url:',url)
	page = urlreq.urlopen(url).read().decode('utf8')
	soup = BeautifulSoup(page, 'html.parser')
	
	# WaPo conveniently wraps their article text in <article> tags.
	text = ''.join(map(lambda p:p.text, soup.find_all('article')))
	
	return soup.title.text, text

# Input WaPo url from command line, then summarize the article into 3 sentences.
wapoUrl = input('Please enter a Washington Post url: ')
urlText = get_wapo_text(wapoUrl)
fs = FreqeuencySummarizer()
summary = fs.summarize(urlText[1], 3)
print(urlText[0])
for sent in summary:
	print(sent)