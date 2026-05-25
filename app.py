import gradio as gr
from request import fetch_github_repositories
from index_qdrant import QdrantManager
from qdrant_client import QdrantClient
def greet(name):
    return f"Hello, {name}!"

def show_repositories():
    return fetch_github_repositories()
def search_ui(query):
    results = manager.search_repositories(query, top_k=5)

    rows = []

    for result in results:
        payload = result.payload

        rows.append([
            payload["name"],
            payload["full_name"],
            payload["description"],
            payload["stars"],
            payload["url"],
            result.score,
        ])

    return rows

demo = gr.Interface(fn=show_repositories, inputs=None, outputs="text")
manager = QdrantManager()
points = []
for index, repo in enumerate(manager.repos):
    text = manager.repo_to_text(repo)
    vector = manager.sentence_embedding(text)
    point = manager.create_point(repo, vector, index)
    points.append(point)
manager.insert_points(points)

demo = gr.Interface(
    fn=search_ui,
    inputs=gr.Textbox(label="Search query"),
    outputs=gr.Dataframe(
        headers=["Repository", "Full name", "Description", "Stars", "URL", "Score"],
        label="Search results",
    ),
)

demo.launch()
