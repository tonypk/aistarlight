"""Form Schema Registry — loads schemas from DB and evaluates formulas safely.

The formula evaluator is a minimal AST-based calculator that only supports:
- Decimal literals
- Field references (e.g. line_1_vatable_sales)
- Operators: + - * /
- Parentheses for grouping
- Built-in functions: max(), min()

No eval(), no exec(), no arbitrary code execution.
"""

import re
from decimal import Decimal, InvalidOperation
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.models.form_schema import FormSchema
from backend.repositories.form_schema import FormSchemaRepository

# ============================================================
# Safe formula tokenizer & evaluator
# ============================================================

# Token types
_NUM = "NUM"
_ID = "ID"
_OP = "OP"
_LPAREN = "LPAREN"
_RPAREN = "RPAREN"
_COMMA = "COMMA"
_FUNC = "FUNC"
_EOF = "EOF"

_TOKEN_RE = re.compile(
    r"""
    (?P<num>\d+(?:\.\d+)?)     |  # decimal number
    (?P<func>max|min)\s*(?=\()  |  # function name before (
    (?P<id>[a-zA-Z_]\w*)        |  # identifier (field reference)
    (?P<op>[+\-*/])             |  # operator
    (?P<lparen>\()              |  # left paren
    (?P<rparen>\))              |  # right paren
    (?P<comma>,)                |  # comma
    \s+                            # whitespace (skip)
    """,
    re.VERBOSE,
)


def _tokenize(formula: str) -> list[tuple[str, str]]:
    tokens = []
    for m in _TOKEN_RE.finditer(formula):
        if m.group("num"):
            tokens.append((_NUM, m.group("num")))
        elif m.group("func"):
            tokens.append((_FUNC, m.group("func")))
        elif m.group("id"):
            tokens.append((_ID, m.group("id")))
        elif m.group("op"):
            tokens.append((_OP, m.group("op")))
        elif m.group("lparen"):
            tokens.append((_LPAREN, "("))
        elif m.group("rparen"):
            tokens.append((_RPAREN, ")"))
        elif m.group("comma"):
            tokens.append((_COMMA, ","))
    tokens.append((_EOF, ""))
    return tokens


class _Parser:
    """Recursive-descent parser for safe formula evaluation."""

    def __init__(self, tokens: list[tuple[str, str]], fields: dict[str, Decimal]):
        self.tokens = tokens
        self.fields = fields
        self.pos = 0

    def _peek(self) -> tuple[str, str]:
        return self.tokens[self.pos]

    def _eat(self, expected_type: str | None = None) -> tuple[str, str]:
        tok = self.tokens[self.pos]
        if expected_type and tok[0] != expected_type:
            raise ValueError(f"Expected {expected_type}, got {tok[0]} ({tok[1]!r})")
        self.pos += 1
        return tok

    def parse(self) -> Decimal:
        result = self._expr()
        if self._peek()[0] != _EOF:
            raise ValueError(f"Unexpected token: {self._peek()}")
        return result

    def _expr(self) -> Decimal:
        """expr = term (('+' | '-') term)*"""
        left = self._term()
        while self._peek() == (_OP, "+") or self._peek() == (_OP, "-"):
            op = self._eat(_OP)[1]
            right = self._term()
            left = left + right if op == "+" else left - right
        return left

    def _term(self) -> Decimal:
        """term = unary (('*' | '/') unary)*"""
        left = self._unary()
        while self._peek() == (_OP, "*") or self._peek() == (_OP, "/"):
            op = self._eat(_OP)[1]
            right = self._unary()
            if op == "*":
                left = left * right
            else:
                left = left / right if right != 0 else Decimal("0")
        return left

    def _unary(self) -> Decimal:
        """unary = '-' unary | atom"""
        if self._peek() == (_OP, "-"):
            self._eat(_OP)
            return -self._unary()
        return self._atom()

    def _atom(self) -> Decimal:
        """atom = NUM | ID | FUNC '(' expr (',' expr)* ')' | '(' expr ')'"""
        tok_type, tok_val = self._peek()

        if tok_type == _NUM:
            self._eat(_NUM)
            return Decimal(tok_val)

        if tok_type == _ID:
            self._eat(_ID)
            return self.fields.get(tok_val, Decimal("0"))

        if tok_type == _FUNC:
            func_name = self._eat(_FUNC)[1]
            self._eat(_LPAREN)
            args = [self._expr()]
            while self._peek()[0] == _COMMA:
                self._eat(_COMMA)
                args.append(self._expr())
            self._eat(_RPAREN)
            if func_name == "max":
                return max(args)
            if func_name == "min":
                return min(args)
            raise ValueError(f"Unknown function: {func_name}")

        if tok_type == _LPAREN:
            self._eat(_LPAREN)
            result = self._expr()
            self._eat(_RPAREN)
            return result

        raise ValueError(f"Unexpected token: {tok_type} ({tok_val!r})")


def evaluate_formula(formula: str, fields: dict[str, Decimal]) -> Decimal:
    """Safely evaluate a formula string using only field references and basic math.

    Args:
        formula: Expression like "line_1 + line_2 + line_3 + line_4"
        fields: Dict of field_id → Decimal value

    Returns:
        Calculated Decimal result.
    """
    tokens = _tokenize(formula)
    parser = _Parser(tokens, fields)
    return parser.parse()


# ============================================================
# Schema registry service functions
# ============================================================


async def get_form_schema(form_type: str, db: AsyncSession) -> FormSchema | None:
    """Load the active schema for a form type from the database."""
    repo = FormSchemaRepository(db)
    return await repo.get_active(form_type)


async def list_active_schemas(db: AsyncSession) -> list[dict[str, Any]]:
    """List all active form schemas (summary info)."""
    repo = FormSchemaRepository(db)
    schemas = await repo.list_active_forms()
    return [
        {
            "form_type": s.form_type,
            "name": s.name,
            "frequency": s.frequency,
            "version": s.version,
        }
        for s in schemas
    ]


def evaluate_formulas(
    schema: FormSchema,
    field_values: dict[str, str],
) -> dict[str, str]:
    """Evaluate all calculation rules from a schema against current field values.

    Args:
        schema: The FormSchema containing calculation_rules.
        field_values: Dict of field_id → string value.

    Returns:
        Updated dict with computed fields filled in.
    """
    result = dict(field_values)

    # Convert to Decimal for calculation
    decimal_fields: dict[str, Decimal] = {}
    for key, val in result.items():
        try:
            decimal_fields[key] = Decimal(str(val))
        except (InvalidOperation, ValueError):
            decimal_fields[key] = Decimal("0")

    # Evaluate rules in order (they should be topologically sorted in the schema)
    rules = schema.calculation_rules or {}
    for field_id, formula in rules.items():
        computed_value = evaluate_formula(formula, decimal_fields)
        decimal_fields[field_id] = computed_value
        result[field_id] = str(computed_value)

    return result


def validate_report_data(schema: FormSchema, data: dict[str, str]) -> list[str]:
    """Validate report data against a schema. Returns list of error messages."""
    errors = []
    schema_def = schema.schema_def or {}

    for section in schema_def.get("sections", []):
        for field in section.get("fields", []):
            field_id = field["id"]
            if field.get("required") and not data.get(field_id):
                errors.append(f"Missing required field: {field.get('label', field_id)}")

    return errors
