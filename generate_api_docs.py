# generate_api_docs.py
"""
API Documentation Generator for OOUMPH Project
Generates a comprehensive single-file API reference for AI-led development
Enhanced with input types and example data
"""

import json
from pathlib import Path
import re
from datetime import datetime

class APIDocumentationGenerator:
    def __init__(self):
        self.modules = [
            'auth_manager', 'community', 'post', 'story', 'connection', 
            'msg', 'service', 'dairy', 'shop', 'vibe_manager', 'job', 
            'monitoring', 'agentic'
        ]
        self.api_reference = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'project': 'OOUMPH Social Platform',
                'version': 'v2.0',
                'total_endpoints': 0
            },
            'modules': {}
        }
    
    def extract_mutations_from_file(self, file_path):
        """Extract mutation definitions from GraphQL mutation files"""
        mutations = {}
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Find class definitions with Field() assignments
            mutation_pattern = r'(\w+)\s*=\s*(\w+)\.Field\(\)'
            
            matches = re.findall(mutation_pattern, content)
            
            for field_name, class_name in matches:
                purpose = self.extract_purpose_from_name(field_name)
                
                # Extract class definition and input parameters
                class_info = self.extract_class_details(content, class_name)
                input_info = self.extract_input_types(content, class_name)
                
                # If no fields found, try to infer from class name
                if not input_info.get('fields'):
                    input_info['fields'] = self.infer_fields_from_name(class_name)
                
                mutations[field_name] = {
                    'class': class_name,
                    'purpose': purpose,
                    'type': 'mutation',
                    'input_fields': input_info.get('fields', []),
                    'input_type': input_info.get('input_type', 'Unknown'),
                    'return_type': class_info.get('output_type', 'Unknown'),
                    'example_input': self.generate_example_input(field_name, input_info.get('fields', [])),
                    'graphql_example': self.generate_mutation_example(field_name, input_info.get('fields', []))
                }
                
        except FileNotFoundError:
            pass
        return mutations
    
    def extract_queries_from_file(self, file_path):
        """Extract query definitions from GraphQL query files"""
        queries = {}
        try:
            with open(file_path, 'r') as f:
                content = f.read()
                
            # Look for resolve_ methods which indicate GraphQL queries
            query_pattern = r'def\s+resolve_(\w+)\(.*?\):'
            matches = re.findall(query_pattern, content)
            
            for query_name in matches:
                purpose = self.extract_purpose_from_name(query_name)
                
                # Extract method signature and parameters
                method_info = self.extract_method_signature(content, query_name)
                
                queries[query_name] = {
                    'purpose': purpose,
                    'type': 'query',
                    'parameters': method_info.get('parameters', []),
                    'return_type': method_info.get('return_type', 'Unknown'),
                    'example_query': self.generate_query_example(query_name, method_info.get('parameters', []))
                }
                
        except FileNotFoundError:
            pass
        return queries
    
    def extract_class_details(self, content, class_name):
        """Extract GraphQL class details including output type"""
        class_pattern = rf'class\s+{class_name}\(.*?\):(.*?)(?=class|\Z)'
        match = re.search(class_pattern, content, re.DOTALL)
        
        if match:
            class_body = match.group(1)
            
            # Look for Output class or return type
            output_pattern = r'class\s+Output\(.*?\):|Output\s*=\s*(\w+)'
            output_match = re.search(output_pattern, class_body)
            
            if output_match:
                return {'output_type': 'Custom Output Type'}
            
            # Look for simple return type
            return_pattern = r'return\s+(\w+)'
            return_match = re.search(return_pattern, class_body)
            if return_match:
                return {'output_type': return_match.group(1)}
        
        return {'output_type': 'Unknown'}
    
    def extract_input_types(self, content, class_name):
        """Extract input field information from mutation class"""
        class_pattern = rf'class\s+{class_name}\(.*?\):(.*?)(?=class|\Z)'
        match = re.search(class_pattern, content, re.DOTALL)
        
        input_info = {'fields': [], 'input_type': 'Unknown'}
        
        if match:
            class_body = match.group(1)
            
            # Look for Arguments class with multiple patterns
            args_patterns = [
                r'class\s+Arguments:(.*?)(?=class|def|\Z)',
                r'class\s+Arguments\([^)]*\):(.*?)(?=class|def|\Z)',
            ]
            
            args_body = None
            for pattern in args_patterns:
                args_match = re.search(pattern, class_body, re.DOTALL)
                if args_match:
                    args_body = args_match.group(1)
                    break
            
            if args_body:
                # Enhanced field extraction patterns
                field_patterns = [
                    r'(\w+)\s*=\s*graphene\.(\w+)\s*\((.*?)\)',
                    r'(\w+)\s*=\s*(\w+Field|String|Int|Boolean|Float|ID|DateTime)\s*\((.*?)\)',
                    r'(\w+)\s*=\s*(\w+)\s*\((.*?)\)',
                ]
                
                for pattern in field_patterns:
                    fields = re.findall(pattern, args_body, re.DOTALL)
                    for field_name, field_type, field_args in fields:
                        # Skip if already added
                        if any(f['name'] == field_name for f in input_info['fields']):
                            continue
                            
                        required = 'required=True' in field_args or 'nullable=False' in field_args
                        
                        # Clean field type
                        field_type = re.sub(r'Field$', '', field_type)
                        
                        input_info['fields'].append({
                            'name': field_name,
                            'type': field_type,
                            'required': required,
                            'description': self.generate_field_description(field_name)
                        })
                
                input_info['input_type'] = f'{class_name}Input'
        
        return input_info
    
    def generate_field_description(self, field_name):
        """Generate field description based on field name"""
        name_lower = field_name.lower()
        
        # Common field descriptions
        descriptions = {
            'id': 'Unique identifier',
            'name': 'Name of the entity',
            'title': 'Title or heading',
            'content': 'Main content or body text',
            'description': 'Detailed description',
            'email': 'Email address',
            'username': 'Username or handle',
            'password': 'Password for authentication',
            'rating': 'Rating score (1-5)',
            'review': 'Review text or feedback',
            'company_id': 'Company identifier',
            'user_id': 'User identifier',
            'community_id': 'Community identifier'
        }
        
        # Check for exact match
        if name_lower in descriptions:
            return descriptions[name_lower]
        
        # Check for partial matches
        for key, desc in descriptions.items():
            if key in name_lower:
                return desc
        
        # Default description
        return f'{field_name.replace("_", " ").title()} field'
    
    def infer_fields_from_name(self, class_name):
        """Infer common fields based on class name"""
        name_lower = class_name.lower()
        fields = []
        
        if 'create' in name_lower:
            if 'review' in name_lower:
                fields = [
                    {'name': 'rating', 'type': 'Int', 'required': True, 'description': 'Rating score (1-5)'},
                    {'name': 'review_text', 'type': 'String', 'required': False, 'description': 'Review content'},
                    {'name': 'title', 'type': 'String', 'required': False, 'description': 'Review title'},
                ]
            elif 'post' in name_lower:
                fields = [
                    {'name': 'content', 'type': 'String', 'required': True, 'description': 'Post content'},
                    {'name': 'title', 'type': 'String', 'required': False, 'description': 'Post title'},
                ]
            elif 'user' in name_lower:
                fields = [
                    {'name': 'username', 'type': 'String', 'required': True, 'description': 'Username'},
                    {'name': 'email', 'type': 'String', 'required': True, 'description': 'Email address'},
                ]
            elif 'company' in name_lower:
                fields = [
                    {'name': 'name', 'type': 'String', 'required': True, 'description': 'Company name'},
                    {'name': 'description', 'type': 'String', 'required': False, 'description': 'Company description'},
                ]
        elif 'update' in name_lower:
            fields = [
                {'name': 'id', 'type': 'ID', 'required': True, 'description': 'ID of item to update'},
            ]
        elif 'delete' in name_lower:
            fields = [
                {'name': 'id', 'type': 'ID', 'required': True, 'description': 'ID of item to delete'},
            ]
        
        return fields
    
    def extract_method_signature(self, content, method_name):
        """Extract method parameters and return info"""
        method_pattern = rf'def\s+resolve_{method_name}\((.*?)\):'
        match = re.search(method_pattern, content)
        
        if match:
            params_str = match.group(1)
            # Parse parameters (simplified)
            params = [p.strip() for p in params_str.split(',') if p.strip() and p.strip() not in ['self', 'info']]
            
            return {
                'parameters': params,
                'return_type': 'Query Result'
            }
        
        return {'parameters': [], 'return_type': 'Unknown'}
    
    def generate_example_input(self, mutation_name, fields):
        """Generate example input data for mutations"""
        if not fields:
            return {}
        
        example = {}
        
        for field in fields:
            field_name = field['name']
            field_type = field['type'].lower()
            
            # Generate appropriate example values based on field name and type
            if 'string' in field_type or 'char' in field_type:
                if 'email' in field_name.lower():
                    example[field_name] = "user@example.com"
                elif 'name' in field_name.lower():
                    example[field_name] = "John Doe"
                elif 'content' in field_name.lower() or 'description' in field_name.lower():
                    example[field_name] = "Sample content text"
                elif 'title' in field_name.lower():
                    example[field_name] = "Sample Title"
                elif 'username' in field_name.lower():
                    example[field_name] = "johndoe123"
                elif 'password' in field_name.lower():
                    example[field_name] = "securePassword123"
                else:
                    example[field_name] = f"sample_{field_name}"
                    
            elif 'int' in field_type or 'id' in field_type:
                if 'id' in field_name.lower():
                    example[field_name] = "clx123456789"
                elif 'rating' in field_name.lower():
                    example[field_name] = 5
                else:
                    example[field_name] = 123
                    
            elif 'bool' in field_type:
                example[field_name] = True
                
            elif 'float' in field_type:
                example[field_name] = 10.5
                
            else:
                example[field_name] = f"<{field_type}>"
        
        return example
    
    def generate_query_example(self, query_name, parameters):
        """Generate example GraphQL query"""
        params_str = ""
        if parameters:
            param_examples = []
            for param in parameters:
                if 'id' in param.lower():
                    param_examples.append(f'{param}: "clx123456789"')
                elif 'limit' in param.lower():
                    param_examples.append(f'{param}: 10')
                elif 'offset' in param.lower():
                    param_examples.append(f'{param}: 0')
                else:
                    param_examples.append(f'{param}: "example_value"')
            
            if param_examples:
                params_str = f"({', '.join(param_examples)})"
        
        return f"""query {{
  {query_name}{params_str} {{
    id
    # Add other fields as needed
  }}
}}"""

    def generate_mutation_example(self, mutation_name, fields):
        """Generate example GraphQL mutation"""
        if not fields:
            return f"""mutation {{
  {mutation_name} {{
    id
    # Add other return fields
  }}
}}"""
        
        input_fields = []
        for field in fields[:5]:  # Show first 5 fields to avoid too long examples
            field_name = field['name']
            field_type = field['type'].lower()
            
            # Generate example values
            if 'string' in field_type or 'char' in field_type:
                if 'email' in field_name.lower():
                    example_val = '"user@example.com"'
                elif 'name' in field_name.lower():
                    example_val = '"John Doe"'
                elif 'content' in field_name.lower():
                    example_val = '"Sample content text"'
                else:
                    example_val = f'"sample_{field_name}"'
            elif 'int' in field_type:
                if 'rating' in field_name.lower():
                    example_val = '5'
                else:
                    example_val = '123'
            elif 'bool' in field_type:
                example_val = 'true'
            elif 'float' in field_type:
                example_val = '10.5'
            else:
                example_val = f'"<{field_type}>"'
                
            input_fields.append(f'    {field_name}: {example_val}')
        
        input_block = ""
        if input_fields:
            input_block = f"""(input: {{
{chr(10).join(input_fields)}
  }})"""
        
        return f"""mutation {{
  {mutation_name}{input_block} {{
    id
    # Add other return fields
  }}
}}"""

    def extract_purpose_from_name(self, name):
        """Generate purpose description from API name"""
        # Common patterns and their meanings
        purposes = {
            'create_': 'Creates a new {}',
            'update_': 'Updates an existing {}',
            'delete_': 'Deletes/removes {}',
            'get_': 'Retrieves {}',
            'list_': 'Lists all {}',
            'send_': 'Sends {}',
            'add_': 'Adds {} to collection',
            'remove_': 'Removes {} from collection',
            'join_': 'Joins {}',
            'leave_': 'Leaves {}',
            'accept_': 'Accepts {}',
            'reject_': 'Rejects {}',
            'ban_': 'Bans user from {}',
            'unban_': 'Unbans user from {}',
            'mute_': 'Mutes {}',
            'unmute_': 'Unmutes {}',
            'pin_': 'Pins {} for highlighting',
            'unpin_': 'Unpins {}',
            'save_': 'Saves {} to collection',
            'unsave_': 'Removes {} from saved items',
            'share_': 'Shares {} with others',
            'view_': 'Records view activity for {}',
            'search_': 'Searches for {}',
            'filter_': 'Filters {} by criteria',
            'my_': 'Retrieves current user\'s {}'
        }
        
        for prefix, template in purposes.items():
            if name.startswith(prefix):
                entity = name[len(prefix):].replace('_', ' ')
                return template.format(entity)
        
        # Default fallback
        return f"Handles {name.replace('_', ' ')} operations"
    
    def scan_module(self, module_name):
        """Scan a module for GraphQL operations"""
        module_data = {
            'queries': {},
            'mutations': {},
            'description': f'{module_name.title()} module operations'
        }
        
        # Paths to check
        base_path = Path(module_name)
        graphql_path = base_path / 'graphql'
        
        # Check for mutations
        mutation_files = [
            graphql_path / 'mutations.py',
            graphql_path / 'mutation.py'
        ]
        
        for mutation_file in mutation_files:
            if mutation_file.exists():
                module_data['mutations'].update(
                    self.extract_mutations_from_file(mutation_file)
                )
        
        # Check for queries
        query_files = [
            graphql_path / 'queries.py',
            graphql_path / 'query.py'
        ]
        
        for query_file in query_files:
            if query_file.exists():
                module_data['queries'].update(
                    self.extract_queries_from_file(query_file)
                )
        
        return module_data
    
    def generate_documentation(self):
        """Generate comprehensive API documentation"""
        print("🔍 Scanning modules for API endpoints...")
        
        for module in self.modules:
            print(f"  📁 Scanning {module}...")
            self.api_reference['modules'][module] = self.scan_module(module)
        
        # Calculate totals
        total_endpoints = 0
        for module_data in self.api_reference['modules'].values():
            total_endpoints += len(module_data['queries']) + len(module_data['mutations'])
        
        self.api_reference['metadata']['total_endpoints'] = total_endpoints
        
        return self.api_reference
    
    def generate_markdown_output(self, api_data):
        """Generate enhanced markdown documentation with input types and examples"""
        md = f"""# OOUMPH API Reference
*Generated on {api_data['metadata']['generated_at']}*

## 📋 Overview
- **Project**: {api_data['metadata']['project']}
- **Version**: {api_data['metadata']['version']}  
- **Total Endpoints**: {api_data['metadata']['total_endpoints']}
- **Modules**: {len(api_data['modules'])}

---

## 🎯 Quick Reference for AI Development

This document provides a comprehensive overview of all available APIs in the OOUMPH platform. Each endpoint includes its purpose, input parameters, example data, and usage context for AI-assisted development.

---

"""
        
        for module_name, module_data in api_data['modules'].items():
            md += f"\n## 🔧 {module_name.upper()} Module\n"
            md += f"{module_data['description']}\n\n"
            
            # Queries section
            if module_data['queries']:
                md += f"### 📋 Queries ({len(module_data['queries'])})\n\n"
                for query_name, query_info in module_data['queries'].items():
                    md += f"#### `{query_name}`\n"
                    md += f"**Purpose**: {query_info['purpose']}\n\n"
                    
                    # Parameters
                    if query_info.get('parameters'):
                        md += "**Parameters**: "
                        md += ", ".join([f"`{p}`" for p in query_info['parameters']])
                        md += "\n\n"
                    
                    # Example query
                    if query_info.get('example_query'):
                        md += "**Example Query**:\n```graphql\n"
                        md += query_info['example_query']
                        md += "\n```\n\n"
                    
                    md += "---\n\n"
            
            # Mutations section  
            if module_data['mutations']:
                md += f"### ✏️ Mutations ({len(module_data['mutations'])})\n\n"
                for mutation_name, mutation_info in module_data['mutations'].items():
                    md += f"#### `{mutation_name}`\n"
                    md += f"**Purpose**: {mutation_info['purpose']}\n\n"
                    
                    # Input fields
                    if mutation_info.get('input_fields'):
                        md += "**Input Fields**:\n\n"
                        md += "| Field | Type | Required | Description |\n"
                        md += "|-------|------|----------|-------------|\n"
                        for field in mutation_info['input_fields']:
                            required_mark = "✅" if field.get('required') else "❌"
                            md += f"| `{field['name']}` | `{field['type']}` | {required_mark} | {field.get('description', 'No description')} |\n"
                        md += "\n"
                    
                    # Example input
                    if mutation_info.get('example_input'):
                        md += "**Example Input**:\n```json\n"
                        md += json.dumps(mutation_info['example_input'], indent=2)
                        md += "\n```\n\n"
                    
                    # GraphQL Example
                    if mutation_info.get('graphql_example'):
                        md += "**GraphQL Example**:\n```graphql\n"
                        md += mutation_info['graphql_example']
                        md += "\n```\n\n"
                    
                    md += "---\n\n"
            
            md += "---\n"
        
        # Add usage examples
        md += """
## 💡 AI Development Guidelines

### Common Patterns
1. **CRUD Operations**: Create, Read, Update, Delete patterns are consistent across modules
2. **User Context**: Most operations require authentication and user context
3. **Batch Operations**: Many modules support bulk operations for efficiency
4. **Real-time Updates**: GraphQL subscriptions available for live updates

### Authentication
```graphql
# Include JWT token in headers
Authorization: Bearer <your-jwt-token>

# Get token via mutation
mutation {
  tokenAuth(username: "user", password: "pass") {
    token
    user { id, username }
  }
}
```

### Module Relationships
- **auth_manager**: Central authentication for all operations
- **community**: Core social features, integrates with most other modules  
- **post**: Content creation, integrates with community, story, vibe_manager
- **connection**: Social networking, used by community and messaging
- **msg**: Direct messaging system
- **vibe_manager**: Reaction/like system across all content types

### Common Input Patterns
- **IDs**: Use format like `"clx123456789"` for entity references
- **Content**: Text fields support markdown and rich content
- **Boolean flags**: Use `true`/`false` for feature toggles
- **Timestamps**: ISO format recommended for date/time fields

### Security Considerations
- All mutations require proper authentication
- Role-based access control implemented per module
- Rate limiting applied to prevent abuse
- Input validation enforced server-side

---

*This documentation is auto-generated from the codebase with enhanced input type analysis. For the most current schema details, consider using GraphQL introspection queries.*
"""
        
        return md
    
    def save_documentation(self, output_file='api_reference.md'):
        """Generate and save the complete documentation"""
        print("🚀 Starting enhanced API documentation generation...")
        
        api_data = self.generate_documentation()
        markdown_content = self.generate_markdown_output(api_data)
        
        # Save markdown file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(markdown_content)
        
        # Save JSON file for programmatic access
        json_file = output_file.replace('.md', '.json')
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(api_data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ Enhanced documentation generated successfully!")
        print(f"📄 Markdown: {output_file}")
        print(f"📊 JSON: {json_file}")
        print(f"🎯 Total endpoints documented: {api_data['metadata']['total_endpoints']}")
        
        # Print summary of enhancements
        mutations_with_inputs = 0
        mutations_without_inputs = 0
        for module_data in api_data['modules'].values():
            for mutation in module_data['mutations'].values():
                if mutation.get('input_fields'):
                    mutations_with_inputs += 1
                else:
                    mutations_without_inputs += 1
        
        print(f"🔍 Enhanced features:")
        print(f"   - {mutations_with_inputs} mutations with input analysis")
        print(f"   - {mutations_without_inputs} mutations using inferred inputs")
        print(f"   - Example input data generated for all mutations")
        print(f"   - GraphQL examples provided for all operations")
        
        return output_file, json_file

if __name__ == "__main__":
    generator = APIDocumentationGenerator()
    md_file, json_file = generator.save_documentation()