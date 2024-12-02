from antlr4 import (
    InputStream,
    CommonTokenStream,
    ParserRuleContext,
    TerminalNode,
)
from project.graph_query_language.LanguageLexer import LanguageLexer
from project.graph_query_language.LanguageParser import LanguageParser


def get_parser(inp):
    input_stream = InputStream(inp)
    lexer = LanguageLexer(input_stream)
    stream = CommonTokenStream(lexer)
    return LanguageParser(stream)


def parse(inp):
    input_stream = InputStream(inp)
    lexer = LanguageLexer(input_stream)
    stream = CommonTokenStream(lexer)
    parser = LanguageParser(stream)
    return parser.prog()


def accepts(inp):
    parser = get_parser(inp)
    parser.removeErrorListeners()
    parser.prog()
    return parser.getNumberOfSyntaxErrors() == 0


def program_to_tree(program: str) -> tuple[ParserRuleContext, bool]:
    try:
        parser = get_parser(program)
        parse_tree = parser.prog()
        success = parser.getNumberOfSyntaxErrors() == 0
        return parse_tree, success
    except Exception as _:
        return None, False


def tree_to_program(tree: ParserRuleContext) -> str:
    if isinstance(tree, TerminalNode):
        return tree.getText()

    program = ""

    for child in tree.getChildren():
        child_text = tree_to_program(child)
        if program and child_text not in ("", "(", ")", "{", "}", ",", ";"):
            program += " "
        program += child_text
    return program


def nodes_count(tree: ParserRuleContext) -> int:
    if isinstance(tree, TerminalNode):
        return 1

    count = 1

    for child in tree.getChildren():
        count += nodes_count(child)
    return count
