
# SimpleWrap - Simple wrapper for C libraries based on ctypes 
# Stefano Pedemonte 
# Aalto University, School of Science, Helsinki 
# Oct. 2013, Helsinki 
# Harvard University, Martinos Center for Biomedical Imaging 
# Dec. 2013, Boston 

__all__ = ['load_c_library','call_c_function','localpath','filepath','int32', 'uint32', 'uint16', 'float32']
from ctypes import *
from numpy import *
import os, sys, inspect
from exceptions import *
import platform 
import copy

if platform.system()=='Linux':
    extensions = ['so','SO']
elif platform.system()=='Darwin':
    extensions = ['dylib','DYLIB']
elif platform.system()=='Windows':
    extensions = ['dll','DLL']
else: 
    extensions = ['so','SO','dylib','DYLIB','dll','DLL'] 


def load_c_library(lib_name,library_path): 
    """Load the dynamic library with the given name (with path). """
    library_found = False 
    for extension in extensions:
        for prefix in ['','lib','lib_']:
            filename = library_path+os.path.sep+prefix+lib_name+"."+extension
            if os.path.exists(filename): 
                library_found = True
                break
        if library_found: 
            break 
    if not library_found: 
        raise InstallationError("The library %s could not be found in %s. Please specify the correct location of add location to the system path."%(lib_name,library_path)) 
    else: 
        try:
            L = CDLL(filename)
        except OSError: 
            raise InstallationError("The library %s was found but could not be loaded. It is likely due to a linking error, missing libraries. "%lib_name) 
        else: 
            return L



def call_c_function(c_function, descriptor): 
    """Call a C function in a dynamic library. The descriptor is a dictionary 
    that contains that parameters and describes how to use them. """
    # set the return type
    c_function.restype = c_int 
    # parse the descriptor, determine the types and instantiate variables if their value is not given 
    argtypes_c = [] 
    args_c = []
    args = [] 
    for d in descriptor:
        if d['name'] == 'status': 
            DescriptorError("variable name 'status' is reserved. ") 
        argtype = d['type']
        arg = d['value']
        if argtype == 'string': 
            if arg == None: 
                if not d.has_key('size'): 
                    raise DescriptorError("'string' with 'value'='None' must have 'size' property. ") 
                arg = ' '*size
            arg_c = c_char_p(arg)
        elif argtype == 'int': 
            if arg == None: 
                arg = 0
            arg = c_int32(arg)
            arg_c = pointer(arg)
        elif argtype == 'uint': 
            if arg == None: 
                arg = 0
            arg = c_uint32(arg)
            arg_c = pointer(arg)			
        elif argtype == 'long': 
            if arg == None: 
                arg = 0
            arg = c_longlong(arg)
            arg_c = pointer(arg)
        elif argtype == 'float': 
            if arg == None: 
                arg = 0.0
            arg = c_float(arg)
            arg_c = pointer(arg)
        elif argtype == 'array':
            if arg == None: 
                if not d.has_key('size'): 
                    raise DescriptorError("'array' with 'value'='None' must have 'size' property. ") 
                if not d.has_key('dtype'): 
                    raise DescriptorError("'array' with 'value'='None' must have 'dtype' property. ") 
                arg = zeros(d['size'],dtype=d['dtype']) 
            arg_c = arg.ctypes.data_as(POINTER(c_void_p)) 
        else: 
            raise UnknownType("Type %s is not supported. "%str(argtype)) 
        argtype_c = type(arg_c) 
        argtypes_c.append(argtype_c) 
        args_c.append(arg_c) 
        args.append(arg) 
    # set the arguments types 
    c_function.argtypes = argtypes_c
    # call the function 
    status = c_function(*args_c) 
    # cast back to Python types 
    for i in range(len(descriptor)): 
        argtype = descriptor[i]['type']
        if argtype in ['int','uint','float','long']: 
            args[i] = args[i].value
        # swap axes of array if requested
        if descriptor[i]['type'] == 'array': 
            if descriptor[i].has_key('swapaxes'): 
                # 1) reshape
                shape = args[i].shape 
                shape2 = list(shape)
                shape = copy.copy(shape2)
                shape[descriptor[i]['swapaxes'][0]] = shape2[descriptor[i]['swapaxes'][1]]
                shape[descriptor[i]['swapaxes'][1]] = shape2[descriptor[i]['swapaxes'][0]]
                args[i] = args[i].reshape(shape)
                # 2) swap axes
                args[i] = args[i].swapaxes(descriptor[i]['swapaxes'][0],descriptor[i]['swapaxes'][1]) 
    # Assemble wrapper object
    class CallResult(): 
        pass 
    result = CallResult()
    dictionary = {}  
    for index in range(len(descriptor)): 
        name = descriptor[index]['name']
        arg = args[index]
        setattr(result,name,arg) 
        dictionary[name] = arg
    setattr(result,'status',status) 
    setattr(result,'values',args) 
    setattr(result,'dictionary',dictionary) 
    return result 



def localpath(): 
    return os.path.dirname(os.path.realpath(inspect.getfile(sys._getframe(1))))

def filepath(fullfilename): 
    return os.path.dirname(os.path.realpath(fullfilename)) 
    

