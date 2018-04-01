"""
Generate a wordcloud from text
"""

from collections import Counter
from os import path

import matplotlib.pyplot as plt
from nltk.corpus import stopwords as S
from wordcloud import WordCloud

d = path.dirname(__file__)
# Read the whole text.
words = [
    # Getting better
    ('Practice planning', 15),
    ('Leading sessions', 15),
    ('Training', 10),
    ('Strategy', 10),
    ('Skill development', 12),
    ('Coaching', 10),
    ('Game nights', 8),
    ('Practice weekends', 10),
    # Interfacing externally
    ('KUPA', 2),
    ('UPAI', 2),
    # Recruitment
    ('Recruitment', 8),
    ("Women's HAT", 8),
    ('Newbie training', 8),
    # Fitness
    ('Warm-ups', 8),
    ('Cool-downs', 8),
    ('Diet', 5),
    ('Strength & Conditioning', 10),
    # Social media
    ('Social media', 5),
    ('Instagram', 5),
    ('Facebook', 5),
    # Documentation
    ('Game videos', 8),
    ('Youtube', 5),
    ('Documentation', 8),
    # Culture
    ('Team culture', 8),
    ('Trips', 8),
    ('Hikes', 8),
    ('Off field', 5),
    ('Spirit circle', 5),
    # Tournaments
    ('Tournaments', 12),
    ('Team selection', 12),
    ('Tryouts', 12),
    ('Registration', 5),
    ('Accommodation', 5),
    # Money
    ('Accounts', 10),
    ('Treasurer', 8),
    # Equipment
    ('Team kit', 5),
    ('Disc bag', 5),
    ('Bibs', 5),
    # Grounds
    ('Grounds', 8),
    ('NCJ', 8),
]
# Generate a word cloud image
wordcloud = WordCloud(
    width=800, height=600, prefer_horizontal=2, background_color='white'
)
wordcloud.generate_from_frequencies(dict(words))
image = wordcloud.to_image()
image.save('wordcloud.png')
image.show()
