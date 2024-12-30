import antlr4
from project.graph_query_language.LanguageLexer import LanguageLexer
from project.graph_query_language.LanguageParser import LanguageParser


class ConvertToProgramListener(antlr4.ParseTreeListener):
    def __init__(self):
        self.tokens = list()

    def visitTerminal(self, node):
        self.tokens.append(node.getText())


class CounterListener(antlr4.ParseTreeListener):
    def __init__(self):
        self.count = 0

    def enterEveryRule(self, _):
        self.count += 1


def get_parser(inp):
    input_stream = antlr4.InputStream(inp)
    lexer = LanguageLexer(input_stream)
    stream = antlr4.CommonTokenStream(lexer)
    return LanguageParser(stream)


def parse(inp):
    input_stream = antlr4.InputStream(inp)
    lexer = LanguageLexer(input_stream)
    stream = antlr4.CommonTokenStream(lexer)
    parser = LanguageParser(stream)
    return parser.prog()


def accepts(inp):
    parser = get_parser(inp)
    parser.removeErrorListeners()
    parser.prog()
    return parser.getNumberOfSyntaxErrors() == 0


def program_to_tree(program: str) -> tuple[antlr4.ParserRuleContext, bool]:
    try:
        parser = get_parser(program)
        parse_tree = parser.prog()
        success = parser.getNumberOfSyntaxErrors() == 0
        return parse_tree, success
    except Exception as _:
        return None, False


def nodes_count(tree: antlr4.ParserRuleContext) -> int:
    if tree is None:
        return 0

    countListener = CounterListener()
    treeWalker = antlr4.ParseTreeWalker()
    treeWalker.walk(countListener, tree)

    return countListener.count


def tree_to_program(tree: antlr4.ParserRuleContext) -> str:
    if tree is None:
        return ""

    convertToProgramListener = ConvertToProgramListener()
    treeWalker = antlr4.ParseTreeWalker()
    treeWalker.walk(convertToProgramListener, tree)

    return " ".join(convertToProgramListener.tokens)
