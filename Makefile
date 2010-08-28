
all: lisp.a lisp.py
	./lisp.a test.lisp > result_c.txt
	diff result_c.txt result.lisp
	python lisp.py test.lisp > result_py.txt
	diff result_py.txt result.lisp
	ruby lisp.rb test.lisp > result_rb.txt
	diff result_rb.txt result.lisp

lisp.a: lisp.c
	cc -Wall $< -o $@

lisp.c:
	wget 'http://nakkaya.com/code/misc/lisp.c'

clean:
	rm *~
