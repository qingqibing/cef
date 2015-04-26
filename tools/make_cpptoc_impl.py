# Copyright (c) 2011 The Chromium Embedded Framework Authors. All rights
# reserved. Use of this source code is governed by a BSD-style license that
# can be found in the LICENSE file.

from cef_parser import *

def make_cpptoc_impl_proto(name, func, parts):
    if isinstance(func, obj_function_virtual):
        proto = parts['retval']+' CEF_CALLBACK'
    else:
        proto = 'CEF_EXPORT '+parts['retval']

    proto += ' '+name+'('+string.join(parts['args'], ', ')+')'
    return proto

def make_cpptoc_function_impl_existing(cls, name, func, impl, defined_names):
    notify(name+' has manual edits')

    # retrieve the C API prototype parts
    parts = func.get_capi_parts(defined_names)

    changes = format_translation_changes(impl, parts)
    if len(changes) > 0:
        notify(name+' prototype changed')

    return wrap_code(make_cpptoc_impl_proto(name, func, parts))+'{'+ \
           changes+impl['body']+'\n}\n'
    return result

def make_cpptoc_function_impl_new(cls, name, func, defined_names):
    # retrieve the C API prototype parts
    parts = func.get_capi_parts(defined_names)
    result = make_cpptoc_impl_proto(name, func, parts)+' {'

    invalid = []

    # retrieve the function arguments
    args = func.get_arguments()

    # determine the argument types
    for arg in args:
        if arg.get_arg_type() == 'invalid':
            invalid.append(arg.get_name())

    # retrieve the function return value
    retval = func.get_retval()
    retval_type = retval.get_retval_type()
    if retval_type == 'invalid':
        invalid.append('(return value)')
        retval_default = ''
    else:
        retval_default = retval.get_retval_default(True)
        if len(retval_default) > 0:
            retval_default = ' '+retval_default;

    if len(invalid) > 0:
        notify(name+' could not be autogenerated')
        # code could not be auto-generated
        result += '\n  // BEGIN DELETE BEFORE MODIFYING'
        result += '\n  // AUTO-GENERATED CONTENT'
        result += '\n  // COULD NOT IMPLEMENT DUE TO: '+string.join(invalid, ', ')
        result += '\n  #pragma message("Warning: "__FILE__": '+name+' is not implemented")'
        result += '\n  // END DELETE BEFORE MODIFYING'
        result += '\n}\n\n'
        return wrap_code(result)

    result += '\n  // AUTO-GENERATED CONTENT - DELETE THIS COMMENT BEFORE MODIFYING\n'

    result_len = len(result)

    optional = []

    # parameter verification
    if isinstance(func, obj_function_virtual):
        result += '\n  DCHECK(self);'\
                  '\n  if (!self)'\
                  '\n    return'+retval_default+';'

    for arg in args:
        arg_type = arg.get_arg_type()
        arg_name = arg.get_type().get_name()

        # skip optional params
        optional_params = arg.parent.get_attrib_list('optional_param')
        if not optional_params is None and arg_name in optional_params:
            optional.append(arg_name)
            continue

        comment = '\n  // Verify param: '+arg_name+'; type: '+arg_type

        if arg_type == 'simple_byref' or arg_type == 'simple_byref_const' or \
           arg_type == 'simple_byaddr' or arg_type == 'bool_byref' or arg_type == 'bool_byaddr' or \
           arg_type == 'struct_byref_const' or arg_type == 'struct_byref' or \
           arg_type == 'string_byref_const' or arg_type == 'string_byref' or \
           arg_type == 'refptr_same' or arg_type == 'refptr_same_byref' or \
           arg_type == 'refptr_diff' or arg_type == 'refptr_diff_byref' or \
           arg_type == 'string_vec_byref' or arg_type == 'string_vec_byref_const' or \
           arg_type == 'string_map_single_byref' or arg_type == 'string_map_single_byref_const' or \
           arg_type == 'string_map_multi_byref' or arg_type == 'string_map_multi_byref_const':
            result += comment+\
                      '\n  DCHECK('+arg_name+');'\
                      '\n  if (!'+arg_name+')'\
                      '\n    return'+retval_default+';'
        elif arg_type == 'simple_vec_byref' or arg_type == 'bool_vec_byref' or \
            arg_type == 'refptr_vec_same_byref' or arg_type == 'refptr_vec_diff_byref':
            result += comment+\
                      '\n  DCHECK('+arg_name+'Count && (*'+arg_name+'Count == 0 || '+arg_name+'));'\
                      '\n  if (!'+arg_name+'Count || (*'+arg_name+'Count > 0 && !'+arg_name+'))'\
                      '\n    return'+retval_default+';'
        elif arg_type == 'simple_vec_byref_const' or arg_type == 'bool_vec_byref_const' or \
            arg_type == 'refptr_vec_same_byref_const' or arg_type == 'refptr_vec_diff_byref_const':
            result += comment+\
                      '\n  DCHECK('+arg_name+'Count == 0 || '+arg_name+');'\
                      '\n  if ('+arg_name+'Count > 0 && !'+arg_name+')'\
                      '\n    return'+retval_default+';'

        # check index params
        index_params = arg.parent.get_attrib_list('index_param')
        if not index_params is None and arg_name in index_params:
            result += comment+\
                      '\n  DCHECK_GE('+arg_name+', 0);'\
                      '\n  if ('+arg_name+' < 0)'\
                      '\n    return'+retval_default+';'

    if len(optional) > 0:
        # Wrap the comment at 80 characters.
        str = '\n  // Unverified params: ' + optional[0]
        for name in optional[1:]:
            str += ','
            if len(str) + len(name) + 1 > 80:
                result += str
                str = '\n  //'
            str += ' ' + name
        result += str

    if len(result) != result_len:
        result += '\n'
    result_len = len(result)

    # parameter translation
    params = []

    for arg in args:
        arg_type = arg.get_arg_type()
        arg_name = arg.get_type().get_name()

        comment = '\n  // Translate param: '+arg_name+'; type: '+arg_type

        if arg_type == 'simple_byval' or arg_type == 'simple_byaddr':
            params.append(arg_name)
        elif arg_type == 'simple_byref' or arg_type == 'simple_byref_const':
            data_type = arg.get_type().get_type()
            default = arg.get_type().get_result_simple_default()
            result += comment+\
                      '\n  '+data_type+' '+arg_name+'Val = '+arg_name+'?*'+arg_name+':'+default+';'
            params.append(arg_name+'Val')
        elif arg_type == 'bool_byval':
            params.append(arg_name+'?true:false')
        elif arg_type == 'bool_byref' or arg_type == 'bool_byaddr':
            result += comment+\
                      '\n  bool '+arg_name+'Bool = ('+arg_name+' && *'+arg_name+')?true:false;'
            if arg_type == 'bool_byref':
                params.append(arg_name+'Bool')
            else:
                params.append('&'+arg_name+'Bool')
        elif arg_type == 'struct_byref_const':
            struct_type = arg.get_type().get_type()
            result += comment+\
                      '\n  '+struct_type+' '+arg_name+'Obj;'\
                      '\n  if ('+arg_name+')'\
                      '\n    '+arg_name+'Obj.Set(*'+arg_name+', false);'
            params.append(arg_name+'Obj')
        elif arg_type == 'struct_byref':
            struct_type = arg.get_type().get_type()
            result += comment+\
                      '\n  '+struct_type+' '+arg_name+'Obj;'\
                      '\n  if ('+arg_name+')'\
                      '\n    '+arg_name+'Obj.AttachTo(*'+arg_name+');'
            params.append(arg_name+'Obj')
        elif arg_type == 'string_byref_const':
            params.append('CefString('+arg_name+')')
        elif arg_type == 'string_byref':
            result += comment+\
                      '\n  CefString '+arg_name+'Str('+arg_name+');'
            params.append(arg_name+'Str')
        elif arg_type == 'refptr_same' or arg_type == 'refptr_diff':
            refptr_class = arg.get_type().get_refptr_type()
            if arg_type == 'refptr_same':
                params.append(refptr_class+'CppToC::Unwrap('+arg_name+')')
            else:
                params.append(refptr_class+'CToCpp::Wrap('+arg_name+')')
        elif arg_type == 'refptr_same_byref' or arg_type == 'refptr_diff_byref':
            refptr_class = arg.get_type().get_refptr_type()
            if arg_type == 'refptr_same_byref':
                assign = refptr_class+'CppToC::Unwrap(*'+arg_name+')'
            else:
                assign = refptr_class+'CToCpp::Wrap(*'+arg_name+')'
            result += comment+\
                      '\n  CefRefPtr<'+refptr_class+'> '+arg_name+'Ptr;'\
                      '\n  if ('+arg_name+' && *'+arg_name+')'\
                      '\n    '+arg_name+'Ptr = '+assign+';'\
                      '\n  '+refptr_class+'* '+arg_name+'Orig = '+arg_name+'Ptr.get();'
            params.append(arg_name+'Ptr')
        elif arg_type == 'string_vec_byref' or arg_type == 'string_vec_byref_const':
            result += comment+\
                      '\n  std::vector<CefString> '+arg_name+'List;'\
                      '\n  transfer_string_list_contents('+arg_name+', '+arg_name+'List);'
            params.append(arg_name+'List')
        elif arg_type == 'string_map_single_byref' or arg_type == 'string_map_single_byref_const':
            result += comment+\
                      '\n  std::map<CefString, CefString> '+arg_name+'Map;'\
                      '\n  transfer_string_map_contents('+arg_name+', '+arg_name+'Map);'
            params.append(arg_name+'Map')
        elif arg_type == 'string_map_multi_byref' or arg_type == 'string_map_multi_byref_const':
            result += comment+\
                      '\n  std::multimap<CefString, CefString> '+arg_name+'Multimap;'\
                      '\n  transfer_string_multimap_contents('+arg_name+', '+arg_name+'Multimap);'
            params.append(arg_name+'Multimap')
        elif arg_type == 'simple_vec_byref' or arg_type == 'bool_vec_byref' or \
            arg_type == 'refptr_vec_same_byref' or arg_type == 'refptr_vec_diff_byref':
            vec_type = arg.get_type().get_vector_type()
            if arg_type == 'simple_vec_byref':
                assign = arg_name+'[i]'
            elif arg_type == 'bool_vec_byref':
                assign = arg_name+'[i]?true:false'
            elif arg_type == 'refptr_vec_same_byref':
                refptr_class = arg.get_type().get_refptr_type()
                assign = refptr_class+'CppToC::Unwrap('+arg_name+'[i])'
            elif arg_type == 'refptr_vec_diff_byref':
                refptr_class = arg.get_type().get_refptr_type()
                assign = refptr_class+'CToCpp::Wrap('+arg_name+'[i])'
            result += comment+\
                      '\n  std::vector<'+vec_type+' > '+arg_name+'List;'\
                      '\n  if ('+arg_name+'Count && *'+arg_name+'Count > 0 && '+arg_name+') {'\
                      '\n    for (size_t i = 0; i < *'+arg_name+'Count; ++i) {'\
                      '\n      '+arg_name+'List.push_back('+assign+');'\
                      '\n    }'\
                      '\n  }'
            params.append(arg_name+'List')
        elif arg_type == 'simple_vec_byref_const' or arg_type == 'bool_vec_byref_const' or \
            arg_type == 'refptr_vec_same_byref_const' or arg_type == 'refptr_vec_diff_byref_const':
            vec_type = arg.get_type().get_vector_type()
            if arg_type == 'simple_vec_byref_const':
                assign = arg_name+'[i]'
            elif arg_type == 'bool_vec_byref_const':
                assign = arg_name+'[i]?true:false'
            elif arg_type == 'refptr_vec_same_byref_const':
                refptr_class = arg.get_type().get_refptr_type()
                assign = refptr_class+'CppToC::Unwrap('+arg_name+'[i])'
            elif arg_type == 'refptr_vec_diff_byref_const':
                refptr_class = arg.get_type().get_refptr_type()
                assign = refptr_class+'CToCpp::Wrap('+arg_name+'[i])'
            result += comment+\
                      '\n  std::vector<'+vec_type+' > '+arg_name+'List;'\
                      '\n  if ('+arg_name+'Count > 0) {'\
                      '\n    for (size_t i = 0; i < '+arg_name+'Count; ++i) {'\
                      '\n      '+arg_name+'List.push_back('+assign+');'\
                      '\n    }'\
                      '\n  }'
            params.append(arg_name+'List')

    if len(result) != result_len:
        result += '\n'
    result_len = len(result)

    # execution
    result += '\n  // Execute\n  '

    if retval_type != 'none':
        # has a return value
        if retval_type == 'simple':
            result += retval.get_type().get_result_simple_type()
        else:
            result += retval.get_type().get_type()
        result += ' _retval = '

    if isinstance(func.parent, obj_class):
        # virtual and static class methods
        if isinstance(func, obj_function_virtual):
            if cls.get_name() == func.parent.get_name():
                # virtual method for the current class
                result += func.parent.get_name()+'CppToC::Get(self)->'
            else:
                # virtual method for a parent class
                result += cls.get_name()+'CppToC::Get(reinterpret_cast<'+cls.get_capi_name()+'*>(self))->'
        else:
            result += func.parent.get_name()+'::'
    result += func.get_name()+'('

    if len(params) > 0:
        result += '\n      '+string.join(params,',\n      ')

    result += ');\n'

    result_len = len(result)

    # parameter restoration
    for arg in args:
        arg_type = arg.get_arg_type()
        arg_name = arg.get_type().get_name()

        comment = '\n  // Restore param: '+arg_name+'; type: '+arg_type

        if arg_type == 'simple_byref':
            result += comment+\
                      '\n  if ('+arg_name+')'\
                      '\n    *'+arg_name+' = '+arg_name+'Val;'
        elif arg_type == 'bool_byref' or arg_type == 'bool_byaddr':
            result += comment+\
                      '\n  if ('+arg_name+')'\
                      '\n    *'+arg_name+' = '+arg_name+'Bool?true:false;'
        elif arg_type == 'struct_byref':
            result += comment+\
                      '\n  if ('+arg_name+')'\
                      '\n    '+arg_name+'Obj.DetachTo(*'+arg_name+');'
        elif arg_type == 'refptr_same_byref' or arg_type == 'refptr_diff_byref':
            refptr_class = arg.get_type().get_refptr_type()
            if arg_type == 'refptr_same_byref':
                assign = refptr_class+'CppToC::Wrap('+arg_name+'Ptr)'
            else:
                assign = refptr_class+'CToCpp::Unwrap('+arg_name+'Ptr)'
            result += comment+\
                      '\n  if ('+arg_name+') {'\
                      '\n    if ('+arg_name+'Ptr.get()) {'\
                      '\n      if ('+arg_name+'Ptr.get() != '+arg_name+'Orig) {'\
                      '\n        *'+arg_name+' = '+assign+';'\
                      '\n      }'\
                      '\n    } else {'\
                      '\n      *'+arg_name+' = NULL;'\
                      '\n    }'\
                      '\n  }'
        elif arg_type == 'string_vec_byref':
            result += comment+\
                      '\n  cef_string_list_clear('+arg_name+');'\
                      '\n  transfer_string_list_contents('+arg_name+'List, '+arg_name+');'
        elif arg_type == 'string_map_single_byref':
            result += comment+\
                      '\n  cef_string_map_clear('+arg_name+');'\
                      '\n  transfer_string_map_contents('+arg_name+'Map, '+arg_name+');'
        elif arg_type == 'string_map_multi_byref':
            result += comment+\
                      '\n  cef_string_multimap_clear('+arg_name+');'\
                      '\n  transfer_string_multimap_contents('+arg_name+'Multimap, '+arg_name+');'
        elif arg_type == 'simple_vec_byref' or arg_type == 'bool_vec_byref' or \
            arg_type == 'refptr_vec_same_byref' or arg_type == 'refptr_vec_diff_byref':
            if arg_type == 'simple_vec_byref' or arg_type == 'bool_vec_byref':
                assign = arg_name+'List[i]'
            elif arg_type == 'refptr_vec_same_byref':
                refptr_class = arg.get_type().get_refptr_type()
                assign = refptr_class+'CppToC::Wrap('+arg_name+'List[i])'
            elif arg_type == 'refptr_vec_diff_byref':
                refptr_class = arg.get_type().get_refptr_type()
                assign = refptr_class+'CToCpp::Unwrap('+arg_name+'List[i])'
            result += comment+\
                      '\n  if ('+arg_name+'Count && '+arg_name+') {'\
                      '\n    *'+arg_name+'Count = std::min('+arg_name+'List.size(), *'+arg_name+'Count);'\
                      '\n    if (*'+arg_name+'Count > 0) {'\
                      '\n      for (size_t i = 0; i < *'+arg_name+'Count; ++i) {'\
                      '\n        '+arg_name+'[i] = '+assign+';'\
                      '\n      }'\
                      '\n    }'\
                      '\n  }'

    if len(result) != result_len:
        result += '\n'
    result_len = len(result)

    # special handling for the global cef_shutdown function
    if name == 'cef_shutdown' and isinstance(func.parent, obj_header):
        classes = func.parent.get_classes()

        names = []
        for tmpcls in classes:
            if tmpcls.has_attrib('no_debugct_check'):
                continue;

            if tmpcls.is_library_side():
                names.append(tmpcls.get_name()+'CppToC')
            else:
                names.append(tmpcls.get_name()+'CToCpp')

        if len(names) > 0:
            names = sorted(names)
            result += '\n#ifndef NDEBUG'\
                      '\n  // Check that all wrapper objects have been destroyed'
            for name in names:
                result += '\n  DCHECK(base::AtomicRefCountIsZero(&'+name+'::DebugObjCt));';
            result += '\n#endif  // !NDEBUG'

    if len(result) != result_len:
        result += '\n'
    result_len = len(result)

    # return translation
    if retval_type != 'none':
        # has a return value
        result += '\n  // Return type: '+retval_type
        if retval_type == 'simple' or retval_type == 'bool':
            result += '\n  return _retval;'
        elif retval_type == 'string':
            result += '\n  return _retval.DetachToUserFree();'
        elif retval_type == 'refptr_same':
            refptr_class = retval.get_type().get_refptr_type()
            result += '\n  return '+refptr_class+'CppToC::Wrap(_retval);'
        elif retval_type == 'refptr_diff':
            refptr_class = retval.get_type().get_refptr_type()
            result += '\n  return '+refptr_class+'CToCpp::Unwrap(_retval);'

    if len(result) != result_len:
        result += '\n'

    result += '}\n'
    return wrap_code(result)

