import soundfile as sf

import numpy as _np

import re as _re
import struct as _struct
import subprocess as _subprocess

class Sound:
    def __init__(self, samples, sample_rate=44100):
        self.samples = samples
        self.sample_rate = sample_rate

    def to_i16le(self, file_path='out.i16le'):
        with open(file_path, 'wb') as file:
            for sample in self.samples:
                i = int(sample * 0x7fff)
                if i > 0x7fff: i = 0x7fff
                elif i < -0x8000: i = -0x8000
                file.write(_struct.pack('<h', i))

    def to_flac(self, file_path='out.flac'):
        sf.write(file_path, self.samples, self.sample_rate, format='FLAC')

    def to_ogg(self, file_path='out.ogg'):
        # soundfile crashes!
        # https://github.com/bastibe/python-soundfile/issues/233
        # https://github.com/bastibe/python-soundfile/issues/266
        # https://github.com/bastibe/python-soundfile/issues/396
        # https://github.com/bastibe/python-soundfile/issues/426
        # sf.write(file_path, self.samples, self.sample_rate, format='OGG')
        self.to_flac('tmp.flac')
        p = _subprocess.run(f'ffmpeg -y -i tmp.flac {file_path}'.split(), stderr=_subprocess.PIPE)
        if p.returncode:
            raise Exception(f'ffmpeg returned non-zero exit status {p.returncode}\nstderr:\n{p.stderr.decode()}')

    def normalize(self):
        m = 1 / max(abs(i) for i in self.samples)
        self.samples = [i * m for i in self.samples]
        return self

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

    def play(self):
        self.to_i16le('tmp.i16le')
        _subprocess.run(f'aplay tmp.i16le --format=S16_LE --rate={self.sample_rate}'.split())

    def plot(self):
        import dansplotcore as dpc
        dpc.plot(self.samples)

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

def i16le_to_flac_stereo(i16le_file_path_l, i16le_file_path_r, flac_file_path):
    i16le_file_l = sf.SoundFile(
        i16le_file_path_l,
        samplerate=44100,
        channels=1,
        format='RAW',
        subtype='PCM_16',
        endian='LITTLE',
    )
    i16le_file_r = sf.SoundFile(
        i16le_file_path_r,
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
        channels=2,
        format='FLAC',
    )
    while True:
        data_l = i16le_file_l.read(frames=4096, always_2d=True)
        data_r = i16le_file_r.read(frames=4096, always_2d=True)
        if data_l.size == 0 or data_r.size == 0: break
        data = _np.concatenate((data_l, data_r), axis=1)
        flac_file.write(data)

def flac_to_flac_stereo(path_l, path_r, path):
    file_l = sf.SoundFile(path_l)
    file_r = sf.SoundFile(path_r)
    file = sf.SoundFile(
        path,
        mode='w',
        samplerate=44100,
        channels=2,
        format='FLAC',
    )
    while True:
        data_l = file_l.read(frames=4096, always_2d=True)
        data_r = file_r.read(frames=4096, always_2d=True)
        if data_l.size == 0 or data_r.size == 0: break
        data = _np.concatenate((data_l, data_r), axis=1)
        file.write(data)
