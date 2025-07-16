from django.http import HttpResponse
from django.middleware.csrf import get_token
from django.contrib.admin.views.decorators import staff_member_required
import json

@staff_member_required
def docs_home(request):
    """
    Professional API documentation landing page
    """
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OOUMPH API Documentation</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                background: #f8f9fa;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 60px 0;
                text-align: center;
            }
            .header h1 { font-size: 3em; margin-bottom: 15px; font-weight: 300; }
            .header p { font-size: 1.1em; opacity: 0.9; max-width: 500px; margin: 0 auto; }
            
            .container { max-width: 1000px; margin: 0 auto; padding: 0 20px; }
            
            .nav-section {
                background: white;
                padding: 50px 0;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            
            .nav-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
                gap: 30px;
                margin-top: 30px;
            }
            
            .nav-card {
                background: white;
                border-radius: 12px;
                padding: 30px;
                text-decoration: none;
                color: inherit;
                transition: all 0.3s ease;
                border: 1px solid #e2e8f0;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            }
            
            .nav-card:hover {
                transform: translateY(-5px);
                box-shadow: 0 10px 25px rgba(0,0,0,0.15);
                text-decoration: none;
                color: inherit;
            }
            
            .nav-card .icon {
                font-size: 2.5em;
                margin-bottom: 15px;
                display: block;
            }
            
            .nav-card h3 {
                font-size: 1.3em;
                margin-bottom: 12px;
                color: #2d3748;
            }
            
            .nav-card p {
                color: #4a5568;
                line-height: 1.5;
                font-size: 0.95em;
            }
            
            .api-overview {
                background: #f8f9fa;
                padding: 50px 0;
            }
            
            .version-cards {
                display: grid;
                grid-template-columns: 1fr 1fr;
                gap: 30px;
                margin-top: 30px;
            }
            
            .version-card {
                background: white;
                border-radius: 10px;
                padding: 30px;
                border-left: 4px solid #667eea;
            }
            
            .version-card h3 {
                font-size: 1.4em;
                margin-bottom: 10px;
                color: #2d3748;
            }
            
            .version-card .status {
                display: inline-block;
                padding: 4px 12px;
                border-radius: 15px;
                font-size: 0.8em;
                font-weight: 500;
                margin-bottom: 15px;
            }
            
            .status.stable {
                background: #c6f6d5;
                color: #22543d;
            }
            
            .status.latest {
                background: #bee3f8;
                color: #2a4365;
            }
            
            .endpoint-info {
                font-family: monospace;
                background: #f7fafc;
                padding: 8px 12px;
                border-radius: 4px;
                font-size: 0.9em;
                color: #2d3748;
                margin: 10px 0;
            }
            
            .quick-access {
                background: white;
                padding: 40px 0;
                text-align: center;
            }
            
            .quick-links {
                display: flex;
                justify-content: center;
                gap: 20px;
                margin-top: 25px;
            }
            
            .quick-link {
                display: inline-block;
                padding: 12px 24px;
                background: #667eea;
                color: white;
                text-decoration: none;
                border-radius: 6px;
                font-weight: 500;
                transition: background 0.3s ease;
            }
            
            .quick-link:hover {
                background: #5a67d8;
                text-decoration: none;
                color: white;
            }
            
            @media (max-width: 768px) {
                .version-cards {
                    grid-template-columns: 1fr;
                    gap: 20px;
                }
                .nav-grid {
                    grid-template-columns: 1fr;
                }
                .header h1 {
                    font-size: 2.2em;
                }
                .quick-links {
                    flex-direction: column;
                    align-items: center;
                }
            }
        </style>
    </head>
    <body>
        <div class="header">
            <div class="container">
                <h1>🚀 OOUMPH API</h1>
                <p>Internal GraphQL API Documentation</p>
            </div>
        </div>

        <div class="nav-section">
            <div class="container">
                <h2 style="text-align: center; font-size: 2em; margin-bottom: 15px; color: #2d3748;">Documentation</h2>
                <p style="text-align: center; font-size: 1em; color: #4a5568; max-width: 500px; margin: 0 auto;">Access API reference and integration guides</p>
                
                <div class="nav-grid">
                    <a href="/docs/reference/" class="nav-card">
                        <span class="icon">📖</span>
                        <h3>API Reference</h3>
                        <p>Complete documentation of all queries, mutations, and types with parameters and examples.</p>
                    </a>
                    
                    <a href="/docs/guide/" class="nav-card">
                        <span class="icon">🎯</span>
                        <h3>Integration Guide</h3>
                        <p>Step-by-step guides for authentication, common operations, and best practices.</p>
                    </a>
                    
                    <a href="/graphql/" class="nav-card" target="_blank">
                        <span class="icon">🎮</span>
                        <h3>GraphiQL Playground</h3>
                        <p>Interactive interface for testing queries and exploring the schema in real-time.</p>
                    </a>
                </div>
            </div>
        </div>

        <div class="api-overview">
            <div class="container">
                <h2 style="text-align: center; font-size: 2em; margin-bottom: 20px; color: #2d3748;">API Endpoints</h2>
                
                <div class="version-cards">
                    <div class="version-card">
                        <span class="status stable">Stable</span>
                        <h3>Version 1</h3>
                        <div class="endpoint-info">/graphql/</div>
                        <p>Production-ready API with core functionality. Recommended for stable integrations.</p>
                        <p style="margin-top: 15px;">
                            <a href="/docs/reference/?version=v1" style="color: #667eea; text-decoration: none; font-weight: 500;">📖 V1 Docs →</a>
                        </p>
                    </div>
                    
                    <div class="version-card">
                        <span class="status latest">Latest</span>
                        <h3>Version 2</h3>
                        <div class="endpoint-info">/graphql/v2/</div>
                        <p>Enhanced version with additional features and improved performance.</p>
                        <p style="margin-top: 15px;">
                            <a href="/docs/reference/?version=v2" style="color: #667eea; text-decoration: none; font-weight: 500;">📖 V2 Docs →</a>
                        </p>
                    </div>
                </div>
            </div>
        </div>

        <div class="quick-access">
            <div class="container">
                <h3 style="margin-bottom: 10px; color: #2d3748;">Quick Access</h3>
                <p style="color: #4a5568; margin-bottom: 20px;">Jump directly to commonly used resources</p>
                <div class="quick-links">
                    <a href="/docs/reference/" class="quick-link">📖 Browse API</a>
                    <a href="/graphql/" class="quick-link" target="_blank">🎮 Test Queries</a>
                    <a href="/docs/guide/" class="quick-link">🎯 Get Started</a>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)