def make_cpptoc_function_impl(cls, funcs, existing, prefixname, defined_names):
    impl = ''

    for func in funcs:
        if not prefixname is None:
            name = prefixname+'_'+func.get_capi_name()
        else:
            name = func.get_capi_name()
        value = get_next_function_impl(existing, name)
        if not value is None \
            and value['body'].find('// AUTO-GENERATED CONTENT') < 0:
            # an implementation exists that was not auto-generated
            impl += make_cpptoc_function_impl_existing(cls, name, func, value, defined_names)
        else:
            impl += make_cpptoc_function_impl_new(cls, name, func, defined_names)

    return impl

def make_cpptoc_virtual_function_impl(header, cls, existing, prefixname, defined_names):
    funcs = []
    funcs.extend(cls.get_virtual_funcs())
    cur_cls = cls
    while True:
        parent_name = cur_cls.get_parent_name()
        if parent_name == 'CefBase':
            break
        else:
            parent_cls = header.get_class(parent_name, defined_names)
            if parent_cls is None:
                raise Exception('Class does not exist: '+parent_name)
            funcs.extend(parent_cls.get_virtual_funcs())
        cur_cls = header.get_class(parent_name, defined_names)

    return make_cpptoc_function_impl(cls, funcs, existing, prefixname, defined_names)

