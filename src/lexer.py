import re
from typing import List, Tuple

# TOKEN_PATTERNS: Order is critical (specific keywords before generic identifiers)
TOKEN_PATTERNS = [
    # 1. Keywords (Case-insensitive)
    (r'\b(SELECT|FROM|WHERE|INSERT|INTO|VALUES|UPDATE|SET|DELETE|AND|OR|NOT|AS|JOIN|ON|GROUP BY|ORDER BY|LIMIT|OFFSET)\b', 'KEYWORD'),
    
    # 2. Built-in Functions
    (r'\b(COUNT|SUM|AVG|MIN|MAX)\b', 'FUNCTION'),
    
    # 3. Operators (Multi-character operators first)
    (r'>=|<=|!=|==|=|>|<|\+|-|\*|/', 'OPERATOR'),
    
    # 4. Literals: Strings (single quotes)
    (r"'[^']*'", 'STRING'),
    
    # 5. Literals: Numbers (integers and floats)
    (r'\b\d+(\.\d+)?\b', 'NUMBER'),
    
    # 6. Syntax Elements
    (r'[\(\)]', 'PARENTHESIS'),
    (r',', 'COMMA'),
    (r';', 'SEMICOLON'),

    # 7. Dot for table.column qualification
    (r'\.', 'DOT'), 

    # 8. Wildcard
    (r'\*', 'WILDCARD'),
    
    # 9. Identifiers (Table/Column names)
    (r'[a-zA-Z_][a-zA-Z0-9_]*', 'IDENTIFIER'),
    
    # 10. Whitespace (token_type=None to skip)
    (r'\s+', None),
]

def tokenize(query: str) -> List[Tuple[str, str]]:
    """Performs lexical analysis on an SQL query string to produce a list of tokens."""
    tokens = []
    position = 0
    query = query.strip()
    
    while position < len(query):
        match_found = False
        
        for pattern, token_type in TOKEN_PATTERNS:
            match = re.match(pattern, query[position:], re.IGNORECASE)
            
            if match:
                value = match.group(0)
                
                if token_type: # Skip whitespace
                    tokens.append((value.upper(), token_type))
                    
                position += len(value)
                match_found = True
                break
        
        if not match_found:
            snippet = query[position:position+10].replace('\n', ' ')
            raise ValueError(f"Lexical Error: Unknown token starting at position {position}. Snippet: '{snippet}...'")
            
    return tokens

if __name__ == '__main__':
    # Test cases for manual verification
    sample_query = "SELECT u.name, COUNT(*) FROM users u WHERE u.age > 25;"
    print("--- Tokenizing Sample Query ---")
    try:
        token_list = tokenize(sample_query)
        for value, type in token_list:
            print(f"Value: '{value}'\t\tType: {type}")
    except ValueError as e:
        print(f"Error: {e}")