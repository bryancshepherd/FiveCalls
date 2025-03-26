To do:
- Add filters to show all categories, top 5, and top 10
- Also add a table with that information
- add button to switch between last 48 hours, last 7 days, and last month
- make display times eastern
- prettify text on charts a bit

How to set up cron jobs on Rasp Pi:

1. Create the Virtual Environment

First, create a virtual environment where your dependencies will be installed.

* in a terminal:

# Create a directory for your project (optional)
mkdir ~/my_project
cd ~/my_project

# Create the virtual environment
python3 -m venv ".fivecalls"

2. Activate the environment
source .fivecalls/bin/activate

3. Install dependencies
pip install -r requirements.txt

4. Create script

4b. Create .tmp directory in project file if it doesn't exist

5. Create cron job in editor

crontab -e

In the file editor that opens

* * * * * /bin/bash -c 'source home/bryan/Projects/FiveCalls/.fivecalls/bin/activate && python home/bryan/Projects/FiveCalls/fetch_data.py >> home/bryan/Projects/FiveCalls/.tmp/cron_fetch_data_logfile.log 2>&1'

5 * * * * /bin/bash -c 'source home/bryan/Projects/FiveCalls/.fivecalls/bin/activate && python home/bryan/Projects/FiveCalls/create_charts.py >> home/bryan/Projects/FiveCalls/.tmp/cron_create_charts_logfile.log 2>&1'


