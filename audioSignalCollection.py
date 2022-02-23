import pyaudio
import wave
import audioop
import numpy as np
import threading
from scipy.signal import butter, lfilter
from scipy.io.wavfile import write, read
import tkinter as tk

form_1 = pyaudio.paInt16 # 16-bit resolution
chans = 1 # 1 channel
samp_rate = 48000 # 48 kHz sampling rate
lowcut = 400 # hi-pass filter
highcut = 3000 # low-pass filter
chunk = 1024 # samples for buffer
record_secs = 3 # seconds to record
dev_index0 = 2 # device index found by p.get_device_info_by_index(ii)
dev_index1 = 3
audio = pyaudio.PyAudio() # create pyaudio instantiation

# bandpass filter
def butter_bandpass(lowcut, highcut, samp_rate, order=5):
    nyq = 0.5 * samp_rate
    low = lowcut / nyq
    high = highcut / nyq
    b, a = butter(order, [low, high], btype='band', analog=False)
    return b, a

def butter_bandpass_filter(data, lowcut, highcut, samp_rate, order=5):
    b, a = butter_bandpass(lowcut, highcut, samp_rate, order=order)
    y = lfilter(b, a, data)
    return y

# store data into frame array
def mic0():
    global frames0, max0
    frames0 = []
    rms0 = []
    # loop through stream and append audio chunks to frame array
    for ii in range(0,int((samp_rate/chunk)*record_secs)):
        data0 = stream0.read(chunk, exception_on_overflow=False)
        frames0.append(data0)
        rms0.append(audioop.rms(data0, 2))
        max0 = np.max(rms0) 
      
def mic1():
    global frames1, max1
    frames1 = []
    rms1 = []
    # loop through stream and append audio chunks to frame array
    for ii in range(0,int((samp_rate/chunk)*record_secs)):
        data1 = stream1.read(chunk, exception_on_overflow=False)
        frames1.append(data1)
        rms1.append(audioop.rms(data1,2))
        max1 = np.max(rms1)
        
def save_wav():
    #dt = str(datetime.datetime.now())
    wav_output_filename = 'mic1.wav' # name of .wav file
    wavefile = wave.open(wav_output_filename,'wb')
    wavefile.setnchannels(chans)
    wavefile.setsampwidth(audio.get_sample_size(form_1))
    wavefile.setframerate(samp_rate)
    wavefile.writeframes(b''.join(frames0))
    wavefile.close()

    #dt = str(datetime.datetime.now())
    wav_output_filename = 'mic2.wav' # name of .wav file
    wavefile = wave.open(wav_output_filename,'wb')
    wavefile.setnchannels(chans)
    wavefile.setsampwidth(audio.get_sample_size(form_1))
    wavefile.setframerate(samp_rate)
    wavefile.writeframes(b''.join(frames1))
    wavefile.close()

def close_stream(s):
    s.stop_stream()
    s.close()

def filtering():
    # filtering and rms calculation
    samplerate, data_unfiltered = read('mic1.wav')
    max_int16 = 2**15
    y = butter_bandpass_filter(data_unfiltered, lowcut, highcut, samplerate, order=5)
    write('mic1_filtered.wav', samplerate, y / max_int16)
          
    samplerate, data_filtered = read('mic1_filtered.wav')
    data_filtered = (data_filtered * max_int16).astype(np.int16)
    rms_filtered = []
    for i in range(0, 240000, 1024):
        j = i + 1024
        sub = data_filtered[i:j]
        rms_filtered.append(audioop.rms(sub, 2))
        max_filtered_1 = np.max(rms_filtered)

    # max rms of filtered mic1
    print("Mic 1 rms filtered: ", max_filtered_1)
    m1_filtered = tk.Label(master=frame, text="Mic 1 rms filtered: "+str(max_filtered_1), bg="#DBDEE0")
    m1_filtered.place(x=260, y = 70)

    samplerate, data_unfiltered = read('mic2.wav')
    y = butter_bandpass_filter(data_unfiltered, lowcut, highcut, samplerate, order=5)
    write('mic2_filtered.wav', samplerate, y / max_int16)
          
    samplerate, data_filtered = read('mic2_filtered.wav')
    data_filtered = (data_filtered * max_int16).astype(np.int16)
    rms_filtered = []
    for i in range(0, 240000, 1024):
        j = i + 1024
        sub = data_filtered[i:j]
        rms_filtered.append(audioop.rms(sub, 2))
        max_filtered_2 = np.max(rms_filtered)

    # max rms of filtered mic2
    print("Mic 2 rms filtered: ", max_filtered_2)
    m2_filtered = tk.Label(master=frame, text="Mic 2 rms filtered: "+str(max_filtered_2), bg="#DBDEE0")
    m2_filtered.place(x=260, y = 90)

    if (max_filtered_1 + max_filtered_2)/2 > 4000:
        print("Car Detected")
        result = tk.Label(master=frame, text="Car Detected", bg="#DBDEE0")
        result.place(x=180, y = 120)
    else:
        result = tk.Label(master=frame, text="Car not Detected", bg="#DBDEE0")
        result.place(x=170, y = 120)
    print("End")


def startAudio():
    print("Start")
    global stream0, stream1
    # create pyaudio stream
    stream0 = audio.open(format = form_1,rate = samp_rate,channels = chans, \
                        input_device_index = dev_index0,input = True, \
                        frames_per_buffer=chunk)
    print("recording mic 1")

    stream1 = audio.open(format = form_1,rate = samp_rate,channels = chans, \
                        input_device_index = dev_index1,input = True, \
                        frames_per_buffer=chunk)
    print("recording mic 2")
    
    # start threading to call record simultaneously
    t1 = threading.Thread(target=mic0)
    t2 = threading.Thread(target=mic1)
    t1.start()
    t2.start()
    t1.join()
    t2.join()
    
    save_wav()
    
    # stop the stream, close it, and terminate the pyaudio instantiation
    close_stream(stream0)
    close_stream(stream1)
    
    print("Mic 1 rms unfiltered: ", max0)
    print("Mic 2 rms unfiltered: ", max1)
    m1_unfiltered = tk.Label(master=frame, text="Mic 1 rms unfiltered: "+str(max0), bg="#DBDEE0")
    m1_unfiltered.place(x=30, y = 70)
    m2_unfiltered = tk.Label(master=frame, text="Mic 2 rms unfiltered: "+str(max1), bg="#DBDEE0")
    m2_unfiltered.place(x=30, y = 90)

    filtering()

if __name__ == "__main__":
    window = tk.Tk()
    frame = tk.Frame(master=window, width=460, height=180, bg="#DBDEE0")
    frame.pack(fill=tk.BOTH, expand=True)
    title = tk.Label(master=frame, text="Vehicle Detection for UAD", bg="#DBDEE0")
    title.place(x=140, y=0)

    button = tk.Button(window, text="Start", command = startAudio)
    button.place(x=200, y=30)

