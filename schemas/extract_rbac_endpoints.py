#!/usr/bin/env python3
"""Extract RBAC/Security endpoints from Veeam API schema."""

import json
from pathlib import Path

def extract_rbac_endpoints(schema):
    """Extract all RBAC/security related endpoints."""

    rbac_endpoints = {}

    # Get all paths that start with /api/v1/security
    for path, methods in schema.get('paths', {}).items():
        if '/security/' in path:
            rbac_endpoints[path] = methods

    return rbac_endpoints

def format_endpoint_details(path, methods):
    """Format endpoint details for display."""

    print(f"\n{'='*80}")
    print(f"PATH: {path}")
    print('='*80)

    for method, details in methods.items():
        if method in ['parameters', 'summary', 'description']:
            continue

        print(f"\n[{method.upper()}]")

        # Summary and description
        if details.get('summary'):
            print(f"Summary: {details['summary']}")
        if details.get('description'):
            print(f"Description: {details['description']}")

        # Tags
        if details.get('tags'):
            print(f"Tags: {', '.join(details['tags'])}")

        # Parameters
        if details.get('parameters'):
            print("\nParameters:")
            for param in details['parameters']:
                if not param.get('name'):
                    continue
                required = " (required)" if param.get('required') else " (optional)"
                param_type = param.get('type', param.get('schema', {}).get('type', 'object'))
                print(f"  - {param['name']} ({param['in']}){required}: {param_type}")
                if param.get('description'):
                    print(f"      {param['description']}")

        # Request body
        if details.get('parameters'):
            for param in details['parameters']:
                if param.get('in') == 'body' and param.get('schema'):
                    print("\nRequest Body Schema:")
                    schema_ref = param['schema'].get('$ref', '')
                    if schema_ref:
                        print(f"  Schema: {schema_ref.split('/')[-1]}")
                    else:
                        print(f"  Schema: {json.dumps(param['schema'], indent=2)}")

        # Responses
        if details.get('responses'):
            print("\nResponses:")
            for status_code, response in details['responses'].items():
                print(f"  {status_code}: {response.get('description', 'No description')}")
                if response.get('schema'):
                    schema_ref = response['schema'].get('$ref', '')
                    if schema_ref:
                        print(f"      Schema: {schema_ref.split('/')[-1]}")
                    elif response['schema'].get('type') == 'array':
                        items_ref = response['schema'].get('items', {}).get('$ref', '')
                        if items_ref:
                            print(f"      Schema: Array of {items_ref.split('/')[-1]}")

        print()

def main():
    """Main function."""
    base_dir = Path(__file__).parent
    schema_path = base_dir / "swagger_v1.3-rev1.json"

    print("Loading schema...")
    with open(schema_path, 'r') as f:
        schema = json.load(f)

    rbac_endpoints = extract_rbac_endpoints(schema)

    print("\n" + "="*80)
    print("VEEAM API - RBAC/SECURITY ENDPOINTS")
    print("="*80)
    print(f"\nTotal RBAC endpoints found: {len(rbac_endpoints)}")

    # List all endpoints first
    print("\nEndpoint Overview:")
    for path in sorted(rbac_endpoints.keys()):
        methods = [m.upper() for m in rbac_endpoints[path].keys() if m not in ['parameters', 'summary', 'description']]
        print(f"  {path}")
        print(f"    Methods: {', '.join(methods)}")

    # Detailed information
    print("\n" + "="*80)
    print("DETAILED ENDPOINT INFORMATION")
    print("="*80)

    for path in sorted(rbac_endpoints.keys()):
        format_endpoint_details(path, rbac_endpoints[path])

    # Save to file
    output_file = base_dir / "rbac_endpoints_details.txt"
    print(f"\n\nSaving detailed output to: {output_file}")

if __name__ == "__main__":
    main()