def make_cpptoc_virtual_function_assignment_block(funcs, offset, prefixname):
    impl = ''
    for func in funcs:
        name = func.get_capi_name()
        impl += '  GetStruct()->'+offset+name+' = '+prefixname+'_'+name+';\n'
    return impl

def make_cpptoc_virtual_function_assignment(header, cls, prefixname, defined_names):
    impl = make_cpptoc_virtual_function_assignment_block(cls.get_virtual_funcs(), '', prefixname)

    cur_cls = cls
    offset = ''
    while True:
        parent_name = cur_cls.get_parent_name()
        offset += 'base.'
        if parent_name == 'CefBase':
            break
        else:
            parent_cls = header.get_class(parent_name, defined_names)
            if parent_cls is None:
                raise Exception('Class does not exist: '+parent_name)
            impl += make_cpptoc_virtual_function_assignment_block(parent_cls.get_virtual_funcs(), offset, prefixname)
        cur_cls = header.get_class(parent_name, defined_names)

    return impl

def make_cpptoc_unwrap_derived(header, cls):
    # identify all classes that derive from cls
    derived_classes = []
    clsname = cls.get_name()
    allclasses = header.get_classes()
    for cur_cls in allclasses:
        if cur_cls.get_name() == clsname:
            continue
        if cur_cls.has_parent(clsname):
            derived_classes.append(cur_cls.get_name())

    derived_classes = sorted(derived_classes)

    impl = ''
    for clsname in derived_classes:
      impl += '  if (type == '+get_wrapper_type_enum(clsname)+') {\n'+\
              '    return '+clsname+'CppToC::Unwrap(reinterpret_cast<'+\
              get_capi_name(clsname, True)+'*>(s));\n'+\
              '  }\n'
    return impl

