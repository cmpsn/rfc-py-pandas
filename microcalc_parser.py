import pyparsing as pp


def parse_field(src: str, suplimentary_chars: str):
    """
    Parse the string with input formula and returns
    a nested list of lists with terms and operations.
    """
    pp.ParserElement.enable_packrat()

    base_expr = pp.Word(pp.alphanums, pp.alphanums + suplimentary_chars)

    muldiv = pp.oneOf("* /")
    plusminus = pp.oneOf("+ -")

    expr = pp.infix_notation(
        base_expr,
        [
            (muldiv, 2, pp.opAssoc.LEFT),
            (plusminus, 2, pp.opAssoc.LEFT),
        ],
    )

    result = expr.parse_string(src, True).as_list()
    # Pyparsing returns a list wraped in a list, so len of result is 1
    # must be unwrapped in the caller
    return result
