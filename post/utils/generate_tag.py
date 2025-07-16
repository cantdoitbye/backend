# from dask.distributed import Client

# def submit_background_task(post_title, post_text, post_uid):
#     """
#     Submit a task to Dask for background processing.
#     Here we will just square a number to verify everything works.
#     """
#     print("inside submitted task")

#     def process_tags_and_execute_query(post_title, post_text, post_uid):
#         from neomodel import db
#         import spacy
#         from textblob import TextBlob

#         # Step 2: Load NLP Model
#         nlp = spacy.load("en_core_web_lg")

#         # Step 3: Define Auto-Tagging Function
#         def auto_tag_text(text):
#             # Process text with spaCy
#             doc = nlp(text)

#             # Extract entities (e.g., people, places)
#             entities = [ent.text for ent in doc.ents]

#             # Extract nouns as keywords
#             keywords = [
#                 token.text for token in doc if token.pos_ in ("NOUN", "PROPN")]

#             # Analyze sentiment with TextBlob
#             sentiment = TextBlob(text).sentiment.polarity
#             sentiment_label = "positive" if sentiment > 0 else "negative" if sentiment < 0 else "neutral"

#             return {
#                 "entities": entities,
#                 "keywords": keywords,
#                 "sentiment": sentiment_label
#             }

#         def run_auto_tagging(post_title, post_text):
#             """
#             Prompts the user for text input, processes the text, and prints the tags.
#             """
#             sample_text = f"{post_title}: {post_text}"

#             # Convert the sample text to lowercase
#             sample_text = sample_text.lower()
#             print(sample_text)
#             tags = auto_tag_text(sample_text)

#             print("\nAuto-Generated Tags:")
#             print(f"Keywords: {tags['keywords']}")
#             print(f"Sentiment: {tags['sentiment']}")

#             return {
#                 'entities': tags['entities'],
#                 'keywords': tags['keywords'],
#                 'sentiment': tags['sentiment']
#             }

#         # Start timing for tag generation
#         print("goint to make connection")
#         db.set_connection("bolt://neo4j:BwA4zwGhfRT8nx5@34.170.99.162:7687")
#         print("connection established successfully")

#         create_tag_and_relationship_query = """
#                                     UNWIND $keywords AS tag
#                                     MERGE (tagNode:Tag {name: tag})
#                                     WITH tagNode
#                                     MATCH (post:Post {uid: $uid})
#                                     MERGE (post)-[r:TAGGED_WITH_KEYWORD]->(tagNode)
#                                     SET r.weight = 0.5
#                                     MERGE (tagNode)-[r_reverse:TAGGED_WITH_KEYWORD]->(post)
#                                     SET r_reverse.weight = 0.5;
#                                 """

        
#         answer = run_auto_tagging(post_title, post_text)
#         keywords = answer['keywords']

#         # Prepare parameters for the query
#         params = {"uid": post_uid, "keywords": keywords}

#         db.cypher_query(create_tag_and_relationship_query, params)

#     # Connecting to Dask client (assuming the Dask scheduler is running on "new_os1:8786")
#     dask_client = Client("tcp://50.28.84.47:8786")

#     # Submit a simple task: square a number (e.g., post_uid as the number to square)
#     future = dask_client.submit(
#         process_tags_and_execute_query, post_title, post_text, post_uid)
#     # result = future.result()  # This will block execution until the task is complete  
#     # print(result) 

#     return
