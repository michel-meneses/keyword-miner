import os
import time
from multiprocessing import cpu_count
from pathlib import Path

import librosa
import soundfile as sf
from textgrid import textgrid
from tqdm.contrib.concurrent import process_map


def segment_audio_file(input_pair):
    """
    Callback function to segment an audio file individually, to be 
    passed as an argument for segmenting multiple files using 
    multiprocessing on Segmenter.segment().

    Parameters:
    input_pair -- One pair of corresponding audio and transcript files
    """
    audio_filepath, alignment_filepath, output_dir_path, sample_rate, min_segment_length_sec = input_pair
    tg = textgrid.TextGrid.fromFile(alignment_filepath)

    original_audio, _ = librosa.load(audio_filepath, sr=sample_rate)

    for segment in tg[0]:
        kwd = segment.mark
        begin = segment.minTime
        end = segment.maxTime

        interval_length = end - begin
        kwd_length = len(kwd)

        if kwd_length and interval_length > min_segment_length_sec:
            start_idx = int(begin * sample_rate)
            end_idx = int(end * sample_rate)
            output_audio = original_audio[start_idx:end_idx]

            output_filepath = output_dir_path / f'{kwd}_{time.time()}.wav'
            sf.write(output_filepath, output_audio, sample_rate, 'PCM_16')


class Segmenter:
    """Segment audio files, given its respective alignment files.

    Attributes
    ----------
    __output_dir_path : str
        The path where the output segmented audio files will be stored.
    __output_sample_rate : int
        The sample rate of the output audio files.
    __min_segment_length_sec : float
        The minimum length (in seconds) of the segmented audio files output by this class.
    __segmentation_chunk_size : int
        The size of each chunk distributed during the audio segmentation via multi-processing.

    Methods
    -------
    segment(List(audio_paths, alignment_paths)):
        Segments audio files from a list, given their respective alignment files.
    """

    def __init__(self, output_dir_path: Path):
        self.__output_dir_path = output_dir_path
        self.__output_sample_rate = 16000
        self.__min_segment_length_sec = 0.3
        self.__segmentation_chunk_size = 10

        os.makedirs(str(self.__output_dir_path), exist_ok=True)

    def segment(self, audio_alignment_pairs):
        """ Segments audio files using their respective alignment files.

        Parameters
        ----------
        List(audio_pth, alignment_pth):
            A list of pairs of paths to each input audio file and its corresponding output alignment file.
        """
        map_input = [(audio_filepath, align_filepath, self.__output_dir_path,
                     self.__output_sample_rate, self.__min_segment_length_sec)
                     for (audio_filepath, align_filepath) in
                     audio_alignment_pairs]

        _ = process_map(segment_audio_file, map_input,
                        desc="Segmenting the audio files into keywords",
                        max_workers=cpu_count(),
                        chunksize=self.__segmentation_chunk_size)
