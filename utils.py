import os
    
import pytz
from openai import OpenAI
import shutil
import datetime
from typing import List, Dict
import requests
from datetime import datetime, timedelta
import base64

def request_github_trending_repos(max_results: int,days: int = 7) -> List[Dict[str, str]]:
    day_diff = (datetime.now() - timedelta(days=days)).strftime('%Y-%m-%d')

    # API endpoint and parameters
    url = 'https://api.github.com/search/repositories'
    params = {
        'q': f'created:>{day_diff}',
        'sort': 'stars',
        'order': 'desc'
    }

    headers = {'Accept': 'application/vnd.github+json'}
    if os.getenv('GITHUB_TOKEN'):
        headers['Authorization'] = f"Bearer {os.getenv('GITHUB_TOKEN')}"

    # Make the request
    response = requests.get(url, params=params, headers=headers, timeout=30)
    if response.status_code != 200:
        print("GitHub search failed:", response.status_code, response.text[:500])
        return None
    data = response.json()

    # Get first 10 items and extract required fields
    repos = []
    for repo in data['items'][:max_results]:
        repo_info = {
            'name': repo['name'],
            'description': repo['description'],
            'language': repo['language'],
            'tags': repo['topics'],
            'watchers_count': repo['watchers_count'],
            'stars_count': repo['stargazers_count'],
            'html_url': repo['html_url']
        }
        
        # Fetch README content
        readme_url = f"https://api.github.com/repos/{repo['full_name']}/readme"
        readme_response = requests.get(readme_url, headers=headers, timeout=30)
        print("readme_response code ", readme_response.status_code)
        repo_info['summary'] = ""
        if readme_response.status_code == 200 and os.getenv("OPENAI_API_KEY"):
            content = readme_response.json().get('content')
            if content:
                # GitHub returns README content in base64 encoded format
                readme_content = base64.b64decode(content).decode('utf-8', errors='ignore')
                # keep the prompt small; the start of a README is enough for a one-line summary
                repo_info['summary'] = query_ai(readme_content[:12000])

        repos.append(repo_info)

    return repos

## Using Google Translate, maybe later do translation on the repos' summary
def translate_text(text, target_language='zh-HK'):
    """
    A simple function to translate text using a free translation API.
    You may need to replace this with a more reliable service.
    """
    try:
        # Using a free translation API - you might want to use a more reliable service
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl=auto&tl={target_language}&dt=t&q={text}"
        response = requests.get(url)
        if response.status_code == 200:
            # Extract the translated text from the response
            result = response.json()
            translated_text = ''.join([sentence[0] for sentence in result[0] if sentence[0]])
            return translated_text
        else:
            return f"[Translation Error: {response.status_code}]"
    except Exception as e:
        return f"[Translation Error: {str(e)}]"

def _cell(text) -> str:
    # keep markdown table rows intact
    return str(text).replace("\r", " ").replace("\n", " ").replace("|", "\\|").strip()

def generate_table(repos: List[Dict[str, str]], column_names: List[str] = [], ignore_keys: List[str] = []) -> str:
    # Filter out ignored columns from column_names
    filtered_columns = [col for col in column_names if col not in ignore_keys]
    
    formatted_repos = []
    for repo in repos:
        formatted_repo = {}
        ## Title and Link
        formatted_repo["Title"] = "**" + "[{0}]({1})".format(repo["name"], repo["html_url"]) + "**"
        
        # Add other columns based on filtered_columns
        if "Description" in filtered_columns and repo["description"] is not None:
            formatted_repo["Description"] = _cell(repo["description"])
            
        if "Language" in filtered_columns and repo["language"] is not None:
            formatted_repo["Language"] = repo["language"]
            
        if "Tags" in filtered_columns and repo["tags"] is not None:
            formatted_repo["Tags"] = tags = ", ".join(repo["tags"]) if repo["tags"] else ""
            if len(tags) > 10:
                formatted_repo["Tags"] = "<details><summary>{0}...</summary><p>{1}</p></details>".format(tags[:5], tags)
            else:
                formatted_repo["Tags"] = tags
                
        if "Summary" in filtered_columns and repo["summary"] is not None:
            formatted_repo["Summary"] = _cell(repo["summary"])
                
        if "Stars Count" in filtered_columns and repo["stars_count"] is not None:
            formatted_repo["Stars Count"] = str(repo["stars_count"])
            
        formatted_repos.append(formatted_repo)

    # Generate table header using filtered columns
    header = "| " + " | ".join(["**" + col + "**" for col in filtered_columns if col is not None]) + " |"
    separator = "| " + " | ".join(["---"] * len(filtered_columns)) + " |"
    
    # Generate table rows
    rows = []
    for repo in formatted_repos:
        row_values = [str(repo.get(col, "")) for col in filtered_columns]
        rows.append("| " + " | ".join(row_values) + " |")
        
    return header + "\n" + separator + "\n" + "\n".join(rows)


def back_up_files():
    # back up README.md and ISSUE_TEMPLATE.md
    shutil.move("README.md", "README.md.bk")
    shutil.move(".github/ISSUE_TEMPLATE.md", ".github/ISSUE_TEMPLATE.md.bk")

def restore_files():
    # restore README.md and ISSUE_TEMPLATE.md
    shutil.move("README.md.bk", "README.md")
    shutil.move(".github/ISSUE_TEMPLATE.md.bk", ".github/ISSUE_TEMPLATE.md")

def remove_backups():
    # remove README.md and ISSUE_TEMPLATE.md
    os.remove("README.md.bk")
    os.remove(".github/ISSUE_TEMPLATE.md.bk")

def get_daily_date():
    # get hongkong time in the format of "March 1, 2021"
    hongkong_timezone = pytz.timezone('HongKong')
    today = datetime.now(hongkong_timezone)
    return today.strftime("%B %d, %Y")
def query_ai(query: str, model: str = "gpt-4o-mini") -> str:
    # query the AI with a specified system role
    system_role = "You are a helpful assistant that ONLY summarizes the content of the GitHub repository by seeing the README.md file. You MUST be CONCISE and to the point by ONE sentence and within 20 WORDS ONLY. PLEASE BE CONCISE. You MUST NOT include any other information in your response except the summary."

    result = ""
    try:
        # Create client with custom base URL if provided
        client = OpenAI(
            api_key=os.getenv("OPENAI_API_KEY"),
            base_url=os.getenv("OPENAI_API_BASE") or None
        )
        
        # Use the new client.chat.completions.create method
        response = client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_role},
                {"role": "user", "content": query}
            ],
            max_tokens=600
        )
        print("response ", response.choices[0].message.content)

        if response.choices[0].message.content is None:
            result = ""
        else:
            response_content = response.choices[0].message.content
            if len(response_content) > 300:  # Limit summary to 300 characters
                result = response_content[:297] + "..."
            else:
                result = response_content
    except Exception as e:
        print(e)
        result = ""  # leave summary blank rather than publishing the error

    return result
