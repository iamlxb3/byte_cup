import pandas as pd
import sys

sys.path.append("..")
from funcs.gen import Seq2SeqDataSet
from torch.utils.data import DataLoader
from funcs.eval_predict import bleu_compute
from funcs.eval_predict import rogue_compute
from funcs.eval_predict import predict_on_test
from utils.helpers import plot_attentions
from exp_config import experiments
import numpy as np
import torch
import argparse
import ipdb


def args_parse():
    parser = argparse.ArgumentParser()
    parser.add_argument('--e', help='the name of the experiment', type=str, required=False,
                        choices=list(experiments.keys()))
    args = parser.parse_args()
    return args


def predict():
    # load experiment
    args = args_parse()
    if args.e is not None:
        cfg = experiments[args.e]
    else:
        from s2s_config import cfg
    target_vocab = cfg.target_vocab
    #

    # load models
    encoder = torch.load(cfg.encoder_path)
    decoder = torch.load(cfg.decoder_path)
    encoder, decoder = encoder.eval(), decoder.eval()
    print("Load encoder from {}, decoder from {}".format(cfg.encoder_path, cfg.decoder_path))
    #

    seq_csv_path = cfg.test_seq_csv_path
    df = pd.read_csv(seq_csv_path)
    mask = df['source'].apply(lambda x: len(x.split(','))) <= cfg.seq_max_len  # filter by length
    df = df[mask]
    X = df['source'].values
    Y = df['target'].values
    uids = df['uid'].values
    uid_dict = dict(zip(df.uid, df.source))

    # get generator
    test_generator = Seq2SeqDataSet(X, Y, uids, cfg.encoder_pad_shape, cfg.decoder_pad_shape,
                                    cfg.src_pad_token, cfg.target_pad_token, cfg.use_pretrain_embedding)
    test_loader = DataLoader(test_generator,
                             batch_size=1,
                             shuffle=False,
                             num_workers=cfg.num_workers,
                             )
    test_loss = []
    rogues = []
    bleus = []

    for i, (src_tensor, target_tensor, uid) in enumerate(test_loader):
        src_words = uid_dict[int(uid)].split(',')
        src_words = [target_vocab[int(index)] for index in src_words]
        loss, decoded_words, target_words, attn_weights = predict_on_test(cfg, encoder, decoder, src_tensor,
                                                                          target_tensor)

        print("-----------------------------------------------------")
        print("loss: ", loss)
        print("target_words: ", target_words)
        print("Decoded_words: ", decoded_words)

        # TODO, add language model
        # target_words = eval(y_df[(y_df.id == val_id)]['index'].values[0])
        #

        # compute rogue & bleu
        rogue = rogue_compute(target_words, decoded_words)
        bleu = bleu_compute(target_words, decoded_words)
        #
        #
        test_loss.append(loss)
        rogues.append(rogue)
        bleus.append(bleu)

        # plot attentions
        if cfg.plot_attn:
            plot_attentions(attn_weights, src_words, decoded_words)

    print("test_loss: ", np.average(test_loss))
    print("rogues: ", np.average(rogues))
    print("bleus: ", np.average(bleus))


if __name__ == '__main__':
    predict()
