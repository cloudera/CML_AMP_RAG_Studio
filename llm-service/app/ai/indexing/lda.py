#
#  CLOUDERA APPLIED MACHINE LEARNING PROTOTYPE (AMP)
#  (C) Cloudera, Inc. 2024
#  All rights reserved.
#
#  Applicable Open Source License: Apache 2.0
#
#  NOTE: Cloudera open source products are modular software products
#  made up of hundreds of individual components, each of which was
#  individually copyrighted.  Each Cloudera open source product is a
#  collective work under U.S. Copyright Law. Your license to use the
#  collective work is as provided in your written agreement with
#  Cloudera.  Used apart from the collective work, this file is
#  licensed for your use pursuant to the open source license
#  identified above.
#
#  This code is provided to you pursuant a written agreement with
#  (i) Cloudera, Inc. or (ii) a third-party authorized to distribute
#  this code. If you do not have a written agreement with Cloudera nor
#  with an authorized and properly licensed third party, you do not
#  have any rights to access nor to use this code.
#
#  Absent a written agreement with Cloudera, Inc. ("Cloudera") to the
#  contrary, A) CLOUDERA PROVIDES THIS CODE TO YOU WITHOUT WARRANTIES OF ANY
#  KIND; (B) CLOUDERA DISCLAIMS ANY AND ALL EXPRESS AND IMPLIED
#  WARRANTIES WITH RESPECT TO THIS CODE, INCLUDING BUT NOT LIMITED TO
#  IMPLIED WARRANTIES OF TITLE, NON-INFRINGEMENT, MERCHANTABILITY AND
#  FITNESS FOR A PARTICULAR PURPOSE; (C) CLOUDERA IS NOT LIABLE TO YOU,
#  AND WILL NOT DEFEND, INDEMNIFY, NOR HOLD YOU HARMLESS FOR ANY CLAIMS
#  ARISING FROM OR RELATED TO THE CODE; AND (D)WITH RESPECT TO YOUR EXERCISE
#  OF ANY RIGHTS GRANTED TO YOU FOR THE CODE, CLOUDERA IS NOT LIABLE FOR ANY
#  DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, PUNITIVE OR
#  CONSEQUENTIAL DAMAGES INCLUDING, BUT NOT LIMITED TO, DAMAGES
#  RELATED TO LOST REVENUE, LOST PROFITS, LOSS OF INCOME, LOSS OF
#  BUSINESS ADVANTAGE OR UNAVAILABILITY, OR LOSS OR CORRUPTION OF
#  DATA.
#
import os

import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer, CountVectorizer
from sklearn.datasets import fetch_20newsgroups
from sklearn.decomposition import NMF, LatentDirichletAllocation
import pymupdf


def display_topics(model, feature_names, _no_top_words):
    for topic_idx, topic in enumerate(model.components_):
        print("Topic %d:" % topic_idx)
        print(
            " ".join(
                [feature_names[i] for i in topic.argsort()[: -_no_top_words - 1 : -1]]
            )
        )


dataset = fetch_20newsgroups(
    shuffle=True, random_state=1, remove=("headers", "footers", "quotes")
)

documents = []
for filename in os.listdir("./docs"):
    if filename.endswith(".pdf"):
        with pymupdf.open(f"./docs/{filename}") as doc:
            document = ""
            for page in doc:
                document += page.get_text()
            documents.append(document)

no_features = 1000

# NMF is able to use tf-idf
# tfidf_vectorizer = TfidfVectorizer(max_df=0.95, min_df=2, max_features=no_features, stop_words='english')
# tfidf = tfidf_vectorizer.fit_transform(documents)
# tfidf_feature_names = tfidf_vectorizer.get_feature_names_out()

# LDA can only use raw term counts for LDA because it is a probabilistic graphical model
tf_vectorizer = CountVectorizer(
    max_df=0.95, min_df=2, max_features=no_features, stop_words="english"
)
tf = tf_vectorizer.fit_transform(documents)
tf_feature_names = tf_vectorizer.get_feature_names_out()

no_topics = 20

# Run NMF
# nmf = NMF(n_components=no_topics, random_state=1, alpha=.1, l1_ratio=.5, init='nndsvd').fit(tfidf)

# Run LDA
lda = LatentDirichletAllocation(
    n_components=no_topics,
    max_iter=20,
    learning_method="online",
    learning_offset=50.0,
    random_state=0,
).fit(tf)

# Unnormalized topic-word counts
topic_word_counts = lda.components_

# Normalize to get p(word | topic)
topic_word_distributions = topic_word_counts / topic_word_counts.sum(
    axis=1, keepdims=True
)

# Unweighted average across topics
p_word = topic_word_distributions.mean(axis=0)

lift = topic_word_distributions / p_word


def get_top_distinctive_words_per_topic(lift, feature_names, top_n=10):
    for topic_idx, word_lifts in enumerate(lift):
        # Get indices sorted by lift descending
        top_indices = word_lifts.argsort()[::-1][:top_n]

        print(f"Topic {topic_idx}:")
        for i in top_indices:
            print(f"  {feature_names[i]} (lift={word_lifts[i]:.2f})")
        print("")


get_top_distinctive_words_per_topic(lift, tf_feature_names, top_n=5)

no_top_words = 10
# display_topics(nmf, tfidf_feature_names, no_top_words)
display_topics(lda, tf_feature_names, no_top_words)
