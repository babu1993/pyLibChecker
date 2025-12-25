"""Main module for pyLibChecker"""
import argparse
import datetime
import json
import os
import sys

from .package_info import PackageInfo

# Command Line Arg parsers
parser = argparse.ArgumentParser(description="Analyzes the installed python packages and provides a report")
parser.add_argument('-v', '--version', action='version', version='%(prog)s 1.0')
parser.add_argument("-pr", "--project_root", help="Specify the root folder for scanning", default=".")
parser.add_argument("-e", "--encoding", help="Specify the file encoding", default="utf-8")
parser.add_argument('-rq', '--req_file', help='Path to requirements.txt or pyproject.toml file', default=None)
parser.add_argument('-ex', '--export', action='store_true', help="Flag for exporting results as html", default=False)

# Jinja Template for result export
REPORT_TEMPLATE = """
<!DOCTYPE html>
<html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>{{project.name}} - pyLibChecker</title>
        <style>
            :root {
                --bg-color: #121212;
                --panel-bg: #1e1e1e;
                --accent-yellow: #f1c40f;
                --accent-blue: #3498db;
                --text-main: #d4d4d4;
                --text-muted: #666; /* Slightly darker for secondary info */
                --border-color: #333;
            }
    
            body {
                background-color: var(--bg-color);
                color: var(--text-main);
                font-family: 'Consolas', 'Monaco', monospace;
                display: flex;
                flex-direction: column; /* Allow content to stack */
                justify-content: center;
                align-items: center;
                min-height: 100vh;
                margin: 0;
                padding: 20px;
            }
    
            .log-panel {
                width: 90%;
                max-width: 800px;
                background-color: var(--panel-bg);
                border: 1px solid var(--border-color);
                border-radius: 8px;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
                overflow: hidden;
                display: flex;
                flex-direction: column;
            }
    
            /* Standard details/summary styling */
            details {
                border-bottom: 1px solid var(--border-color);
            }
    
            summary {
                list-style: none;
                padding: 20px;
                cursor: pointer;
                display: flex;
                flex-direction: column;
                gap: 8px;
            }
    
            summary:hover { background-color: #252525; }
    
            .log-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
            }
    
            .project-name { color: var(--accent-blue); font-weight: bold; font-size: 1.4rem }
    
            .meta-group {
                display: flex;
                gap: 15px;
                font-size: 0.85rem;
            }
    
            .version-tag {
                color: var(--accent-yellow);
                border: 1px solid var(--accent-yellow);
                padding: 1px 5px;
                border-radius: 3px;
            }
    
            .timestamp { color: var(--text-muted); }
    
            .content {
                padding: 0 20px 20px;
                color: #aaa;
                font-size: 0.95rem;
            }
    
            /* Footer Styling */
            .panel-footer {
                background-color: #181818;
                padding: 15px 20px;
                border-top: 1px solid var(--border-color);
                text-align: center;
                font-size: 0.75rem;
                color: var(--text-muted);
            }
    
            .panel-footer a {
                color: var(--accent-blue);
                text-decoration: none;
            }
            select {
                background: var(--panel-bg);
                color: var(--text-main);
                border: 1px solid var(--border-color);
                padding: 8px 12px;
                border-radius: 4px;
                cursor: pointer;
                font-family: inherit;
            }
            .panel-footer a:hover { text-decoration: underline; }
            .table-container {
                width: 100%;
                max-width: 800px;
                background: var(--panel-bg);
                border-radius: 8px;
                border: 1px solid var(--border-color);
                overflow: hidden;
                box-shadow: 0 10px 30px rgba(0,0,0,0.5);
            }
    
            table {
                width: 100%;
                border-collapse: collapse; /* Essential for border control */
                text-align: left;
            }
    
            th, td {
                padding: 15px;
                border: 1px solid var(--border-color);
            }
    
            /* 1. Remove borders for the first and last header cells */
            th:first-child, 
            th:last-child {
                border: none;
                background-color: transparent;
            }
    
            /* Style for the active headers */
            th:nth-child(2), 
            th:nth-child(3) {
                background-color: #252525;
                color: var(--accent-blue);
                text-transform: uppercase;
                font-size: 0.85rem;
                letter-spacing: 1px;
            }
    
            /* Optional: Cell content styling */
            .version-num {
                color: var(--accent-green);
                font-weight: bold;
            }
            .status {
                font-size: 0.8rem;
            }
            .status:hover {
                cursor: pointer
            }
            .status-update { color: var(--accent-yellow); }
            .status-stable { color: #888; }
            .status-remove { color: #FF0000; }
            .status-remove:hover {
                cursor: not-allowed
            }

            .modal {
                display: none; /* Hidden by default */
                position: fixed;
                z-index: 100;
                left: 0;
                top: 0;
                width: 100%;
                height: 100%;
                background-color: var(--modal-overlay);
                justify-content: center;
                align-items: center;
            }
    
            .modal-content {
                background-color: var(--panel-bg);
                padding: 25px;
                border: 1px solid var(--accent-blue);
                border-radius: 8px;
                width: 400px;
                box-shadow: 0 0 20px rgba(52, 152, 219, 0.3);
            }
    
            .modal-header {
                display: flex;
                justify-content: space-between;
                align-items: center;
                border-bottom: 1px solid var(--border-color);
                padding-bottom: 10px;
                margin-bottom: 15px;
            }
    
            .close-btn {
                cursor: pointer;
                color: var(--text-main);
                font-size: 24px;
            }
    
            .file-list {
                list-style: none;
                padding: 0;
                color: var(--accent-green);
            }
    
            .file-list li::before {
                content: "\f5ce";
            }
        </style>
    </head>
    <body>
        <div class="log-panel">
            <details open>
                <summary>
                    <div class="log-header">
                        <span class="project-name">{{project.name}}</span>
                        <div class="meta-group">
                            {% if project.has_version %}
                            <span class="version-tag">{{project.version}}</span>
                            {% endif %}
                            <span class="timestamp">{{timestamp}}</span>
                        </div>
                    </div>
                </summary>
                <div class="content">
                    <div class="table-container">
                        <table id="versionTable">
                            <thead>
                                <tr>
                                    <th></th> <th>Current Version</th>
                                    <th>Latest Version</th>
                                    <th>
                                        <select id="statusFilter" onchange="filterTable()">
                                            <option value="all">All</option>
                                            <option value="REQUIRES_UPDATE">REQUIRES_UPDATE</option>
                                            <option value="UP_TO_DATE">UP_TO_DATE</option>
                                            <option value="NOT_USED">NOT_USED</option>
                                        </select>
                                    </th> 
                                </tr>
                            </thead>
                            <tbody>
                                {% for package in packages %}
                                    {% if package.status == "UP_TO_DATE"%}
                                    {% set status_class = "status-stable" %}
                                    {% elif package.status == "REQUIRES_UPDATE" %}
                                    {% set status_class = "status-update" %}
                                    {% elif package.status == "NOT_USED" %}
                                    {% set status_class = "status-remove" %}
                                    {% endif %}
                                    <tr>
                                        <td>{{package.name}}</td>
                                        <td class="version-num">{{package.current_version}}</td>
                                        <td class="version-num"><a href={{package.url}}>{{package.latest_version}}</a></td>
                                        <td class="status {{status_class}}" onclick="showFiles('{{package.name}}', {{package.import_info}})" title="Click for details">{{package.status}}</td>
                                    </tr>
                                {% endfor %}
                            </tbody>
                        </table>
                    </div>
                </div>
            </details>
            <footer class="panel-footer">
                &copy; pyLibChecker 1.0.0 
            </footer>
        </div>    
        <div id="fileModal" class="modal">
            <div class="modal-content">
                <div class="modal-header">
                    <span id="modalTitle" style="color: var(--accent-blue); font-weight: bold;">Files</span>
                    <span class="close-btn" onclick="closeModal()">&times;</span>
                </div>
                <ul id="fileListContainer" class="file-list">
                    </ul>
            </div>
        </div>
        <script>
            function filterTable() {
                const dropdown = document.getElementById("statusFilter");
                const filterValue = dropdown.value;
                const table = document.getElementById("versionTable");
                const rows = table.getElementsByTagName("tr");
                for (let i = 1; i < rows.length; i++) {
                    const statusCell = rows[i].getElementsByTagName("td")[3]; // The 4th column
                    if (statusCell) {
                        const statusText = statusCell.textContent || statusCell.innerText;
                        
                        if (filterValue === "all" || statusText === filterValue) {
                            rows[i].style.display = ""; // Show row
                        } else {
                            rows[i].style.display = "none"; // Hide row
                        }
                    }
                }
            }
            function showFiles(packageName, files) {
                if (files.length){
                    const modal = document.getElementById("fileModal");
                    const title = document.getElementById("modalTitle");
                    const list = document.getElementById("fileListContainer");
            
                    title.innerText = "Library Ref: " + packageName;
                    list.innerHTML = ""; // Clear old list
            
                    files.forEach(file => {
                        let li = document.createElement("li");
                        li.textContent = file;
                        list.appendChild(li);
                    });
            
                    modal.style.display = "flex";
                }
            }
        
            function closeModal() {
                document.getElementById("fileModal").style.display = "none";
            }
        
            // Close if clicking outside the box
            window.onclick = function(event) {
                const modal = document.getElementById("fileModal");
                if (event.target == modal) {
                    closeModal();
                }
            }
        </script>
    </body>
</html>
"""


