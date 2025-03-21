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
f_rm = open("README.md", "w", encoding='utf-8')
f_rm.write("""# 🌟 Daily Trending Repositories

<div align="center">
![GitHub last commit](https://img.shields.io/github/last-commit/marc-ko/daily-trending-repo)
![GitHub stars](https://img.shields.io/github/stars/marc-ko/daily-trending-repo)
![GitHub forks](https://img.shields.io/github/forks/marc-ko/daily-trending-repo)
![GitHub issues](https://img.shields.io/github/issues/marc-ko/daily-trending-repo)
</div>

## 📋 About

This project automatically tracks and curates trending repositories from GitHub daily. Stay updated with the most exciting new projects in the developer community! With AI Summarization, you can get the summary of the repository by seeing the README.md file as well!.

### 🔥 Features

- 🔄 **Weekly Updates**: Fresh content every week Wednesday
- 🌐 **Diverse Categories**: Covering all major programming languages and topics
- ⭐ **Star-based Ranking**: Sorted by community popularity
- 📊 **Detailed Information**: Including descriptions, languages, and statistics

## 📈 Latest Trending Repositories

Last update: {0}

""".format(current_date))

f_rm.write("""<details>
<summary>ℹ️ How to Use This Repository</summary>

1. **Star & Watch**: Click the 'Star' and 'Watch' buttons to receive weekly email notifications
2. **Browse**: Explore trending repositories organized by popularity
3. **Contribute**: Feel free to open issues or suggest improvements

</details>

---

""")

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
is_table = generate_table(repos[:issues_result], column_names)
f_rm.write(rm_table)
f_rm.write("\n\n")
f_is.write(is_table)
f_is.write("\n\n")
time.sleep(5) # avoid being blocked

f_rm.close()
f_is.close()
remove_backups()