@staff_member_required
def api_reference(request):
    """
    Comprehensive API reference documentation
    """
    version = request.GET.get('version', 'v1')
    endpoint = '/graphql/v2/' if version == 'v2' else '/graphql/'
    
    html = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OOUMPH API Reference - {version.upper()}</title>
        <style>
            * {{ margin: 0; padding: 0; box-sizing: border-box; }}
            body {{ 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                background: #f8f9fa;
            }}
            
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px 0;
            }}
            
            .header-content {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 0 20px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            }}
            
            .header h1 {{
                font-size: 2em;
                font-weight: 300;
            }}
            
            .header-controls {{
                display: flex;
                gap: 15px;
                align-items: center;
            }}
            
            .version-selector select {{
                padding: 8px 12px;
                border-radius: 6px;
                border: none;
                background: rgba(255,255,255,0.2);
                color: white;
                font-size: 14px;
            }}
            
            .header-link {{
                color: rgba(255,255,255,0.9);
                text-decoration: none;
                padding: 8px 16px;
                border-radius: 4px;
                transition: background 0.3s ease;
            }}
            
            .header-link:hover {{
                background: rgba(255,255,255,0.2);
                color: white;
                text-decoration: none;
            }}
            
            .main-content {{
                max-width: 1200px;
                margin: 0 auto;
                padding: 40px 20px;
                display: grid;
                grid-template-columns: 250px 1fr;
                gap: 40px;
            }}
            
            .sidebar {{
                background: white;
                border-radius: 8px;
                padding: 30px;
                height: fit-content;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                position: sticky;
                top: 20px;
            }}
            
            .sidebar h3 {{
                margin-bottom: 20px;
                color: #2d3748;
                font-size: 1.2em;
            }}
            
            .sidebar ul {{
                list-style: none;
            }}
            
            .sidebar li {{
                margin-bottom: 8px;
            }}
            
            .sidebar a {{
                color: #4a5568;
                text-decoration: none;
                padding: 8px 12px;
                border-radius: 4px;
                display: block;
                transition: all 0.3s ease;
            }}
            
            .sidebar a:hover,
            .sidebar a.active {{
                background: #667eea;
                color: white;
                text-decoration: none;
            }}
            
            .content {{
                background: white;
                border-radius: 8px;
                padding: 40px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            
            .content h2 {{
                color: #2d3748;
                margin-bottom: 20px;
                font-size: 2em;
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 10px;
            }}
            
            .content h3 {{
                color: #2d3748;
                margin: 30px 0 15px 0;
                font-size: 1.3em;
            }}
            
            .endpoint-section {{
                margin-bottom: 40px;
                padding: 20px;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background: #f8f9fa;
            }}
            
            .endpoint-header {{
                display: flex;
                align-items: center;
                margin-bottom: 15px;
            }}
            
            .method-badge {{
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 0.9em;
                font-weight: 500;
                margin-right: 15px;
            }}
            
            .query-badge {{
                background: #c6f6d5;
                color: #22543d;
            }}
            
            .mutation-badge {{
                background: #fed7d7;
                color: #742a2a;
            }}
            
            .description {{
                color: #4a5568;
                margin-bottom: 20px;
                line-height: 1.6;
            }}
            
            .params-table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            
            .params-table th,
            .params-table td {{
                text-align: left;
                padding: 12px;
                border-bottom: 1px solid #e2e8f0;
            }}
            
            .params-table th {{
                background: #f7fafc;
                font-weight: 600;
                color: #2d3748;
            }}
            
            .type-info {{
                color: #805ad5;
                font-family: monospace;
                font-size: 0.9em;
            }}
            
            .example-section {{
                background: #2d3748;
                color: #e2e8f0;
                padding: 20px;
                border-radius: 8px;
                margin: 20px 0;
            }}
            
            .example-section h4 {{
                color: white;
                margin-bottom: 15px;
            }}
            
            .code-block {{
                background: #1a202c;
                padding: 15px;
                border-radius: 4px;
                font-family: monospace;
                overflow-x: auto;
                white-space: pre-wrap;
            }}
            
            @media (max-width: 768px) {{
                .main-content {{
                    grid-template-columns: 1fr;
                    gap: 20px;
                }}
                .sidebar {{
                    order: 2;
                    position: static;
                }}
            }}
        </style>
        <script>
            // We'll load schema data dynamically
            let schemaData = null;
            
            async function loadSchema() {{
                try {{
                    const response = await fetch('{endpoint}', {{
                        method: 'POST',
                        headers: {{
                            'Content-Type': 'application/json',
                        }},
                        body: JSON.stringify({{
                            query: `
                                query IntrospectionQuery {{
                                    __schema {{
                                        queryType {{ name }}
                                        mutationType {{ name }}
                                        types {{
                                            name
                                            description
                                            kind
                                            fields(includeDeprecated: true) {{
                                                name
                                                description
                                                args {{
                                                    name
                                                    description
                                                    type {{
                                                        name
                                                        kind
                                                        ofType {{
                                                            name
                                                            kind
                                                        }}
                                                    }}
                                                    defaultValue
                                                }}
                                                type {{
                                                    name
                                                    kind
                                                    ofType {{
                                                        name
                                                        kind
                                                    }}
                                                }}
                                                isDeprecated
                                                deprecationReason
                                            }}
                                            inputFields {{
                                                name
                                                description
                                                type {{
                                                    name
                                                    kind
                                                    ofType {{
                                                        name
                                                        kind
                                                    }}
                                                }}
                                                defaultValue
                                            }}
                                        }}
                                    }}
                                }}
                            `
                        }})
                    }});
                    
                    const result = await response.json();
                    schemaData = result.data;
                    renderDocumentation();
                }} catch (error) {{
                    console.error('Failed to load schema:', error);
                    document.getElementById('content').innerHTML = `
                        <div style="text-align: center; padding: 60px; color: #e53e3e;">
                            <h2>⚠️ Unable to Load API Schema</h2>
                            <p>Please ensure the GraphQL endpoint is accessible.</p>
                            <a href="{endpoint}" target="_blank" style="color: #667eea;">Try GraphiQL →</a>
                        </div>
                    `;
                }}
            }}
            
            function renderDocumentation() {{
                if (!schemaData || !schemaData.__schema) return;
                
                const schema = schemaData.__schema;
                const types = schema.types;
                
                // Find Query and Mutation types
                const queryType = types.find(t => t.name === schema.queryType?.name);
                const mutationType = types.find(t => t.name === schema.mutationType?.name);
                
                let sidebarHTML = '';
                let contentHTML = '';
                
                // Generate sidebar
                sidebarHTML += '<h3>📖 API Reference</h3><ul>';
                sidebarHTML += '<li><a href="#overview" onclick="showSection(\\'overview\\')">Overview</a></li>';
                
                if (queryType?.fields) {{
                    sidebarHTML += '<li><a href="#queries" onclick="showSection(\\'queries\\')">Queries (' + queryType.fields.length + ')</a></li>';
                }}
                
                if (mutationType?.fields) {{
                    sidebarHTML += '<li><a href="#mutations" onclick="showSection(\\'mutations\\')">Mutations (' + mutationType.fields.length + ')</a></li>';
                }}
                
                sidebarHTML += '<li><a href="#types" onclick="showSection(\\'types\\')">Types</a></li>';
                sidebarHTML += '</ul>';
                
                document.getElementById('sidebar').innerHTML = sidebarHTML;
                
                // Generate content sections
                contentHTML += generateOverviewSection(schema);
                
                if (queryType?.fields) {{
                    contentHTML += generateQueriesSection(queryType.fields);
                }}
                
                if (mutationType?.fields) {{
                    contentHTML += generateMutationsSection(mutationType.fields);
                }}
                
                contentHTML += generateTypesSection(types);
                
                document.getElementById('content').innerHTML = contentHTML;
            }}
            
            function generateOverviewSection(schema) {{
                return `
                    <div id="overview">
                        <h2>🚀 API Overview</h2>
                        <div class="description">
                            <p>Welcome to the OOUMPH GraphQL API documentation. This API provides comprehensive access to community management, user authentication, and social features.</p>
                            
                          
                            
                            <h3>📡 Endpoint Information</h3>
                            <div class="endpoint-section">
                                <p><strong>GraphQL Endpoint:</strong> <code>{endpoint}</code></p>
                                <p><strong>Method:</strong> POST</p>
                                <p><strong>Content-Type:</strong> application/json</p>
                            </div>
                        </div>
                    </div>
                `;
            }}
            
            function generateQueriesSection(queries) {{
                let html = '<div id="queries"><h2>🔍 Queries</h2>';
                html += '<p class="description">Queries are used to fetch data from the API. They are read-only operations.</p>';
                
                queries.forEach(query => {{
                    if (query.name.startsWith('__')) return; // Skip introspection fields
                    
                    html += `
                        <div class="endpoint-section">
                            <div class="endpoint-header">
                                <span class="method-badge query-badge">QUERY</span>
                                <h3>${{query.name}}</h3>
                            </div>
                            ${{query.description ? `<div class="description">${{query.description}}</div>` : ''}}
                    `;
                    
                    if (query.args && query.args.length > 0) {{
                        html += `
                            <h4>Parameters</h4>
                            <table class="params-table">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>Type</th>
                                        <th>Description</th>
                                    </tr>
                                </thead>
                                <tbody>
                        `;
                        
                        query.args.forEach(arg => {{
                            const typeName = arg.type.name || arg.type.ofType?.name || 'Unknown';
                            html += `
                                <tr>
                                    <td><strong>${{arg.name}}</strong></td>
                                    <td class="type-info">${{typeName}}</td>
                                    <td>${{arg.description || 'No description available'}}</td>
                                </tr>
                            `;
                        }});
                        
                        html += '</tbody></table>';
                    }}
                    
                    const returnType = query.type.name || query.type.ofType?.name || 'Unknown';
                    html += `
                        <p><strong>Returns:</strong> <span class="type-info">${{returnType}}</span></p>
                        
                        <div class="example-section">
                            <h4>📝 Example Query</h4>
                            <div class="code-block">query {{
  ${{query.name}}${{query.args.length > 0 ? '(' + query.args.map(arg => arg.name + ': $' + arg.name).join(', ') + ')' : ''}} {{
    # Add your fields here
  }}
}}</div>
                        </div>
                    </div>
                    `;
                }});
                
                html += '</div>';
                return html;
            }}
            
            function generateMutationsSection(mutations) {{
                let html = '<div id="mutations"><h2>✏️ Mutations</h2>';
                html += '<p class="description">Mutations are used to modify data in the API. They can create, update, or delete resources.</p>';
                
                mutations.forEach(mutation => {{
                    if (mutation.name.startsWith('__')) return;
                    
                    html += `
                        <div class="endpoint-section">
                            <div class="endpoint-header">
                                <span class="method-badge mutation-badge">MUTATION</span>
                                <h3>${{mutation.name}}</h3>
                            </div>
                            ${{mutation.description ? `<div class="description">${{mutation.description}}</div>` : ''}}
                    `;
                    
                    if (mutation.args && mutation.args.length > 0) {{
                        html += `
                            <h4>Parameters</h4>
                            <table class="params-table">
                                <thead>
                                    <tr>
                                        <th>Name</th>
                                        <th>Type</th>
                                        <th>Description</th>
                                    </tr>
                                </thead>
                                <tbody>
                        `;
                        
                        mutation.args.forEach(arg => {{
                            const typeName = arg.type.name || arg.type.ofType?.name || 'Unknown';
                            html += `
                                <tr>
                                    <td><strong>${{arg.name}}</strong></td>
                                    <td class="type-info">${{typeName}}</td>
                                    <td>${{arg.description || 'No description available'}}</td>
                                </tr>
                            `;
                        }});
                        
                        html += '</tbody></table>';
                    }}
                    
                    const returnType = mutation.type.name || mutation.type.ofType?.name || 'Unknown';
                    html += `
                        <p><strong>Returns:</strong> <span class="type-info">${{returnType}}</span></p>
                        
                        <div class="example-section">
                            <h4>📝 Example Mutation</h4>
                            <div class="code-block">mutation {{
  ${{mutation.name}}${{mutation.args.length > 0 ? '(' + mutation.args.map(arg => arg.name + ': $' + arg.name).join(', ') + ')' : ''}} {{
    # Add your fields here
  }}
}}</div>
                        </div>
                    </div>
                    `;
                }});
                
                html += '</div>';
                return html;
            }}
            
            function generateTypesSection(types) {{
                let html = '<div id="types"><h2>📋 Types</h2>';
                html += '<p class="description">GraphQL types define the structure of data that can be queried or mutated.</p>';
                
                const customTypes = types.filter(t => 
                    !t.name.startsWith('__') && 
                    t.kind === 'OBJECT' && 
                    t.name !== 'Query' && 
                    t.name !== 'Mutation'
                ).slice(0, 10); // Show first 10 types
                
                customTypes.forEach(type => {{
                    html += `
                        <div class="endpoint-section">
                            <h3>${{type.name}}</h3>
                            ${{type.description ? `<div class="description">${{type.description}}</div>` : ''}}
                    `;
                    
                    if (type.fields && type.fields.length > 0) {{
                        html += `
                            <table class="params-table">
                                <thead>
                                    <tr>
                                        <th>Field</th>
                                        <th>Type</th>
                                        <th>Description</th>
                                    </tr>
                                </thead>
                                <tbody>
                        `;
                        
                        type.fields.forEach(field => {{
                            const typeName = field.type.name || field.type.ofType?.name || 'Unknown';
                            html += `
                                <tr>
                                    <td><strong>${{field.name}}</strong></td>
                                    <td class="type-info">${{typeName}}</td>

                                    <td>${{field.description || 'No description available'}}</td>
                                </tr>
                            `;
                        }});
                        
                        html += '</tbody></table>';
                    }}
                    
                    html += '</div>';
                }});
                
                if (customTypes.length === 10) {{
                    html += '<p style="text-align: center; margin: 30px 0; color: #4a5568;"><em>Showing first 10 types. Use GraphiQL for complete type exploration.</em></p>';
                }}
                
                html += '</div>';
                return html;
            }}
            
            function showSection(sectionId) {{
                // Update active link
                document.querySelectorAll('.sidebar a').forEach(link => {{
                    link.classList.remove('active');
                }});
                document.querySelector(`[href="#${{sectionId}}"]`).classList.add('active');
                
                // Scroll to section
                document.getElementById(sectionId).scrollIntoView({{ behavior: 'smooth' }});
            }}
            
            function switchVersion(version) {{
                window.location.href = `/docs/reference/?version=${{version}}`;
            }}
            
            // Load schema when page loads
            window.addEventListener('load', loadSchema);
        </script>
    </head>
    <body>
        <div class="header">
            <div class="header-content">
                <h1>📖 API Reference - {version.upper()}</h1>
                <div class="header-controls">
                    <select onchange="switchVersion(this.value)">
                        <option value="v1" {'selected' if version == 'v1' else ''}>Version 1</option>
                        <option value="v2" {'selected' if version == 'v2' else ''}>Version 2</option>
                    </select>
                    <a href="/docs/" class="header-link">🏠 Home</a>
                    <a href="{endpoint}" class="header-link" target="_blank">🎮 GraphiQL</a>
                </div>
            </div>
        </div>

        <div class="main-content">
            <div class="sidebar" id="sidebar">
                <div style="text-align: center; color: #4a5568;">
                    Loading navigation...
                </div>
            </div>
            
            <div class="content" id="content">
                <div style="text-align: center; padding: 60px; color: #4a5568;">
                    <h2>📡 Loading API Documentation...</h2>
                    <p>Fetching schema information from your GraphQL endpoint.</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)

@staff_member_required
def integration_guide(request):
    """
    Integration guide for developers
    """
    html = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>OOUMPH API Integration Guide</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { 
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                line-height: 1.6;
                color: #333;
                background: #f8f9fa;
            }
            
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 60px 0;
                text-align: center;
            }
            
            .header h1 { font-size: 3em; margin-bottom: 20px; font-weight: 300; }
            .header p { font-size: 1.2em; opacity: 0.9; }
            
            .container { max-width: 1000px; margin: 0 auto; padding: 40px 20px; }
            
            .guide-section {
                background: white;
                border-radius: 12px;
                padding: 40px;
                margin: 30px 0;
                box-shadow: 0 4px 6px rgba(0,0,0,0.05);
            }
            
            .guide-section h2 {
                color: #2d3748;
                margin-bottom: 20px;
                font-size: 2em;
                border-bottom: 3px solid #667eea;
                padding-bottom: 10px;
            }
            
            .guide-section h3 {
                color: #2d3748;
                margin: 30px 0 15px 0;
                font-size: 1.4em;
            }
            
            .step-list {
                counter-reset: step-counter;
                list-style: none;
                margin: 30px 0;
            }
            
            .step-list li {
                counter-increment: step-counter;
                margin: 20px 0;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 8px;
                border-left: 4px solid #667eea;
                position: relative;
            }
            
            .step-list li::before {
                content: counter(step-counter);
                position: absolute;
                left: -15px;
                top: 15px;
                background: #667eea;
                color: white;
                width: 30px;
                height: 30px;
                border-radius: 50%;
                display: flex;
                align-items: center;
                justify-content: center;
                font-weight: bold;
                font-size: 0.9em;
            }
            
            .code-example {
                background: #2d3748;
                color: #e2e8f0;
                padding: 20px;
                border-radius: 8px;
                font-family: monospace;
                overflow-x: auto;
                margin: 15px 0;
                position: relative;
            }
            
            .code-title {
                background: #4a5568;
                color: white;
                padding: 8px 15px;
                border-radius: 4px 4px 0 0;
                font-size: 0.9em;
                font-weight: 500;
                margin: -20px -20px 15px -20px;
            }
            
            .feature-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 30px;
                margin: 30px 0;
            }
            
            .feature-card {
                background: #f8f9fa;
                padding: 30px;
                border-radius: 8px;
                border-left: 4px solid #667eea;
            }
            
            .feature-card h4 {
                color: #2d3748;
                margin-bottom: 15px;
                font-size: 1.2em;
            }
            
            .feature-card ul {
                margin: 15px 0;
                padding-left: 20px;
            }
            
            .warning-box {
                background: #fff5f5;
                border: 1px solid #fed7d7;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                border-left: 4px solid #f56565;
            }
            
            .info-box {
                background: #ebf8ff;
                border: 1px solid #bee3f8;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
                border-left: 4px solid #4299e1;
            }
            
            .nav-links {
                display: flex;
                justify-content: space-between;
                margin: 40px 0;
                padding: 20px 0;
                border-top: 1px solid #e2e8f0;
            }
            
            .nav-link {
                color: #667eea;
                text-decoration: none;
                padding: 10px 20px;
                border-radius: 6px;
                transition: background 0.3s ease;
            }
            
            .nav-link:hover {
                background: #667eea;
                color: white;
                text-decoration: none;
            }
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 Integration Guide</h1>
            <p>Step-by-step guide to integrate with the OOUMPH API</p>
        </div>

        <div class="container">
            <div class="guide-section">
                <h2>🚀 Getting Started</h2>
                <p>This guide will walk you through integrating with the OOUMPH GraphQL API. Whether you're building a web application, mobile app, or server-side integration, these steps will get you started quickly.</p>
                
                <div class="info-box">
                    <h4>💡 What You'll Learn</h4>
                    <ul>
                        <li>How to authenticate with the API</li>
                        <li>Making your first GraphQL queries</li>
                        <li>Working with communities and users</li>
                        <li>Handling files and media uploads</li>
                        <li>Best practices and error handling</li>
                    </ul>
                </div>
            </div>

            <div class="guide-section">
                <h2>🔐 Authentication</h2>
                <p>The OOUMPH API uses JWT (JSON Web Tokens) for authentication. Here's how to get started:</p>
                
                <ol class="step-list">
                    <li>
                        <h3>Get Your Access Token</h3>
                        <p>First, you'll need to authenticate and obtain a JWT token:</p>
                        <div class="code-example">
                            <div class="code-title">GraphQL Mutation</div>