def analyze_packages(**kwargs):
    """Public API for using the pyLibChecker"""
    try:
        PackageInfo.get_installed_packages(**kwargs)
        if kwargs.get("output_format", None) == 'json':
            packages = PackageInfo.to_json(**kwargs)
            return json.dumps(packages)
        return PackageInfo.installed_packages
    except Exception as e:
        raise e


def main() -> None:
    """Main method for cli tool"""
    args = parser.parse_args()
    path = args.project_root
    path = os.path.abspath(path) if path else os.path.abspath(os.getcwd())
    if not os.path.exists(path):
        print(f"Specified path does not exist: {path}")
        sys.exit(1)
    if args.req_file:
        req_path = os.path.abspath(args.requirements)
        if not os.path.exists(req_path):
            print(f"Specified requirements.txt or pyproject.toml file does not exist: {req_path}")
            sys.exit(1)
    kwargs = {
        "project_root": path,
        "encoding": args.encoding,
        "req_file": args.req_file
    }
    print("Analysing....\n")
    packages = analyze_packages(**kwargs)
    for package in packages:
        print(package)
    if args.export:
        try:
            from jinja2 import Template
            packages = PackageInfo.to_json(project_root=path)
            template_dict = {
                "timestamp": datetime.datetime.now(tz=datetime.UTC).strftime("%d/%m/%Y %H:%M:%S"),
                "project": {
                    "name": path.rsplit(os.sep, 1)[1],
                    "has_version": False
                },
                "packages": packages
            }
            template = Template(REPORT_TEMPLATE)
            with open("index.html", 'w') as fp:
                fp.write(template.render(**template_dict))
        except ImportError:
            print(f"Install the pyLibChecker with report extension 'pip install pyLibChecker[report]'")
            sys.exit(1)
        except Exception as e:
            print(f"Issues with result exporting. Please report it to project home page\n{e}")
            sys.exit(1)