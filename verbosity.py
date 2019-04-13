import sys
import os

class VerbosityMeta(type):
    '''
    Metaclass for Verbosity, disallowing manual modification of variables
    '''

    ## Marks that operations on variables inside Verbosity class are allowed
    ## or disallowed(disallowed by default)
    _is_internal_op = False

    def __setattr__(self, name, value):
        '''
        Sets an attribute of class `self` named `name` with value `value`
        if allowed.

        If not allowed, raises `ValueError`.
        '''
        if self._is_internal_op is False:
            raise ValueError('Can\'t manually modify Verbosity state')
        else:
            super(type(self), self).__setattr__(name, value)

def _safe_verbosity_modify(func):
    '''
    Wrapper decorator that allows our function to be called in such a way
    that the function can safely modify state of Verbosity class' variables.
    '''
    def wrapper(*args, **kwargs):
        VerbosityMeta._is_internal_op = True
        func(*args, **kwargs)
        VerbosityMeta._is_internal_op = False
    return wrapper

class Verbosity(object, metaclass=VerbosityMeta):
    '''
    Class representing verbosity.

    This class allows to set verbosity to certain level, create new verbosity
    levels as well as decorating functions to print messages or call functions
    at different points for functions.

    Variables inside this class(not instance variables though) can not be
    modified outside of this class.
    '''

    ## Default verbosity levels.
    NONE = 0
    INFO = 1
    DEBUG = 2
    TOTAL = 3

    ## Internal mappings for verbosity levels.
    _verbosities = [NONE, INFO, DEBUG, TOTAL]
    _verbositiesmap = { 'NONE': NONE, 'INFO': INFO, 'DEBUG': DEBUG, 'TOTAL': TOTAL,
                        NONE: 'NONE', INFO: 'INFO', DEBUG: 'DEBUG', TOTAL: 'TOTAL', }

    ## Verbosity level.
    ## To modify this value safely please use `set` static method instead
    ## of just writing to this variable.
    level = NONE

    ## Dummy class and variable
    class _Internal_Dummy(object):
        '''
        Dummy class for `Verbosity.PARAMETERS`
        '''
    
    PARAMETERS = _Internal_Dummy()

    @classmethod
    def get_verbosities(cls):
        '''
        Returns a dictionary with a mapping of all values to string representations
        as well as all string mappings to integers of all available recognized
        verbosities.
        '''
        return dict(cls._verbositiesmap)

    @classmethod
    @_safe_verbosity_modify
    def set(cls, new_verbosity, verify=True):
        '''
        Sets the verbosity level to new_verbosity.

        `new_verbosity` can be either a string or an integer. The integer has
        to be equal to one of the verbosity values. The string has to be equal
        to one of the registered verbosities.

        If `verify` is set to `False`(`True` by default), the value that is set
        is not going to be verified, otherwise the set will only succeed if
        the value of `new_verbosity` is recognized.

        Returns the old verbosity level.
        '''
        _vb = None
        if isinstance(new_verbosity, str):
            _vb = cls._verbositiesmap.get(new_verbosity, None)
            if verify is True and _vb is None:
                return
            _v = cls.level
            cls.level = _vb
            return _v
        elif isinstance(new_verbosity, int):
            _vb = new_verbosity
            if verify is True and Verbosity._verbosities.count(_vb) == 0:
                return
            _v = cls.level
            cls.level = _vb
            return _v
        raise TypeError('new_verbosity has to be int or str')

    @classmethod
    @_safe_verbosity_modify
    def add(cls, verbosity_name, verbosity_level):
        '''
        Adds new verbosity to the Verbosity class.
        
        The new verbosity will thereafter be available as an attribute
        of class Verbosity.

        Add doesn't modify the state of verbosities if a verbosity with either
        the same name or the same value already exists.

        `verbosity_name` must be a string and `verbosity_level` must be an integer.

        `verbosity_level` equal to -1 cannot be registered.
        '''
        if isinstance(verbosity_name, str) is False or isinstance(verbosity_level, int) is False:
            raise TypeError('verbosity_name has to be str(is {}), verbosity_level has to be int(is {})'\
                                .format(type(verbosity_name), type(verbosity_level)))

        if cls._verbositiesmap.get(verbosity_name, None) is not None:
            return
        if cls._verbositiesmap.get(verbosity_level, None) is not None:
            return
        
        if verbosity_level == -1:
            return

        setattr(cls, verbosity_name, verbosity_level)
        cls._verbosities.append(verbosity_level)
        cls._verbositiesmap.update({ verbosity_name: verbosity_level,
                                            verbosity_level: verbosity_name })
    
    @classmethod
    @_safe_verbosity_modify
    def _del_key(cls, table_key_int, table_key_str):
        '''
        Tries to remove values from internal list and dictionary.
        Cannot raise an exception.

        FOR INTERNAL USE ONLY.
        '''
        try:
            cls._verbosities.remove(table_key_int)
        except:
            pass
        try:
            cls._verbositiesmap.pop(table_key_int)
        except:
            pass
        try:
            cls._verbositiesmap.pop(table_key_str)
        except:
            pass

    @classmethod
    @_safe_verbosity_modify
    def remove(cls, verbosity):
        '''
        Removes given verbosity from being recognized.

        `verbosity` can be either a string, in which case it is the name of
        the verbosity(the attribute name), or it can be an integer,
        in which case it is its numeric representation.
        '''
        if isinstance(verbosity, str):
            try:
                delattr(cls, verbosity)
                val = cls._verbositiesmap[verbosity]
                Verbosity._del_key(val, verbosity)
            except AttributeError:
                pass
            except:
                raise
        elif isinstance(verbosity, int):
            try:
                delattr(cls, cls._verbositiesmap[verbosity])
                cls._del_key(verbosity, cls._verbositiesmap[verbosity])
            except (AttributeError, KeyError):
                pass
            except:
                raise
    
    @staticmethod
    def _handle_msg(msg, *args, e=None, out=sys.stdout,
                    end='\n', flush=True, **kwargs):
        '''
        Calls `msg` with `*args` if its callable object, otherwise
        prints `msg` formatted with `*args`.

        If `msg` is neither of those, and is not None, raises TypeError.

        FOR INTERNAL USE ONLY.
        '''
        if callable(msg):
            if e is not None:
                msg(e)
            else:
                msg()
        elif isinstance(msg, str):
            out.write(msg.format(*args))
            if len(msg) > 0:
                out.write(end)
            if flush is True:
                out.flush()
        elif isinstance(msg, tuple):
            is_args = msg[0] == Verbosity.PARAMETERS
            if e is not None:
                if is_args:
                    return msg[1](e, *args, **kwargs)
                return msg[0](e, *msg[1:])
            else:
                if is_args:
                    return msg[1](*args, **kwargs)
                return msg[0](*msg[1:])
        elif msg is None:
            pass
        else:
            raise TypeError('msg has to be callable, str or tuple(actual type: {})'.format(type(msg)))
    
    @classmethod
    def printer(cls, verb, msg_before="", msg_after="", msg_except=None,
                rethrow=None, bubble=True, out=sys.stdout,
                out_end='\n', flush=True):
        '''
        A decorator for a function that allows showing given messages, if
        verbosity is set to `verb`.

        `msg_*` parameters can be either functions, strings or tuples.
        
        - In case of functions, `msg_before` and `msg_after` should take
        no arguments, and `msg_except` should take the exception raised as an argument.
        - In case of tuples, if the first value of the tuple is `Verbosity.PARAMETERS`,
        then the parameters to the decorating function will be passed to the
        function that should be second value inside that tuple.
        - In case of `msg_except`, the first parameter of the function will
        still be the exception, followed by arguments.
        - If the first value of the tuple is not `Verbosity.PARAMETERS`, then
        the first value should be a function and this function will be executed
        with the remaining values of the tuple passed into it as `*args`.

        If `rethrow` is provided, it has to be a boolean value(`True` or `False`)
        or None, otherwise TypeError is raised.
        When `rethrow` is `False`, any exception from executing
        the decorated function will not be re-raised. If `rethrow` is set to
        `True`, it will re-raised after `msg_except` has been handled.
        `rethrow` equal to None has same effect as being `False`.

        Can be chained indefinitely, albeit might cause stack overflow, as they
        are executed recursively.

        If `msg_except` is not provided or is `None` and `rethrow` is not None,
        `rethrow` is automatically set to `True` as the decorator expects
        internal handling of exceptions raised by the decorated function.

        `out` controls where the output will be sent into.
        
        `out_end` is a string to append after the message has been posted to `out`.

        `flush` controls whether to flush the output after posting the message.
        '''
        def outer_wrapper(func):
            @_safe_verbosity_modify
            def wrapper(*args, **kwargs):
                nonlocal rethrow
                is_ = verb == cls.level
                if is_:
                    if isinstance(rethrow, bool) is False and rethrow is not None:
                        raise TypeError('rethrow expected to be None or bool(actual type: {})'
                                                .format(type(rethrow)))
                    if msg_except is None:
                        rethrow = True if rethrow is not None else False

                    cls._handle_msg(msg_before, out=out, out_end=out_end,
                                        flush=flush, *args, **kwargs)
                    try:
                        _v = cls.level
                        if bubble is False:
                            cls.level = -1
                        func(*args, **kwargs)
                        cls.level = _v
                    except Exception as e:
                        cls._handle_msg(msg_except, e=e, out=out, out_end=out_end,
                                        flush=flush, *args, **kwargs)
                        if rethrow is True:
                            raise
                    else:
                        cls._handle_msg(msg_after, out=out, out_end=out_end,
                                        flush=flush, *args, **kwargs)
                else:
                    func(*args, **kwargs)
            return wrapper
        return outer_wrapper

if __name__ == "__main__":
    pass