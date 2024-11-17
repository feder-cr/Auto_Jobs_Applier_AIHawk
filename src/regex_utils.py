import re

def generate_regex_patterns_for_blacklisting(blacklist):
    """
    Converts each blacklist entry to a regex pattern that ensures all words appear, in any order.

    Example of pattern for job title:
          title_blacklist = ["Data Engineer", "Software Engineer"]
          patterns = ['(?i)(?=.*data)(?=.*engineer)', '(?i)(?=.*software)(?=.*engineer)']

    Description:
      - '?=.*' => Regex expression that allows us to check if the following pattern appears
                   somewhere in the string searched.
      - '(?i)' => Regex flag for case-insensitive matching.
    """
    patterns = []
    for term in blacklist:
        # Split term into words, including splitting CamelCase words
        words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+|[^\s\w]+', term)
        # Escape each word to handle special characters
        words_escaped = [re.escape(word.strip()) for word in words if word.strip()]
        # Create a lookahead for each word to ensure it appears in the string
        lookaheads = [fr"(?=.*{word})" for word in words_escaped]
        # Combine lookaheads with a pattern that allows flexible separators between the words
        pattern = "(?i)" + "".join(lookaheads)  # Ensures all words are present, case-insensitive
        patterns.append(pattern)
    return patterns