mutation LoginUser {
  tokenAuth(email: "user@example.com", password: "yourpassword") {
    token
    refreshToken
    user {
      uid
      username
      email
    }
  }
}
                        </div>
                    </li>
                    
                    <li>
                        <h3>Include Token in Requests</h3>
                        <p>Add the JWT token to your request headers:</p>
                        <div class="code-example">
                            <div class="code-title">HTTP Headers</div>
Authorization: Bearer YOUR_JWT_TOKEN_HERE
Content-Type: application/json
                        </div>
                    </li>
                    
                    <li>
                        <h3>Refresh Your Token</h3>
                        <p>When your token expires, use the refresh token to get a new one:</p>
                        <div class="code-example">
                            <div class="code-title">GraphQL Mutation</div>
mutation RefreshToken {
  refreshToken(refreshToken: "YOUR_REFRESH_TOKEN") {
    token
    refreshToken
  }
}
                        </div>
                    </li>
                </ol>
            </div>

            <div class="guide-section">
                <h2>🏘️ Working with Communities</h2>
                <p>Communities are the core feature of the OOUMPH platform. Here's how to work with them:</p>
                
                <div class="feature-grid">
                    <div class="feature-card">
                        <h4>📝 Create a Community</h4>
                        <div class="code-example">
mutation CreateCommunity {
  createCommunity(input: {
    name: "My Community"
    description: "A great place to connect"
    communityType: INTEREST_GROUP
    communityCircle: INNER
    memberUid: ["user1", "user2"]
  }) {
    success
    message
    community {
      uid
      name
    }
  }
}
                        </div>
                    </div>
                    
                    <div class="feature-card">
                        <h4>🔍 Get Communities</h4>
                        <div class="code-example">
