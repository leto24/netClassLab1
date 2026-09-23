import math
SPEED_OF_LIGHT = 3e8 # meters per second
# Task 1: Return the period T (seconds) of a signal with frequency f (Hz)
def period(f):
    return 1/f
# Task 2: Return the wavelength (meters) of a signal with frequency f (Hz)
def wavelength(f):
    return SPEED_OF_LIGHT/f

# Task 3: Return the bandwidth (Hz) given the lowest and highest frequencies
def bandwidth(f_min, f_max):
    return f_max - f_min

# Task 4: Return the attenuation (dB) given input and output power
def attenuation_db(p_in, p_out):
    return 10 * math.log10(p_in/p_out)

# Task 5: Return the Nyquist capacity (bps) for bandwidth B and M signal levels
def nyquist_capacity(B, M):
    return 2 * B * math.log2(M)
# Task 6: Return the Shannon capacity (bps) for bandwidth B and SNR in dB
def shannon_capacity(B, snr_db):
    snr = 10 ** (snr_db / 10)
    return B * math.log2(1 + snr)

# ----- Do not change anything below this line -----
print("Task 1: Period of 2 Hz signal =", period(2), "seconds")
print("Task 2: Wavelength of 100 MHz FM radio =", wavelength(100e6), "meters")
print("Task 3: Bandwidth of 1000 Hz to 3000 Hz =", bandwidth(1000, 3000), "Hz")
print("Task 4: Loss from 10 mW to 5 mW =", round(attenuation_db(10, 5), 2), "dB")
print("Task 5: Nyquist, B = 3100 Hz, M = 2 =", nyquist_capacity(3100, 2), "bps")
print("Task 5: Nyquist, B = 3100 Hz, M = 8 =", nyquist_capacity(3100, 8), "bps")
print("Task 6: Shannon, B = 1 MHz, SNR = 24 dB =",
round(shannon_capacity(1e6, 24) / 1e6, 2), "Mbps")