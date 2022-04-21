import numpy as np
import spacy
import json
import sys
from run3_clean_captions_small import preprocess_sentence2
g_datadir = "data_ALL/"
#fName = "../data/news_dataset.json"  # original 
#fName = "../data_small/my_news_dataset_00.json" # smallDataSet

# xysim: start : https://kodlogs.com/45150/nameerror-name-unicode-is-not-defined-in-python-3
def unicode(x):
    return str(x)
# xysim : end

np.random.seed(42)
nlp = spacy.load('en',disable=[ 'parser', 'tagger'])
nlp.add_pipe(nlp.create_pipe('sentencizer'))

#with open(fName, "r") as f:
    #news_dataset = json.load(f)
with open(g_datadir + "news_dataset.json", "r") as f:
    news_dataset = json.load(f)

with open(g_datadir + "captioning_dataset.json", "r") as f:
    captioning_dataset = json.load(f)

ids = list(set([news['imgid'].split('_')[0] for news in news_dataset]))
articles = [unicode(captioning_dataset[i]['article']) for i in ids]
len_articles = len(articles)

print('Sanity check len of ids: %d, len of cap dataset: %d, len of news dataset %d' % (
    len(ids), len(captioning_dataset), len(news_dataset)))

# free up the memory
del news_dataset, captioning_dataset

article_dataset = {}
for ix, sentences in enumerate(nlp.pipe(articles, n_threads=12, batch_size=2000)):
    key = ids[ix]
    print(sentences.sents)
    art_ner = {i.text: i.label_ for i in sentences.ents}
    article_sentence = []
    article_sentence_ner = []
    for sen_ in sentences.sents:
        #             sen = filter(lambda x: x in printable, sen)
        print("sen_ :", sen_)
        try:
            print("-----------1")
            sen = preprocess_sentence2(sen_.text.encode('ascii', errors='ignore'))
            print("-----------2")
            for d in sen_:
                if d.ent_iob_ != 'O':
                    #                 import ipdb; ipdb.set_trace()
                    article_sentence_ner.append(' '.join(sen))
                    break
            article_sentence.append(' '.join(sen))
        except:
            print ("exception: ", key)

    article_dataset[key] = {'sentence': article_sentence, 'sentence_ner': article_sentence_ner, 'ner': art_ner}
    sys.stdout.write('\rPercentage is done: %.4f' % (ix / float(len_articles)))
    sys.stdout.flush()
    break
with open(g_datadir + "article.json", 'w') as f:
    json.dump(article_dataset, f)
    print('Finished!')