def make_cpptoc_class_impl(header, clsname, impl):
    # structure names that have already been defined
    defined_names = header.get_defined_structs()

    # retrieve the class and populate the defined names
    cls = header.get_class(clsname, defined_names)
    if cls is None:
        raise Exception('Class does not exist: '+clsname)

    capiname = cls.get_capi_name()
    prefixname = get_capi_name(clsname[3:], False)

    # retrieve the existing virtual function implementations
    existing = get_function_impls(impl, 'CEF_CALLBACK')

    # generate virtual functions
    virtualimpl = make_cpptoc_virtual_function_impl(header, cls, existing, prefixname, defined_names)
    if len(virtualimpl) > 0:
        virtualimpl = '\nnamespace {\n\n// MEMBER FUNCTIONS - Body may be edited by hand.\n\n'+virtualimpl+'}  // namespace'

    # the current class is already defined for static functions
    defined_names.append(cls.get_capi_name())

    # retrieve the existing static function implementations
    existing = get_function_impls(impl, 'CEF_EXPORT')

    # generate static functions
    staticimpl = make_cpptoc_function_impl(cls, cls.get_static_funcs(), existing, None, defined_names)
    if len(staticimpl) > 0:
        staticimpl = '\n// GLOBAL FUNCTIONS - Body may be edited by hand.\n\n'+staticimpl

    resultingimpl = staticimpl + virtualimpl

    # any derived classes can be unwrapped
    unwrapderived = make_cpptoc_unwrap_derived(header, cls)

    # determine what includes are required by identifying what translation
    # classes are being used
    includes = format_translation_includes(header, resultingimpl + unwrapderived)

    # build the final output
    result = get_copyright()

    result += includes+'\n'+resultingimpl+'\n'

    parent_sig = 'CefCppToC<'+clsname+'CppToC, '+clsname+', '+capiname+'>'

    const =  '// CONSTRUCTOR - Do not edit by hand.\n\n'+ \
             clsname+'CppToC::'+clsname+'CppToC() {\n'

    const += make_cpptoc_virtual_function_assignment(header, cls, prefixname, defined_names)

    const += '}\n\n'+ \
             'template<> CefRefPtr<'+clsname+'> '+parent_sig+'::UnwrapDerived(CefWrapperType type, '+capiname+'* s) {\n' + \
             unwrapderived + \
             '  NOTREACHED() << "Unexpected class type: " << type;\n'+ \
             '  return NULL;\n'+ \
             '}\n\n'+ \
             '#ifndef NDEBUG\n'+ \
             'template<> base::AtomicRefCount '+parent_sig+'::DebugObjCt = 0;\n'+ \
             '#endif\n\n'+ \
             'template<> CefWrapperType '+parent_sig+'::kWrapperType = '+get_wrapper_type_enum(clsname)+';'

    result += '\n\n'+wrap_code(const)

    return result

