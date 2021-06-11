"""
This script takes as an input the directory where the Doxygen xml output is.
From the files in the directory it will print out an approximate attempt at the text required for binding with emscripten.

- It will *not* deal with overloaded methods.
- It will *not* create definitions for constructors.

usage:
 python extract_emscripten_helper.py <directory-to-doxygen-xml-content>
"""
import html
import mimetypes
import os
import re
import sys
from os import listdir
from os.path import isfile, join

import xml.etree.ElementTree as XmlTree

IGNORE_FUNCTIONS_WITH_BRIEF_DESCRIPTION = ['Move constructor', 'Destructor', 'Copy constructor', 'Assignment operator']
BASIC_BOOLEAN_METHODS = ["need"]
NAMES_REQUIRING_NAMESPACE = ["UnitsPtr", "VariablePtr", "ResetPtr", "ComponentPtr", "VariablePairPtr", "ModelPtr", "AnalyserExternalVariablePtr",
                             "ImportSourcePtr", "AnyItem", "CellmlElementType", "UnitPtr"]
NAMES_REQUIRING_UNITS_QUALIFICATION = ["Prefix", "StandardUnit"]
NAMES_REQUIRING_VARIABLE_QUALIFICATION = ["InterfaceType"]
PARAM_NAME_MAP = {"oldUnits": "units", "variable1": "variable"}


def set_overload_text(overload):
    overload_text = ''
    if overload:
        overload_text = 'ByXXX'

    return overload_text


def print_test_header(f, class_name, method_name, overload_text=''):
    f.write(f'  test("Checking {class_name}.{method_name}{overload_text}.", () => {{\n')


def print_test_footer(f):
    f.write('  });\n')


def declare_class_variable(f, class_name):
    f.write(f'    const x = new libcellml.{class_name}()\n\n')


def print_boolean_test(f, class_name, method_name):
    print_test_header(f, class_name, method_name)
    declare_class_variable(f, class_name)
    f.write(f'    expect(x.{method_name}()).toBe(true)\n')
    print_test_footer(f)


def print_string_pair_test(f, class_name, method_name):
    base_function_name = convert_to_base_method_name(method_name)
    print_test_header(f, class_name, method_name)
    declare_class_variable(f, class_name)
    f.write(f'    x.set{base_function_name[0].upper()}{base_function_name[1:]}("something")\n')
    f.write(f'    expect(x.{method_name}()).toBe("something")\n')
    print_test_footer(f)


def print_pair_test(f, class_name, method_name):
    base_function_name = convert_to_base_method_name(method_name)
    if base_function_name.endswith('String'):
        print_string_pair_test(f, class_name, base_function_name)
    else:
        print_test_header(f, class_name, base_function_name)
        declare_class_variable(f, class_name)
        f.write(f'    x.set{base_function_name[0].upper()}{base_function_name[1:]}("something")\n')
        f.write(f'    expect(x.{method_name}()).toBe("something")\n')
        print_test_footer(f)


def print_skeleton_test(f, class_name, method_name, overload):
    overload_text = set_overload_text(overload)
    print_test_header(f, class_name, method_name, overload_text)
    declare_class_variable(f, class_name)
    f.write(f'    expect(x.{method_name}{overload_text}()).toBe("")\n')
    print_test_footer(f)


def print_test(f, class_name, method_name, overload=False, is_pair=False):
    """  test('Checking Model name.', () => {
    const m = new libcellml.Model()

    expect(m.name()).toBe('');

    m.setName('model-test')
    expect(m.name()).toBe('model-test');
  });
"""
    if method_name[:4] in BASIC_BOOLEAN_METHODS:
        print_boolean_test(f, class_name, method_name)
    elif is_pair:
        print_pair_test(f, class_name, method_name)
    else:
        print_skeleton_test(f, class_name, method_name, overload)


def convert_to_base_method_name(name):
    base_method_name = name[:]
    if name.startswith("set"):
        base_method_name = name[3].lower() + name[4:]

    return base_method_name


