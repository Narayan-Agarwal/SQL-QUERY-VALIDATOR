from typing import List, Tuple
# Use relative import for running as a module (python -m src.parser)
from .lexer import tokenize 

# The token tuple type: (VALUE, TYPE)
Token = Tuple[str, str]

class Parser:
    """
    Finalized, Consolidated Recursive Descent Parser. This version consolidates
    the SELECT list logic to guarantee flow control and resolve the persistent bug.
    """
    def __init__(self, tokens: List[Token]):
        self.tokens = tokens
        self.current_token_index = 0
        self.current_token = self.tokens[0] if self.tokens else None
        
    def _advance(self):
        """Moves to the next token in the stream."""
        self.current_token_index += 1
        if self.current_token_index < len(self.tokens):
            self.current_token = self.tokens[self.current_token_index]
        else:
            self.current_token = None

    def _expect(self, expected_type: str, value: str = None):
        """
        Checks if the current token matches the expected type and optional value.
        Advances if successful, raises an error otherwise.
        """
        if self.current_token is None:
            raise SyntaxError(f"Syntax Error: Expected '{expected_type}' but found end of query.")
            
        token_value, token_type = self.current_token
        
        if token_type != expected_type:
            raise SyntaxError(f"Syntax Error: Expected token type '{expected_type}' but got '{token_type}' ('{token_value}').")
            
        if value is not None and token_value.upper() != value.upper():
            raise SyntaxError(f"Syntax Error: Expected keyword '{value}' but got '{token_value}'.")
            
        self._advance()

    # --- TOP-LEVEL GRAMMAR RULES ---

    def parse_query(self):
        if not self.current_token:
            return
        token_value = self.current_token[0].upper()
        
        if token_value == 'SELECT':
            self.parse_select_statement()
        elif token_value == 'INSERT':
            self.parse_insert_statement()
        elif token_value == 'UPDATE':
            self.parse_update_statement()
        elif token_value == 'DELETE':
            self.parse_delete_statement()
        else:
            raise SyntaxError(f"Syntax Error: Expected a statement (SELECT, INSERT, UPDATE, DELETE) but got '{token_value}'")

        if self.current_token and self.current_token[1] == 'SEMICOLON':
            self._advance()
        
        if self.current_token is not None:
             raise SyntaxError(f"Syntax Error: Found extra tokens after statement completion: '{self.current_token[0]}'")

    # --- DML STATEMENT PARSERS ---

    def parse_select_statement(self):
        """
        FINAL FIX: Merges the list logic here for robust flow control.
        """
        self._expect('KEYWORD', 'SELECT')
        
        # --- START CONSOLIDATED SELECT LIST LOGIC ---
        
        # 1. Handle the list of items or the wildcard
        if self.current_token and self.current_token[1] == 'WILDCARD':
            self._advance() # Consume *
        else:
            # Parse the first item
            self.parse_select_item()
            
            # Parse subsequent items separated by commas
            while self.current_token and self.current_token[1] == 'COMMA':
                self._advance() # Consume COMMA
                self.parse_select_item()

        # --- END CONSOLIDATED SELECT LIST LOGIC ---
        
        self._expect('KEYWORD', 'FROM') # This will now execute correctly.
        self.parse_table_list()
        
        # Optional Clauses
        while self.current_token:
            token_value = self.current_token[0].upper()
            
            if token_value == 'WHERE':
                self._advance() 
                self.parse_condition()
                
            elif token_value == 'GROUP':
                self._advance() 
                self._expect('KEYWORD', 'BY') 
                self.parse_column_list()
                
            elif token_value == 'ORDER':
                self._advance() 
                self._expect('KEYWORD', 'BY') 
                self.parse_column_list()

            elif token_value == 'LIMIT':
                self._advance() 
                self.parse_value() 
            else:
                break 

    def parse_insert_statement(self):
        self._expect('KEYWORD', 'INSERT')
        self._expect('KEYWORD', 'INTO')
        self._expect('IDENTIFIER') 
        self._expect('PARENTHESIS', '(')
        self.parse_column_list() 
        self._expect('PARENTHESIS', ')')
        self._expect('KEYWORD', 'VALUES')
        self._expect('PARENTHESIS', '(')
        self.parse_value_list() 
        self._expect('PARENTHESIS', ')')

    def parse_update_statement(self):
        self._expect('KEYWORD', 'UPDATE')
        self.parse_table_alias_item() 
        self._expect('KEYWORD', 'SET')
        self.parse_assignment_list() 
        if self.current_token and self.current_token[0].upper() == 'WHERE':
            self._advance() 
            self.parse_condition()

    def parse_delete_statement(self):
        self._expect('KEYWORD', 'DELETE')
        self._expect('KEYWORD', 'FROM')
        self.parse_table_alias_item() 
        if self.current_token and self.current_token[0].upper() == 'WHERE':
            self._advance() 
            self.parse_condition()


    # --- SUB-CLAUSE PARSERS (Simplified/Consolidated) ---
    
    # We remove the old parse_select_list function entirely as its logic is now merged.

    def parse_select_item(self):
        """
        Handles column names, aliases, or function calls.
        """
        
        if self.current_token and self.current_token[1] == 'FUNCTION':
            self._advance() 
            self._expect('PARENTHESIS', '(')
            
            if self.current_token and self.current_token[1] == 'WILDCARD':
                self._advance() 
            elif self.current_token and self.current_token[1] == 'IDENTIFIER':
                self.parse_qualified_identifier() 
            else:
                 raise SyntaxError("Syntax Error: Expected column name, '*', or value inside function.")
                 
            self._expect('PARENTHESIS', ')')
            
        elif self.current_token and self.current_token[1] == 'IDENTIFIER':
            self.parse_qualified_identifier()
        else:
            # This error is now only raised if we expected a new item after a comma, 
            # or if the list started incorrectly.
            raise SyntaxError("Syntax Error: Expected column name, function, or '*' in SELECT list.")
            
        # 2. Optional ALIAS
        if self.current_token and self.current_token[0].upper() == 'AS':
            self._advance()
            self._expect('IDENTIFIER') 
        elif self.current_token and self.current_token[1] == 'IDENTIFIER':
            self._advance() 

    def parse_qualified_identifier(self):
        self._expect('IDENTIFIER')
        if self.current_token and self.current_token[1] == 'DOT':
            self._advance() 
            self._expect('IDENTIFIER') 

    def parse_table_list(self):
        self.parse_table_alias_item() 
        while self.current_token and self.current_token[1] == 'COMMA':
            self._advance() 
            self.parse_table_alias_item() 

    def parse_table_alias_item(self):
        self._expect('IDENTIFIER') 
        if self.current_token and self.current_token[0].upper() == 'AS':
            self._advance() 
            self._expect('IDENTIFIER') 
        elif self.current_token and self.current_token[1] == 'IDENTIFIER':
            self._advance() 

    def parse_column_list(self):
        self._expect('IDENTIFIER') 
        while self.current_token and self.current_token[1] == 'COMMA':
            self._advance() 
            self._expect('IDENTIFIER') 

    def parse_assignment_list(self):
        self._expect('IDENTIFIER') 
        self._expect('OPERATOR', '=')
        self.parse_value() 
        while self.current_token and self.current_token[1] == 'COMMA':
            self._advance() 
            self._expect('IDENTIFIER') 
            self._expect('OPERATOR', '=')
            self.parse_value() 

    def parse_value_list(self):
        self.parse_value()
        while self.current_token and self.current_token[1] == 'COMMA':
            self._advance() 
            self.parse_value()

    def parse_condition(self):
        self.parse_comparison()
        while self.current_token and self.current_token[0].upper() in ('AND', 'OR'):
            self._advance() 
            self.parse_comparison()

    def parse_comparison(self):
        self.parse_value() 
        self._expect('OPERATOR') 
        self.parse_value() 

    def parse_value(self):
        if self.current_token and self.current_token[1] in ('NUMBER', 'STRING'):
            self._advance()
        elif self.current_token and self.current_token[1] == 'IDENTIFIER':
             self.parse_qualified_identifier()
        else:
            current = self.current_token[0] if self.current_token else "END OF QUERY"
            raise SyntaxError(f"Syntax Error: Expected value (identifier, number, or string) but got '{current}'")


