from gmft.auto import AutoTableFormatter
import inspect

print("Dir(AutoTableFormatter class):")
print(dir(AutoTableFormatter))

try:
    formatter = AutoTableFormatter()
    print("\nDir(formatter instance):")
    print(dir(formatter))
    
    # Check if 'extract' exists and inspect it
    if hasattr(formatter, 'extract'):
        print("\nformatter.extract signature:")
        print(inspect.signature(formatter.extract))
        
    # Check if 'format' exists
    if hasattr(formatter, 'format'):
        print("\nformatter.format signature:")
        print(inspect.signature(formatter.format))
        
except Exception as e:
    print(f"\nError instantiating/inspecting: {e}")
