import os
from langchain.embeddings.openai import OpenAIEmbeddings
from langchain.vectorstores import AtlasDB
from nomic import AtlasProject, login
from pyarrow import feather
import json
import requests
import bs4
import argparse
import openai
from urllib.parse import urlparse



from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate, ChatPromptTemplate
from langchain.chains import LLMChain

from langchain.prompts import (
    ChatPromptTemplate,
    PromptTemplate,
    SystemMessagePromptTemplate,
    AIMessagePromptTemplate,
    HumanMessagePromptTemplate,
)
from langchain.schema import AIMessage, HumanMessage, SystemMessage

ATLAS_TEST_API_KEY = "Gqpc4gaUpPCh45uGQcCxoBtMiNfTjRMr0V-yIsYnhvC_0"
project_name = "headline_news_5"

login(ATLAS_TEST_API_KEY)

os.environ["OPENAI_API_KEY"] = ""

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False


def rank_headlines(headlines, persona, max_headlines=3):
    messages = [
        {
            "role": "system",
            "content": "You are an AI system which ranks the relevance of headlines based on an individual's stated preferences."
        },
        {
            "role": "user",
            "content": (
                "Below are the headlines:\n" +
                "".join([f"{i+1}. {headline['embed_text']}\n" for i, headline in enumerate(headlines)]) +
                f"Below is the individual's stated preference:\n{persona}\n\n"
                f"Rank the headlines based on their relevance to the individual's preference, with 1 being the most relevant and N being the least relevant. If there are more than {max_headlines} headlines, only return the top {max_headlines} headlines."
            )
        }
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0.9,
    )

    rankings = response['choices'][0]['message']['content']

    ranked_headlines = []
    for line in rankings.split("\n"):
        try:
            rank, headline = line.split(". ", 1)
            index = int(rank) - 1
            ranked_headlines.append(headlines[index])
        except (ValueError, IndexError):
            continue

        if len(ranked_headlines) >= max_headlines:
            break

    return ranked_headlines




def run_with_truncated_input(chain, headline, preference_string, max_length=100):
    truncated_headline = headline[:max_length]
    return chain.run(headline=truncated_headline, preference_string=preference_string)

# ...
def get_individual_summary(article):
    truncated_article = truncate_text(article, 450)

    messages = [
        {
            "role": "system",
            "content": "You are an AI system which writes a summary of an article, tweet, or other source of information. Speak as though you are talking to an audience of readers in a email newsletter"
        },
        {
            "role": "user",
            "content": f"""
            Below is the source:
            {truncated_article}

            Write a summary of this article. Do not make up or remove any information from the article. The summary should be succinct and no more than 4 sentences, but effective, informativ, interesting, and relevant to the user's preference. Give a pun or joke about the story at the end in the style of morning brew.
            If a source cannot be accessed due to a "Bad Request", "Javascript" or another technical error, such as a 403 error that detected you were a bot that scraped it, please skip it and return just a period
            """
        }
    ]

    response = openai.ChatCompletion.create(
        model="gpt-4",
        messages=messages,
        temperature=0.9,
    )

    summary = response['choices'][0]['message']['content']
    return summary





def truncate_text(text, word_limit):
    words = text.split()
    if len(words) > word_limit:
        truncated_words = words[:word_limit]
        truncated_text = " ".join(truncated_words)
        return truncated_text
    return text


def format_summaries(relevant_headlines):
    formatted_summaries = []
    for headline in relevant_headlines:
        if "summary" in headline:
            formatted_summary = f"{headline}:\n{headline['summary']}\n\n"
            formatted_summaries.append(formatted_summary)
    return "".join(formatted_summaries)


