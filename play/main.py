"""
# https://machinelearningmastery.com/timedistributed-layer-for-long-short-term-memory-networks-in-python/
# https://github.com/keras-team/keras/blob/master/examples/imdb_lstm.py
# https://gist.github.com/mbollmann/ccc735366221e4dba9f89d2aab86da1e # attention LSTM
# https://github.com/keras-team/keras/issues/1472
"""

import numpy as np
import keras
import math
import random
import glob
import os
import re
import ipdb
from keras.models import Sequential
from seq2seq.models import SimpleSeq2Seq
from keras.layers import Dense, Dropout, Bidirectional
from keras.optimizers import RMSprop, adam
from keras.models import Sequential
from keras.layers import LSTM, Dense
from keras.layers import Embedding, TimeDistributed
from seq2seq.models import AttentionSeq2Seq
from keras.models import Model
from keras.layers import Input, LSTM, Dense
from keras.layers import add

from keras.layers import merge


def random_gen(X_paths, Y_paths, batch_size=10):
    while True:
        X_Y_paths = list(zip(X_paths, Y_paths))
        random.shuffle((X_Y_paths))
        X_paths, Y_paths = zip(*X_Y_paths)

        x_batch = []
        y_batch = []

        for i, x_path in enumerate(X_paths):
            y_path = Y_paths[i]
            x = np.load(x_path)
            y = np.load(y_path)
            x = np.array([x])
            y = np.array([y])
            x_batch.append(x)
            y_batch.append(y)

            assert len(x_batch) == len(y_batch)
            if len(x_batch) == batch_size:
                x_batch = np.concatenate(x_batch)
                y_batch = np.concatenate(y_batch)

                # # get dy_batch
                # dy_batch = y_batch.copy()
                # for i, ty in enumerate(dy_batch):
                #     new_ty = np.roll(ty, 1, axis=0)
                #     new_ty[0] *= 0.0
                #     dy_batch[i] = new_ty
                # #

                # get dy_batch
                dy_batch = np.zeros_like(y_batch)

                yield ([x_batch, dy_batch], y_batch)
                x_batch = []
                y_batch = []




def train_X_Y_load(data_dir):
    x_npys = glob.glob(os.path.join(data_dir, 'x_*.npy'))
    y_npys = glob.glob(os.path.join(data_dir, 'y_*.npy'))
    assert len(x_npys) == len(y_npys)

    X = []
    Y = []
    for x_npy in x_npys:
        id = re.findall(r'x_([0-9]+).npy', x_npy)[0]
        y_npy = os.path.join(data_dir, 'y_{}.npy'.format(id))
        X.append(x_npy)
        Y.append(y_npy)
    return X, Y

def encode_decoder():
    encoder_dim = 20
    decoder_dim = 20

    encoder_inputs = Input(shape=(None, 300))

    _, state_h_f, state_c_f = LSTM(encoder_dim, return_state=True)(encoder_inputs)

    #_, state_h_b, state_c_b = LSTM(encoder_dim, return_state=True, go_backwards=True)(encoder_inputs)

    # # We discard `encoder_outputs` and only keep the states.
    # state_h = merge.concatenate([state_h_f, state_h_b])
    # state_c = merge.concatenate([state_c_f, state_c_b])

    encoder_states = [state_h_f, state_c_f]

    decoder_inputs = Input(shape=(25, 7560))
    decoder_outputs = LSTM(decoder_dim, return_sequences=True)(decoder_inputs, initial_state=encoder_states)

    decoder_dense = Dense(7560, activation='softmax')
    decoder_outputs = decoder_dense(decoder_outputs)

    model = Model([encoder_inputs, decoder_inputs], decoder_outputs)
    model.compile(optimizer='rmsprop', loss='categorical_crossentropy')
    model.summary()  # maybe Keras bug?

    return model

# x_train = sequence.pad_sequences(x_train, maxlen=maxlen)
# x_test = sequence.pad_sequences(x_test, maxlen=maxlen)


def main():
    # config
    batch_size = 1

    # load model
    model1 = encode_decoder()

    # load data
    data_dir = r'D:\byte_cup\data\baseline\train'
    X, Y = train_X_Y_load(data_dir)
    print("Load train paths complete!")

    # split into train/val
    train_X = X[:80]
    train_Y = Y[:80]
    val_X = X[80:]
    val_Y = Y[80:]
    train_N = len(train_X)
    val_N = len(val_X)

    train_gen = random_gen(train_X, train_Y, batch_size=batch_size)
    train_step_size = int(math.ceil(train_N / batch_size))
    val_gen = random_gen(val_X, val_Y, batch_size=batch_size)
    val_step_size = int(math.ceil(val_N / batch_size))

    # train
    model1.fit_generator(generator=train_gen,
                         validation_data=val_gen,
                         epochs=100,
                         steps_per_epoch=train_step_size,
                         validation_steps=val_step_size,
                         )


main()