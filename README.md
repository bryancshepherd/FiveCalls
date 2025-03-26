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

5. Create cron job in editor

crontab -e

In the file that opens

* * * * * /bin/bash -c 'source /home/pi/my_project/venv/bin/activate && python /home/pi/my_project/my_script.py'

