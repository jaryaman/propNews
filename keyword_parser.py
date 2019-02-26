def parse_keywords(x):
    """Parses a logic statement and outputs its DNF form (ORs of ANDs).
    
    The string must respect nested bracketting, using '(',')', use OR and AND to delimit logic.
    If arguments containing space, enclose the argument in double quotes.
    
    >>> keys = 'poverty AND (global OR "international challenge" OR (africa AND (subafrica OR subaf)) OR india OR (lower AND (middle OR mid OR (m AND M)) AND income))'
    [['poverty', 'global'],
     ['poverty', 'international challenge'],
     ['poverty', 'africa', 'subafrica'],
     ['poverty', 'africa', 'subaf'],
     ['poverty', 'india'],
     ['poverty', 'lower', 'middle', 'income'],
     ['poverty', 'lower', 'mid', 'income'],
     ['poverty', 'lower', 'm', 'M', 'income']]
     
    Returns a list of lists in DNF form.
    """
    import pyparsing
    from itertools import product, chain
    content = pyparsing.Word(pyparsing.alphanums)
    parser = pyparsing.nestedExpr( '(', ')', content=content)
    x = '('+x+')'
    token_list = parser.parseString(x).asList()
    while len(token_list)==1: token_list = token_list[0]
    def unroll(y):
        if isinstance(y, str): return [y.strip('"')]
        else:
            if 'AND' in y and 'OR' in y: raise RuntimeError('check bracketting--cannot have both AND and OR in same clause: %s' %str(y))
            if 'OR' in y:
                y = list(filter(lambda a: a!='OR', y))
                return list(chain.from_iterable([unroll(a) for a in y]))
            else:
                y = list(filter(lambda a: a!='AND', y))
                return list(product(*[unroll(a) for a in y]))
    def flatten(y):
        if isinstance(y, str): return [y]
        else:
            out = list()
            for a in y: out += flatten(a)
        return out
    token_list = [flatten(x) for x in unroll(token_list)]
    return token_list
