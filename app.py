import gradio as gr
from request import fetch_github_repositories
def greet(name):
    return f"Hello, {name}!"

def show_repositories():
    return fetch_github_repositories()

demo = gr.Interface(fn=show_repositories, inputs=None, outputs="text")
demo.launch()