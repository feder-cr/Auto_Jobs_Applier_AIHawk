import re

def generate_regex_patterns_for_blacklisting(blacklist):
        # Converts each blacklist entry to a regex pattern that ensures all words appear, in any order
        #
        # Example of pattern for job title:
        #       title_blacklist = ["Data Engineer", "Software Engineer"]
        #       patterns = ['(?=.*\\bData\\b)(?=.*\\bEngineer\\b)', '(?=.*\\bSoftware\\b)(?=.*\\bEngineer\\b)']
        #
        # Description:
        #   '?=.*' => Regex expression that allows us to check if the following pattern appears
        #             somewhere in the string searched, even if there are any characters before the word
        #   '\b{WORD}\b' => Regex expression for a word boundry, that the WORD is treated as whole words
        #                    rather than as parts of other words.
        patterns = []
        for term in blacklist:
            # Split term into individual words
            words = term.split()
            # Create a lookahead for each word to ensure it appears independently
            lookaheads = [fr"(?=.*\b{re.escape(word)}\b)" for word in words]
            # Combine lookaheads with a pattern that allows flexible separators between the words
            pattern = "".join(lookaheads)  # Ensures all words are present            
            patterns.append(pattern)
        return patterns