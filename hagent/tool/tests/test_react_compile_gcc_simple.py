#!/usr/bin/env python3
"""
Iterative C++ compile fix using GCC and LLM_wrap.
This script uses React to drive iterations where GCC is invoked
to check code syntax and an LLM wrapper is used to generate fixes.
"""

import os
import re
import subprocess
import tempfile
from typing import List, Dict

from hagent.tool.react import React
from hagent.tool.compile import Diagnostic
from hagent.core.llm_wrap import LLM_template, LLM_wrap


def extract_errors(gcc_output: str) -> list:
    """
    Extracts GCC errors (including context) from compiler output.

    Args:
        gcc_output: The compiler output string.

    Returns:
        A list of error block strings. Each block includes an error line and its context.
    """
    error_blocks = []
    current_block = None

    for line in gcc_output.splitlines():
        # Start a new error block if the line contains 'error:'
        if re.match(r'.*error:', line):
            if current_block:
                error_blocks.append(current_block)
            current_block = line + '\n'
        elif current_block:
            # Continuation of the current error block.
            current_block += line + '\n'
    if current_block:
        error_blocks.append(current_block)
    return error_blocks


def check_callback_cpp(code: str) -> List[Diagnostic]:
    """
    Checks if the provided C++ code compiles using g++ in syntax-check mode.

    Returns a list of Diagnostic objects if errors are found; an empty list otherwise.
    """
    with tempfile.NamedTemporaryFile(delete=False, suffix='.cpp') as tmp:
        tmp_name = tmp.name
        tmp.write(code.encode('utf-8'))

    try:
        # Run g++ in syntax-check mode (-fsyntax-only) without linking.
        result = subprocess.run(['g++', '-std=c++17', '-fsyntax-only', tmp_name], capture_output=True, text=True)
        if result.returncode != 0:
            diags = []
            for msg in extract_errors(result.stderr):
                # Create a Diagnostic with the error message.
                diags.append(Diagnostic(msg))
            return diags
        return []
    finally:
        if os.path.exists(tmp_name):
            os.remove(tmp_name)


def fix_callback_cpp(current_code: str, diag: Diagnostic, fix_example: dict, delta: bool, iteration_count: int) -> str:
    """
    Calls the LLM wrapper to fix the C++ code based on a given diagnostic.

    Constructs a prompt incorporating the diagnostic message and the current code,
    then returns the fixed code generated by the LLM. If no fix is provided,
    returns the original code.
    """
    # Determine the path to the LLM configuration file.
    conf_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'llm_wrap_conf1.yaml')
    
    try:
        # Initialize LLM_wrap instance using configuration from file.
        # Use the name that exists in the config file
        lw = LLM_wrap(
            name='test_react_compile_slang_simple', 
            log_file='test_react_compile_gcc_simple.log', 
            conf_file=conf_file
        )
        
        # Call inference with the current code
        if not fix_example or not fix_example.get('fix_question'):
            results = lw.inference({'code': current_code}, 'direct_prompt', n=1)
        else:
            # Merge fix_example with the current code for the prompt
            results = lw.inference({**fix_example, 'code': current_code}, 'example_prompt', n=1)
        
        if results and len(results) > 0:
            fixed_code = results[0]
            # Return the fixed code if it differs from the current code
            if fixed_code and fixed_code.strip() != current_code.strip():
                return fixed_code
    except Exception as e:
        print(f"LLM inference failed: {e}")
    
    return current_code


def test_react_with_db():
    """Test React with a database file."""
    # Create a temporary DB file
    with tempfile.NamedTemporaryFile(delete=False, suffix='.yaml') as tmp:
        tmp_name = tmp.name
        # Write a sample DB entry
        tmp.write(b"missing_semicolon:\n  fix_question: 'code with missing semicolon'\n  fix_answer: 'code with semicolon'\n")
    
    try:
        # Initialize React with the DB file
        react_tool = React()
        setup_success = react_tool.setup(db_path=tmp_name, learn=True, max_iterations=3)
        assert setup_success, f"React setup failed: {react_tool.error_message}"
        
        # A C++ snippet with a missing semicolon
        faulty_code = r"""
#include <iostream>

int main() {
    std::cout << "Hello World" << std::endl
    return 0;
}
"""
        
        # Run the React cycle with the provided callbacks
        fixed_code = react_tool.react_cycle(faulty_code, check_callback_cpp, fix_callback_cpp)
        
        # Check results
        assert fixed_code, "Failed to fix the code"
        assert ";" in fixed_code, "Semicolon not added to the fixed code"
        
        # Check the log
        log = react_tool.get_log()
        assert len(log) > 0, "Log should contain entries"
        
        print("Test with DB passed!")
    finally:
        # Clean up
        if os.path.exists(tmp_name):
            os.remove(tmp_name)


def test_react_without_db():
    """Test React without a database file."""
    # Initialize React without a DB file
    react_tool = React()
    setup_success = react_tool.setup(learn=False, max_iterations=3, comment_prefix="//")
    assert setup_success, f"React setup failed: {react_tool.error_message}"
    
    # A C++ snippet with a missing semicolon
    faulty_code = r"""
#include <iostream>

int main() {
    std::cout << "Hello World" << std::endl
    return 0;
}
"""
    
    # Run the React cycle with the provided callbacks
    fixed_code = react_tool.react_cycle(faulty_code, check_callback_cpp, fix_callback_cpp)
    
    # Check results
    assert fixed_code, "Failed to fix the code"
    assert ";" in fixed_code, "Semicolon not added to the fixed code"
    
    print("Test without DB passed!")


if __name__ == '__main__':
    # Run the tests
    test_react_with_db()
    test_react_without_db()
    
    # Original example code
    react_tool = React()
    setup_success = react_tool.setup(db_path='foo.yaml', learn=True, max_iterations=3)
    if not setup_success:
        print(f'React setup failed: {react_tool.error_message}')
        exit(1)

    # A C++ snippet with a missing semicolon.
    faulty_code = r"""
#include <iostream>

int main() {
    std::cout << "Hello World" << std::endl
    return 0;
}
"""

    # Run the React cycle with the provided callbacks.
    fixed_code = react_tool.react_cycle(faulty_code, check_callback_cpp, fix_callback_cpp)

    # Print results.
    if fixed_code:
        print('Successfully fixed code:\n')
        print(fixed_code)
    else:
        print('Could not fix the code within the iteration limits.')
