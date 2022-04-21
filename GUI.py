from kivy.uix.button import Button
from kivy.app import App
from functools import partial
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder
from kivy.uix.textinput import TextInput
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Label
from kivy.uix.label import Label
from kivy.clock import Clock
from kivy.uix.image import Image
from kivy.properties import StringProperty
import os
import json

Builder.load_string("""
#: import ScrollView kivy.uix.scrollview

<MyLayout>:
    BoxLayout:
        orientation: "vertical"
        spacing: 20
        padding: 20
        #size_hint_y: 1
        Label:
            text: 'Enter the Url for news/articles to be captioned:'
            text_size:self.size
            halign:'left'
            valign:'bottom'
            size_hint_y: 0.1
        BoxLayout:
            spacing: 20
            size_hint: (1, .5)
            TextInput: 
                id: in1
                hint_text: 'Enter the Url here'
                size_hint: (.8, .5)
            Button: 
                text: 'Clear All'
                size_hint: (.2, .5)
                on_press: app.clearText()
        Label:
            id: out1
            text: '::'
            text_size:self.size
            halign:'left'
            valign:'bottom'
            size_hint_y: 0.3
        BoxLayout:
            orientation: "horizontal"
            spacing: 20
            #padding: 20        
            size_hint_y: 0.5
            Button: 
                id: okbtn
                text: 'Get news/articles'
                size_hint: (.2, .6)
                on_press: app.pressGetNews()
                on_release: app.releaseGetNews()                          
            Button: 
                text: 'Print news/articles'
                size_hint: (.2, .6)
                background_color : (1,0,0,1)
                on_press: app.printDataset()
            Button: 
                id: genbtn
                text: 'Generate caption'
                size_hint: (.2, .6)
                on_press: app.pressGenCap()
                on_release: app.releaseGenCap()
            Button: 
                text: 'Print caption'
                size_hint: (.2, .6)
                background_color : (1,0,0,1)
                on_press: app.printCap()

        BoxLayout:
            orientation: "horizontal"
            spacing: 20
            #padding: 20        
            size_hint_y: 1.8
            Image:
                id: img1
                source: 'images.jpg'
                #size_hint_x: None
                #size_hint_y: None
                size_hint:(1,1)
            ScrollView:
                Label:
                    id: content_text
                    size_hint_y: None
                    height: self.texture_size[1]
                    text: u"Article"
                    text_size: (self.width-20), None
                    line_height: 1.5
                    valign: "top"
                
""")


class MyLayout(App, BoxLayout):
    
    def printCap(self):
        try:
            f = open('vis/att.json')
            att = json.load(f)
            f.close()
            f = open('vis/ctx.json')
            ctx = json.load(f)
            f.close()
            f = open('vis/rand.json')
            rand = json.load(f)
            f.close()
            self.ids.content_text.text = "Generated caption \n================\natt: %s" %(att)+"\n"+"ctx: %s" %(ctx)+"\n"+"rand: %s" %(rand)+"\n"
        except:
            myText = 'Caption file not found'
            self.textDisplay_callback(myText)
            Clock.schedule_once(lambda dt: self.textDisplay_callback(),2)
            self.ids.content_text.text = 'Caption not found'
    def printDataset(self):
        try:
            self.ids.img1.source = 'resized/TEST1_0.jpg'
            f = open('data_ALL/captioning_dataset.json')
            data = json.load(f)
            f.close()
            self.ids.content_text.text = "Article\n======\n"+data['TEST1']['article']
        except:
            myText = 'Article/Image not found'
            self.textDisplay_callback(myText)
            Clock.schedule_once(lambda dt: self.textDisplay_callback(),2)
            self.ids.content_text.text = 'Article not found'
    
    def pressGenCap(self):
        
        myText = 'Generating caption'
        self.textDisplay_callback(myText)
        self.ids.genbtn.disabled = True
        self.ids.genbtn.text = "Processing..."
    
    def releaseGenCap(self):
        self.runALL_capGen()
    
    def pressGetNews(self):
        userIn = self.ids.in1.text
        if userIn == '':
            myText = 'Please provide a valid url'
            self.textDisplay_callback(myText)
        else:
            myText = "Retrieving news data for "
            self.printOut(userIn, myText)
    
    def releaseGetNews(self):
        userIn = self.ids.in1.text
        if userIn == '':
            Clock.schedule_once(lambda dt: self.textDisplay_callback(),2)
        else:            
            self.runALL_cap(userIn)
    
    def textDisplay_callback(self,myText='::'):
        self.ids.out1.text = myText
        
    def clearText(self):
        self.ids.in1.text = ''
        
    def printOut(self, userIn, myText):
        self.ids.okbtn.disabled = True
        self.ids.okbtn.text = "Processing..."
        myText = myText + "\r\n%s" % userIn
        self.textDisplay_callback(myText)
        
    def runALL_capGen(self):
        # 3
        os.system("python run3_clean_captions_small.py")
        # 4
        os.system("python run4_create_article_set_small.py")
        # 5
        os.system("python run5_prepro_labels_small.py")
        # 6
        os.system("python run6_prepro_images_small.py")
        # 7
        os.system("python run7_prepro_articles_avg_small.py")
        # 8
        os.system("python run8_eval_samll.py")
        # 9
        os.system("python run9_insert_small.py")
        myText = "Done"
        self.textDisplay_callback(myText)
        self.ids.genbtn.disabled = False
        self.ids.genbtn.text = "Generate caption"
        
    def runALL_cap(self, userIn):
        # 1
        os.system("python run1_get_newsdata.py --url "+ userIn)
        # 2
        os.system("python run2_resize.py")
        
        myText = "Done"
        self.textDisplay_callback(myText)
        self.ids.okbtn.text = "Generate news/articles"
        self.ids.okbtn.disabled = False
        
    def build(self):
        return self
   
if __name__ == "__main__":
    MyLayout().run()
    
    
    
    