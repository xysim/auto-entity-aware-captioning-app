import requests
from bs4 import BeautifulSoup
import unidecode
import subprocess
import os
import urllib.request
import argparse
import json

g_imgdir = "images/"
g_filedir = "data_ALL/"
g_fileName =g_filedir+ "captioning_dataset.json"
g_imgid = "TEST1"
g_test_url = "https://malaysia.news.yahoo.com/sam-ke-ting-appeal-against-132906825.html"


def browse_and_getTxt(seed_url,name=g_fileName):
    try:
        html_text = requests.get(seed_url).text
        soup = BeautifulSoup(html_text, "html.parser")
        
        mydivs = soup.find_all("div", {"class": "caas-body"})
        myfigcap = soup.find_all("figcaption", {"class": "caption-collapse"})
        txt = ''
        data = '' 
        
        for data in mydivs:  # .find_all("p"): 
            tmp =  str(data.get_text())
            txt = txt + tmp
        #saveData(txt,name)        
        #return True, txt
        txt2 = ''
        data2 = '' 
        for data2 in myfigcap:  # .find_all("p"): 
            tmp =  str(data2.get_text())
            txt2 = txt2 + tmp
        # print("text", txt)
        # print("_________________________________________________")
        # print("_________________________________________________")
        # print("text2", txt2)
        # print("_________________________________________________")
        txt2 = unidecode.unidecode(txt2)
        #txt = txt.lstrip(txt2)
        txt = unidecode.unidecode(txt)
        saveData(txt,txt2,name)        
        return True, txt, txt2
        
    except:
        return False, txt
        
def saveData(data,caption,name=g_fileName):
    
      
    # python object(dictionary) to be dumped
    dict1 ={
        g_imgid: {
            "images": {"0":caption},
            "article": data
        }
    }
      
    # the json file where the output must be stored
    out_file = open(name, "w")
      
    json.dump(dict1, out_file, indent = 6)
      
    out_file.close()





def get_img(url,name=g_imgid):
    request = requests.get(url)
    content = request.content
    soup = BeautifulSoup(content, "html.parser")
    mydivs = soup.find_all("div", {"class": "caas-body-content"})

    txt = []
    data = '' 
    for data in mydivs:  
        tmp =  data.find_all("img", {"class": "caas-img"})
        txt = txt + tmp
        

    count = 0
    for img in txt:
        
        try:
            urllib.request.urlretrieve(img.get('src'), g_imgdir+name+"_"+str(count)+".jpg")
            #print("get ok: ", img.get('src'))
            count += 1
            print("success: ======", img.get('src'), "==============")
        except:
            print("exception: ", img.get('src'))
    

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('--url', type=str, default=g_test_url, help='input url')
    args = parser.parse_args()
    
    
    ok_Or_not, result, caption = browse_and_getTxt(args.url)
    if (ok_Or_not == True):
        print(result)
    else:
        print("error")
    get_img(args.url)



