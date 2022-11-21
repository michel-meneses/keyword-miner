import os
import re
from multiprocessing import cpu_count
from pathlib import Path

import numpy as np
import pandas as pd
from tqdm.contrib.concurrent import process_map

from datasets.transcribed_dataset import TranscribedDataset

__output_sample_rate = 16000


def convert_to_wav(audio_filepath):
    """Converts an audio file (in any format) to a .wav file with a sampling rate of 16kHz.

    Parameters
    ----------
    audio_filepath : str 
        The absolute path to the input audio file.
    """
    output_filepath = Path(audio_filepath).with_suffix('.wav')
    os.system(
        f"ffmpeg -hide_banner -loglevel panic -i "
        f"{audio_filepath} -ar {__output_sample_rate} {output_filepath}"
    )


def delete_audio_file(audio_filepath):
    """Deletes the specified audio file."""
    os.remove(audio_filepath)


def create_labels_from_transcript(path_transcript_pair):
    """Exports the lines of the input transcript file as individual .lab files for each audio file.

    Parameters
    ----------
    trans_filepath_str : str 
        The absolute path to the input transcript file.
    """
    filepath = path_transcript_pair[0].with_suffix('.lab')
    content = path_transcript_pair[1]

    content = content.upper()
    content = re.sub(r'[^\w\s]', '', content)
    first_space_idx = content.find(' ')
    if first_space_idx == 0:
        content = content[1:]

    with open(filepath, 'w', encoding='utf-8') as file:
        file.write(content)


class TranscribedDatasetMozilla(TranscribedDataset):
    """Implementation of a transcribed dataset compatible with the input format of Mozilla Common Voice."""
    
    def __init__(self, root_path, language):
        super(TranscribedDatasetMozilla, self).__init__(root_path, language)

    def _preprocess(self):
        """Formats this dataset to make it compatible to the aligner.

        All the .mp3 audio files are converted to .wav and their original copies are deleted. 
        Additionally, a .lab file is generated for each .wav audio file based on the transcript 
        files with extension .trans.txt.
        """

        audio_path_list_wav = [str(path.absolute()) for path in self._root_path.rglob('*.wav')]
        print(f"{len(audio_path_list_wav)} .wav audio files available.")

        audio_path_list_mp3 = [str(path.absolute()) for path in self._root_path.rglob('*.mp3')]
        print(f"{len(audio_path_list_mp3)} .mp3 audio files available.")

        if len(audio_path_list_mp3):
            process_map(convert_to_wav, audio_path_list_mp3,
                        desc="Converting audio files to .wav",
                        max_workers=cpu_count(),
                        chunksize=self._multiprocessing_chunk_size)
            process_map(delete_audio_file, audio_path_list_mp3,
                        desc="Deleting the .mp3 files",
                        max_workers=cpu_count(),
                        chunksize=self._multiprocessing_chunk_size)

        transcript_tsv = self._root_path / 'validated.tsv'
        transcript_df = pd.read_csv(transcript_tsv, sep='\t', low_memory=False)
        transcript_filtered_df = transcript_df[['path', 'sentence']].dropna()
        print(f"{len(transcript_filtered_df)} transcripts found.")

        trans_parent = self._root_path / 'clips'
        path_transcript_pair = [(trans_parent / elem[0], elem[1]) for elem in
                                np.array(transcript_filtered_df)]

        process_map(create_labels_from_transcript, path_transcript_pair,
                    desc="Creating the .lab files", max_workers=cpu_count())
        print('Transcribed dataset is ready!')
