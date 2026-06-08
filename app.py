import json

import gradio as gr
import requests
from index_qdrant import QdrantManager

GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
DEFAULT_GROQ_MODEL = "llama-3.1-8b-instant"
GROQ_MODELS = [
    DEFAULT_GROQ_MODEL,
    "llama-3.3-70b-versatile",
    "meta-llama/llama-4-scout-17b-16e-instruct",
]


def format_result_for_groq(result):
    payload = result.payload
    return {
        "name": payload.get("name"),
        "full_name": payload.get("full_name"),
        "description": payload.get("description"),
        "stars": payload.get("stars"),
        "forks": payload.get("forks"),
        "url": payload.get("url"),
        "score": result.score,
    }


def summarize_with_groq(query, results, api_key, model):
    if not api_key:
        return "Add a Groq API key before sending results to Groq."

    result_context = json_safe_dumps([
        format_result_for_groq(result) for result in results
    ])

    prompt = (
        "The user searched a vector database of Rust GitHub repositories.\n"
        f"Query: {query}\n\n"
        f"Search results JSON:\n{result_context}\n\n"
        "Explain the best matches in a concise, practical way. Mention which "
        "repositories look most relevant and why. Include useful links when helpful."
    )

    response = requests.post(
        GROQ_CHAT_COMPLETIONS_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model or DEFAULT_GROQ_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": (
                        "You help developers interpret vector search results. "
                        "Be direct, accurate, and do not invent facts beyond the "
                        "provided results."
                    ),
                },
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.2,
        },
        timeout=30,
    )
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"].strip()


def json_safe_dumps(value):
    return json.dumps(value, indent=2, ensure_ascii=False)


def search_ui(query, groq_api_key, send_to_groq, groq_model):
    if not query:
        return [], ""

    results = manager.search_repositories(query, top_k=10)

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

    groq_response = ""
    if send_to_groq:
        groq_api_key = groq_api_key or ""
        groq_model = groq_model or DEFAULT_GROQ_MODEL
        try:
            groq_response = summarize_with_groq(
                query=query,
                results=results,
                api_key=groq_api_key.strip(),
                model=groq_model.strip(),
            )
        except requests.HTTPError as error:
            groq_response = f"Groq request failed: {error.response.text}"
        except requests.RequestException as error:
            groq_response = f"Groq request failed: {error}"
        except (KeyError, IndexError) as error:
            groq_response = f"Groq returned an unexpected response: {error}"

    return rows, groq_response


manager = QdrantManager()
manager.ensure_indexed()

with gr.Blocks(title="Rust Repository Vector Search") as demo:
    gr.Markdown("# Rust Repository Vector Search")
    gr.Markdown(
        "Search indexed GitHub repositories and optionally send the query plus results to Groq."
    )

    with gr.Row():
        query_input = gr.Textbox(label="Search query", scale=2)
        search_button = gr.Button("Search", variant="primary")

    with gr.Accordion("Groq options", open=False):
        send_to_groq_input = gr.Checkbox(label="Send query and results to Groq")
        groq_api_key_input = gr.Textbox(
            label="Groq API key",
            type="password",
            placeholder="gsk_...",
        )
        groq_model_input = gr.Dropdown(
            label="Groq model",
            choices=GROQ_MODELS,
            value=DEFAULT_GROQ_MODEL,
            allow_custom_value=True,
        )

    results_output = gr.Dataframe(
        headers=["Repository", "Full name", "Description", "Stars", "URL", "Score"],
        label="Search results",
    )
    groq_output = gr.Markdown(label="Groq response")

    search_button.click(
        fn=search_ui,
        inputs=[
            query_input,
            groq_api_key_input,
            send_to_groq_input,
            groq_model_input,
        ],
        outputs=[results_output, groq_output],
    )
    query_input.submit(
        fn=search_ui,
        inputs=[
            query_input,
            groq_api_key_input,
            send_to_groq_input,
            groq_model_input,
        ],
        outputs=[results_output, groq_output],
    )

demo.launch()