query GetMyCommunities {
  myCommunity {
    uid
    name
    description
    numberOfMembers
    groupIconUrl {
      url
    }
  }
}
                        </div>
                    </div>
                </div>
            </div>

            <div class="guide-section">
                <h2>👥 User Management</h2>
                <p>Manage user profiles, connections, and interactions:</p>
                
                <h3>Get User Profile</h3>
                <div class="code-example">
query GetUserProfile {
  userProfile(uid: "user_uid_here") {
    uid
    username
    email
    profile {
      bio
      profilePic {
        url
      }
    }
  }
}
                </div>

                <h3>Update User Profile</h3>
                <div class="code-example">
mutation UpdateProfile {
  updateProfile(input: {
    bio: "Updated bio"
    designation: "Software Developer"
  }) {
    success
    message
  }
}
                </div>
            </div>

            <div class="guide-section">
                <h2>📁 File Uploads</h2>
                <p>Handle media and file uploads in your application:</p>
                
                <ol class="step-list">
                    <li>
                        <h3>Upload File</h3>
                        <p>Use the upload endpoint to upload files:</p>
                        <div class="code-example">
                            <div class="code-title">HTTP POST to /upload/</div>
POST /upload/
Content-Type: multipart/form-data

{
  "file": [your_file],
  "file_type": "image"
}
                        </div>
                    </li>
                    
                    <li>
                        <h3>Use File ID</h3>
                        <p>Use the returned file ID in your GraphQL mutations:</p>
                        <div class="code-example">
