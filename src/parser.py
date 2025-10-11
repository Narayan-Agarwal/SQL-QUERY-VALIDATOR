from typing import List, Tuple
# Use relative import for running as a module (python -m src.parser)
from .lexer import tokenize 

# The token tuple type: (VALUE, TYPE)
Token = Tuple[str, str]

class Parser:
    """
    Finalized, Expanded Recursive Descent Parser for a comprehensive subset of SQL.
    Includes SELECT, INSERT, UPDATE, DELETE, and complex clauses.
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
        """
        <Query> ::= <Statement> [ ; ]
        """
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

        # Optional semicolon at the end
        if self.current_token and self.current_token[1] == 'SEMICOLON':
            self._advance()
        
        # Check for trailing junk
        if self.current_token is not None:
             raise SyntaxError(f"Syntax Error: Found extra tokens after statement completion: '{self.current_token[0]}'")

    # --- DML STATEMENT PARSERS ---

    def parse_select_statement(self):
        """
        <SelectStmt> ::= SELECT <SelList> FROM <TableList> [ WHERE <Condition> ] [ GROUP BY <ColList> ] [ ORDER BY <ColList> ] [ LIMIT <Value> ]
        """
        self._expect('KEYWORD', 'SELECT')
        self.parse_select_list()
        self._expect('KEYWORD', 'FROM')
        self.parse_table_list()
        
        # Optional Clauses
        while self.current_token:
            token_value = self.current_token[0].upper()
            
            if token_value == 'WHERE':
                self._advance() 
                self.parse_condition()
                
            elif token_value == 'GROUP':
                self._advance() # Consume GROUP
                self._expect('KEYWORD', 'BY') # Consume BY
                self.parse_column_list()
                
            elif token_value == 'ORDER':
                self._advance() # Consume ORDER
                self._expect('KEYWORD', 'BY') # Consume BY
                self.parse_column_list()

            elif token_value == 'LIMIT':
                self._advance() 
                self.parse_value() # Expect a value for the limit
            
            # If the token is not a recognized optional keyword, stop the loop
            else:
                break 

    def parse_insert_statement(self):
        """
        <InsertStmt> ::= INSERT INTO <Identifier> ( <ColList> ) VALUES ( <ValueList> )
        """
        self._expect('KEYWORD', 'INSERT')
        self._expect('KEYWORD', 'INTO')
        self._expect('IDENTIFIER') # Table name
        
        self._expect('PARENTHESIS', '(')
        self.parse_column_list() # List of columns
        self._expect('PARENTHESIS', ')')
        
        self._expect('KEYWORD', 'VALUES')
        self._expect('PARENTHESIS', '(')
        self.parse_value_list() # List of values
        self._expect('PARENTHESIS', ')')

    def parse_update_statement(self):
        """
        <UpdateStmt> ::= UPDATE <Identifier> SET <AssignmentList> [ WHERE <Condition> ]
        FIX: Uses the corrected method name parse_table_alias_item()
        """
        self._expect('KEYWORD', 'UPDATE')
        self.parse_table_alias_item() # CORRECTED CALL
        self._expect('KEYWORD', 'SET')
        self.parse_assignment_list() # col = value, ...

        # Optional WHERE clause
        if self.current_token and self.current_token[0].upper() == 'WHERE':
            self._advance() 
            self.parse_condition()

    def parse_delete_statement(self):
        """
        <DeleteStmt> ::= DELETE FROM <Identifier> [ WHERE <Condition> ]
        FIX: Uses the corrected method name parse_table_alias_item()
        """
        self._expect('KEYWORD', 'DELETE')
        self._expect('KEYWORD', 'FROM')
        self.parse_table_alias_item() # CORRECTED CALL
        
        # Optional WHERE clause
        if self.current_token and self.current_token[0].upper() == 'WHERE':
            self._advance() 
            self.parse_condition()


    # --- SUB-CLAUSE PARSERS ---

    def parse_select_list(self):
        """
        <SelList> ::= <SelItem> { , <SelItem> } | *
        """
        if self.current_token and self.current_token[1] == 'WILDCARD':
            self._advance() # Consume *
            return
            
        self.parse_select_item()

        while self.current_token and self.current_token[1] == 'COMMA':
            self._advance() # Consume COMMA
            self.parse_select_item()

    def parse_select_item(self):
        """
        Handles column names, aliases, or function calls.
        FIX: Logic corrected to properly handle COUNT(*)
        """
        
        # 1. Parse the base item (Qualified Identifier or Function)
        
        # Check for FUNCTION (e.g., COUNT(*))
        if self.current_token and self.current_token[1] == 'FUNCTION':
            self._advance() # Consume FUNCTION
            self._expect('PARENTHESIS', '(')
            
            # Function argument is any valid value item (including qualified identifier or wildcard)
            if self.current_token and self.current_token[1] == 'WILDCARD':
                self._advance() # Consume * (e.g., COUNT(*))
            elif self.current_token and self.current_token[1] == 'IDENTIFIER':
                self.parse_qualified_identifier() # Handles name or alias.name
            else:
                 raise SyntaxError("Syntax Error: Expected column name, '*', or value inside function.")
                 
            self._expect('PARENTHESIS', ')')
            
        # Standard column identifier (potentially qualified)
        elif self.current_token and self.current_token[1] == 'IDENTIFIER':
            self.parse_qualified_identifier()
        else:
            raise SyntaxError("Syntax Error: Expected column name, function, or '*' in SELECT list.")
            
        # 2. Optional ALIAS (e.g., AS name or just name)
        if self.current_token and self.current_token[0].upper() == 'AS':
            self._advance() # Consume AS
            self._expect('IDENTIFIER') # Consume alias name
        # Simple alias check (e.g., SELECT col alias FROM table)
        elif self.current_token and self.current_token[1] == 'IDENTIFIER':
            self._advance() # Consume the simple alias identifier

    def parse_qualified_identifier(self):
        """
        Handles identifiers that may be qualified (e.g., table.column or just column).
        """
        self._expect('IDENTIFIER')
        if self.current_token and self.current_token[1] == 'DOT':
            self._advance() # Consume DOT
            self._expect('IDENTIFIER') # Consume column name

    def parse_table_list(self):
        """
        <TableList> ::= <TableAliasItem> { , <TableAliasItem> } 
        """
        self.parse_table_alias_item() 
        
        while self.current_token and self.current_token[1] == 'COMMA':
            self._advance() # Consume COMMA
            self.parse_table_alias_item() 

    def parse_table_alias_item(self):
        """
        Handles a table name and its optional alias (e.g., users u).
        <TableAliasItem> ::= <Identifier> [ AS <Identifier> | <Identifier> ]
        """
        self._expect('IDENTIFIER') # Table name
        
        # Optional ALIAS (e.g., AS u)
        if self.current_token and self.current_token[0].upper() == 'AS':
            self._advance() # Consume AS
            self._expect('IDENTIFIER') # Consume alias name
        # Simple alias (e.g., users u)
        elif self.current_token and self.current_token[1] == 'IDENTIFIER':
            self._advance() # Consume the simple alias identifier 

    def parse_column_list(self):
        """
        <ColList> ::= <Identifier> { , <Identifier> }
        Used in GROUP BY, ORDER BY, and INSERT statements.
        """
        self._expect('IDENTIFIER') # First column
        
        while self.current_token and self.current_token[1] == 'COMMA':
            self._advance() # Consume COMMA
            self._expect('IDENTIFIER') # Next column

    def parse_assignment_list(self):
        """
        <AssignmentList> ::= <Identifier> = <Value> { , <Identifier> = <Value> }
        Used in UPDATE statements (SET clause).
        """
        self._expect('IDENTIFIER') # Column name
        self._expect('OPERATOR', '=')
        self.parse_value() # Value to assign
        
        while self.current_token and self.current_token[1] == 'COMMA':
            self._advance() # Consume COMMA
            self._expect('IDENTIFIER') # Next column name
            self._expect('OPERATOR', '=')
            self.parse_value() # Next value

    def parse_value_list(self):
        """
        <ValueList> ::= <Value> { , <Value> }
        Used in INSERT statements (VALUES clause).
        """
        self.parse_value()
        
        while self.current_token and self.current_token[1] == 'COMMA':
            self._advance() # Consume COMMA
            self.parse_value()

    def parse_condition(self):
        """
        <Condition> ::= <Comparison> { AND | OR <Condition> }
        """
        self.parse_comparison()
        
        # Handle compound conditions (AND/OR)
        while self.current_token and self.current_token[0].upper() in ('AND', 'OR'):
            self._advance() # Consume AND/OR
            self.parse_comparison()

    def parse_comparison(self):
        """
        <Comparison> ::= <Value> <Operator> <Value>
        """
        self.parse_value() # Left-hand side
        self._expect('OPERATOR') # Comparison operator (e.g., >, = or !=)
        self.parse_value() # Right-hand side

    def parse_value(self):
        """
        <Value> ::= <QualifiedIdentifier> | <NUMBER> | <STRING>
        """
        if self.current_token and self.current_token[1] in ('NUMBER', 'STRING'):
            self._advance()
        elif self.current_token and self.current_token[1] == 'IDENTIFIER':
             # Allow identifier on RHS of comparison (e.g., col1 = col2)
             self.parse_qualified_identifier()
        else:
            current = self.current_token[0] if self.current_token else "END OF QUERY"
            raise SyntaxError(f"Syntax Error: Expected value (identifier, number, or string) but got '{current}'")


def validate_query(query: str) -> str:
    """
    Main function to orchestrate the Lexical and Syntactic Analysis, 
    returning a clean status message or error string.
    """
    try:
        # 1. Lexical Analysis
        tokens = tokenize(query)

        # 2. Syntactic Analysis
        parser = Parser(tokens)
        parser.parse_query()
        
        # If no exception was raised
        return "✅ VALIDATION SUCCESS: Query structure is fully valid."
        
    except (ValueError, SyntaxError) as e:
        # ValueError from Lexer, SyntaxError from Parser
        return f"❌ VALIDATION FAILED: {type(e).__name__}: {str(e)}"
        
    except Exception as e:
        return f"❌ UNEXPECTED ERROR: {type(e).__name__}: {str(e)}"
        

if __name__ == '__main__':
    # --- FINAL CORRECTED TEST SUITE ---
    
    print("\n--- Running Final Corrected SQL Validation Test Suite ---\n")

    test_queries = [
        # VALID SELECT Tests (Includes Qualified Names, Aliases, and COUNT(*))
        ("SELECT u.name, COUNT(*) AS total FROM users u WHERE u.age > 25 GROUP BY u.name ORDER BY total LIMIT 10;", "VALID (SELECT with Clauses)"),
        ("SELECT user_id, name FROM users u, orders o WHERE u.id = o.user_id;", "VALID (Simple Join, Alias, Qualified WHERE)"), 
        ("SELECT name, age FROM users;", "VALID (Simple SELECT)"),
        ("SELECT total_price AS price, item_name FROM invoices;", "VALID (Select Alias)"),

        # VALID DML Tests
        ("INSERT INTO employees (id, name) VALUES (1, 'Alice');", "VALID (INSERT)"),
        ("UPDATE products SET price = 1500, stock = 10 WHERE id = 5;", "VALID (UPDATE)"),
        ("DELETE FROM logs WHERE date < '2023-01-01';", "VALID (DELETE)"),
        
        # INVALID Tests (Should all fail)
        ("SELECT name, FROM users;", "INVALID (Missing item after comma)"),
        ("INSERT INTO employees (name) VALUES ('Bob' 50000);", "INVALID (Missing comma in VALUES)"),
        ("UPDATE products SET price 1500 WHERE id = 5;", "INVALID (Missing operator in SET)"),
        ("SELECT * FROM table WHERE column = 5$;", "INVALID (Lexical Error)"),
    ]

    for query, expectation in test_queries:
        print(f"[{expectation}] Query: {query}")
        result = validate_query(query)
        print(f"  Result: {result}\n")