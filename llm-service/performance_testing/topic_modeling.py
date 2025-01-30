from fastopic import FASTopic
from topmost.preprocess import Preprocess

# Prepare your dataset.
docs = [
    "doc 1",
    "doc 2",  # ...
]

# Preprocess the dataset. This step tokenizes docs, removes stopwords, and sets max vocabulary size, etc.
# preprocess = Preprocess(vocab_size=your_vocab_size, tokenizer=your_tokenizer, stopwords=your_stopwords_set)
preprocess = Preprocess()

model = FASTopic(50, preprocess)
top_words, doc_topic_dist = model.fit_transform(docs)