def determine_set_get_pairs(methods):
    pairs = {}
    for key in methods:
        s = key.split('::')
        function_name = s.pop()
        lower_method_name = convert_to_base_method_name(function_name)
        if lower_method_name in pairs:
            pairs[lower_method_name] += 1
        else:
            pairs[lower_method_name] = 1

    pairs = dict(filter(lambda elem: elem[1] == 2, pairs.items()))
    return pairs


def print_test_file(data):
    """
const libCellMLModule = require('libcellml.js/libcellml.common')
let libcellml = null

describe("Model tests", () => {
  beforeAll(async () => {
        libcellml = await libCellMLModule();
    });
})
    """
    set_get_pairs = determine_set_get_pairs(data['methods'])
    visited_pairs = []
    full_class_name = data['name']
    s = full_class_name.split('::')
    class_name = s.pop()
    with open('tests.txt', 'a') as f:
        f.write('\n')
        f.write("""
const libCellMLModule = require('libcellml.js/libcellml.common')
let libcellml = null

""")
        f.write(f'describe("{class_name} tests", () => {{\n')
        f.write("""  beforeAll(async () => {
    libcellml = await libCellMLModule();
  });
""")
        for key in data['methods']:
            s = key.split('::')
            function_name = s.pop()

            base_function_name = convert_to_base_method_name(function_name)
            if base_function_name in visited_pairs:
                continue
            is_pair = base_function_name in set_get_pairs
            if is_pair:
                visited_pairs.append(base_function_name)
            method_information = data['methods'][key]
            if len(method_information) == 1:
                print_test(f, class_name, function_name, is_pair=is_pair)
            else:
                for info in method_information:
                    print_test(f, class_name, function_name, overload=True)
        f.write('})\n')


def add_namespace_to_class():
    with open('wrapping.txt') as f:
        content = f.read()

    for name in NAMES_REQUIRING_NAMESPACE:
        content = re.sub(r'\b' + name + r'\b', f'libcellml::{name}', content)
        # content = content.replace('\b' + name + '\b', f'libcellml::{name}')

    for name in NAMES_REQUIRING_UNITS_QUALIFICATION:
        content = re.sub(r'\b' + name + r'\b', f'libcellml::Units::{name}', content)
        # content = content.replace('\b' + name + '\b', f'libcellml::Units::{name}')
        # Undo bad replacements
        # if name == "Prefix":
        #     content = content.replace("Attributelibcellml::Units::Prefix", "AttributePrefix")
        # elif name == "StandardUnit":
        #     content = content.replace("Bylibcellml::Units::StandardUnit", "ByStandardUnit")

    for name in NAMES_REQUIRING_VARIABLE_QUALIFICATION:
        content = re.sub(r'\b' + name + r'\b', f'libcellml::Variable::{name}', content)
        # content = content.replace('\b' + name + '\b', f'libcellml::Variable::{name}')
        # Undo bad replacements
        # if name == "InterfaceType":
        #     content = content.replace("setlibcellml::Variable::InterfaceType", "setInterfaceType")
        #     content = content.replace("Bylibcellml::Variable::InterfaceType", "ByInterfaceType")
        #     content = content.replace("removelibcellml::Variable::InterfaceType", "removeInterfaceType")
        #     content = content.replace("haslibcellml::Variable::InterfaceType", "hasInterfaceType")
        #     content = content.replace("permitslibcellml::Variable::InterfaceType", "permitsInterfaceType")

    with open('wrapping.txt', 'w') as f:
        f.write(content)


