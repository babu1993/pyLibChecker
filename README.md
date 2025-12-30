# pyLibLens
This is a lightweight utility library designed to audit your Python environment. It scans your installed packages and requirement files to identify outdated versions and provide a summary

## Installation
```commandline
pip install pyliblens
```


## Usage
This lib can be used as both cli tool as well as python lib.

Using in Python 

```
from pyliblens import analyze_packages
# Need to provide the project source if the current file is not in the root directory
packages = analyze_packages()
```

using cli (use --help for details)

```commandline
pyliblens
```

for report export use below commands
```commandline
pip install pyliblens[report]
pyliblens -ex
```
this will create a index.html report for use.


