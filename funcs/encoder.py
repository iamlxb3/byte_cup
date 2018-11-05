import torch
import ipdb
import torch.nn as nn


# RNN
class EncoderRnn(nn.Module):
    def __init__(self, input_dim, hidden_dim, vocab_size):
        super(EncoderRnn, self).__init__()
        self.hidden_size = hidden_dim
        n_layers = 1
        self.embedding = nn.Embedding(vocab_size, input_dim)
        self.rnn = nn.RNN(input_dim, hidden_dim, n_layers)

    def forward(self, xt, sorted_seq_lens, sorted_indices, ht):
        """

        :param xt: torch.Size([batch_size, time_steps, feature_dim])
        :param sorted_seq_lens:
        :param sorted_indices: torch.Size([num_layers * num_directions, batch_size, hidden_dim])
        :param ht:
        :return:
            encoder_outputs : torch.Size([time_steps, batch_size, 256]),
            encoder_hidden: torch.Size([num_layers * num_directions, batch_size, 256])
        """
        xt = self.embedding(xt).view(xt.size(0), xt.size(1), -1) # output -> (seq_len, batch_size, input_dim)
        xt = nn.utils.rnn.pack_padded_sequence(xt, lengths=sorted_seq_lens)
        output, hidden = self.rnn(xt, ht)
        output = nn.utils.rnn.pad_packed_sequence(output)[0]  # 返回的seq长度可能和输入的不一样，大概是pad_packed的功能
        output = output.index_select(1, torch.tensor(sorted_indices))

        # 范围的seq是这个batch里面最大的，输入短的seq的有效输出与输入长度一样，剩下的应该都是0
        return output, hidden

    def initHidden(self, batch, device):
        return torch.zeros(1, batch, self.hidden_size, device=device)


# GRU
class EncoderGru(nn.Module):
    def __init__(self, input_size, hidden_size, n_layers=1):
        super(EncoderGru, self).__init__()
        self.hidden_size = hidden_size
        self.n_layers = n_layers
        self.gru = nn.GRU(input_size, hidden_size, self.n_layers)
        # self.x_max_length = 150

    def forward(self, input, h0):
        output, hidden = self.gru(input, h0)
        return output, hidden

    def initHidden(self, batch, device):
        return torch.zeros(1, batch, self.hidden_size, device=device)