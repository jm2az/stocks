import re
import sys
from bs4 import BeautifulSoup
from urllib2 import urlopen
from pprint import pprint as pp

class stock:
    
    def __init__(self, ticker):
        if type(ticker) is not str:
            raise TypeError('Ticker must be a string')
        self.ticker = ticker

    # Get all the necessary information for calculations
    def get_info(self):
        self.get_stock_info()
        self.get_industry_info()
        self.get_risk_free_rate()
        self.get_snp_rate()
        self.calculate_attributes()

    # Returns a dict of attributes and their values
    def get_attributes(self):
        atts = {}
        atts['name'] = self.name
        atts['ticker'] = self.ticker.upper()
        atts['cur_price'] = self.cur_price
        atts['target'] = self.target
        atts['beta'] = self.beta
        atts['div_cash'] = self.div_cash
        atts['div_percent'] = self.div_percent
        atts['risk_free_rate'] = self.risk_free_rate
        atts['snp_rate'] = self.snp_rate
        atts['coe'] = self.coe
        atts['npv'] = self.npv
        atts['roi'] = self.roi
        atts['irr'] = self.irr
        atts['url'] = self.url
        atts['sector'] = self.sector
        atts['industry'] = self.industry
        return atts

    # Get name, current price, target, beta, and dividends from Main Page
    def get_stock_info(self):
        uri = 'http://finance.yahoo.com/q?s={}'.format(self.ticker)
        self.url = uri
        soup = get_soup(uri)
        tds = soup.find_all('td')
        self.target = float(tds[6].string)
        beta_text = tds[7].string
        self.beta = 1 if beta_text == 'N/A' else float(beta_text)
        div_text = tds[16].string
        dividends = re.split(' ', div_text)
        try:
            self.div_cash = float(dividends[0])
        except:
            self.div_cash = 0.0
        try:
            self.div_percent = float(re.sub('[\(\)\%]', '', dividends[1])) / 100
        except: 
            self.div_percent = 0.0
        self.cur_price = float(tds[3].string)
        h2s = soup.find_all('h2')
        self.name = str(re.split('\(', h2s[2].string)[0].strip().replace(',', ''))

    # Get industry info
    def get_industry_info(self):
        uri = 'http://finance.yahoo.com/q/in?s={}+Industry'.format(self.ticker)
        soup = get_soup(uri)
        tds = soup.find_all('td')[8].findChildren()
        sector = str(tds[10].string)
        industry = str(tds[14].string)
        self.sector = sector
        self.industry = industry
 
    # Calculates cost of equity, tax rate, cost of debt, WACC, NPV, and ROI
    def calculate_attributes(self):
        # Cost of equity via CAPM
        self.coe = self.risk_free_rate + self.beta * (self.snp_rate - self.risk_free_rate)
        self.npv = (self.target + self.div_cash) / (1 + self.coe) - self.cur_price
        self.roi = self.npv / self.cur_price
        self.irr = (self.target + self.div_cash) / (self.cur_price) - 1

    # Get risk free rate
    def get_risk_free_rate(self):
        uri = 'http://money.cnn.com/data/bonds/'
        soup = get_soup(uri)
        spans = soup.find_all('span', {'stream' : 'last_572971'})
        self.risk_free_rate = float(spans[0].text) / 100

    # Get S&P rate
    def get_snp_rate(self):
        uri = 'http://money.cnn.com/data/markets/sandp/'
        soup = get_soup(uri)
        parent_div = soup.find('div', {'id' : 'wsod_quoteRight'})
        self.snp_rate = float(parent_div.findChildren()[13].text.replace('+', '').replace('%', '')) / 100


# Used to get the soup of the stock on Yahoo Finance
def get_soup(uri):
    try:
        response = urlopen(uri)
        html = response.read()
        soup = BeautifulSoup(html)
    except: # Retry if failed
        response = urlopen(uri)
        html = response.read()
        soup = BeautifulSoup(html)
    return soup

# Converts market capitalization into int of proper magnitude
def convert_mark_cap(value):
    if value == 'N/A':
        return 0
    size = len(value)
    mult = value[size-1]
    sci = float(value[:size-1])
    return sci * {'K' : 1000, 'M' : 1000000, 'B' : 1000000000}[mult]

# Converts negative accounting numbers into negative ints or floats
def check_for_negative(value):
    if re.search('\(', value):
        value = '-' + value
    value = re.sub('[\(\),]', '', value)
    if '.' in value:
        return float(value)
    return int(value)
