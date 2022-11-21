import abc
from pathlib import Path


class TranscribedDataset(metaclass=abc.ABCMeta):
    """This interface defines the boundary of a transcribed speech dataset.

    Attributes
    ----------
    _root_path : Path
        The path to the root folder of this dataset.
    _language : str
        The language of this dataset (compatible to the aligner implementation).
    _multiprocessing_chunk_size : int
        A parameter of the tqdm multiprocessing library.

    Methods
    -------
    _preprocess():
        Must format the this dataset to make it compatible to the aligner.    
    """

    def __init__(self, root_path: Path, language: str):
        self._root_path = root_path
        self._language = language
        self._multiprocessing_chunk_size = 10
        self._preprocess()

    @property
    def root_path(self):
        return self._root_path

    @property
    def language(self):
        return self._language

    @classmethod
    def __subclasshook__(cls, subclass):
        return (hasattr(subclass, '_preprocess')
                and callable(subclass._preprocess)
                or NotImplemented)

    @abc.abstractmethod
    def _preprocess(self):
        """Must format the this dataset to make it compatible to the aligner."""
        raise NotImplementedError
