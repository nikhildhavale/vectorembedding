import requests
import os
import json
OUTPUT_FILE = "rust_repos.json"
def save_repos(repos):
    with open(OUTPUT_FILE, "w", encoding="utf-8") as file:
        json.dump(repos, file, indent=2)
def fetch_github_repositories(limit=1000):
    url = "https://api.github.com/search/repositories"
    params = {
        "q": "language:Rust",
        "sort": "stars",
        "order": "desc",
        "per_page": 100,
        "page": 1,
    }
    if os.path.exists(OUTPUT_FILE):
        return f"Repositories already saved in {OUTPUT_FILE}"

    response = requests.get(url, params=params)
    for page in range(1, (limit // 100) + 1):
        all_repos = []
        params["page"] = page
        response = requests.get(url, params=params)
        if response.status_code == 200:
            data = response.json()
            for repo in data["items"]:
                all_repos.append({
                "name": repo["name"],
                "full_name": repo["full_name"],
                "description": repo["description"],
                "stars": repo["stargazers_count"],
                "forks": repo["forks_count"],
                "url": repo["html_url"],
                "language": repo["language"],
            })
            save_repos(all_repos)
        else:
            print(f"Failed to fetch data: {response.status_code}")
            break
