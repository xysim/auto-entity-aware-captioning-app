import tqdm
import h5py
import spacy
import numpy as np
import json
import argparse
g_datadir = "data_ALL/"
def open_json(path):
    with open(path, "r") as f:
        return json.load(f)

def get_word_vector(sen):
    sen=nlp(str(sen))
    return sen.doc.vector

def save_h5(file_save, data):
    f_lb = h5py.File(file_save, "w")
    dt = h5py.special_dtype(vlen=np.dtype('float64'))
    ds = f_lb.create_dataset('average', (len(data), 300, ), dtype=dt)
    for i,d in tqdm.tqdm(enumerate(data)):
        ds[i] = d
    f_lb.close()

def create_rep(art):
    data = []
    keys = []
    for k, v in tqdm.tqdm(art.items()):
        v = v['sentence']
        if len(v) < sen_len + 1:
            temp = np.zeros([300, len(v)])
            for i, sents in enumerate(v):
                temp[:, i] = get_word_vector(sents.lower())
        else:
            temp = np.zeros([300, sen_len + 1])
            for i, sents in enumerate(v[:sen_len]):
                temp[:, i] = get_word_vector(sents.lower())
            temp[:, sen_len] = np.average([get_word_vector(sents.lower()) for sents in v[sen_len:]])
        data.append(temp)
        keys.append(k)
    return keys, data

if __name__ == '__main__':
    sen_len = 54
    np.random.seed(42)
    nlp = spacy.load('en_core_web_lg', disable=['parser', 'tagger'])

    full = open_json(g_datadir + 'article.json')
    keys, data = create_rep(full)
    json.dump(keys, open(g_datadir + 'articles_full_avg_keys.json', 'w'))
    save_h5(g_datadir + 'articles_full_avg.h5', data)