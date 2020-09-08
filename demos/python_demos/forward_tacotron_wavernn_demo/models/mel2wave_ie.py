import os.path as osp
import logging as log

from openvino.inference_engine import IECore
import numpy as np

from utils.wav_processing import *


class WaveRNNIE:
    def __init__(self, model_upsample, model_rnn, target=11000, overlap=550, hop_length=275, bits=9, device='CPU',
                 verbose=False):
        """
        return class provided WaveRNN inference.

        :param model_upsample: path to xml with upsample model of WaveRNN
        :param model_rnn: path to xml with rnn parameters of WaveRNN model
        :param target: length of the processed fragments
        :param overlap: overlap of the processed frames
        :param hop_length: The number of samples between successive frames, e.g., the columns of a spectrogram.
        :return:
        """
        super().__init__()
        self.verbose = verbose
        self.device = device
        self.target = target
        self.overlap = overlap
        self.dynamic_overlap = overlap
        self.hop_length = hop_length
        self.bits = bits
        self.indent = 550
        self.pad = 2
        self.batch_sizes = [1, 2, 4, 8, 16, 32, 64, 128, 256]
        self.ie = IECore()

        self.upsample_net = self.load_network(model_upsample)
        self.upsample_exec = self.create_exec_network(self.upsample_net)

        self.rnn_net = self.load_network(model_rnn)
        self.rnn_exec = self.create_exec_network(self.rnn_net, batch_sizes=self.batch_sizes)

        # fixed number of the mels in mel-spectrogramm
        self.mel_len = self.upsample_net.inputs['mels'].shape[1] - 2 * self.pad
        self.rnn_width = self.rnn_net.inputs['x'].shape[1]

    def load_network(self, model_xml):
        model_bin_name = ".".join(osp.basename(model_xml).split('.')[:-1]) + ".bin"
        model_bin = osp.join(osp.dirname(model_xml), model_bin_name)
        # Read IR
        log.info("Loading network files:\n\t{}\n\t{}".format(model_xml, model_bin))
        net = self.ie.read_network(model=model_xml, weights=model_bin)

        print("#################################################################")
        print("Model: {0}. Inputs: {1}".format(model_xml, net.inputs))
        print("#################################################################")
        print("Model: {0}. Outputs: {1}".format(model_xml, net.outputs))

        return net

    def create_exec_network(self, net, batch_sizes=None):
        if batch_sizes is not None:
            exec_net = []
            for b_s in batch_sizes:
                net.batch_size = b_s
                exec_net.append(self.ie.load_network(network=net, device_name=self.device))
        else:
            exec_net = self.ie.load_network(network=net, device_name=self.device)
        return exec_net

    @staticmethod
    def get_rnn_init_states(b_size=1, rnn_dims=328):
        h1 = np.zeros((b_size, rnn_dims), dtype=float)
        h2 = np.zeros((b_size, rnn_dims), dtype=float)
        x = np.zeros((b_size, 1), dtype=float)
        return h1, h2, x

    def forward(self, mels):
        n_parts = mels.shape[1] // self.mel_len + 1 if mels.shape[1] % self.mel_len > 0 else mels.shape[
                                                                                                 1] // self.mel_len
        upsampled_mels = []
        aux = []
        last_padding = 0
        for i in range(n_parts):
            i_start = i * self.mel_len
            i_end = i_start + self.mel_len
            if i_end > mels.shape[1]:
                last_padding = i_end - mels.shape[1]
                mel = np.pad(mels[:, i_start:mels.shape[1], :], ((0, 0), (0, last_padding), (0, 0)), 'constant',
                             constant_values=0)
            else:
                mel = mels[:, i_start:i_end, :]

            upsampled_mels_b, aux_b = self.forward_upsample(mel)
            upsampled_mels.append(upsampled_mels_b)
            aux.append(aux_b)
        if len(aux) > 1:
            upsampled_mels = np.concatenate(upsampled_mels, axis=1)
            aux = np.concatenate(aux, axis=1)
        else:
            upsampled_mels = upsampled_mels[0]
            aux = aux[0]
        if last_padding > 0:
            upsampled_mels = upsampled_mels[:, :-last_padding * self.hop_length, :]
            aux = aux[:, :-last_padding * self.hop_length, :]

        upsampled_mels, (_, self.dynamic_overlap) = fold_with_overlap(upsampled_mels, self.target, self.overlap)
        aux, _ = fold_with_overlap(aux, self.target, self.overlap)

        audio = self.forward_rnn(mels, upsampled_mels, aux)

        return audio

    def forward_upsample(self, mels):
        mels = pad_tensor(mels, pad=self.pad)

        out = self.upsample_exec.infer(inputs={"mels": mels})
        upsample_mels, aux = out["upsample_mels"][:, self.indent:-self.indent, :], out["aux"]
        return upsample_mels, aux

    def forward_rnn(self, mels, upsampled_mels, aux):
        wave_len = (mels.shape[1] - 1) * self.hop_length

        d = aux.shape[2] // 4
        aux_split = [aux[:, :, d * i:d * (i + 1)] for i in range(4)]

        b_size, seq_len, _ = upsampled_mels.shape

        if b_size not in self.batch_sizes:
            raise Exception('Incorrect batch size {0}. Correct should be 2 ** something'.format(b_size))

        active_network = self.batch_sizes.index(b_size)

        h1, h2, x = self.get_rnn_init_states(b_size, self.rnn_width)

        output = []

        for i in range(seq_len):
            m_t = upsampled_mels[:, i, :]

            a1_t, a2_t, a3_t, a4_t = \
                (a[:, i, :] for a in aux_split)

            out = self.rnn_exec[active_network].infer(inputs={"m_t": m_t, "a1_t": a1_t, "a2_t": a2_t, "a3_t": a3_t,
                                                              "a4_t": a4_t, "h1.1": h1, "h2.1": h2, "x": x})

            logits = out["logits"]
            h1 = out["h1"]
            h2 = out["h2"]

            sample = infer_from_discretized_mix_logistic(logits)

            x = sample[:]
            x = np.expand_dims(x, axis=1)
            output.append(sample)

        output = np.stack(output).transpose(1, 0)
        output = output.astype(np.float64)

        if b_size > 1:
            output = xfade_and_unfold(output, self.dynamic_overlap)
        else:
            output = output[0]

        fade_out = np.linspace(1, 0, 20 * self.hop_length)
        output = output[:wave_len]
        output[-20 * self.hop_length:] *= fade_out
        return output