def print_class(data):
    with open('wrapping.txt', 'a') as wrapping_file:
        wrapping_file.write('\n')

        full_class_name = data['name']
        s = full_class_name.split('::')
        class_name = s.pop()

        wrapping_file.write('# include <emscripten/bind.h>\n\n')
        wrapping_file.write(f'# include "libcellml/{class_name.lower()}.h"\n\n')
        wrapping_file.write('using namespace emscripten;\n\n')
        wrapping_file.write(f'EMSCRIPTEN_BINDINGS(libcellml_{class_name.lower()})\n{{\n')

        enums = data['enums']
        for enum in enums:
            enum_name = enum['name']
            wrapping_file.write(f'    enum_<{full_class_name}::{enum_name}>("{enum_name}")\n')
            for value in enum['values']:
                wrapping_file.write(f'        .value("{value}", {full_class_name}::{enum_name}::{value})\n')
            wrapping_file.write('    ;\n\n')

        wrapping_file.write(f'    class_<{full_class_name}>("{class_name}")\n')
        for key in data['methods']:
            s = key.split('::')
            function_name = s.pop()
            method_information = data['methods'][key]
            if len(method_information) == 1:
                wrapping_file.write(f'        .function("{function_name}", &{key})\n')
            else:
                for info in method_information:
                    params = info["param_list"]
                    const = " const" if info["const"] else ""
                    if len(params):
                        first_param_name = params[0]["name"]
                        if first_param_name in PARAM_NAME_MAP:
                            first_param_name = PARAM_NAME_MAP[first_param_name]
                        function_variation = first_param_name[0].upper() + first_param_name[1:]
                    else:
                        function_variation = 'XXX'
                    param_list = ', '.join([p["type"] for p in params])
                    wrapping_file.write(f'        .function("{function_name}By{function_variation}", select_overload<{info["returns"]}({param_list}){const}>(&{key}))\n')

        wrapping_file.write('    ;\n}\n')

        print_header = True
        for warning in data['warnings']:
            if print_header:
                wrapping_file.write(f'\nWarnings: {class_name}\n')
                print_header = False
            wrapping_file.write(f' - {warning}\n')


def extract_parameters(elements):
    params = []
    for element in elements:
        type_ = element.find("./type")
        text = ''.join([e for e in type_.itertext()])
        name = element.find("./declname").text
        params.append({
            "type": html.unescape(text),
            "name": name,
        })

    return params


def print_out_near_emscripten_format(source_file):
    tree = XmlTree.parse(source_file)
    root = tree.getroot()
    cs = root.findall("compounddef[@kind='class']")
    data = {'name': None, 'methods': {}, 'warnings': [], 'enums': []}
    for c in cs:
        full_class_name = c.find('./compoundname').text
        data['name'] = full_class_name
        es = c.findall("./sectiondef[@kind='public-type']/memberdef[@kind='enum']")
        for e in es:
            name = e.find("./name").text
            value_elements = e.findall("./enumvalue")
            values = []
            for value_element in value_elements:
                values.append(value_element.find("./name").text)

            data['enums'].append({
                "name": name,
                "values": values,
            })

        fs = c.findall("./sectiondef[@kind='public-func']/memberdef[@kind='function']")
        for f in fs:
            d = f.find("./briefdescription/para").text
            if d is None:
                data['warnings'].append(f'Non standard brief description!!! {f.find("./definition").text}')
                continue
            r = [True for tt in IGNORE_FUNCTIONS_WITH_BRIEF_DESCRIPTION if d.startswith(tt)]
            if len(r):
                data['warnings'].append(f'Function not marked with Doxygen directive @private: {f.find("./definition").text}')
                continue
            function_definition = f.find("./definition").text
            return_type = f.find("./type")
            function_return_type = ''.join([e for e in return_type.itertext()])
            args_string = f.find("./argsstring").text

            p = function_definition.split(' ')
            if len(p) > 1:
                full_definition = p[1]
                param_elements = f.findall("./param")
                params = extract_parameters(param_elements)
                method_object = {
                    "name": full_definition,
                    "returns": function_return_type,
                    "param_list": params,
                    "const": args_string.endswith(" const")
                }
                if full_definition in data['methods']:
                    data['methods'][full_definition].append(method_object)
                else:
                    data['methods'][full_definition] = [method_object]

    print_class(data)
    print_test_file(data)


def process_file(source_file):
    if os.path.exists(source_file):
        result = mimetypes.guess_type(source_file)
        if len(result) > 1 and result[0] == 'application/xml':
            print_out_near_emscripten_format(source_file)


def main():
    args = sys.argv[:]

    source_dir = args.pop()
    if os.path.exists(source_dir) and os.path.isdir(source_dir):
        with open('wrapping.txt', 'w'):
            pass
        with open('tests.txt', 'w'):
            pass
        dir_files = [join(source_dir, f) for f in listdir(source_dir) if isfile(join(source_dir, f)) and f.startswith('classlibcellml_1_1')]
        for f in dir_files:
            process_file(f)

        add_namespace_to_class()


if __name__ == "__main__":
    main()
