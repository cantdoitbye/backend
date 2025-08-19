import re

# WORKING pattern using \U00000000 format for emoji ranges
WORKING_EMOJI_PATTERN = re.compile(
    r"^["
    r"a-zA-Z0-9 !@#$%^&*()_+\-=\[\]{}|;':\",./<>?`~"
    r"\u00C0-\u017F"  # Latin Extended (these work with \u)
    r"\u0100-\u024F"  # Latin Extended Additional
    r"\u1E00-\u1EFF"  # Latin Extended Additional
    r"\u2000-\u206F"  # General Punctuation
    r"\u2070-\u209F"  # Superscripts and Subscripts
    r"\u20A0-\u20CF"  # Currency Symbols
    r"\u2100-\u214F"  # Letterlike Symbols
    r"\u2190-\u21FF"  # Arrows
    r"\u2200-\u22FF"  # Mathematical Operators
    r"\u2300-\u23FF"  # Miscellaneous Technical
    r"\u2400-\u243F"  # Control Pictures
    r"\u2440-\u245F"  # Optical Character Recognition
    r"\u2460-\u24FF"  # Enclosed Alphanumerics
    r"\u2500-\u257F"  # Box Drawing
    r"\u2580-\u259F"  # Block Elements
    r"\u25A0-\u25FF"  # Geometric Shapes
    r"\u2600-\u26FF"  # Miscellaneous Symbols
    r"\u2700-\u27BF"  # Dingbats
    r"\U0001F000-\U0001F02F"  # Mahjong Tiles (using \U format)
    r"\U0001F030-\U0001F09F"  # Domino Tiles
    r"\U0001F0A0-\U0001F0FF"  # Playing Cards
    r"\U0001F100-\U0001F1FF"  # Enclosed Alphanumeric Supplement
    r"\U0001F200-\U0001F2FF"  # Enclosed Ideographic Supplement
    r"\U0001F300-\U0001F5FF"  # Miscellaneous Symbols and Pictographs
    r"\U0001F600-\U0001F64F"  # Emoticons
    r"\U0001F650-\U0001F67F"  # Ornamental Dingbats
    r"\U0001F680-\U0001F6FF"  # Transport and Map Symbols
    r"\U0001F700-\U0001F77F"  # Alchemical Symbols
    r"\U0001F780-\U0001F7FF"  # Geometric Shapes Extended
    r"\U0001F800-\U0001F8FF"  # Supplemental Arrows-C
    r"\U0001F900-\U0001F9FF"  # Supplemental Symbols and Pictographs
    r"\U0001FA00-\U0001FA6F"  # Chess Symbols
    r"\U0001FA70-\U0001FAFF"  # Symbols and Pictographs Extended-A
    r"]+$", re.UNICODE
)

# Test cases
test_values = [
    "test@1🚀",  # Your failing case
    "test@1",    # Without emoji
    "🚀",        # Just emoji
    "hello 😀",  # Text with emoji
    "test@1🎉🎯🌟",  # Multiple emojis
    "Hello World! 👋🌍",  # More complex case
    "Special chars !@# with emoji 🎯",  # Mixed case
]

print("Testing WORKING EMOJI pattern:")
print("=" * 50)

for test_value in test_values:
    result = WORKING_EMOJI_PATTERN.match(test_value)
    print(f"'{test_value}' -> {'✅ PASS' if result else '❌ FAIL'}")

print("\nIf all tests pass above, the pattern is working correctly!")