import requests
from lxml import html
import os
import io
import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn import preprocessing
from sklearn.preprocessing import MinMaxScaler
import numpy as np

class GetData:
	def __init__(self, brand, make, output):
		self.brand = brand
		self.make = make
		self.headers = {'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_11_5) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/50.0.2661.102 Safari/537.36'}
		self.fOut = io.open(output, 'w', encoding = 'utf-8')
		self.fOut.write('title,year,engine_size,fuel_type,milage,price\n')
		self.model = LinearRegression()

	def standardise(self, input_):
		return str(input_).replace('\n', '').replace('\r', '').replace(',', '').strip()

	def createString(self, listKeys):
		self.string = ''
		for key in listKeys: self.string = self.string + ',' + self.standardise(str(key))
		self.string = (self.string + '\n').lstrip(',')

		return self.string

	def scrape(self):
		for i in range(0, 2000, 28):
			self.response = requests.get('https://www.donedeal.ie/cars/{}/{}?start={}'.format(self.brand, self.make, str(i)), headers = self.headers)
			self.retuned = html.fromstring(self.response.content)
			self.table = self.retuned.xpath('//*[@id="searchResultsPanel"]/ul/li')

			for j in range(len(self.table)):
				try: self.title = self.retuned.xpath('//*[@id="searchResultsPanel"]/ul/li[{}]/a/div/div[2]/div[1]/p//text()'.format(j))[0]
				except: self.title = ''

				try: self.year = self.retuned.xpath('//*[@id="searchResultsPanel"]/ul/li[{}]/a/div/div[2]/div[1]/ul[2]/li[1]//text()'.format(j))[0]
				except: self.year = ''

				try: self.motor = self.retuned.xpath('//*[@id="searchResultsPanel"]/ul/li[{}]/a/div/div[2]/div[1]/ul[2]/li[2]//text()'.format(j))[0]
				except: self.motor = ''

				self.engine_size, self.fuel = '', ''
				if self.motor != '':
					self.engine_size = self.motor.split()[0]
					self.fuel = self.motor.split()[-1]

				try: self.milage = (self.retuned.xpath('//*[@id="searchResultsPanel"]/ul/li[{}]/a/div/div[2]/div[1]/ul[2]/li[3]//text()'.format(j))[0]).split()[0]
				except: self.milage = '0'

				try: self.price = (self.retuned.xpath('//*[@id="searchResultsPanel"]/ul/li[{}]/a/div/div[2]/div[2]/div[2]/div/p//text()'.format(j)))
				except: self.price = ''

				self.price = [str(y).replace('\x80', '').replace('£', '') for y in self.price]
				self.price = [y for y in self.price if y != '']

				try: self.price = self.price[0]
				except: self.price = ''

				if self.title != '':
					self.line = self.createString([self.title, self.year, self.engine_size, self.fuel, self.milage, self.price])
					self.fOut.write(self.line)


class MultivariablePredictor:
	def __init__(self, dataset, _y, _e, _f, _m):
		self.dataset = io.open(dataset, 'r', encoding = 'utf-8').readlines()[1:]
		self._y = _y
		self._e = _e
		self._f = _f
		self._m = _m
		self.encoding = preprocessing.LabelEncoder()
		self.model = LinearRegression()

	def standardise(self, dataset):
		self.data = dataset
		self.years, self.engines, self.fuels, self.milages, self.prices = [], [], [], [], []

		for line in self.data:
			line = line.replace('\n', '')
			self.line = line.split(',')

			if self.line[3].strip() not in ('Diesel', 'Hybrid', 'Petrol', 'Electric'):
				continue

			if self.line[4].strip() == '' or self.line[4].strip() == '0':
				continue

			if self.line[5].strip() == '' or self.line[5].strip() == 'No Price':
				continue

			self.years.append(self.line[1]), self.engines.append(self.line[2]), self.fuels.append(self.line[3]), self.milages.append(self.line[4]), self.prices.append(self.line[5])
		
		self.dataframe = pd.DataFrame()
		self.dataframe['years'] = self.years
		self.dataframe['engines'] = self.engines
		self.dataframe['fuel_type'] = self.fuels
		self.dataframe['milage'] = self.milages
		self.dataframe['price'] = self.prices
		return self.dataframe

	def rescaling(self, values, headers):
		self.values = values
		for header in headers:
			self.dataset[header] = self.scaler.fit_transform(np.array(self.values[header].values))
		return self.values

	def run(self):
		self.clearData = self.standardise(self.dataset)
		self.clearData['fuel_type'] = self.encoding.fit_transform(self.clearData['fuel_type'].values)
		self.x = self.clearData.loc[:, ['years', 'engines', 'fuel_type', 'milage']]
		self.y = self.clearData.loc[:, ['price']]
		self.model.fit(self.x, self.y)

		self._f = self.encoding.transform([self._f])[0]
		self.x = pd.DataFrame([[self._y, self._e, self._f, self._m]], columns = ['years', 'engines', 'fuel_type', 'milage'])
		print ('Price you can sell your car for: ', round(self.model.predict(self.x)[0][0], 3))


# GetData(brand = 'BMW', make = '3-Series', output = 'output.csv').scrape()
MultivariablePredictor(	dataset = 'output.csv',
						_y = '2009',
						_e = '2.0',
						_f = 'Diesel',
						_m = 180000).run()