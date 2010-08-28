#!/usr/bin/env python

import sys

class Atom(object):
    def __init__(self, name):
        self.name = name
    def __str__(self):
        return self.name
#    def __eq__(self,other):
#        return isinstance(other,Atom) and self.name==other.name
class Cons(object):
    def __init__(self, car, cdr):
        self.car = car
        self.cdr = cdr # cdr must be None or Cons
    def append(self, obj):
        li = self
        while li.cdr:
            li = li.cdr
        assert(not li.cdr)
        li.cdr = Cons(obj, None)
    def to_list(self):
        l = []
        li = self
        while li:
            l.append(li.car)
            li = li.cdr
        return l
    def __str__(self):
        if not self.car and not self.cdr:
            return '()'
        return '(%s)'%' '.join([str(e) for e in self.to_list()])
class Func(object):
    def __init__(self, func):
        self.func = func
    def __str__(self):
        return '%func'
class Lambda(object):
    def __init__(self, args, exp):
        self.args = args
        self.exp = exp
    def __str__(self):
        return '#%s %s'%(self.args, self.exp)

# primitives
tee = Atom('#T')
nil = Cons(None,None)

def fn_car(args, env):
    return args.car.car
def fn_cdr(args, env):
    return args.car.cdr
def fn_quote(args, env):
    return args.car
def fn_cons(args, env):
    l = Cons(args.car, None)
    args = args.cdr.car
    for i in args.to_list():
        l.append(i) 
    return l
def fn_equal(args, env):
    first = args.car
    second = args.cdr.car
    if first.name==second.name:
        return tee
    else:
        return nil
def fn_atom(args, env):
    if isinstance(args.car,Atom):
        return tee
    else:
        return nil
def fn_cond(args, env):
    for i in args.to_list():
        pred = eval(i.car, env)
        ret = i.cdr.car
        
        if pred != nil:
            return eval(ret,env)
    return nil

def interleave(c1, c2):
    l = Cons(Cons(c1.car, Cons(c2.car, None)), None)
    c1 = c1.cdr
    c2 = c2.cdr
    
    for i in c1.to_list():
        l.append( Cons(c1.car, Cons(c2.car,None)) )
        c2 = c2.cdr
    return l

def to_cons(li):
    l = Cons(li[0],None)
    for i in li[1:]:
        l.append(i)
    return l
def replace_atom(exp, to):
    if isinstance(exp, Cons):
        return to_cons([replace_atom(i,to) for i in exp.to_list()])
    else:
        assert isinstance(exp, Atom)
        for item in to.to_list():
            atom = item.car
            replacement = item.cdr.car
            
            if atom.name==exp.name:
                return replacement
        return exp

def fn_lambda(args, env):
    lamb = args.car
    args = args.cdr
    assert isinstance(lamb,Lambda)
    li = interleave(lamb.args,args)
    exp = replace_atom(lamb.exp,li)
    return eval(exp,env)

def fn_label(args, env):
    env.append(Cons(Atom(args.car.name), Cons(args.cdr.car, None)))
    return tee

def lookup(name, env):
    for item in env.to_list():
        nm = item.car
        val = item.cdr.car
        if nm.name == name:
            return val

def init_env():
    def entry(name, fn):
        return Cons(Atom(name),Cons(Func(fn),None))
    env = Cons(entry('QUOTE',fn_quote),None)
    env.append(entry('CAR',fn_car))
    env.append(entry('CDR',fn_cdr))
    env.append(entry('CONS',fn_cons))
    env.append(entry('EQUAL',fn_equal))
    env.append(entry('ATOM',fn_atom))
    env.append(entry('COND',fn_cond))
    env.append(entry('LAMBDA',fn_lambda))
    env.append(entry('LABEL',fn_label))

    return env

def eval_fn(exp, env):
    symbol = exp.car
    args = exp.cdr
    
    if isinstance(symbol, Lambda):
        return fn_lambda(exp,env)
    elif isinstance(symbol, Func):
        return symbol.func(args,env)
    else:
        return exp

def eval(exp, env):
    #print 'eval: %s'%exp
    if isinstance(exp, Cons):
        if isinstance(exp.car, Atom) and exp.car.name=='LAMBDA':
            largs = exp.cdr.car
            lexp = exp.cdr.cdr.car
            return Lambda(largs,lexp)
        else:
            return eval_fn(to_cons([eval(e,env) for e in exp.to_list()]), env)
    else:
        assert isinstance(exp, Atom)
        val = lookup(exp.name, env)
        if val:
            return val
        return exp

def next_token(input):
    ch = input.getc()
    while ch and ch.isspace():
        ch = input.getc()
        
    if ch=='\n':
        ch = input.getc()
    if not ch:
        exit(0)
    
    if ch==')':
        return Atom(')')
    if ch=='(':
        return Atom('(')
    
    buffer = ''
    index = 0
    while not ch.isspace() and ch!=')':
        buffer += str(ch)
        ch = input.getc()
        
    if ch==')':
        input.ungetc(ch)

    return Atom(buffer)

def read_tail(input):
    token = next_token(input)
    
    if token.name==')':
        return None
    elif token.name=='(':
        first = read_tail(input)
        second = read_tail(input)
        return Cons(first,second)
    else:
        first = token
        second = read_tail(input)
        return Cons(first,second)

def read(f):
    token = next_token(f)
    if token.name=='(':
        return read_tail(f)
    return token

class FileBuffer:
    def __init__(self,fileobj):
        self.f = fileobj
        self.buffer = []
    def eof(self):
        if self.buffer:
            return False
        c = self.getc()
        if not c:
            return True
        self.ungetc(c)
        return False

    def getc(self):
        if self.buffer:
            self.buffer,r = self.buffer[:-1], self.buffer[-1]
            return r
        c = self.f.read(1)
        if c=='': return None
        return c

    def ungetc(self,char):
        self.buffer.append(char)

if __name__=='__main__':
    env = init_env()
    
    if len(sys.argv)>1:
        f = FileBuffer(open(sys.argv[1],'r'))
    else:
        f = FileBuffer(sys.stdin)

    while not f.eof():
        sys.stdout.write('> ')
        sys.stdout.flush()
        r = read(f)
        e = eval(r, env)
        print e

