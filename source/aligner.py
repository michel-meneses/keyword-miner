import os
import shutil
from multiprocessing import cpu_count
from pathlib import Path

from tqdm.contrib.concurrent import process_map

from datasets.transcribed_dataset import TranscribedDataset


def get_audio_alignment_pairs(input_tuple):
    """Returns the paths to the pair of corresponding audio and alignment files.

    Returns the paths to the pair of corresponding audio and alignment 
    files, given the path to the alignment file. Folders and files names
    and placement must follow the same pattern inside each root folder.

    Parameters
    ----------
    input_tuple:
        A tuple of the paths to the transcript file, to its root folder and to the audio files root folders.

    Returns
    -------
    [(audio_file_path, alignment_file_path)]: 
        A single pair of paths to the audio file and its respective transcript file.
    """
    alignment_file_path, alignment_root_path, audio_root_path = input_tuple
    audio_file_path = alignment_file_path.replace(alignment_root_path, audio_root_path)
    audio_file_path = audio_file_path.replace('.TextGrid', '.wav')
    return audio_file_path, alignment_file_path


class Aligner:
    """This class points out the timestamp of keywords in transcribed speech audio files.

    Attributes
    ----------
    __input_dataset_path : Path
        The root path of the input transcribed dataset.
    __language : str 
        The language of the model, the recordings and transcripts, to be used for FA.
    __align_temp_dir -- The path to where this aligner outputs its 
    temporary alignment files.
    __input_lexicon_path -- Path to the lexicon dictionary used by this 
    aligner's ASR model.
    __clear_cache -- Indicates if this aligner's cache should be cleared
     before aligning a new dataset.
    __multiprocessing_chunk_size -- The size of each chunk distributed 
    during multi-processing.

    Methods:
    align() -- Generates a timestamp alignment file for each audio file 
    within the input dataset.
    __clear_garbage() -- Deletes the intermediate output files generated
    during the alignment.
    """

    def __init__(self, input_dataset: TranscribedDataset, input_lexicon_path: Path, clear_cache):
        self.__input_dataset_path = input_dataset.root_path
        self.__language = input_dataset.language
        temp_dir_name = f'{self.__input_dataset_path.stem}_temp_alignment'
        self.__align_temp_dir = self.__input_dataset_path.parent / temp_dir_name
        self.__input_lexicon_path = input_lexicon_path
        self.__clear_cache = clear_cache
        self.__multiprocessing_chunk_size = 10

        os.makedirs(str(self.__align_temp_dir), exist_ok=True)

    def align(self):
        """Generates a timestamp alignment file (.TextGrid) for each audio file within the input dataset.

        Returns
        -------
        audio_alignment_pairs:
            A list of paired paths pointing to corresponding input audio and output alignment files.
        """

        cache_tag = '-c' if self.__clear_cache else ''
        os.system(
            f'mfa align '
            f'{self.__input_dataset_path} {self.__input_lexicon_path} '
            f'{self.__language} {self.__align_temp_dir} '
            f'{cache_tag} -j {2}'
        )
        align_paths = [str(path.absolute()) for path in self.__align_temp_dir.rglob('*.TextGrid')]
        alignment_root_path_str, audio_root_path = str(self.__align_temp_dir), str(self.__input_dataset_path)
        map_inputs = [(align_path, alignment_root_path_str, audio_root_path) for align_path in align_paths]
        audio_alignment_pairs = process_map(
            get_audio_alignment_pairs, map_inputs,
            desc='Associating alignment with audio files',
            max_workers=cpu_count(),
            chunksize=self.__multiprocessing_chunk_size)
        return audio_alignment_pairs

    def clear_garbage(self):
        """Deletes intermediate output files generated during the alignment."""
        shutil.rmtree(self.__align_temp_dir)
