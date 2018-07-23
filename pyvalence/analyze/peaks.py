import scipy.signal as signal


def find_peaks(x, height=None, threshold=None,
               distance=None, prominence=None, width=None,
               wlen=None, rel_height=0.5):
    """ use scipy.signal find peaks ver batim atm
        https://docs.scipy.org/doc/scipy/reference/generated/scipy.signal.find_peaks.html#scipy.signal.find_peaks
    """
    peaks, _ = signal.find_peaks(
        x, height, threshold, distance, prominence, width, wlen, rel_height
    )
    return peaks


def integrate():
    pass
