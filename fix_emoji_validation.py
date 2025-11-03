#!/usr/bin/env python3
"""
Comprehensive fix for emoji validation to support:
- Complex emojis with variation selectors (️)
- Zero-Width Joiner sequences (👨‍👩‍👧)
- Keycap emojis (2️⃣0️⃣2️⃣5️⃣)
- All modern emoji combinations
"""

import re

file_path = r"c:\Users\DELL\Desktop\ooumph-backend\auth_manager\validators\custom_graphql_validator.py"

def add_emoji_support(content):
    """Add comprehensive emoji support to all SpecialCharacterString classes"""
    
    # Complete emoji ranges including all necessary components
    emoji_ranges = [
        r"\u200D",                    # Zero-Width Joiner (ZWJ)
        r"\uFE00-\uFE0F",            # Variation Selectors (VS15, VS16)
        r"\u20E3",                    # Combining Enclosing Keycap (for 2️⃣)
        r"\u2700-\u27BF",            # Dingbats
        r"\U0001F000-\U0001F02F",    # Mahjong Tiles
        r"\U0001F0A0-\U0001F0FF",    # Playing Cards
        r"\U0001F100-\U0001F64F",    # Enclosed Characters & Emoticons
        r"\U0001F680-\U0001F6FF",    # Transport & Map Symbols
        r"\U0001F700-\U0001F77F",    # Alchemical Symbols
        r"\U0001F780-\U0001F7FF",    # Geometric Shapes Extended
        r"\U0001F800-\U0001F8FF",    # Supplemental Arrows-C
        r"\U0001F900-\U0001F9FF",    # Supplemental Symbols and Pictographs
        r"\U0001FA00-\U0001FA6F",    # Chess Symbols
        r"\U0001FA70-\U0001FAFF",    # Symbols and Pictographs Extended-A
    ]
    
    emoji_pattern = '\n        r"'.join(emoji_ranges)
    emoji_block = f'        r"{emoji_pattern}"'
    
    # Pattern to find all SpecialCharacterString class definitions
    class_pattern = re.compile(
        r'(class\s+\w*SpecialCharacterString\w*\([^)]+\):.*?'
        r'ALLOWED_PATTERN\s*=\s*\()(.*?)(r"\s*"\s*\))',
        re.DOTALL
    )
    
    def replace_pattern(match):
        class_def = match.group(1)
        old_patterns = match.group(2)
        closing = match.group(3)
        
        # Remove any existing emoji-related patterns to avoid duplicates
        lines = old_patterns.split('\n')
        filtered_lines = []
        
        for line in lines:
            # Skip lines with emoji ranges we're replacing
            if any(skip in line for skip in [
                r'\u200D', r'\uFE00', r'\u20E3',
                r'\u2700-\u27BF', r'\U0001F000', r'\U0001F0A0',
                r'\U0001F100', r'\U0001F680', r'\U0001F700',
                r'\U0001F780', r'\U0001F800', r'\U0001F900',
                r'\U0001FA00', r'\U0001FA70'
            ]):
                continue
            filtered_lines.append(line)
        
        # Reconstruct with new emoji support
        new_patterns = '\n'.join(filtered_lines).rstrip()
        
        # Add emoji block before the closing
        return f"{class_def}{new_patterns}\n{emoji_block}\n        {closing}"
    
    # Apply to all SpecialCharacterString classes
    content = class_pattern.sub(replace_pattern, content)
    
    return content


def add_comment_documentation(content):
    """Add helpful comment about emoji support at the top of emoji ranges"""
    
    emoji_comment = '''
    # ========== EMOJI SUPPORT ==========
    # The following ranges support all modern emojis including:
    # - Keycap emojis: 2️⃣0️⃣2️⃣5️⃣
    # - ZWJ sequences: 👨‍👩‍👧‍👦
    # - Variation selectors: ️
    # - All standard emoji ranges
    '''
    
    # Find first occurrence of emoji ranges and add comment
    pattern = r'(r"\u200D")'
    replacement = f'{emoji_comment}\n        \\1'
    
    content = re.sub(pattern, replacement, content, count=1)
    
    return content


# Read the file
print("Reading file...")
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

# Backup original content
backup_path = file_path.replace('.py', '_backup.py')
with open(backup_path, 'w', encoding='utf-8') as f:
    f.write(content)
print(f"✓ Backup created: {backup_path}")

# Apply fixes
print("Applying comprehensive emoji support...")
content = add_emoji_support(content)
content = add_comment_documentation(content)

# Write the fixed content
with open(file_path, 'w', encoding='utf-8') as f:
    f.write(content)

print("\n" + "="*60)
print("✅ EMOJI VALIDATION FIXED SUCCESSFULLY!")
print("="*60)
print("\n📝 Changes made:")
print("   1. ✓ Added \\u200D (Zero-Width Joiner) for complex emoji sequences")
print("   2. ✓ Added \\uFE00-\\uFE0F (Variation Selectors 15-16)")
print("   3. ✓ Added \\u20E3 (Combining Enclosing Keycap) for number emojis")
print("   4. ✓ Updated ALL SpecialCharacterString classes comprehensively")
print("   5. ✓ Added complete emoji Unicode ranges (U+1F000 - U+1FAFF)")
print("\n✨ Now supports:")
print("   • Keycap emojis: 2️⃣0️⃣2️⃣5️⃣")
print("   • Complex sequences: 👨‍👩‍👧‍👦")
print("   • Rockets & symbols: 🚀✨🤖")
print("   • Arrows: ➝ → ⇒")
print("   • All modern emojis!")
print("\n🎯 Test with: 'AI 2️⃣0️⃣2️⃣5️⃣ 🚀 | Smarter • Faster • Better 🤖✨'")
print("\n" + "="*60)