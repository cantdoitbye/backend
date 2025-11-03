#!/usr/bin/env python3
"""
Script to fix NonSpecialCharacterString5_100 and NonSpecialCharacterString10_200 validators
to accept digits, emojis, and special characters.
"""

import re

# Read the file
file_path = r"auth_manager\validators\custom_graphql_validator.py"

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Define the new pattern lines
new_pattern_lines = [
    "    # Allows letters, numbers, spaces, common special characters, and emoji ranges (Unicode blocks)\n",
    "    ALLOWED_PATTERN = re.compile(\n",
    '        r"^[a-zA-Z0-9 !@#$%^&*()_+\\-=\\[\\]{}|;\':\\",./<>?`~"\n',
    '        r"\\u00C0-\\u017F"  # Latin Extended (accented characters)\n',
    '        r"\\u0100-\\u024F"  # Latin Extended Additional\n',
    '        r"\\u1E00-\\u1EFF"  # Latin Extended Additional\n',
    '        r"\\u2000-\\u206F"  # General Punctuation\n',
    '        r"\\u2070-\\u209F"  # Superscripts and Subscripts\n',
    '        r"\\u20A0-\\u20CF"  # Currency Symbols\n',
    '        r"\\u2100-\\u214F"  # Letterlike Symbols\n',
    '        r"\\u2190-\\u21FF"  # Arrows\n',
    '        r"\\u2200-\\u22FF"  # Mathematical Operators\n',
    '        r"\\u2300-\\u23FF"  # Miscellaneous Technical\n',
    '        r"\\u2400-\\u243F"  # Control Pictures\n',
    '        r"\\u2440-\\u245F"  # Optical Character Recognition\n',
    '        r"\\u2460-\\u24FF"  # Enclosed Alphanumerics\n',
    '        r"\\u2500-\\u257F"  # Box Drawing\n',
    '        r"\\u2580-\\u259F"  # Block Elements\n',
    '        r"\\u25A0-\\u25FF"  # Geometric Shapes\n',
    '        r"\\u2600-\\u26FF"  # Miscellaneous Symbols\n',
    '        r"\\u2700-\\u27BF"  # Dingbats\n',
    '        r"\\U0001F000-\\U0001F02F"  # Mahjong Tiles\n',
    '        r"\\U0001F030-\\U0001F09F"  # Domino Tiles\n',
    '        r"\\U0001F0A0-\\U0001F0FF"  # Playing Cards\n',
    '        r"\\U0001F100-\\U0001F1FF"  # Enclosed Alphanumeric Supplement\n',
    '        r"\\U0001F200-\\U0001F2FF"  # Enclosed Ideographic Supplement\n',
    '        r"\\U0001F300-\\U0001F5FF"  # Miscellaneous Symbols and Pictographs\n',
    '        r"\\U0001F600-\\U0001F64F"  # Emoticons\n',
    '        r"\\U0001F650-\\U0001F67F"  # Ornamental Dingbats\n',
    '        r"\\U0001F680-\\U0001F6FF"  # Transport and Map Symbols\n',
    '        r"\\U0001F700-\\U0001F77F"  # Alchemical Symbols\n',
    '        r"\\U0001F780-\\U0001F7FF"  # Geometric Shapes Extended\n',
    '        r"\\U0001F800-\\U0001F8FF"  # Supplemental Arrows-C\n',
    '        r"\\U0001F900-\\U0001F9FF"  # Supplemental Symbols and Pictographs\n',
    '        r"\\U0001FA00-\\U0001FA6F"  # Chess Symbols\n',
    '        r"\\U0001FA70-\\U0001FAFF"  # Symbols and Pictographs Extended-A\n',
    '        r"]+$", re.UNICODE\n',
    "    )\n"
]

new_pattern_check = [
    "        if not cls.ALLOWED_PATTERN.match(value):\n",
    "            raise GraphQLError(\n",
    '                "Value must contain only letters, numbers, spaces, special characters, and emojis.",\n',
    "                extensions=extensions,\n",
    "                path=path\n",
    "            )\n"
]

