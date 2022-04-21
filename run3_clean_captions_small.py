import json
import nltk
import spacy
import numpy as np
import tqdm
import unidecode
from bs4 import BeautifulSoup
import re
import unicodedata
from itertools import groupby
g_datadir = "data_ALL/"
g_infile = "captioning_dataset.json"
g_outfile = "news_dataset.json"
def remove_non_ascii(words):
    """Remove non-ASCII characters from list of tokenized words"""
    new_words = []
    for word in words:
        new_word = unicodedata.normalize('NFKD', word).encode('ascii', 'ignore').decode('utf-8', 'ignore')
        new_words.append(new_word)
    return new_words

def remove_punctuation(words):
    """Remove punctuation from list of tokenized words"""
    new_words = []
    for word in words:
        new_word = re.sub(r'[^\w\s]', '', word)
        if new_word != '':
            new_words.append(new_word)
    return new_words

def normalize(words):
    words = remove_non_ascii(words)
    words = remove_punctuation(words)
    return words


def strip_html(text):
    soup = BeautifulSoup(text, "html.parser")
    return soup.get_text()


def remove_between_square_brackets(text):
    return re.sub('\[[^]]*\]', '', text)


def denoise_text(text):
    text = strip_html(text)
    text = remove_between_square_brackets(text)
    return text


def preprocess_sentence(sen):
    sen = sen.strip()
    #print("-----------12")
    sen = sen.encode('ascii',errors='ignore')
    #print("-----------13")
    sen = sen.decode()
    #print("-----------14")
    sen = unidecode.unidecode(sen)
    #print("-----------15")
    sen = denoise_text(sen)
    #print("-----------16")
    sen = nltk.tokenize.word_tokenize(sen)
    #print("-----------17")
    sen = normalize([str(s) for s in sen])

    return sen

def preprocess_sentence2(sen):
    sen = sen.strip()
    #print("-----------12")
    #sen = sen.encode('ascii',errors='ignore')
    #print("-----------13")
    sen = sen.decode()
    #print("-----------14")
    sen = unidecode.unidecode(sen)
    #print("-----------15")
    sen = denoise_text(sen)
    #print("-----------16")
    sen = nltk.tokenize.word_tokenize(sen)
    #print("-----------17")
    sen = normalize([str(s) for s in sen])

    return sen

def NER(sen):
    doc = nlp(str(sen))

    tokens = [d.text for d in doc]

    temp = [d.ent_type_+'_' if d.ent_iob_ != 'O' else d.text for d in doc]
    return [x[0] for x in groupby(temp)], tokens




if __name__ == '__main__':
    
    
    np.random.seed(42)
    nlp = spacy.load('en', disable=['parser', 'tagger'])
    print('Loading spacy modules.')
    news_data = []
    news_data_test = []
    news_data_val = []
    counter = 0
    test_num, val_num, train_num = 0, 0, 0



    print('Loading the json.')
    with open(g_datadir+g_infile, "r") as f:
        captioning_dataset = json.load(f)



    for k, anns in captioning_dataset.items():

        for ix, img in anns['images'].items():
            try:
                
                print(counter)
                print(img)

                img = preprocess_sentence(img)
                template, full = NER(' '.join(img))
                if len(' '.join(template)) != 0:
                    split = "test"
                    news_data.append({'filename': k + '_' + ix + '.jpg', 
                                      'filepath': 'resized', 
                                      'cocoid': counter,
                                      'imgid': k + '_' + ix, 
                                      'sentences': [], 
                                      'sentences_full': [],
                                      'split': split})
                    news_data[counter]['sentences'].append(
                        {'imgid': counter, 
                         'raw': ' '.join(template), 
                         'tokens': template})
                    news_data[counter]['sentences_full'].append(
                        {'imgid': counter, 
                         'raw': ' '.join(full), 
                         'tokens': full})

                    
                    counter += 1
            except:
                print ("exception :",img)

    with open(g_datadir+g_outfile, "w") as f:
        json.dump(news_data, f)
        