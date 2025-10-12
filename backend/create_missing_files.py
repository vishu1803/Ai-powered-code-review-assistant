#!/usr/bin/env python3
"""Script to create all missing __init__.py files and basic structures."""

import os
from pathlib import Path

# Define all directories that need __init__.py files
directories = [
    "app",
    "app/api",
    "app/api/middlewares", 
    "app/api/v1",
    "app/api/dependencies",
    "app/core",
    "app/models",
    "app/models/ai",
    "app/models/database", 
    "app/models/schemas",
    "app/services",
    "app/utils",
    "app/utils/helpers",
    "app/utils/parsers", 
    "app/utils/validators",
    "app/workers",
    "app/integrations",
    "app/integrations/github",
    "app/integrations/gitlab",
    "app/integrations/bitbucket",
    "app/integrations/jira",
]

def create_init_files():
    """Create __init__.py files in all directories."""
    base_path = Path(__file__).parent
    
    for directory in directories:
        dir_path = base_path / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            with open(init_file, "w") as f:
                f.write(f'"""${directory.replace("/", ".")} package."""\n')
            print(f"Created: {init_file}")

if __name__ == "__main__":
    create_init_files()
    print("✅ All missing __init__.py files created!")