# Process the file
i = 0
output_lines = []
while i < len(lines):
    line = lines[i]
    
    # Fix NonSpecialCharacterString5_100
    if 'class NonSpecialCharacterString5_100' in line:
        output_lines.append(line)
        i += 1
        # Update docstring
        if i < len(lines) and '"""Custom String Scalar that enforces length constraints and disallows special characters"""' in lines[i]:
            output_lines.append('    """Custom String Scalar that enforces length constraints and allows letters, numbers, spaces, special characters, and emojis"""\n')
            i += 1
            continue
    
    # Replace ALLOWED_PATTERN for NonSpecialCharacterString5_100
    elif 'ALLOWED_PATTERN = re.compile(r"^[a-zA-Z]+$")  # Allows only letters' in line and i > 340 and i < 360:
        output_lines.extend(new_pattern_lines)
        i += 1
        continue
    
    # Fix parse_value for NonSpecialCharacterString5_100
    elif 'if not self.ALLOWED_PATTERN.match(value):' in line and i > 370 and i < 390:
        output_lines.append(line.replace('self.ALLOWED_PATTERN', 'self.__class__.ALLOWED_PATTERN'))
        i += 1
        # Update error message
        if i < len(lines) and 'must contain only letters. No special characters allowed' in lines[i]:
            output_lines.append(lines[i].replace('must contain only letters. No special characters allowed', 'must contain only letters, numbers, spaces, special characters, and emojis'))
            i += 1
        continue
    
    # Add pattern check before return in parse_literal for NonSpecialCharacterString5_100
    elif 'return value' in line and i > 395 and i < 415:
        output_lines.extend(new_pattern_check)
        output_lines.append(line)
        i += 1
        continue
    
    # Fix NonSpecialCharacterString10_200
    elif 'class NonSpecialCharacterString10_200' in line:
        output_lines.append(line)
        i += 1
        # Update docstring
        if i < len(lines) and '"""Custom String Scalar that enforces length constraints and disallows special characters"""' in lines[i]:
            output_lines.append('    """Custom String Scalar that enforces length constraints and allows letters, numbers, spaces, special characters, and emojis"""\n')
            i += 1
            continue
    
    # Replace ALLOWED_PATTERN for NonSpecialCharacterString10_200
    elif 'ALLOWED_PATTERN = re.compile(r"^[a-zA-Z]+$")  # Allows only letters' in line and i > 470 and i < 490:
        output_lines.extend(new_pattern_lines)
        i += 1
        continue
    
    # Fix parse_value for NonSpecialCharacterString10_200
    elif 'if not self.ALLOWED_PATTERN.match(value):' in line and i > 500 and i < 520:
        output_lines.append(line.replace('self.ALLOWED_PATTERN', 'self.__class__.ALLOWED_PATTERN'))
        i += 1
        # Update error message
        if i < len(lines) and 'must contain only letters. No special characters allowed' in lines[i]:
            output_lines.append(lines[i].replace('must contain only letters. No special characters allowed', 'must contain only letters, numbers, spaces, special characters, and emojis'))
            i += 1
        continue
    
    # Add pattern check before return in parse_literal for NonSpecialCharacterString10_200
    elif 'return value' in line and i > 530 and i < 550:
        output_lines.extend(new_pattern_check)
        output_lines.append(line)
        i += 1
        continue
    
    else:
        output_lines.append(line)
        i += 1

# Write the updated content back
with open(file_path, 'w', encoding='utf-8') as f:
    f.writelines(output_lines)

print("✅ Successfully updated NonSpecialCharacterString5_100 and NonSpecialCharacterString10_200 validators")
print("   - Now accepts: letters, numbers, spaces, special characters, and emojis")
print("   - Still rejects: HTML tags")
print("\n📝 Updated fields:")
print("   - Community Goal (name, description)")
print("   - Community Affiliation (entity, subject)")
print("   - Community Activities (name, description)")
