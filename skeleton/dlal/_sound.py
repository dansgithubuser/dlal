import soundfile as sf

import re as _re

class Sound:
    def __init__(self, samples, sample_rate):
        self.samples = samples
        self.sample_rate = sample_rate

    def to_flac(self, file_path):
        sf.write(file_path, self.samples, self.sample_rate, format='FLAC')

    def split(self, threshold=None, window_backward=400, window_forward=400):
        if threshold == None:
            threshold = max(self.samples) / 20
        silence = [{True: 1, False: 0}[abs(i) < threshold] for i in self.samples]
        windowed_silence = []
        w = sum(silence[:window_forward-1]) + window_backward
        for i, v in enumerate(silence):
            if i + window_forward < len(silence):
                w += silence[i + window_forward]
            else:
                w += 1
            if i - window_backward >= 0:
                w -= silence[i - window_backward]
            else:
                w -= 1
            windowed_silence.append(w == window_backward + window_forward - 1)
        result = []
        sound = None
        for i, v in enumerate(self.samples):
            if not windowed_silence[i]:
                if not sound:
                    sound = Sound([], self.sample_rate)
                sound.samples.append(v)
            elif sound:
                result.append(sound)
                sound = None
        if sound:
            result.append(sound)
        return result

def read(file_path):
    data, sample_rate = sf.read(file_path)
    return Sound([float(i) for i in data], sample_rate)

def i16le_to_flac(i16le_file_path, flac_file_path=None):
    if flac_file_path == None:
        flac_file_path = _re.sub(r'\.i16le$', '', i16le_file_path) + '.flac'
    data, sample_rate = sf.read(
        i16le_file_path,
        samplerate=44100,
        channels=1,
        format='RAW',
        subtype='PCM_16',
        endian='LITTLE',
    )
    sf.write(flac_file_path, data, sample_rate, format='FLAC')
