from collections import defaultdict
import re
from typing import List, Set
import requests
from datetime import datetime, timedelta
import json
import os

# OpenAI API Configuration
API_KEY = 'e7185bf06b954868b9d65d577ac37c18'
API_BASE = 'https://api.aimlapi.com/v1/chat/completions'

class WordRecommendationSystem:
    def __init__(self):
        self.word_trie = {}
        self.word_frequencies = defaultdict(int)
        self.common_search_terms = set()
        self.recent_queries = []
        self.last_ai_update = None
        self.ai_suggestions_cache = {}
        
    def add_word(self, word: str) -> None:
        """Add a word to the trie and update its frequency"""
        word = word.lower().strip()
        if not word:
            return
            
        self.word_frequencies[word] += 1
        
        # Add to trie
        current = self.word_trie
        for char in word:
            if char not in current:
                current[char] = {}
            current = current[char]
        current['*'] = word
        
    def add_common_terms(self, terms: List[str]) -> None:
        """Add a list of common search terms"""
        for term in terms:
            self.common_search_terms.add(term.lower().strip())
            self.add_word(term)
            
    def get_ai_suggestions(self, prefix: str, context: str = "") -> List[str]:
        """Get AI-powered suggestions based on the prefix and recent search context"""
        if not API_KEY:
            print("Error: OpenAI API key is not set")
            return []
            
        cache_key = f"{prefix}:{context}"
        
        # Check cache first
        if cache_key in self.ai_suggestions_cache:
            cache_entry = self.ai_suggestions_cache[cache_key]
            if datetime.now() - cache_entry['timestamp'] < timedelta(hours=1):
                return cache_entry['suggestions']
        
        try:
            # Prepare context for the AI
            recent_searches = ", ".join(self.recent_queries[-5:]) if self.recent_queries else ""
            
            prompt = f"""Given the search prefix "{prefix}" and considering these recent searches: {recent_searches},
            suggest 5 relevant dark web search terms that would be most useful. Context: {context}
            Format: return only a JSON array of strings."""
            
            headers = {
                'Authorization': f'Bearer {API_KEY}',
                'Content-Type': 'application/json',
                'Accept': 'application/json'
            }
            
            payload = {
                'model': 'gpt-3.5-turbo',
                'messages': [
                    {'role': 'system', 'content': 'You are a dark web search assistant. Provide relevant search suggestions.'},
                    {'role': 'user', 'content': prompt}
                ],
                'temperature': 0.7,
                'max_tokens': 150
            }
            
            print(f"Making request to OpenAI API with headers: {headers}")  # Debug line
            
            response = requests.post(
                f'{API_BASE}/chat/completions',
                headers=headers,
                json=payload,
                timeout=10
            )
            
            if response.status_code != 200:
                print(f"API request failed with status {response.status_code}: {response.text}")
                return []
                
            response_data = response.json()
            
            try:
                content = response_data['choices'][0]['message']['content']
                suggestions = json.loads(content)
                if not isinstance(suggestions, list):
                    raise ValueError("API response is not a list")
                
                # Cache the results
                self.ai_suggestions_cache[cache_key] = {
                    'timestamp': datetime.now(),
                    'suggestions': suggestions
                }
                
                return suggestions
                
            except (KeyError, json.JSONDecodeError, ValueError) as e:
                print(f"Error parsing API response: {e}")
                print(f"Response content: {response_data}")
                return []
            
        except requests.exceptions.RequestException as e:
            print(f"API request failed: {e}")
            return []
        except Exception as e:
            print(f"Unexpected error in get_ai_suggestions: {e}")
            return []
            
    def get_words_with_prefix(self, prefix: str, max_suggestions: int = 5) -> List[str]:
        """Get words that start with the given prefix, combining trie-based and AI suggestions"""
        prefix = prefix.lower().strip()
        
        # Get traditional trie-based suggestions
        trie_suggestions = self._get_trie_suggestions(prefix, max_suggestions)
        
        # Get AI-powered suggestions
        ai_suggestions = self.get_ai_suggestions(prefix)
        
        # Combine and deduplicate suggestions
        all_suggestions = []
        seen = set()
        
        # Prioritize AI suggestions but ensure some variety
        for suggestion in ai_suggestions + trie_suggestions:
            if suggestion not in seen and len(all_suggestions) < max_suggestions:
                all_suggestions.append(suggestion)
                seen.add(suggestion)
        
        return all_suggestions
        
    def _get_trie_suggestions(self, prefix: str, max_suggestions: int = 5) -> List[str]:
        """Get traditional trie-based suggestions"""
        if not prefix:
            return list(self.common_search_terms)[:max_suggestions]
            
        # Find node representing prefix
        current = self.word_trie
        for char in prefix:
            if char not in current:
                return []
            current = current[char]
            
        # Collect all words under this node
        words = []
        def collect_words(node, path):
            if '*' in node:
                words.append(node['*'])
            for char, child in node.items():
                if char != '*':
                    collect_words(child, path + char)
                    
        collect_words(current, prefix)
        
        # Sort by frequency and return top suggestions
        words.sort(key=lambda x: (-self.word_frequencies[x], x))
        return words[:max_suggestions]
        
    def process_search_query(self, query: str) -> List[str]:
        """Process a search query and extract words"""
        words = re.findall(r'\w+', query.lower())
        for word in words:
            self.add_word(word)
            
        # Update recent queries
        self.recent_queries.append(query)
        if len(self.recent_queries) > 10:
            self.recent_queries.pop(0)
            
        return words

# Initialize with common dark web search terms
common_terms = [
    "drugs", "weapons", "hacking", "bitcoin", "cryptocurrency", 
    "marketplace", "forum", "anonymous", "security", "privacy",
    "tor", "onion", "hidden", "encrypted", "secure",
    "market", "buy", "sell", "trade", "exchange"
]

recommendation_system = WordRecommendationSystem()
recommendation_system.add_common_terms(common_terms) 