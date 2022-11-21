import argparse
import configparser
import sys
from pathlib import Path

from datasets.transcribed_dataset_librispeech import TranscribedDatasetLibriSpeech
from datasets.transcribed_dataset_mozilla import TranscribedDatasetMozilla
from source.aligner import Aligner
from source.segmenter import Segmenter


def print_banner():
    banner = r"""
 +-+-+-+-+-+-+-+ +-+-+-+-+-+
 |K|e|y|w|o|r|d| |M|i|n|e|r|
 +-+-+-+-+-+-+-+ +-+-+-+-+-+
 """
    print(banner)


def get_args():
    parser = argparse.ArgumentParser(
        description="Arguments to run Keyword Miner")
    parser.add_argument('-c', '--config', type=str,
                        default='inputs/configs/local_mozilla.conf',
                        help="Path to a config file.")
    return vars(parser.parse_args(args=sys.argv[1:]))


def get_config(config_filepath):
    config_parser = configparser.ConfigParser()
    config_parser.read(config_filepath)
    return config_parser


def run(config):
    general_config = config['General']

    input_ds_name = general_config.get('input_dataset_name')
    input_dir_path = Path(general_config.get('input_dir_path'))
    input_lexicon_path = Path(general_config.get('input_lexicon_path'))
    output_dir_path = Path(general_config.get('output_dir_path'))
    language = general_config.get('language')
    clear_cache = general_config.getboolean('clear_cache')

    assert input_dir_path and output_dir_path, "You must inform the input and output dir paths in the config."

    if input_dir_path == 'librispeech':
        dataset = TranscribedDatasetLibriSpeech(input_dir_path, language)
    elif input_dir_path == 'mozilla':
        dataset = TranscribedDatasetMozilla(input_dir_path, language)
    else:
        raise NameError(f'Input dataset name not supported yet: {input_ds_name}')

    aligner = Aligner(dataset, input_lexicon_path, clear_cache)
    segmenter = Segmenter(output_dir_path)

    audio_alignment_pairs = aligner.align()
    segmenter.segment(audio_alignment_pairs)
    aligner.clear_garbage()

    output_audio_paths_list = [str(path.absolute()) for path in output_dir_path.rglob('*.wav')]
    print(f"{len(output_audio_paths_list)} .wav audio files generated.")
    print('Finished!')


if __name__ == '__main__':
    print_banner()
    args = get_args()
    config_args = get_config(args.get('config'))
    run(config_args)
