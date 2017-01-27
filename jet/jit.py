from compressor import JetBuilder
from utils import sanitize_name, get_caller_info
from intake import placeholder
import jet


_func_cached_dict = {}

def jit(*shapes):
    def decorator(func):
        _func_cached_dict[id(func)] = {'func': None, 'shapes': shapes}

        def wrapper(*args):
            if not jet.jet_mode:
                return func(*args)

            func_id = id(func)
            func_cached = _func_cached_dict[func_id]['func']
            if func_cached is not None:
                return func_cached(*args)

            shapes = _func_cached_dict[func_id]['shapes']

            arg_names = func.__code__.co_varnames[0:func.__code__.co_argcount]

            if len(shapes) != len(arg_names) and shapes:
                raise ValueError('Shapes length does not match the arguments length.')

            if not shapes:
                shapes = [arg.shape if hasattr(arg, 'shape') else () for arg in args]
                _func_cached_dict[func_id]['shapes'] = shapes

            ph = map(lambda (idx, name): jet.placeholder(
                        name=name, shape=shapes[idx]), enumerate(arg_names))
            fun_name = func.__code__.co_name
            jb = JetBuilder(out=[func(*ph)],
                    file_name=sanitize_name('{}_{}_{func_name}'.format(
                            *get_caller_info('jit.py')[1:-1],
                            func_name=fun_name)),
                    fun_name=fun_name)
            
            jet_class = getattr(jb.build(), jb.class_name)
            jet_func = getattr(jet_class(), jb.fun_name)
            _func_cached_dict[func_id]['func'] = jet_func

            return jet_func(*args)
        return wrapper

    if shapes and callable(shapes[0]):
        func = shapes[0]
        shapes = ()
        return decorator(func)
    return decorator

if __name__ == "__main__":
    import numpy
    
    jet.set_options(jet_mode=True)

    @jit((2,), ())
    def test_func(a, b):
        return a + b

    @jit()
    def test_func2(a, b):
        return a - b

    @jit
    def test_func3(a, b):
        return a * b

    a = jet.array((2,))
    b = 1.0
    print test_func(numpy.array([1, 2]), b)
    print test_func(numpy.array([1, 4]), b)
    print test_func2(numpy.array([1, 2]), b)
    print test_func3(numpy.array([1, 2]), b)

    print _func_cached_dict
