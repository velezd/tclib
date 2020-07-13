from copy import copy
import os
import fnmatch

from .structures.testcase import TestCase
from .structures.requirement import Requirement
from .exceptions import CollisionError, UnknownParentError, DocfilesError

def _iter_documents(directory, pattern):
    for root, dirs, files in os.walk(directory):
        for filename in files:
            if fnmatch.fnmatchcase(filename, pattern):
                yield os.path.join(root, filename)

def diff(old, new):
    if old is None:
        old_requirements = set()
        old_cases = set()
    else:
        old_requirements = set(old.requirements)
        old_cases = set(old.testcases)
    new_requirements = set(new.requirements)
    new_cases = set(new.testcases)
    retval = {
        "removed" : {
            "testplans" : set(),
            "requirements" : old_requirements.difference(new_requirements),
            "testcases" : old_cases.difference(new_cases),
        },
        "added" : {
            "testplans" : set(),
            "requirements" : new_requirements.difference(old_requirements),
            "testcases" : new_cases.difference(old_cases),
        },
        "changed" : {
            "testplans" : set(),
            "requirements" : set(),
            "testcases" : set(),
        },
        "unchanged" : {
            "testplans" : set(),
            "requirements" : old_requirements.intersection(new_requirements),
            "testcases" : old_cases.intersection(new_cases),
        },
    }
    # WILL ACTIVATE LATER WHEN TESTPLANS ARE ADDED
    #for testplan_id in copy(retval["unchanged"]["testplans"]):
    #    if old.testplans[testplan_id] != new.testplans[testplan_id]:
    #        retval["unchanged"]["testplans"].remove(testplan_id)
    #        retval["changed"]["testplans"].add(testplan_id)
    for requirement_id in copy(retval["unchanged"]["requirements"]):
        if old.requirements[requirement_id] != new.requirements[requirement_id]:
            retval["unchanged"]["requirements"].remove(requirement_id)
            retval["changed"]["requirements"].add(requirement_id)
    for case_id in copy(retval["unchanged"]["testcases"]):
        if old.testcases[case_id] != new.testcases[case_id]:
            retval["unchanged"]["testcases"].remove(case_id)
            retval["changed"]["testcases"].add(case_id)
    return retval

class Library():
    def __init__(self, directory):
        self.directory = directory
        self.testcases = self._load_testcases()
        self.requirements = self._load_requirements()
        self._calculate_and_stabilize()

    def _load_testcases(self):
        return self._load_structures(self.directory, '*.tc.yaml', TestCase)

    def _load_requirements(self):
        return self._load_structures(self.directory, '*.req.yaml', Requirement)

    def _load_structures(self, directory, pattern, cls):
        """
        Load structures strored in files of name matching ``pattern`` from
        provided ``directory`` and use the ``cls`` to construct them.

        The structures are loaded in greedy way and in case there's an error
        which prevents constructing the structure, it's skipped and retried
        loading later (hoping that there's the missing information now present).
        """
        structures = dict()
        docfiles = list(_iter_documents(directory, pattern))
        while docfiles:
            docfile_loaded = False
            for docfile in copy(docfiles):
                try:
                    structure = cls(docfile, library=self, basedir=directory)
                except UnknownParentError:
                    continue
                try:
                    # try to find if structure of the same id
                    other = structures[structure.id]
                    raise CollisionError("Attempted to load two structures of the same type with the same id (name)", structure.filename, other.filename)
                except KeyError:
                    pass
                structures[structure.id] = structure
                docfiles.remove(docfile)
                docfile_loaded = True
            if not docfile_loaded:
                break
        if docfiles:
            raise DocfilesError(docfiles)
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