def validate_query(query: str) -> str:
    try:
        tokens = tokenize(query)
        parser = Parser(tokens)
        parser.parse_query()
        return "✅ VALIDATION SUCCESS: Query structure is fully valid."
        
    except (ValueError, SyntaxError) as e:
        return f"❌ VALIDATION FAILED: {type(e).__name__}: {str(e)}"
        
    except Exception as e:
        return f"❌ UNEXPECTED ERROR: {type(e).__name__}: {str(e)}"
        

if __name__ == '__main__':
    print("\n--- Running Final Consolidated SQL Validation Test Suite ---\n")

    test_queries = [
        ("SELECT * FROM users;", "VALID (Simple SELECT *)"), # Test case for the fix
        ("SELECT u.name, COUNT(*) AS total FROM users u WHERE u.age > 25 GROUP BY u.name ORDER BY total LIMIT 10;", "VALID (SELECT with Clauses)"),
        ("SELECT user_id, name FROM users u, orders o WHERE u.id = o.user_id;", "VALID (Simple Join, Alias, Qualified WHERE)"), 
        ("SELECT name, age FROM users;", "VALID (Simple SELECT)"),
        
        ("INSERT INTO employees (id, name) VALUES (1, 'Alice');", "VALID (INSERT)"),
        ("UPDATE products SET price = 1500, stock = 10 WHERE id = 5;", "VALID (UPDATE)"),
        
        ("SELECT name, FROM users;", "INVALID (Missing item after comma)"),
        ("UPDATE products SET price 1500 WHERE id = 5;", "INVALID (Missing operator in SET)"),
        ("SELECT * FROM table WHERE column = 5$;", "INVALID (Lexical Error)"),
    ]

    for query, expectation in test_queries:
        print(f"[{expectation}] Query: {query}")
        result = validate_query(query)
        print(f"  Result: {result}\n")
