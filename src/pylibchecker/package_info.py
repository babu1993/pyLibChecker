"""Package module"""
import csv
import logging
import os
import site
from enum import Enum
from typing import Set

import yarg
from packaging.metadata import parse_email

from .import_info import ImportInfo
from .requirement_parser import RequirementParser, RequirementInfo

logger = logging.getLogger(__file__)

class Status(Enum):
    """Package status"""
    TICK = ("\U00002713", "UP_TO_DATE")
    UPDATE = ("\U00002B06", "REQUIRES_UPDATE")
    NOT_USED = ("\U0000274C", "NOT_USED")

class PackageInfo:
    """Information class which holds analysis summary"""
    # Python installation locations
    package_locations = site.getsitepackages()
    package_locations.append(site.getusersitepackages())
    # Complete installed packages
    installed_packages = []

    def __init__(self, **kwargs):
        self.name = kwargs["name"]
        self.current_version = kwargs["version"]
        self.latest_version = kwargs.get("latest_version")
        self.root_modules = kwargs.get("root_modules", {})
        self.url = kwargs.get('url')
        self.import_info = kwargs.get("import_info", None)
        self.used = False
        self.up_to_date = False

    def get_status(self) -> Status:
        """Utility method for getting status"""
        status = Status.TICK if self.up_to_date else Status.UPDATE
        status = status if self.used else Status.NOT_USED
        return status

    def __eq__(self, other):
        return self.name == other.name

    def __hash__(self):
        return hash(self.name)

    def __repr__(self):
        status = self.get_status()
        return (f"name:{self.name} | current_version:{self.current_version} | "
                f"latest_version:{self.latest_version} | "
                f"{self.import_info} | {status.value[0]}")
    def json(self, root_path:str):
        """Exports details in json format"""
        status = self.get_status()
        json_dict = {"name": self.name, "current_version": self.current_version,
                     "latest_version": self.latest_version, "url": self.url,
                     "status": status.value[1]}
        info_dict = self.import_info.json() if self.used else []
        root_path = root_path.removesuffix(os.sep)
        json_dict['import_info'] = [info.removeprefix(root_path) for info in info_dict]
        return json_dict

    @staticmethod
    def to_json(**kwargs):
        """Utility function for json export"""
        root_path = kwargs.get("project_root", "")
        if PackageInfo.installed_packages:
            json_list = [package.json(root_path) for package in PackageInfo.installed_packages]
            return json_list
        return []

    @staticmethod
    def get_installed_packages(**kwargs):
        """Main function for analyzing the installed packages. It does following steps
         1. Gets the list of library from requirements
         2. Fetches the installed packages and compare it with requirements
         3. Cross-checks the source code and marks unused packages
         4. Finally updates the latest version from pypi

         This library uses PEP-427 standard(https://peps.python.org/pep-0427/#the-dist-info-directory), any
         deviation in dist-info will be neglected

        """
        requirements: Set[RequirementInfo] = RequirementParser.get_packages_from_requirements(**kwargs)
        for pkg_location in PackageInfo.package_locations:
            if not os.path.exists(pkg_location):
                logger.info(f"Package location not exist:{pkg_location}")
                continue
            for pkg in os.listdir(pkg_location):
                if pkg.strip().endswith(".dist-info"):
                    installed_python_file_list = []
                    try:
                        with open(os.path.join(pkg_location, pkg, 'RECORD'), 'r', encoding='utf-8') as f:
                            reader = csv.reader(f)
                            for row in reader:
                                if row[0].endswith('.py') and not row[0].startswith('_'):
                                    installed_python_file_list.append(row[0])
                        with open(os.path.join(pkg_location, pkg, 'METADATA'), 'r', encoding='utf-8') as f:
                            info, _ = parse_email(f.read())
                        package_info = PackageInfo(name=info['name'], version=info['version'])
                        if package_info in requirements:
                            if installed_python_file_list:
                                package_info.root_modules = set(
                                    map(lambda x: x.split("/", 1)[0], installed_python_file_list))
                            PackageInfo.installed_packages.append(package_info)
                    except FileNotFoundError as e:
                        logger.info(f"File not found: {e.filename}")
                        continue
                    except Exception as e:
                        logger.exception(e)
                        continue
        imports = ImportInfo.get_import_info(path=kwargs.get('project_root', '.'),
                                             site_packages=PackageInfo.package_locations,
                                             encoding=kwargs.get('encoding', 'utf-8'))

        for package in PackageInfo.installed_packages:
            for module in package.root_modules:
                package.import_info = imports.get(module)
            if package.import_info:
                package.used = True
                y_pkg = yarg.get(package.name)
                if not y_pkg:
                    print(f"Package not found in PyPI: {package.name}")
                    continue
                package.latest_version = y_pkg.latest_release_id
                package.url = y_pkg.pypi_url
                package.up_to_date = package.latest_version == package.current_version
            else:
                package.used=False