def get_summary(persona):
    
    atlas = AtlasProject(
        name="headline_news_5",
    )

    projection = atlas.projections[0]
    projection._download_feather()

    data = feather.read_feather("tiles/0/0/0.feather")

    # data is a pandas dataframe with the column _topic_depth_1
    # get the _id field for for one entry in each topic
    ids = []
    for topic in data["_topic_depth_3"].unique():
        ids.append(data[data["_topic_depth_3"] == topic]["id_field"].iloc[0])

    ids = [str(x) for x in ids]

    headlines = atlas.get_data(ids)

    os.environ["OPENAI_API_KEY"] = "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"

    llm = OpenAI(temperature=0.9)

    system_message = "You are an AI system which determines whether a headline, tweet, or other source is of interest to an individual based on their stated preferences."
    system_message_prompt = SystemMessagePromptTemplate.from_template(system_message)
    human_template = """
    Below is the source:
    {headline}

    Below is the individual's stated preference:
    {preference_string}

    If the source seems relevant to the individual’s preference, say ["RELEVANT"]. If the source doesn't seem relevant or violates their preferences in any way, say ["IRRELEVANT"]
    """
    human_message_prompt = HumanMessagePromptTemplate.from_template(human_template)

    chat_prompt = ChatPromptTemplate.from_messages(
        messages=[system_message_prompt, human_message_prompt]
    )

    chain1 = LLMChain(llm=llm, prompt=chat_prompt)

    relevant_headlines = []

    # save candidate headlines to json

    with open("candidate_headlines.json", "w") as f:
        json.dump(headlines, f)


    import concurrent.futures

    def process_headline(headline):
        test = run_with_truncated_input(
            chain1,
            headline=headline["embed_text"],
            preference_string=persona,
        )
        if "IRRELEVANT" not in test:
            return headline
        return None

    def parallelize_function(headlines):
        relevant_headlines = []
        with concurrent.futures.ThreadPoolExecutor() as executor:
            futures = {
                executor.submit(process_headline, headline): headline
                for headline in headlines
            }
            for future in concurrent.futures.as_completed(futures):
                result = future.result()
                if result:
                    relevant_headlines.append(result)
        return relevant_headlines

    relevant_headlines = parallelize_function(headlines)

    print(len(relevant_headlines))
    

    # save relevant headlines to json
    with open("relevant_headlines.json", "w") as f:
        json.dump(relevant_headlines, f)

    # get the cached relevant headline data
    # with open("relevant_headlines.json", "r") as f:
    #     relevant_headlines = json.load(f)

    for headline in relevant_headlines:
        if (
            headline["feed_title"] != "Twitter Feed"
            and headline["feed_title"] != "Reddit Feed"
            and headline["link"] != "null"
            and is_valid_url(headline["link"])
        ):
            # use beautiful soup to get the article text from the headline link
            r = requests.get(headline["link"])
            soup = bs4.BeautifulSoup(r.text, "html.parser")
            article = soup.text
            headline["article"] = article



    # save relevant headlines with article to json
    with open("relevant_headlines_with_article_and_summary.json", "w") as f:
        json.dump(relevant_headlines, f)

    # # get the cached relevant headline data
    # with open("relevant_headlines_with_article_and_summary.json", "r") as f:
    #     relevant_headlines = json.load(f)

    # now we want to combine the headlines together


    if len(relevant_headlines) > 3:
        relevant_headlines = rank_headlines(relevant_headlines, persona)

    for headline in relevant_headlines:
        if "article" in headline and headline["article"]:
            summary = get_individual_summary(headline["article"])
            headline["summary"] = summary




    formatted_summaries = []
    for headline in relevant_headlines:
        if "summary" in headline:
            formatted_summary = f"{headline['embed_text']}:\n{headline['summary']}\n\n"
            formatted_summaries.append(formatted_summary)
    return "".join(formatted_summaries)

def main():
    parser = argparse.ArgumentParser(description="Get a summary based on a persona.")
    parser.add_argument(
        "--persona",
        type=str,
        required=True,
        help="A string describing the individual's stated preferences.",
    )

    args = parser.parse_args()
    persona = args.persona

    summary = get_summary(persona)
    print(summary)


if __name__ == "__main__":
    main()
