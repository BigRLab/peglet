from peglet import *

## Parser('x = ')('')
#. ()

def p(grammar, text, **kwargs):
    parse = Parser(grammar, **globals())
    try: 
        return parse(text, **kwargs)
    except Unparsable, e:
        return e

metagrammar = r"""
grammar       =  _ rules
rules         =  rule rules               
              |  rule
rule          =  name [=] _ expr \. _       make_rule
expr          =  term \| _ expr             alt
              |  term
term          =  factors : _ name           reduce_
              |  factors
factors       =  factor factors             seq
              |                             empty
factor        =  '((?:\\.|[^'])*)' _        literal
              |  name                       rule_ref
name          =  (\w+) _
_             =  \s*
"""

def make_rule(name, expr): return '%s: %s' % (name, expr)
def alt(e1, e2):           return '%s/%s' % (e1, e2)
def reduce_(e, name):      return '%s =>%s' % (e, name)
def seq(e1, *e2):          return '%s+%s' % ((e1,) + e2) if e2 else e1
def empty():               return '<>'
def literal(regex):        return '/%s/' % regex
def rule_ref(name):        return '<%s>' % name

## p(metagrammar, ' hello = bargle. goodbye = hey there.aloha=.')
#. ('hello: <bargle>+<>', 'goodbye: <hey>+<there>+<>', 'aloha: <>')
## p(metagrammar, ' hello arg = bargle.')
#. Unparsable('grammar', ' hello ', 'arg = bargle.')
##### p(metagrammar, "'goodbye' world", rule='term')
####. ('/goodbye/+<world>+<>',)

bal = r"""
allbalanced =  _ bal !.
_           =  \s*
bal         =  \( _ bal \) _ hug bal
            |  (\w+) _
            |
"""
## p(bal, '(x) y')
#. (('x',), 'y')
## p(bal, 'x y')
#. Unparsable('allbalanced', 'x ', 'y')

curl = r"""
one_expr =  _ expr $
_        =  \s*
expr     =  { _ exprs } _ hug
         |  ([^{}\s]+) _
exprs    =  expr exprs
         |
"""
## p(curl, '')
#. Unparsable('one_expr', '', '')
## p(curl, '{}')
#. ((),)
## p(curl, 'hi')
#. ('hi',)
## p(curl, '{hi {there} {{}}}')
#. (('hi', ('there',), ((),)),)

multiline_rules = r"""
hi =  /this /is
      /a /rule
   |  /or /this
"""

## p(multiline_rules, "thisisarule")
#. ()
## p(multiline_rules, "orthis")
#. ()
## p(multiline_rules, "thisisnot")
#. Unparsable('hi', 'thisis', 'not')
