'''
class to scrap from the website www.automobile.it
'''

# Useful imports
from selenium import webdriver
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import numpy as np
from bs4 import BeautifulSoup
import urllib
import os
import pandas as pd
from requests import get
from contextlib import closing

'''
import cPickle
import urllib
import requests
'''


class Automobile():
	def __init__(self,csvpath=None):
		self.AUTOMOBILE_FRONTPAGE = 'https://www.automobile.it/'
		self.pt1 = 'usate/'
		self.pt2 ='?dove=milano_comune'
		self.pt3 = '&immatricolazione=2005'
		self.pt4 = '&km_max=350000_km'
		self.pt5 = '&prezzo_a=100000'
		self.pt6 = '&tipo_di_usato=auto_d_epoca,aziendale,dimostrativo'
		# location of chromedriver
		chromedriver = "/Users/Luca/Documents/Python/chromedriver"
		# Create a browser
		self.opts = Options() 
		self.opts.headless = True
		self.browser = webdriver.Chrome(options=self.opts,executable_path = chromedriver)
		work_dir = os.getcwd()
		self.img_dir = work_dir + "/car_images"
		try:
		   os.mkdir(img_dir)
		except:
		    pass
		self.full_car_df = pd.DataFrame()


	# opens a Chrome browser and connects to the webpage 
	def connect(self):
		URL = self.AUTOMOBILE_FRONTPAGE + self.pt1 + self.pt2 + self.pt3 + self.pt4 + self.pt5 + self.pt6;
		self.browser.get(URL)

	# returns the number of available results and pages
	def number_of_results(self):
		numeri = self.browser.find_element(By.XPATH,"/html/body/main/section[2]/div/div/footer/div[2]/div/nav/div[1]")
		n_results = int(numeri.text.split(" ")[0])
		n_pages = int(numeri.text.split(" ")[3])
		return n_results, n_pages

	# return the list of links to each car founded
	def get_links(self, test=True):
		link_list = [];
		results_on_page = self.browser.find_elements_by_class_name("search-item__title")
		n_results, n_pages = self.number_of_results()

		if test:
			n_pages = 2
		else:
			pass
		for page in range(n_pages):
			print("Getting links from page {}".format(page))
			URL = self.AUTOMOBILE_FRONTPAGE + self.pt1 + "page-" + str(page) + self.pt2 + self.pt3 + self.pt4 + self.pt5 + self.pt6
			self.browser.get(URL)
			self.browser.implicitly_wait(2)
			results_on_page = self.browser.find_elements_by_class_name("search-item__title")
			for (i,result) in enumerate(results_on_page):
				print("{:4d}%".format(int((i+1)/len(results_on_page)*100)))
				
				link_list.append([el for el in result.find_element_by_tag_name("div").get_attribute("data-link").split("/") if len(el)>0])

		print("Links gathered")

		return link_list

	def page_scraping(self,link):
		# connect on the link
		URL = self.AUTOMOBILE_FRONTPAGE + link[0] + "/" + link[1]

		response = simple_get(URL)
		soup = BeautifulSoup(response, 'html.parser')

		# Save the image of the  car
		self.save_image(flag=False)
		vehicle_snapshot = vehicle_snapshot(soup)
		# vehicle_data = vehicle_data(soup)
		# vehicle_features = vehicle_features(soup)

		name = soup.find(class_="vip__header__title" ).text
		location = soup.find(class_="vip__location__link").text
		iD = link[1]
		price = int(soup.find(class_="vip__price__title").text.replace(".","").split(" ")[-1])
		immatriculationMonth = vehicle_snapshot[0][0]
		immatriculationYear = int(vehicle_snapshot[0][1])
		Km = int(vehicle_snapshot[1][0].replace[".",""].split(" ")[0])
		engineKW = int(v_snap[2][0].split(" ")[0])
		engineCV = int(v_snap[2][1].strip("()").split(" ")[0])
		fuelType = vehicle_snapshot[3][0]
		drivetrain = vehicle_snapshot[4][0]

		#feature_names = ["name", "location","iD","price","immatriculationMonth","immatriculationYear","Km","engineKW","engineCV","fuelType","drivetrain"]

		temp_df = pd.DataFrame({
			"name" : name,
			"location" : location,
			"iD" : iD,
			"price" : price,
			"immatriculationMonth" : immatriculationMonth,
			"immatriculationYear" : immatriculationYear,
			"Km" : Km,
			"engineKW" : engineKW,
			"engineCV" : engineCV,
			"fuelType" : fuelType,
			"drivetrain" : drivetrain
			})

		self.full_car_df = pd.concat([self.full_car_df ,temp_df],axis=0)
    


	def save_image(self,flag):
		if flag:
			try: 
				self.browser.find_element_by_xpath("/html/body/div[4]/div/div/div/a").click()
			except:
				pass

			img = self.browser.find_element_by_xpath("/html/body/main/section[2]/article/div[1]/div[2]/figure/img[1]")
			
			try:
				img.screenshot(self.img_dir + "/" + link[1] + ".png") 
			except:
				pass
		else:
			pass

	# Gather the snapshot of the car given the page soup
	def vehicle_snapshot(soup):
		vehicle_snapshot=[]
		for row in soup.find_all("li",class_="ad-snapshot__item"):
			out_row=[]
			for el in row.find_all("span"):
				if len(el)>0:
					out_row.append(el.text)
			vehicle_snapshot.append(out_row)

		return vehicle_snapshot

	# Gather the data from the car given the page soup
	def vehicle_data(soup):
		vehicle_data = []
		table = soup.find('table', attrs={'class':'vehicle__data'})
		vehicle_table = table.find('tbody')

		rows = vehicle_table.find_all('tr')
		for row in rows:
			cols = row.find_all('td')
			cols = [el.text.strip() for el in cols]
			vehicle_data.append([el for el in cols if el])

		return vehicle_data

	# Gather the vehicle features
	def vehicle_features(soup):
		table = soup.find('div', attrs={'id':"panel-2"})
		rows = prova.find_all("dl")
		vehicle_features = []
		for cols in rows:
			features = []
			try:
				feat = cols.find("dt").text
				features.append(feat)
				[features.append(el.text) for el in cols.find_all("dd")]
			except:
				pass
			if len(features)>0:
				vehicle_features.append(features)

		return vehicle_features


	# Closes the session
	def close(self):
		self.browser.close()

def simple_get(url):
	try:
		with closing(get(url, stream=True)) as resp:
			if is_good_response(resp):
				return resp.content
			else:
				return None

	except RequestException as e:
		log_error('Error during requests to {0} : {1}'.format(url, str(e)))
		return None


def is_good_response(resp):

    content_type = resp.headers['Content-Type'].lower()
    return (resp.status_code == 200 
            and content_type is not None 
            and content_type.find('html') > -1)

def log_error(e):
	print(e)




if __name__ == '__main__':
	auto = Automobile()
	auto.connect()
	link_list = auto.get_links()

	for i in range(5):
		auto.page_scraping(link_list[i])
	print(auto.full_car_df)
	auto.close()








