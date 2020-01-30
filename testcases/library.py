import os
import fnmatch

from .structures.testcase import TestCase
from .structures.requirement import Requirement

def _iter_documents(directories, pattern):
    for directory in directories:
        for root, dirs, files in os.walk(directory):
            for filename in files:
                if fnmatch.fnmatchcase(filename, pattern):
                    yield os.path.join(root, filename)

class Library():
    def __init__(self, directories=None):
        if directories is None:
            directories = []
        self.directories = directories
        self.testcases = self._load_testcases()
        self.requirements = self._load_requirements()
        self._calculate_and_stabilize()

    def _load_testcases(self):
        return self._load_structures(self.directories, '*.tc.yaml', TestCase)

    def _load_requirements(self):
        return self._load_structures(self.directories, '*.req.yaml', Requirement)

    def _load_structures(self, directories, pattern, cls):
        structures = dict()
        for docfile in _iter_documents(directories, pattern):
            structure = cls(docfile, library=self)
            structures[structure.id] = structure
        return structures

    def _calculate_and_stabilize_structures(self, structures):
        unstable = set(structures.keys())
        last_count = 0
        while len(unstable) != last_count:
            last_count = len(unstable)
            for structure_id in list(unstable):
                if structures[structure_id].stabilize():
                    unstable.remove(structure_id)
        return len(unstable) == 0

    def _calculate_and_stabilize(self):
        self._calculate_and_stabilize_structures(self.requirements)
        self._calculate_and_stabilize_structures(self.testcases)
