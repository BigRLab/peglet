"""
Parsing with PEGs, or a minimal usable subset thereof.
"""

import collections, re

def Parser(grammar, **actions):
    r"""Make a parsing function from a PEG grammar. You supply the
    grammar as a string of productions like "a = b c | d", like the
    example grammar below. All the tokens making up the productions
    must be whitespace-separated. Each token, besides the '=' and '|'
    is a regex, a rule name, or an action name. (Possibly preceded by
    '!' for negation: !foo successfully parses when foo *fails* to
    parse.)

    Results get added by regex captures and transformed by actions
    (which are named like ':hug' below; to say what 'hug' means
    here, make it a keyword argument).

    A regex token in the grammar either starts with '/' or is a
    non-identifier token. An identifier that's not a defined rule name
    is an error. (So, when you write an incomplete grammar, you get a
    BadGrammar exception instead of an incorrect parse.)

    The parsing function maps a string a results tuple or raises
    Unparsable. (It can optionally take a rule name to start from, by
    default the first in the grammar.) It doesn't necessarily match
    the whole input, just a prefix.

    >>> parse_s_expression = Parser(r'''
    ... one_expr = _ expr !.
    ... _        = \s*
    ... expr     = \( _ exprs \) _  hug
    ...          | ([^()\s]+) _
    ... exprs    = expr exprs
    ...          | ''',             hug = lambda *vals: vals)
    >>> parse_s_expression('  (hi (john mccarthy) (()))')
    (('hi', ('john', 'mccarthy'), ((),)),)
    >>> parse_s_expression('(too) (many) (exprs)')
    Traceback (most recent call last):
    Unparsable: ('one_expr', '(too) ', '(many) (exprs)')
    """
    rules = extend(parse_grammar(grammar), **actions)
    return lambda text: parse(rules, text)

def parse_grammar(grammar):
    parts = re.split(r'\s('+_identifier+')\s+=\s', ' '+grammar)
    if not parts: raise BadGrammar("No grammar")
    if parts[0].strip(): raise BadGrammar("Missing left hand side", parts[0])
    if len(set(parts[1::2])) != len(parts[1::2]):
        raise BadGrammar("Multiply-defined rule(s)", grammar)
    rules = dict((lhs, [alt.split() for alt in re.split(r'\s[|](?:\s|$)', rhs)])
                 for lhs, rhs in zip(parts[1::2], parts[2::2]))
    rules['_start'] = [[parts[1]]]
    return rules

def extend(dic, **kwargs):
    result = dict(kwargs)
    result.update(dic)
    return result

_identifier = r'[A-Za-z_]\w*'

# A parsing state: a position in the input text and a values tuple.
State = collections.namedtuple('State', 'pos vals'.split())

def parse(peg, text):
    utmost = [0]
    st = parsing(peg, {}, text, {}, utmost, State(0, ()))
    if st: return st.vals
    else: raise Unparsable(peg['_start'][0][0] if isinstance(peg, dict) else peg,
                           text[:utmost[0]], text[utmost[0]:])

# Each parsing function starts from a pos in text and returns
# either None (failure) or an updated state. We also track utmost:
# a mutable box holding the rightmost position positively reached.

def parsing(peg, rules, text, memos, utmost, st):
    assert isinstance(rules, dict)
    assert isinstance(text, str)
    assert isinstance(memos, dict)
    assert isinstance(utmost, list)
    assert isinstance(st, State)
    if isinstance(peg, dict):
        peg = ('_start', peg)
    if isinstance(peg, tuple):
        name, rules = peg
        assert isinstance(name, str)
        assert isinstance(rules, dict)
        st2 = parse_rule(name, rules, text, memos, utmost, st.pos)
        return st2 and State(st2.pos, st.vals + st2.vals)
    elif isinstance(peg, str):
        if peg.startswith('!'):
            return None if parsing(peg[1:], rules, text, memos, [0], st) else st
        elif peg in rules:
            return parsing(rules[peg] if callable(rules[peg]) else (peg, rules),
                           rules, text, memos, utmost, st)
        else:
            return match(peg, rules, text, memos, utmost, st)
    elif callable(peg):
        return (peg(text, utmost, st) if hasattr(peg, 'is_peg')
                else State(st.pos, (peg(*st.vals),)))
    else:
        assert False, ("Bad peg", peg)

def parse_rule(name, rules, text, memos, utmost, pos):
    try: return memos[name, pos]
    except KeyError:
        result = memos[name, pos] = really_parse_rule(name, rules, text, memos, utmost, pos)
        return result

def really_parse_rule(name, rules, text, memos, utmost, pos):
    assert isinstance(name, str)
    assert isinstance(rules, dict)
    for alternative in rules[name]:
        st = parse_sequence(alternative, rules, text, memos, utmost, pos)
        if st: return st
    return None

def parse_sequence(tokens, rules, text, memos, utmost, pos):
    st = State(pos, ())
    for token in tokens:
        st = parsing(token, rules, text, memos, utmost, st)
        if not st: break
    return st

def match(token, rules, text, memos, utmost, st):
    if re.match(_identifier+'$', token):
        raise BadGrammar("Missing rule: %s" % token)
    if re.match(r'/.', token): token = token[1:]
    m = re.match(token, text[st.pos:])
    if not m: return None
    utmost[0] = max(utmost[0], st.pos + m.end())
    return State(st.pos + m.end(), st.vals + m.groups())

class Unparsable(Exception): pass
class BadGrammar(Exception): pass

def maybe(parse, *args, **kwargs): # XXX rename to 'attempt'?
    try: return parse(*args, **kwargs)
    except Unparsable: return None

# Some often-used actions:
def hug(*xs): return xs
def join(*strs): return ''.join(strs)

def position(text, utmost, st):
    return State(st.pos, st.vals + (st.pos,))
position.is_peg = True