mutation UpdateCommunity {
  updateCommunity(input: {
    uid: "community_uid"
    groupIconId: "file_id_from_upload"
  }) {
    success
    message
  }
}
                        </div>
                    </li>
                </ol>
            </div>

            <div class="guide-section">
                <h2>⚠️ Error Handling</h2>
                <p>Properly handle errors and edge cases in your application:</p>
                
                <div class="warning-box">
                    <h4>🚨 Common Error Scenarios</h4>
                    <ul>
                        <li><strong>Authentication Failed:</strong> Check your JWT token</li>
                        <li><strong>Permission Denied:</strong> Verify user has required permissions</li>
                        <li><strong>Invalid Input:</strong> Validate input data before sending</li>
                        <li><strong>Rate Limiting:</strong> Implement proper retry logic</li>
                    </ul>
                </div>

                <h3>Example Error Response</h3>
                <div class="code-example">
{
  "errors": [
    {
      "message": "Authentication required",
      "locations": [{"line": 2, "column": 3}],
      "path": ["myCommunity"]
    }
  ],
  "data": {
    "myCommunity": null
  }
}
                </div>
            </div>

            <div class="guide-section">
                <h2>✅ Best Practices</h2>
                
                <div class="feature-grid">
                    <div class="feature-card">
                        <h4>🔄 Query Optimization</h4>
                        <ul>
                            <li>Request only the fields you need</li>
                            <li>Use pagination for large datasets</li>
                            <li>Batch multiple operations when possible</li>
                            <li>Cache responses appropriately</li>
                        </ul>
                    </div>
                    
                    <div class="feature-card">
                        <h4>🛡️ Security</h4>
                        <ul>
                            <li>Always validate user inputs</li>
                            <li>Store JWT tokens securely</li>
                            <li>Use HTTPS in production</li>
                            <li>Implement proper error handling</li>
                        </ul>
                    </div>
                    
                    <div class="feature-card">
                        <h4>📱 Performance</h4>
                        <ul>
                            <li>Use connection pooling</li>
                            <li>Implement request timeouts</li>
                            <li>Monitor API usage</li>
                            <li>Handle offline scenarios</li>
                        </ul>
                    </div>
                    
                    <div class="feature-card">
                        <h4>🧪 Testing</h4>
                        <ul>
                            <li>Test with GraphiQL first</li>
                            <li>Use mock data for development</li>
                            <li>Test error scenarios</li>
                            <li>Validate response schemas</li>
                        </ul>
                    </div>
                </div>
            </div>

            <div class="nav-links">
                <a href="/docs/" class="nav-link">← Back to Documentation</a>
                <a href="/docs/reference/" class="nav-link">API Reference →</a>
            </div>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html)