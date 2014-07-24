import dis


def rebuild_code(func_code, mapping):
    co_argcount = func_code.co_argcount
    co_nlocals = func_code.co_nlocals
    co_stacksize = func_code.co_stacksize
    co_flags = func_code.co_flags
    co_code = func_code.co_code
    co_consts = func_code.co_consts
    co_names = func_code.co_names
    co_varnames = func_code.co_varnames
    co_filename = func_code.co_filename
    co_name = func_code.co_name
    co_firstlineno = func_code.co_firstlineno
    co_lnotab = func_code.co_lnotab
    co_freevars = func_code.co_freevars
    co_cellvars = func_code.co_cellvars
    code = (ord(b) for b in co_code)
    codestring = []
    names = list(co_names)
    names_consts = {}
    consts = list(co_consts)
    while True:
        #fetch next opcode. stop if we already at the end
        try:
            opcode, arg = code.next(), None
        except StopIteration:
            break

        #skip functions with unknown opcodes
        if opcode == dis.EXTENDED_ARG:
            return f
        #fetch argument
        elif opcode >= dis.HAVE_ARGUMENT:
            arg = [code.next() for _ in xrange(2)]

        if opcode == dis.opmap['LOAD_GLOBAL']:
            name_pos = arg[0] + arg[1]*256
            name = names[name_pos]
            if name in mapping:
                #if we not created const for name yet
                if name not in names_consts:
                    consts.append(mapping[name])
                    names_consts[name] = len(consts) - 1
                #change opcode and arg to const
                opcode = dis.opmap['LOAD_CONST']
                arg = reversed(divmod(names_consts[name], 256))

        #append opcode, with args if any, to new codestring
        codestring.append(opcode)
        if arg is not None:
            codestring.extend(arg)
    #map(names.remove, names_consts.keys()) - names can be used somewhere else in the code
    codestring = ''.join(chr(b) for b in codestring)
    new_code = type(func_code)(co_argcount, co_nlocals, co_stacksize,
        co_flags, codestring, tuple(consts), co_names, co_varnames, co_filename,
        co_name, co_firstlineno, co_lnotab, co_freevars, co_cellvars)

    return new_code


def constantize(*dargs, **dkwargs):
    dkwargs.update({k.__name__:k for k in dargs})
    def constantize_decorator(f):
        func_closure = f.func_closure
        func_defaults = f.func_defaults
        func_doc = f.func_doc
        func_name = f.func_name
        func_code = f.func_code
        func_dict = f.func_dict
        func_globals = f.func_globals
        return type(f)(rebuild_code(func_code, dkwargs), func_globals,
            func_name, func_defaults, func_closure)
    return constantize_decorator


if __name__ == '__main__':
    def test(b):
        res = []
        for c in b:
            if isinstance(c, (tuple, list)):
                res.append(len(c))

    @constantize(*(len, isinstance, list, tuple))
    def ctest(b):
        res = []
        for c in b:
            if isinstance(c, (tuple, list)):
                res.append(len(c))

    import timeit
    import os
    dis.dis(test)
    dis.dis(ctest)

    assert test != ctest
    test([[]])
    ctest([[]])
    setup = os.linesep.join((
        'from __main__ import test, ctest',
        'param = sum(([(),None,[]] for _ in xrange(100)), [])'))
    avg = lambda x: sum(x)/len(x)
    run = lambda x: timeit.timeit(x, setup, number=10000)
    original = avg(sorted(run('test(param)') for x in xrange(10))[1:-1])
    patched = avg(sorted(run('ctest(param)') for x in xrange(10))[1:-1])
    print '%s/%s=%s' % (patched, original, patched/original)
