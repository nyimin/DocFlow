from gmft.auto import AutoTableFormatter
import inspect

print("AutoTableFormatter.format signature:")
print(inspect.signature(AutoTableFormatter.format))

print("\nAutoTableFormatter.extract signature (if exists):")
try:
    print(inspect.signature(AutoTableFormatter.extract))
except AttributeError:
    print("No extract method.")

print("\nDir(AutoTableFormatter):")
print(dir(AutoTableFormatter))
