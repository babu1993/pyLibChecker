"""Import info module"""
import ast
import logging
import os

logger = logging.getLogger(__file__)

class ImportInfo:
    """Gathers info about imports in the projects.
    it captures the files in which it is used.
    """
    def __init__(self, file_path, root_module):
        self.file_paths = {file_path}
        self.root_module = root_module

    def json(self):
        return list(self.file_paths)
    def __repr__(self):
        return f"file_path:{self.file_paths}"

    @staticmethod
    def get_import_info(path: str, site_packages=None, encoding='utf-8') -> dict:
        """Utility method for analyzing the imports in the project
        Args:
            path: root path of the project
            site_packages: site packages location, will be used to skip library src file analysis
            encoding: python file encoding
        Returns:
            dict: {package_name: Info}
        """
        if not site_packages:
            site_packages = []
        raw_imports = set()
        for root, dirs, files in os.walk(path):
            if any([root.startswith(site_package_path) for site_package_path in site_packages ]):
                continue
            for file in files:
                if file.endswith('.py'):
                    file_path = os.path.join(root, file)
                    try:
                        with open(file_path, 'r', encoding=encoding) as f:
                            contents = f.read()
                            tree = ast.parse(contents)
                            for node in ast.walk(tree):
                                if isinstance(node, ast.Import):
                                    for sub_node in node.names:
                                        raw_imports.add((sub_node.name, file_path))
                                elif isinstance(node, ast.ImportFrom):
                                    raw_imports.add((node.module, file_path))
                    except Exception as e:
                        print(f"Error reading file {file_path}: {e}")
        imports_from_source:dict = {}
        for raw_import in [n for n in raw_imports if n]:
            cleaned_name = None
            if raw_import[0]:
                cleaned_name, _, _ = raw_import[0].partition(".")
            else:
                logger.info(f"No module:{raw_import}")
            if cleaned_name:
                if cleaned_name in imports_from_source:
                    imports_from_source[cleaned_name].file_paths.add(raw_import[1])
                else:
                    imports_from_source[cleaned_name] = ImportInfo(file_path=raw_import[1], root_module=cleaned_name)
        return imports_from_source