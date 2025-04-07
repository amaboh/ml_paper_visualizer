#!/usr/bin/env python
"""
Inspect the mistralai package to understand its structure.
"""
import sys
import inspect

print(f"Python version: {sys.version}")

try:
    import mistralai
    print(f"mistralai version: {mistralai.__version__ if hasattr(mistralai, '__version__') else 'Unknown'}")
    print("\nContents of mistralai package:")
    print("----------------------------")
    for name in dir(mistralai):
        if not name.startswith('__'):
            print(f"- {name}")
    
    print("\nTrying to import Mistral client:")
    from mistralai import Mistral
    print("Success! Mistral client imported.")
    print("\nAttributes and methods of Mistral client:")
    print("----------------------------")
    for name in dir(Mistral):
        if not name.startswith('__'):
            print(f"- {name}")
    
    # Check for exceptions
    print("\nLooking for exception classes:")
    print("----------------------------")
    try:
        # Try importing from exceptions module
        try:
            from mistralai import exceptions
            print("Found exceptions module!")
            for name in dir(exceptions):
                if not name.startswith('__'):
                    print(f"- {name}")
        except ImportError:
            print("No 'exceptions' module found.")
        
        # Check if any exception classes exist directly in mistralai
        exception_classes = [name for name in dir(mistralai) if 'Error' in name or 'Exception' in name]
        if exception_classes:
            print("\nFound exception classes in mistralai module:")
            for name in exception_classes:
                print(f"- {name}")
                obj = getattr(mistralai, name)
                if inspect.isclass(obj) and issubclass(obj, Exception):
                    print(f"  (Confirmed this is an Exception subclass)")
        else:
            print("\nNo exception classes found directly in mistralai module.")
    
    except Exception as e:
        print(f"Error while inspecting exceptions: {e}")

except ImportError as e:
    print(f"Error importing mistralai: {e}")
except Exception as e:
    print(f"Unexpected error: {e}") 