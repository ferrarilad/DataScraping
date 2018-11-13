import numpy as np
from bs4 import BeautifulSoup
import urllib
import os
import pandas as pd
from requests import get
from contextlib import closing
import shutil


class Automobile():
	def __init__(self,csvpath=None):
		self.AUTOMOBILE_FRONTPAGE = 'https://www.automobile.it'
		self.pt1 = '/usate'
		self.pt2 = '/?dove=milano'
		self.pt3 = '&immatricolazione=2005'
		self.pt4 = '&km_max=350000_km'
		self.pt5 = '&prezzo_a=100000'
		self.pt6 = '&tipo_di_usato=auto_d_epoca,aziendale,dimostrativo'
		work_dir = os.getcwd()
		self.img_dir = work_dir + "/car_images"
		try:
		   os.mkdir(self.img_dir)
		except:
		    pass
		self.full_car_df = pd.DataFrame()

	def simple_get(self,url):
		try:
			with closing(get(url, stream=True)) as resp:
				if self.is_good_response(resp):
					return resp.content
				else:
					return None

		except RequestException as e:
			self.log_error('Error during requests to {0} : {1}'.format(url, str(e)))
			return None


	def is_good_response(self,resp):

	    content_type = resp.headers['Content-Type'].lower()
	    return (resp.status_code == 200 
	            and content_type is not None 
	            and content_type.find('html') > -1)

	def log_error(self,e):
		print(e)

	def n_results_n_pages(self,URL):
		soup = BeautifulSoup(self.simple_get(URL),'html.parser')
		n_results = soup.find(class_="pagination__total")
		out = []
		for el in n_results.text.strip().split(" "):
			try:
				out.append(int(el))
			except:
				pass
		return out


	def get_auto_snapshot(self,auto_snapshot):
		title = auto_snapshot.find(class_="search-item__pictures__container")["title"]
		data_link = auto_snapshot.find(class_="search-item__pictures__container")["data-link"]
		Id = auto_snapshot.find(class_="search-item__pictures__container")["data-link"].split("/")[-1]
		img_link = "http:"+auto_snapshot.find(class_="search-item__pictures__container")["style"].split("url(")[-1][:-1]
		try:
			self.get_image(img_link,Id)
			return True, {"Id" : Id, "Title" : title,"DataLink" : data_link}

		except:
			print("Image not found for\nLink: {}\n ID: {}\n".format(img_link,Id))
			return False, {}
			pass

	def get_image(self,img_link,Id):
		if Id + ".png" in os.listdir(self.img_dir):
			pass
		else:
			response = get(img_link, stream=True)
			with open(self.img_dir+"/"+Id+".png", 'wb') as out_file:
				shutil.copyfileobj(response.raw, out_file)


	def process_page(self,page_n):
		temp_df = pd.DataFrame()
		URL = self.AUTOMOBILE_FRONTPAGE + self.pt1 + "/page-" + str(page_n) + self.pt2 + self.pt3 + self.pt4 + self.pt5 + self.pt6
		soup = BeautifulSoup(self.simple_get(URL),'html.parser')


		print("Processing page {:4d}".format(page_n+1))
		for (i,auto_announce) in enumerate(soup.find_all(class_="search-item__body")):

			has_image, auto_dict = self.get_auto_snapshot(auto_announce)

			if has_image:
				soup_buff = BeautifulSoup(self.simple_get(self.AUTOMOBILE_FRONTPAGE+auto_dict["DataLink"]),'html.parser')

				data = self.auto_data(soup_buff)
				technical = self.auto_technical(soup_buff)
				dotazione = self.auto_dotazione(soup_buff)

				auto_dict = {**auto_dict,**data}
				auto_dict = {**auto_dict,**technical}
				auto_dict = {**auto_dict,**dotazione}
				temp_df = temp_df.append(pd.Series(data=auto_dict),ignore_index=True)

			print("{:4d}% completed".format((i+1)*100//len(soup.find_all(class_="search-item__body"))))
		return temp_df

	def auto_data(self,soup):
		data = {}
		data["price"] = soup.find(class_="vip__price__title").text.replace(".","").split(" ")[-1]
		vehicle_snapshot=[]
		for row in soup.find_all("li",class_="ad-snapshot__item"):
			out_row=[]
			for el in row.find_all("span"):
				if len(el)>0:
					out_row.append(el.text)
			vehicle_snapshot.append(out_row)
		
		data["immatriculationMonth"] = vehicle_snapshot[0][0]
		data["immatriculationYear"] = int(vehicle_snapshot[0][1])
		data["Km"] = int(vehicle_snapshot[1][0].replace(".","").split(" ")[0])
		data["engineKW"] = int(vehicle_snapshot[2][0].split(" ")[0])
		data["engineCV"] = int(vehicle_snapshot[2][1].strip("()").split(" ")[0])
		data["fuelType"] = vehicle_snapshot[3][0]
		data["drivetrain"] = vehicle_snapshot[4][0].split(" ")[-1]
		return data

	# Gather the vehicle features
	def auto_technical(self,soup):
		technical_features = {}

		table = soup.find('div', attrs={'id':"panel-2"})
		rows = table.find_all("dl")

		for row in rows:
			try:
				feature = row.find("dt").text
				technical_features[feature]=[el.text for el in row.find_all("dd")]
			except:
				pass

		return technical_features

	def auto_dotazione(self,soup):
		dotazione = {}

		table=soup.find("table")
		rows = table.find_all("tr")

		for row in rows:
			cols = row.find_all("td")
			for col in cols:
				if col["class"][-1]=="table__cell--label":
					key = col.text
				if col["class"][-1]=="table__cell--value":
					feat = col.text.strip("\n")

			dotazione[key] = feat

		return dotazione

	def full_data_extraction(self):
		URL = self.AUTOMOBILE_FRONTPAGE + self.pt1 + self.pt2 + self.pt3 + self.pt4 + self.pt5 + self.pt6
		n_results, n_pages = self.n_results_n_pages(URL)
		print("There are {} results distributed on {} pages".format(n_results,n_pages))

		for page_n in range(n_pages):
			temp_df = self.process_page(page_n)
			self.full_car_df = self.full_car_df.append(temp_df)
			self.full_car_df.to_csv("full_car_df.csv")

		return True


if __name__ == "__main__":
	auto = Automobile()
	auto.full_data_extraction()
	completed = print(auto.full_car_df)
	if completed:
		print("completed")

