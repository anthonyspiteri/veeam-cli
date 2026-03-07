#!/usr/bin/env python3
"""Compare Veeam API Swagger schemas between versions."""

import json
from pathlib import Path
from collections import defaultdict

def load_schema(filepath):
    """Load JSON schema file."""
    with open(filepath, 'r') as f:
        return json.load(f)

def compare_schemas(old_schema, new_schema):
    """Compare two Swagger schemas and report differences."""

    print("=" * 80)
    print("VEEAM API SCHEMA COMPARISON: 13.0.0 (rev0) vs 13.0.1 (rev1)")
    print("=" * 80)

    # Version info
    old_version = old_schema.get('info', {}).get('version', 'unknown')
    new_version = new_schema.get('info', {}).get('version', 'unknown')
    print(f"\nOld Version: {old_version}")
    print(f"New Version: {new_version}")

    # Paths comparison
    old_paths = set(old_schema.get('paths', {}).keys())
    new_paths = set(new_schema.get('paths', {}).keys())

    added_paths = new_paths - old_paths
    removed_paths = old_paths - new_paths
    common_paths = old_paths & new_paths

    print(f"\n{'ENDPOINTS SUMMARY':-^80}")
    print(f"Old endpoints: {len(old_paths)}")
    print(f"New endpoints: {len(new_paths)}")
    print(f"Added: {len(added_paths)}")
    print(f"Removed: {len(removed_paths)}")
    print(f"Modified/Same: {len(common_paths)}")

    if added_paths:
        print(f"\n{'ADDED ENDPOINTS':-^80}")
        for path in sorted(added_paths):
            methods = list(new_schema['paths'][path].keys())
            methods = [m.upper() for m in methods if m not in ['parameters', 'summary', 'description']]
            print(f"  + {path}")
            print(f"      Methods: {', '.join(methods)}")

    if removed_paths:
        print(f"\n{'REMOVED ENDPOINTS':-^80}")
        for path in sorted(removed_paths):
            methods = list(old_schema['paths'][path].keys())
            methods = [m.upper() for m in methods if m not in ['parameters', 'summary', 'description']]
            print(f"  - {path}")
            print(f"      Methods: {', '.join(methods)}")

    # Check for modified endpoints
    modified_endpoints = []
    for path in common_paths:
        old_methods = set(old_schema['paths'][path].keys()) - {'parameters', 'summary', 'description'}
        new_methods = set(new_schema['paths'][path].keys()) - {'parameters', 'summary', 'description'}

        if old_methods != new_methods:
            modified_endpoints.append({
                'path': path,
                'added_methods': new_methods - old_methods,
                'removed_methods': old_methods - new_methods
            })
        else:
            # Check if operation details changed
            for method in new_methods:
                if old_schema['paths'][path][method] != new_schema['paths'][path][method]:
                    # Check what changed
                    old_op = old_schema['paths'][path][method]
                    new_op = new_schema['paths'][path][method]

                    changes = []
                    if old_op.get('parameters') != new_op.get('parameters'):
                        changes.append('parameters')
                    if old_op.get('responses') != new_op.get('responses'):
                        changes.append('responses')
                    if old_op.get('summary') != new_op.get('summary'):
                        changes.append('summary')
                    if old_op.get('description') != new_op.get('description'):
                        changes.append('description')

                    if changes:
                        modified_endpoints.append({
                            'path': path,
                            'method': method.upper(),
                            'changes': changes
                        })
                    break

    if modified_endpoints:
        print(f"\n{'MODIFIED ENDPOINTS':-^80}")
        print(f"Total modified: {len(modified_endpoints)}")
        for item in modified_endpoints[:20]:  # Show first 20
            if 'method' in item:
                print(f"  ~ {item['path']} [{item['method']}]")
                print(f"      Changed: {', '.join(item['changes'])}")
            else:
                added = [m.upper() for m in item['added_methods']]
                removed = [m.upper() for m in item['removed_methods']]
                print(f"  ~ {item['path']}")
                if added:
                    print(f"      Added methods: {', '.join(added)}")
                if removed:
                    print(f"      Removed methods: {', '.join(removed)}")

        if len(modified_endpoints) > 20:
            print(f"\n  ... and {len(modified_endpoints) - 20} more modified endpoints")

    # Definitions/Components comparison
    old_defs = set(old_schema.get('definitions', {}).keys())
    new_defs = set(new_schema.get('definitions', {}).keys())

    added_defs = new_defs - old_defs
    removed_defs = old_defs - new_defs

    print(f"\n{'SCHEMA DEFINITIONS SUMMARY':-^80}")
    print(f"Old definitions: {len(old_defs)}")
    print(f"New definitions: {len(new_defs)}")
    print(f"Added: {len(added_defs)}")
    print(f"Removed: {len(removed_defs)}")

    if added_defs:
        print(f"\n{'ADDED DEFINITIONS':-^80}")
        for defn in sorted(added_defs)[:30]:  # Show first 30
            print(f"  + {defn}")
        if len(added_defs) > 30:
            print(f"  ... and {len(added_defs) - 30} more")

    if removed_defs:
        print(f"\n{'REMOVED DEFINITIONS':-^80}")
        for defn in sorted(removed_defs)[:30]:
            print(f"  - {defn}")
        if len(removed_defs) > 30:
            print(f"  ... and {len(removed_defs) - 30} more")

    # Tags comparison
    old_tags = {tag['name'] for tag in old_schema.get('tags', [])}
    new_tags = {tag['name'] for tag in new_schema.get('tags', [])}

    if old_tags != new_tags:
        print(f"\n{'TAGS CHANGES':-^80}")
        added_tags = new_tags - old_tags
        removed_tags = old_tags - new_tags
        if added_tags:
            print(f"Added tags: {', '.join(sorted(added_tags))}")
        if removed_tags:
            print(f"Removed tags: {', '.join(sorted(removed_tags))}")

    print(f"\n{'='*80}")
    print("Comparison complete!")
    print("=" * 80)

def main():
    """Main function."""
    base_dir = Path(__file__).parent

    old_schema_path = base_dir / "swagger_v1.3-rev0.json"
    new_schema_path = base_dir / "swagger_v1.3-rev1.json"

    print("Loading schemas...")
    old_schema = load_schema(old_schema_path)
    new_schema = load_schema(new_schema_path)

    compare_schemas(old_schema, new_schema)

if __name__ == "__main__":
    main()
