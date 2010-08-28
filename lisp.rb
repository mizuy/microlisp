#!/usr/bin/env ruby
class Atom
  attr_reader :name
  def initialize(name)
    @name = name
  end
  def to_s()
    @name
  end
end

#monkey patch
class Cons
  include Enumerable
  attr_accessor :car
  attr_accessor :cdr
  def initialize(car, cdr)
    @car = car
    @cdr = cdr
  end
  def append(obj)
    li = self
    while li.cdr
      li = li.cdr
    end
    li.cdr = Cons.new(obj, nil)
  end
  def each()
    li = self
    while li
      yield li.car
      li = li.cdr
    end
  end    
  def to_s()
    (not @car and not @cdr) ? '()' : "(#{to_a.join(' ')})"
  end
end

class Func
  attr_reader :func
  def initialize(func)
    @func = func
  end
  def to_s()
    '%func'
  end
end

class Lambda
  attr_reader :args,:exp
  def initialize(args, exp)
    @args = args
    @exp = exp
  end
  def to_s()
    "#{@args} #{@exp}"
  end
end

module Enumerable
  def to_cons()
    raise 'to_cons for empty array' unless length > 0
    l = Cons.new(self[0], nil)
    shift
    each do |i|
      l.append i
    end
    l
  end
end


class Lisp
  def init_env()
    @tee = Atom.new '#T'
    @none = Cons.new nil,nil

    %w(QUOTE CAR CDR CONS EQUAL ATOM COND LAMBDA LABEL).map{|name|
      [Atom.new(name.upcase),Func.new(self.method('fn_'+name.downcase))].to_cons
    }.to_cons
  end

  def fn_car(args, env)
    args.car.car
  end
  def fn_cdr(args, env)
    args.car.cdr
  end
  def fn_quote(args, env)
    args.car
  end
  def fn_cons(args, env)
    l = Cons.new(args.car, nil)
    args = args.cdr.car
    args.each do |i|
      l.append i
    end
    l
  end
  def fn_equal(args, env)
    first = args.car
    second = args.cdr.car
    r = ((first.name==second.name) ? @tee : @none)
    r
  end
  def fn_atom(args, env)
    args.car.is_a?(Atom) ? @tee : @none
  end
  def fn_cond(args, env)
    args.each do |i|
      pred = eval i.car,env
      ret = i.cdr.car
      return eval(ret,env) if pred != @none
    end
    return @none
  end

  def fn_lambda(args, env)
    lambda = args.car
    args = args.cdr
    li = interleave(lambda.args, args)
    exp = replace_atom(lambda.exp, li)
    eval(exp,env)
  end

  def fn_label(args, env)
    env.append [Atom.new(args.car.name), args.cdr.car].to_cons
    @tee
  end

  def interleave(c1, c2)
    c1.to_a.zip(c2.to_a).map {|i| i.to_cons}.to_cons
  end

  def replace_atom(exp, to)
    if exp.is_a? Cons
      exp.map {|i| replace_atom i,to}.to_cons
    else
      to.each {|i|
        atom = i.car
        replacement = i.cdr.car
        return replacement if atom.name == exp.name
      }
      exp
    end
  end

  def lookup(name, env)
    env.each do |i|
      nm = i.car
      val = i.cdr.car
      return val if nm.name == name
    end
    nil
  end

  def eval_fn(exp, env)
    symbol = exp.car
    args = exp.cdr
    if symbol.is_a? Lambda
      fn_lambda(exp,env)
    elsif symbol.is_a? Func
      symbol.func.call(args,env)
    else
      exp
    end
  end

  def eval(exp, env)
    if exp.is_a? Cons
      if exp.car.is_a?(Atom) and exp.car.name=='LAMBDA'
        largs = exp.cdr.car
        lexp = exp.cdr.cdr.car
        Lambda.new largs,lexp
      else
        eval_fn(exp.map {|e| eval(e,env)}.to_cons, env)
      end
    else
      lookup(exp.name, env) || exp
    end
  end

  def next_token(input)
    ch = input.getc
    while ch and ch.chr =~ /\s/
      ch = input.getc
    end
    
    exit(0) if not ch
    ch = input.getc if ch.chr=='\n'
    return Atom.new(')') if ch.chr==')'
    return Atom.new('(') if ch.chr=='('
    
    name = ""
    while not ch.chr=~/\s/ and ch.chr!=')'
      name += ch.chr
      ch = input.getc
    end
    
    input.ungetc ch if ch.chr==')'
    
    Atom.new(name)
  end

  def read_tail(input)
    token = next_token(input)
    
    if token.name==')'
      nil
    elsif token.name=='('
      first = read_tail(input)
      second = read_tail(input)
      Cons.new(first, second)
    else
      first = token
      second = read_tail(input)
      Cons.new(first, second)
    end
  end

  def read(f)
    token = next_token(f)
    token.name=='(' ? read_tail(f) : token
  end

  def main()
    env = init_env()
    if ARGV.length > 0
      $stdout.flush
      f = File.open ARGV[0]
    else
      f = $stdin
    end
    
    while 1
      print '> '
      $stdout.flush
      r = read(f)
      e = eval(r, env)
      puts e
    end
  end

end

Lisp.new.main
