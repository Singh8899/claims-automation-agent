import re

from dotenv import find_dotenv, load_dotenv

load_dotenv(find_dotenv())


class PromptInjectionFilter:
    def __init__(self):
        self.dangerous_patterns = [
            re.compile(r'ignore\s+(all\s+)?previous\s+instructions?', re.IGNORECASE),
            re.compile(r'you\s+are\s+now\s+(in\s+)?developer\s+mode', re.IGNORECASE),
            re.compile(r'system\s+override', re.IGNORECASE),
            re.compile(r'reveal\s+prompt', re.IGNORECASE),
        ]

        # Fuzzy matching patterns
        self.fuzzy_patterns = [
            'ignore', 'bypass', 'override', 'reveal', 'delete', 'system'
        ]

    def detect_injection(self, text: str) -> bool:
        # Standard pattern matching
        if any(pattern.search(text) for pattern in self.dangerous_patterns):
            return True

        # Fuzzy matching for misspelled words
        words = re.findall(r'\b\w+\b', text.lower())
        for word in words:
            for pattern in self.fuzzy_patterns:
                if self._is_similar_word(word, pattern):
                    return True
        return False

    def _is_similar_word(self, word: str, target: str) -> bool:
        if len(word) != len(target) or len(word) < 3:
            return False
        return (word[0] == target[0] and
                word[-1] == target[-1] and
                sorted(word[1:-1]) == sorted(target[1:-1]))

class OutputValidator:
    def __init__(self):
        self.suspicious_patterns = [
            re.compile(r'SYSTEM\s*[:]\s*You\s+are', re.IGNORECASE),
            re.compile(r'instructions?[:]\s*\d+\.', re.IGNORECASE),
        ]

    def validate_output(self, output: str) -> bool:
        return not any(pattern.search(output) for pattern in self.suspicious_patterns)

    def filter_response(self, response: str) -> str:
        if not self.validate_output(response) or len(response) > 5000:
            return "I cannot provide that information for security reasons."
        return response
