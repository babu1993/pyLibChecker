"""Requirement parser module"""
import os
import tomllib
from typing import Set

from packaging.requirements import Requirement


class RequirementInfo:
    """Data class for Requirement info"""

    def __init__(self, name):
        req = Requirement(name)
        self.name = req.name
        self.req = req

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        return f"name:{self.name}"


class RequirementParser:
    """Utility Class for requirement parser"""

    @staticmethod
    def req_path_generator(path, req_file_names=None, skip_path=None):
        """Scans and finds the requirement file location. This will
        scan for requirements.txt orr pyproject.toml. if anything other than
        this needs to be provided via args"""
        if req_file_names is None:
            req_file_names = ['pyproject.toml', 'requirements.txt']
        if skip_path is None:
            skip_path = ['site-packages']
        for path, _, files in os.walk(path):
            is_skip_path = any([x in path for x in skip_path])
            if is_skip_path:
                continue
            for file in files:
                if file in req_file_names:
                    yield os.path.join(path, file)


    @staticmethod
    def get_packages_from_requirements(**kwargs) -> Set[RequirementInfo]:
        """Parses requirement file and constructs requirement info"""
        requirements: Set[RequirementInfo] = set()
        req_files_location = kwargs.get("req_file")
        if not req_files_location:
            req_files_location = RequirementParser.req_path_generator(os.path.abspath(kwargs.get("project_root", ".")))
        for req_file_location in req_files_location:
            if req_file_location.endswith(".toml"):
                with open(req_file_location, 'rb') as f:
                    toml = tomllib.load(f)
                    for req in toml['project']['dependencies']:
                        requirements.add(RequirementInfo(req))
            else:
                with open(req_file_location, 'r') as f:
                    for req in f:
                        requirements.add(RequirementInfo(req))
        return requirements