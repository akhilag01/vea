import os
import json
import uuid
from langchain.vectorstores import AtlasDB
from langchain.embeddings.openai import OpenAIEmbeddings
import nomic

def datafile_to_embedding_data(filename):
    with open(filename, "r") as f:
        data = json.load(f)

    if isinstance(data, list):
        items = data
        feed_title = ""
        feed_link = ""
    else:
        items = data.get("items", [])
        feed_title = data["title"] if "title" in data else ""
        feed_link = data["link"] if "link" in data else ""

    metadata = [
        {
            "id_field": str(uuid.uuid4()),
            "embed_text": " - ".join([x["title"], x["description"]])
            if "description" in x
            else x["title"],
            "title": x["title"],
            "description": x["description"] if "description" in x else "",
            "link": x["link"] if "link" in x and x["link"] is not None else "",
            "pubDate": x["pubDate"] if "pubDate" in x else "",
            "feed_title": feed_title,
            "feed_link": feed_link,
            "image_link": x["image"] if "image" in x else "",  # Add image link to metadata
        }
        for x in items
    ]
    return metadata

nomic.login("Gqpc4gaUpPCh45uGQcCxoBtMiNfTjRMr0V-yIsYnhvC_0")

vectorstore = nomic.AtlasProject(
    name="headline_news_6",
    reset_project_if_exists=False,
    is_public=True,
    unique_id_field="id_field",
    modality="text",
)

# Embed only all_rss_data.json
metadata = datafile_to_embedding_data("data_sources/all_rss_data.json")
vectorstore.add_text(data=metadata)
metadata = datafile_to_embedding_data("data_sources/us.json")
vectorstore.add_text(data=metadata)

#files = [
    #"scrapers/hn.json",
    #"scrapers/reddit_posts.json",
#]
#for filename in files:
    #metadata = datafile_to_embedding_data(filename)
    #vectorstore.add_text(data=metadata)

vectorstore.create_index(
    name="v1.1",
    indexed_field="embed_text",
    build_topic_model=True,
    topic_label_field="embed_text",
    colorable_fields=["feed_title", "id_field"],
)
