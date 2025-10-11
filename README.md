# SQL Query Validator (Lexical and Syntactic Analysis) 📝

## Project Overview 💡

This project implements a robust **SQL Query Validator** based on **Formal Language Theory**. The tool validates the structure (syntax) of common SQL Data Manipulation Language (DML) statements (`SELECT`, `INSERT`, `UPDATE`, `DELETE`) by dividing the process into two phases: Lexical Analysis and Syntactic Analysis.

This serves as a strong demonstration of compiler design principles, using **Regular Expressions** for tokenization and a **Context-Free Grammar (CFG)** for structural parsing.

***

## Technical Concepts & Implementation Details

### 1. Lexical Analysis (The Tokenizer)
* **Implementation:** Hand-coded in Python using the built-in `re` module (`src/lexer.py`).
* **Function:** Scans the raw SQL query, recognizing keywords, identifiers, operators, and literals, converting them into a stream of structured **tokens** (e.g., `('SELECT', 'KEYWORD')`).
* **Feature:** Correctly handles **qualified names** (`alias.column`) by tokenizing the dot (`.`).

### 2. Syntactic Analysis (The Parser)
* **Implementation:** A custom-built **Recursive Descent Parser** (`src/parser.py`), a top-down parsing technique.
* **Core Concept:** Implements a comprehensive **Context-Free Grammar (CFG)**. Each rule in the grammar is mapped to a dedicated Python function (e.g., `parse_select_statement()`).
* **Validation Coverage:** The grammar validates complex SQL features including:
    * Multiple statement types (`SELECT`, `INSERT`, `UPDATE`, `DELETE`).
    * **Complex Clauses:** `GROUP BY`, `ORDER BY`, `LIMIT`.
    * **Aliases:** Column aliasing (`AS`) and table aliasing (`users u`).
    * **Boolean Logic:** Compound `WHERE` conditions (`AND`/`OR`).
* **Error Handling:** Provides specific `SyntaxError` feedback indicating where the query deviates from the defined grammar.

***

## System Architecture

The validator is deployed as a simple full-stack application  that integrates the theory concepts with a practical interface.

| Component | Technology | Role |
| :--- | :--- | :--- |
| **Frontend** | HTML/JavaScript (`index.html`) | User interface for input and display of validation results. |
| **Backend API** | Python/Flask (`app.py`) | Handles HTTP POST requests, orchestrates the validation engine, and returns JSON responses. |
| **Core Logic** | Python (`src/`) | Performs the Lexical $\rightarrow$ Syntactic analysis pipeline. |

***

## Getting Started

### Prerequisites
* Python 3.8+
* `git` (for cloning the repository)

### Setup and Installation

1.  **Clone the Repository:**
    ```bash
    git clone [https://github.com/Narayan-Agarwal/SQL-QUERY-VALIDATOR.git](https://github.com/Narayan-Agarwal/SQL-QUERY-VALIDATOR.git)
    cd SQL-QUERY-VALIDATOR
    ```

2.  **Create and Activate Virtual Environment:**
    ```bash
    python -m venv venv
    venv\Scripts\activate   # On Windows (use source venv/bin/activate on Linux/macOS)
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

### How to Run and Test

1.  **Start the Backend API (Flask):** Keep this terminal window open and running.
    ```bash
    python app.py
    ```
    The server will start at `http://127.0.0.1:5000/`.

2.  **Open the Frontend:**
    * Navigate to the project root directory in your file explorer.
    * **Double-click** `index.html` to open the validator interface in your web browser.

3.  **Test Queries:** Enter various SQL statements to confirm correct validation (e.g., `SELECT COUNT(id) AS total FROM products;` vs. `INSERT INTO users VALUES (10);`).

***

## Repository Structure

SQL-QUERY-VALIDATOR/
├── .gitignore          # Tells Git to ignore venv, __pycache__, etc.
├── README.md           # Project documentation and setup guide (The file you are reading)
├── app.py              # Flask API entry point (Connects UI to core logic)
├── index.html          # Frontend UI (HTML, CSS, and JavaScript for user interaction)
├── requirements.txt    # List of all Python dependencies (Flask, flask-cors)
├── venv/               # (IGNORED by Git) Virtual environment folder
└── src/                # Core Validation Engine
    ├── lexer.py        # Lexical Analyzer (Tokenization via Regular Expressions)
    └── parser.py       # Syntactic Analyzer (Context-Free Grammar / Recursive Descent Parser)
