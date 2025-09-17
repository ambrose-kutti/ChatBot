# Import the pipeline from transformers

from transformers import pipeline

# Create a sentiment analysis tool

analyzer = pipeline("sentiment-analysis")

# Try it with some example texts

texts = [

    "I love this product!",
    "To be Born again, Baby, To be Born Again",
    "Like Jennie,I think i really like",
    "Under the Paris Twilight,Kiss me"
]

# Analyze each text
for text in texts:

    result = analyzer(text)

    print(f"\\nText: {text}")

    print(f"Sentiment: {result[0]['label']}")

    print(f"Confidence: {result[0]['score']:.4f}")