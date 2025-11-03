"""
Script to fix overly restrictive validators in custom_graphql_validator.py
This makes SpecialCharacterString2_100 and SpecialCharacterString2_500 more permissive
"""

import re

def fix_validators():
    file_path = r'c:\Users\DELL\Desktop\ooumph-backend\auth_manager\validators\custom_graphql_validator.py'
    
    print(f"Reading {file_path}...")
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    
    # Pattern 1: Fix parse_value method - comment out the ALLOWED_PATTERN check
    pattern1 = r'(\s+)if not self\.__class__\.ALLOWED_PATTERN\.match\(value\):\s+self\.raise_error\(f"\{self\.field_name\} must contain only letters, numbers, spaces, special characters, and emojis\."\)'
    replacement1 = r'\1# Validation relaxed - allow all Unicode characters\n\1# if not self.__class__.ALLOWED_PATTERN.match(value):\n\1#     self.raise_error(f"{self.field_name} must contain only letters, numbers, spaces, special characters, and emojis.")'
    
    content = re.sub(pattern1, replacement1, content)
    
    # Pattern 2: Fix parse_literal method - comment out the ALLOWED_PATTERN check
    pattern2 = r'(\s+)if not cls\.ALLOWED_PATTERN\.match\(value\):\s+raise GraphQLError\(\s+"Value must contain only letters, numbers, spaces, special characters, and emojis\.",\s+extensions=extensions,\s+path=path\s+\)'
    replacement2 = r'\1# Validation relaxed - allow all Unicode characters\n\1# if not cls.ALLOWED_PATTERN.match(value):\n\1#     raise GraphQLError(\n\1#         "Value must contain only letters, numbers, spaces, special characters, and emojis.",\n\1#         extensions=extensions,\n\1#         path=path\n\1#     )'
    
    content = re.sub(pattern2, replacement2, content)
    
    if content == original_content:
        print("⚠️ No changes were made. The patterns may have already been fixed or the regex didn't match.")
        return False
    
    # Backup original file
    backup_path = file_path + '.backup'
    print(f"Creating backup at {backup_path}...")
    with open(backup_path, 'w', encoding='utf-8') as f:
        f.write(original_content)
    
    # Write fixed content
    print(f"Writing fixed content to {file_path}...")
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✅ Validators fixed successfully!")
    print("\nChanges made:")
    print("- Commented out overly restrictive ALLOWED_PATTERN validation")
    print("- Both parse_value and parse_literal methods updated")
    print("- Validators now accept all Unicode characters")
    
    return True

if __name__ == '__main__':
    try:
        success = fix_validators()
        if success:
            print("\n" + "="*60)
            print("NEXT STEPS:")
            print("="*60)
            print("1. The validators have been fixed")
            print("2. Fix your GraphQL query syntax:")
            print("   mutation {")
            print("     createCommunityPost(input: { ... }) {")
            print("       success")
            print("       message")
            print("     }")
            print("   }")
            print("3. Restart your Django server if it's running")
            print("="*60)
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
