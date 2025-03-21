import sys
import time
import pytz
import requests
from datetime import datetime

from utils import request_github_trending_repos, generate_table, back_up_files,\
    restore_files, remove_backups, get_daily_date, query_ai


hongkong_timezone = pytz.timezone('HongKong')

# NOTE: arXiv API seems to sometimes return an unexpected empty list.

# get current beijing time date in the format of "2021-08-01"
current_date = datetime.now(hongkong_timezone).strftime("%Y-%m-%d")
# get last update date from README.md
with open("README.md", "r") as f:
    while True:
        line = f.readline()
        if "Last update:" in line: break
    last_update_date = line.split(": ")[1].strip()
    # if last_update_date == current_date:
        # sys.exit("Already updated today!")


max_result = 20 # maximum query results from arXiv API for each keyword
issues_result = 10 # maximum papers to be included in the issue


column_names = ["Title", "Description", "Language", "Summary", "Tags", "Stars Count", "HTML URL"]


back_up_files() # back up README.md and ISSUE_TEMPLATE.md



# write to README.md
f_rm = open("README.md", "w", encoding='utf-8') # file for README.md
f_rm.write("# Daily Trending Repositories\n")
f_rm.write("The project automatically finds trending repositories from GitHub.\n\nThe subheadings in the README file represent the search keywords.\n\nOnly the most recent repositories for each keyword are retained, up to a maximum of 3000 repositories.\n\nYou can click the 'Star' and 'Watch' button to receive daily *email* notifications.\n\nLast update: {0}\n\n".format(current_date))

# write to ISSUE_TEMPLATE.md
f_is = open(".github/ISSUE_TEMPLATE.md", "w", encoding='utf-8') # file for ISSUE_TEMPLATE.md
f_is.write("---\n")
f_is.write("title: Latest {0} Trending Repositories - {1}\n".format(issues_result, get_daily_date()))
f_is.write("labels: documentation\n")
f_is.write("---\n")
f_is.write("# 📚 Weekly Trending Repositories Update\n\n")
f_is.write("### 📅 Date: {0}\n\n".format(get_daily_date()))
f_is.write("Welcome to today's collection of the latest research papers! Below you'll find the top {0} papers for each category.\n\n".format(issues_result))
f_is.write("💡 **Note**: For a better reading experience and access to more papers, please visit our [Github Repository](https://github.com/marc-ko/daily-trending-repo).\n\n")
f_is.write("---\n\n")

repos = request_github_trending_repos(max_result)
# f_rm.write("## {0}\n".format(repo['name']))
# f_is.write("## 📑 {0}\n".format(repo['name']))
if repos is None: # failed to get repos
    print("Failed to get repos!")
    f_rm.close()
    f_is.close()
    restore_files()
    sys.exit("Failed to get repos!")
rm_table = generate_table(repos, column_names)
is_table = generate_table(repos[:issues_result], column_names, ignore_keys=["summary"])
f_rm.write(rm_table)
f_rm.write("\n\n")
f_is.write(is_table)
f_is.write("\n\n")
time.sleep(5) # avoid being blocked

f_rm.close()
f_is.close()
remove_backups()
