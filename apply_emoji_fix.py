#!/usr/bin/env python3
"""Direct fix for emoji validation"""

file_path = r"c:\Users\DELL\Desktop\ooumph-backend\auth_manager\validators\custom_graphql_validator.py"

# Read file
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# The exact string to find and replace
old_text = '        r"\\U0001FA70-\\U0001FAFF"  # Symbols and Pictographs Extended-A\n        r"]+$", re.UNICODE'

new_text = '''        r"\\U0001FA70-\\U0001FAFF"  # Symbols and Pictographs Extended-A
        r"\\u200D"  # Zero-Width Joiner (ZWJ) - for complex emoji sequences
        r"\\uFE00-\\uFE0F"  # Variation Selectors (VS15, VS16) - for emoji variations
        r"\\u20E3"  # Combining Enclosing Keycap - for keycap emojis like 2️⃣
        r"]+$", re.UNICODE'''

# Count occurrences
count = content.count(old_text)
print(f"Found {count} occurrences to replace")

# Replace all occurrences
if count > 0:
    content = content.replace(old_text, new_text)
    
    # Write back
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Successfully updated {count} SpecialCharacterString classes!")
    print("\n🎯 Added:")
    print("   • \\u200D (Zero-Width Joiner)")
    print("   • \\uFE00-\\uFE0F (Variation Selectors)")
    print("   • \\u20E3 (Combining Enclosing Keycap)")
    print("\n⚠️  RESTART SERVER NOW!")
else:
    print("❌ Pattern not found! File might already be fixed or has different format.")
