from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

import torch
import torch.nn as nn
from torch.autograd import Variable

import numpy as np
import json
from json import encoder
import random
import string
import time
import os
import sys
import misc.utils as utils
from pycocoevalcap.bleu.bleu import Bleu
from pycocoevalcap.rouge.rouge import Rouge
from pycocoevalcap.cider.cider import Cider
from pycocoevalcap.meteor.meteor import Meteor
from pycocoevalcap.spice.spice import Spice
g_infile = "captioning_dataset.json"
g_outfile = "news_dataset.json"
g_datadir = "data_ALL/"
def language_eval(dataset, preds, model_id, split):
    import sys
    if 'coco' in dataset:
        sys.path.append("coco-caption")
        annFile = 'coco-caption/annotations/captions_val2014.json'
    else:
        # TODO: NYTIMES
        if split == 'val':
            annFile = g_datadir + 'val.json'
            with open(annFile, 'rb') as f: dataset = json.load(f)
        else:
            annFile = g_datadir + g_outfile
            with open(annFile, 'rb') as f: dataset = json.load(f)

        # TODO: BREAKINGNEWS
        # with open("/home/abiten/Desktop/Thesis/newspaper/breakingnews/bnews_caps.json", "rb") as f: dataset = json.load(f)
        print("------------------>>s")
        id_to_ix = {v['cocoid']: ix for ix, v in enumerate(dataset)}
        hypo = {v['image_id']: [v['caption']] for v in preds}
        print(preds)
        print(hypo.keys())
        print(id_to_ix)
        
        print(dataset)
        ref = {k: [i['raw'] for i in dataset[id_to_ix[k]]['sentences']] for k in hypo.keys()}
        final_scores = evaluate(ref, hypo)
        print('Bleu_1:\t', final_scores['Bleu_1'])
        print('Bleu_2:\t', final_scores['Bleu_2'])
        print('Bleu_3:\t', final_scores['Bleu_3'])
        print('Bleu_4:\t', final_scores['Bleu_4'])
        # print('METEOR:\t', final_scores['METEOR'])
        print('ROUGE_L:', final_scores['ROUGE_L'])
        print('CIDEr:\t', final_scores['CIDEr'])
        # print('Spice:\t', final_scores['Spice'])
        return final_scores


        # sys.path.append("f30k-caption")
        # annFile = 'f30k-caption/annotations/dataset_flickr30k.json'
    from pycocotools.coco import COCO
    from pycocoevalcap.eval import COCOEvalCap

    encoder.FLOAT_REPR = lambda o: format(o, '.3f')

    if not os.path.isdir('eval_results'):
        os.mkdir('eval_results')
    cache_path = os.path.join('eval_results/', model_id + '_' + split + '.json')

    coco = COCO(annFile)
    valids = coco.getImgIds()

    # filter results to only those in MSCOCO validation set (will be about a third)
    preds_filt = [p for p in preds if p['image_id'] in valids]
    print('using %d/%d predictions' % (len(preds_filt), len(preds)))
    json.dump(preds_filt, open(cache_path, 'w')) # serialize to temporary json file. Sigh, COCO API...

    cocoRes = coco.loadRes(cache_path)
    cocoEval = COCOEvalCap(coco, cocoRes)
    cocoEval.params['image_id'] = cocoRes.getImgIds()
    cocoEval.evaluate()

    # create output dictionary
    out = {}
    for metric, score in cocoEval.eval.items():
        out[metric] = score

    imgToEval = cocoEval.imgToEval
    for p in preds_filt:
        image_id, caption = p['image_id'], p['caption']
        imgToEval[image_id]['caption'] = caption
    with open(cache_path, 'w') as outfile:
        json.dump({'overall': out, 'imgToEval': imgToEval}, outfile)

    return out

def evaluate(ref, hypo):
    scorers = [
        (Bleu(4), ["Bleu_1", "Bleu_2", "Bleu_3", "Bleu_4"]),
        # (Meteor(), "METEOR"),
        (Rouge(), "ROUGE_L"),
        (Cider(), "CIDEr")
        # (Spice(), "Spice")
    ]
    final_scores = {}
    for scorer, method in scorers:
        score, scores = scorer.compute_score(ref, hypo)
        if type(score) == list:
            for m, s in zip(method, score):
                final_scores[m] = s
        else:
            final_scores[method] = score

    return final_scores