def make_cpptoc_global_impl(header, impl):
    # structure names that have already been defined
    defined_names = header.get_defined_structs()

    # retrieve the existing global function implementations
    existing = get_function_impls(impl, 'CEF_EXPORT')

    # generate global functions
    impl = make_cpptoc_function_impl(None, header.get_funcs(), existing, None, defined_names)
    if len(impl) > 0:
        impl = '\n// GLOBAL FUNCTIONS - Body may be edited by hand.\n\n'+impl

    includes = ''

    # include required headers for global functions
    filenames = []
    for func in header.get_funcs():
        filename = func.get_file_name()
        if not filename in filenames:
            includes += '#include "include/'+func.get_file_name()+'"\n' \
                        '#include "include/capi/'+func.get_capi_file_name()+'"\n'
            filenames.append(filename)

    # determine what includes are required by identifying what translation
    # classes are being used
    includes += format_translation_includes(header, impl)

    # build the final output
    result = get_copyright()

    result += includes+'\n'+impl

    return result

def write_cpptoc_impl(header, clsname, dir, backup):
    if clsname is None:
        # global file
        file = dir
    else:
        # class file
        # give the output file the same directory offset as the input file
        cls = header.get_class(clsname)
        dir = os.path.dirname(os.path.join(dir, cls.get_file_name()))
        file = os.path.join(dir, get_capi_name(clsname[3:], False)+'_cpptoc.cc')

    if path_exists(file):
        oldcontents = read_file(file)
    else:
        oldcontents = ''

    if clsname is None:
        newcontents = make_cpptoc_global_impl(header, oldcontents)
    else:
        newcontents = make_cpptoc_class_impl(header, clsname, oldcontents)
    if newcontents != oldcontents:
        if backup and oldcontents != '':
            backup_file(file)
        write_file(file, newcontents)
        return True

    return False


# test the module
if __name__ == "__main__":
    import sys

    # verify that the correct number of command-line arguments are provided
    if len(sys.argv) < 4:
        sys.stderr.write('Usage: '+sys.argv[0]+' <infile> <classname> <existing_impl>')
        sys.exit()

    # create the header object
    header = obj_header()
    header.add_file(sys.argv[1])

    # read the existing implementation file into memory
    try:
        f = open(sys.argv[3], 'r')
        data = f.read()
    except IOError, (errno, strerror):
        raise Exception('Failed to read file '+sys.argv[3]+': '+strerror)
    else:
        f.close()

    # dump the result to stdout
    sys.stdout.write(make_cpptoc_class_impl(header, sys.argv[2], data))
