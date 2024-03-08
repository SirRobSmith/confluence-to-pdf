# confluence-to-pdf
A simple tool to extract data from legacy on-premises confluence servers, creating a PDF archive.

# Usage
Should you feel motivated to use this tool, the folllowing setup is required. 

1. Install Python3
2. Clone this repo
3. cd /your-local-folder
4. Create a Python virtual environment (python3 -m venv .venv)
5. Run '. ./venv/bin/activate'
6. run 'pip install atlassian-python-api'
7. Export Variables to allow basic auth to your on-premises confluence server (export OP_USER=<your username>, export OP_PASS=<your password>
8. Set appropriate values within app.py for 'googleDriveBase' and 'confluenceServer' and 'sites' (the latter being the sitekeys you wish to export)
9. Run the code with 'python3 app.py'

# Monitoring
The tool pipes status to a log file within your 'googleDriveBase' folder. To view this live run the command 'tail -f <log file>'
