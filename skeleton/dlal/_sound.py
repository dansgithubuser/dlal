import soundfile as sf

import re as _re

class Sound:
    def __init__(self, samples, sample_rate):
        self.samples = samples
        self.sample_rate = sample_rate

    def to_flac(self, file_path):
        sf.write(file_path, self.samples, self.sample_rate, format='FLAC')

    def split(self, threshold=0, window_backward=400, window_forward=400):
        '''
        Split sound at each sample where window is entirely below threshold (discard the quiet parts).
        Yielded sounds will have start_sample and start_time set.
        '''
        # find where the window is below threshold
        silence = [{True: 1, False: 0}[abs(i) <= threshold] for i in self.samples]
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
        # yield sounds
        sound = None
        for i, v in enumerate(self.samples):
            if not windowed_silence[i]:
                # sound
                if not sound:
                    sound = Sound([], self.sample_rate)
                    sound.start_sample = i
                    sound.start_time = i / self.sample_rate
                sound.samples.append(v)
            elif sound:
                # silence, sound until now
                yield sound
                sound = None
        if sound:
            yield sound

    def copy(self, start=0, end=-1):
        start *= self.sample_rate
        if end < 0:
            end = len(self.samples) + (end + 1) * self.sample_rate
        else:
            end *= self.sample_rate
        start = int(start)
        end = int(end)
        return Sound(self.samples[start:end], self.sample_rate)

def read(file_path, channel=0):
    data, sample_rate = sf.read(file_path, always_2d=True)
    return Sound([float(i[channel]) for i in data], sample_rate)

def i16le_to_flac(i16le_file_path, flac_file_path=None):
    if flac_file_path == None:
        flac_file_path = _re.sub(r'\.i16le$', '', i16le_file_path) + '.flac'
    i16le_file = sf.SoundFile(
        i16le_file_path,
        samplerate=44100,
        channels=1,
        format='RAW',
        subtype='PCM_16',
        endian='LITTLE',
    )
    flac_file = sf.SoundFile(
        flac_file_path,
        mode='w',
        samplerate=44100,
        channels=1,
        format='FLAC',
    )
    while True:
        data = i16le_file.read(frames=4096, always_2d=True)
        if data.size == 0: break
        flac_file.write(data)
