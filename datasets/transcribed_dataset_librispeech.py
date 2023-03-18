import os
from pathlib import Path
from multiprocessing import cpu_count
from datasets.transcribed_dataset import TranscribedDataset

from tqdm.contrib.concurrent import process_map

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
    os.chmod(audio_filepath, 0o777)
    os.remove(audio_filepath)


def create_labels_from_transcript(trans_filepath_str):
    """Exports the lines of the input transcript file as individual .lab files for each audio file.

    Parameters
    ----------
    trans_filepath_str : str 
        The absolute path to the input transcript file.
    """
    trans_filepath = Path(trans_filepath_str)
    trans_parent = trans_filepath.parent

    with open(trans_filepath, 'r') as file:
        labels_list = file.readlines()

    for label in labels_list:
        first_space_idx = label.find(' ')
        label_filename = trans_parent / label[:first_space_idx]
        label_filename = label_filename.with_suffix('.lab')

        label_text = label[first_space_idx + 1:].strip()

        with open(label_filename, 'w') as file:
            file.write(label_text)


class TranscribedDatasetLibriSpeech(TranscribedDataset):
    """Implementation of a transcribed dataset compatible with the input format of LibriSpeech."""

    def __init__(self, root_path, language):
        super(TranscribedDatasetLibriSpeech, self).__init__(root_path, language)

    def _preprocess(self):
        """Formats this dataset to make it compatible to the aligner.

        All the .flac audio files are converted to .wav and their original copies are deleted. 
        Additionally, a .lab file is created for each .wav audio file based on the transcript files
        with extension .trans.txt.
        """

        audio_path_list_wav = [str(path.absolute()) for path in self._root_path.rglob('*.wav')]
        print(f"{len(audio_path_list_wav)} .wav audio files available.")

        audio_path_list_flac = [str(path.absolute()) for path in self._root_path.rglob('*.flac')]
        print(f"{len(audio_path_list_flac)} .flac audio files available.")

        if len(audio_path_list_flac):
            process_map(convert_to_wav, audio_path_list_flac,
                        desc="Converting audio files to .wav",
                        max_workers=cpu_count(),
                        chunksize=self._multiprocessing_chunk_size)
            process_map(delete_audio_file, audio_path_list_flac,
                        desc="Deleting the .flac files",
                        max_workers=cpu_count(),
                        chunksize=self._multiprocessing_chunk_size)

        trans_paths_list = [str(path.absolute()) for path in self._root_path.rglob('*.trans.txt')]
        print(f"{len(trans_paths_list)} transcripts found.")

        process_map(create_labels_from_transcript, trans_paths_list,
                    desc="Creating the .lab files", max_workers=cpu_count())
        print('Transcribed dataset is ready!')