def eval_split(cnn_model, model, crit, loader, eval_kwargs={}, return_attention=False):
    verbose = eval_kwargs.get('verbose', True)
    num_images = eval_kwargs.get('num_images', eval_kwargs.get('val_images_use', -1))
    split = eval_kwargs.get('split', 'val')
    lang_eval = eval_kwargs.get('language_eval', 0)
    dataset = eval_kwargs.get('dataset', 'news')
    beam_size = eval_kwargs.get('beam_size', 1)

    # Make sure in the evaluation mode
    cnn_model.eval()
    model.eval()

    loader.reset_iterator(split)

    n = 0
    loss = 0
    loss_sum = 0
    loss_evals = 1e-8
    predictions = []

    while True:
        data = loader.get_batch(split)
        #print("data : ", data)
        #print("n : ", n)
        data['images'] = utils.prepro_images(data['images'], False)
        n = n + loader.batch_size

        #evaluate loss if we have the labels
        loss = 0
        # vis_attention, sen_attention = [], []
        # Get the image features first
        tmp = [data['images'], data.get('labels', np.zeros(1)), data.get('masks', np.zeros(1))]
        tmp = [Variable(torch.from_numpy(_), requires_grad=False).cuda() for _ in tmp]
        images, labels, masks = tmp
        with torch.no_grad():
            att_feats = cnn_model(images).permute(0, 2, 3, 1) # .contiguous()
            # att_feats = _att_feats = cnn_model(images).permute(0, 2, 3, 1).contiguous()
            # fc_feats = _fc_feats = att_feats.mean(2).mean(1)
            fc_feats = att_feats.mean(2).mean(1)
        sen_embed = data.get('sen_embed', None)

        # forward the model to get loss
        if data.get('labels', None) is not None:

            att_feats = att_feats.unsqueeze(1).expand(*((att_feats.size(0), loader.seq_per_img,) + att_feats.size()[1:])).contiguous().view(*((att_feats.size(0) * loader.seq_per_img,) + att_feats.size()[1:]))
            fc_feats = fc_feats.unsqueeze(1).expand(*((fc_feats.size(0), loader.seq_per_img,) + fc_feats.size()[1:])).contiguous().view(*((fc_feats.size(0) * loader.seq_per_img,) + fc_feats.size()[1:]))
            if sen_embed is not None:
                with torch.no_grad():
                    sen_embed = np.array(sen_embed, dtype=np.float32)
                    loss = crit(model(fc_feats, att_feats, labels, Variable(torch.from_numpy(sen_embed)).cuda()),
                                labels[:, 1:], masks[:, 1:])
            else:
                loss = crit(model(fc_feats, att_feats, labels), labels[:,1:], masks[:,1:]).data[0]
            loss_sum += loss
            loss_evals = loss_evals + 1

        # forward the model to also get generated samples for each image
        # Only leave one feature for each image, in case duplicate sample
        # fc_feats, att_feats = _fc_feats, _att_feats
        # forward the model to also get generated samples for each image
        if sen_embed is not None:
            if return_attention:
                seq, _, atts = model.sample(fc_feats, att_feats, eval_kwargs, Variable(torch.from_numpy(sen_embed)).cuda(),
                                            return_attention)
                vis_attention = np.array([att[0] for att in atts])
                sen_attention = np.array([att[1] for att in atts])
            else:
                seq, _= model.sample(fc_feats, att_feats, eval_kwargs,
                                            Variable(torch.from_numpy(sen_embed)).cuda(),
                                            return_attention)

        else:
            seq, _ = model.sample(fc_feats, att_feats, eval_kwargs)
        #set_trace()
        sents = utils.decode_sequence(loader.get_vocab(), seq)
        print("-------------11-----------------")
        print("sents:", sents)
        for k, sent in enumerate(sents):
            print("k:",k)
            print("sent:", sent)
            entry = {'image_id': data['infos'][k]['id'], 'caption': sent, 'image_path': data['infos'][k]['file_path']}
            print("-------------112-----------------")
            if return_attention:
                sen_length = len(sent.split())
                entry['vis_att'] = vis_attention[:sen_length, k, :].tolist()
                entry['sen_att'] = sen_attention[:sen_length, k, :].tolist()
            if eval_kwargs.get('dump_path', 0) == 1:
                entry['file_name'] = data['infos'][k]['file_path']
            predictions.append(entry)
            if eval_kwargs.get('dump_images', 0) == 1:
                # dump the raw image to vis/ folder
                
                cmd = 'copy "' + os.path.join(eval_kwargs['image_root'], data['infos'][k]['file_path']) + '" vis\imgs\img' + str(len(predictions)) + '.jpg' # bit gross
                print(cmd)
                os.system(cmd)
            print("-------------111-----------------")
            if verbose:
                print('image %s: %s' %(entry['image_id'], entry['caption']))
        print("-------------12-----------------")
        # if we wrapped around the split or used up val imgs budget then bail
        ix0 = data['bounds']['it_pos_now']
        ix1 = data['bounds']['it_max']
        if num_images != -1:
            ix1 = min(ix1, num_images)
        for i in range(n - ix1):
            predictions.pop()
        print("--------------13----------------")
        # break
        if verbose:
            print('evaluating validation preformance... %d/%d (%f)' %(ix0 - 1, ix1, loss))

        if data['bounds']['wrapped']:
            break
        if num_images >= 0 and n >= num_images:
            break
    print("----------------14--------------")
    lang_stats = None
    if lang_eval == 1:
        lang_stats = language_eval(dataset, predictions, eval_kwargs['id'], split)

    # if sen_embed is not None:
    #     atts = [{'file_path': d['file_path'], 'vis_att':vis_attention[i], 'sen_att':sen_attention[i]} for i, d in enumerate(data['infos'])]
    #     return loss_sum/loss_evals, predictions, lang_stats, atts
    # Switch back to training mode
    model.train()
    return loss_sum/loss_evals, predictions, lang_stats
