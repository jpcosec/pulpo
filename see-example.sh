#!/bin/bash

# Pulpo Core - See Examples Script
# Demonstrates the 3 complete example projects

set -e

EXAMPLES_DIR="./examples"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Colors
BLUE='\033[0;34m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Banner
echo -e "${BLUE}╔════════════════════════════════════════════════════════════════╗${NC}"
echo -e "${BLUE}║        Pulpo Core - Example Project Viewer                    ║${NC}"
echo -e "${BLUE}╚════════════════════════════════════════════════════════════════╝${NC}"
echo ""

# Check if examples directory exists
if [ ! -d "$EXAMPLES_DIR" ]; then
    echo -e "${YELLOW}Error: examples directory not found at $EXAMPLES_DIR${NC}"
    exit 1
fi

# Menu
show_menu() {
    echo -e "${GREEN}Available Examples:${NC}"
    echo ""
    echo "  1) Todo List       (Beginner) - Simple CRUD + workflows"
    echo "  2) Pokemon         (Intermediate) - Domain modeling + game mechanics"
    echo "  3) E-commerce      (Advanced) - Parallelization + multi-domain"
    echo ""
    echo "  4) View all examples at once"
    echo "  5) Extract all examples to /tmp for testing"
    echo "  6) Exit"
    echo ""
}

# Show single example
show_example() {
    local name=$1
    local dir=$2
    local description=$3

    echo -e "${GREEN}=== $name ===${NC}"
    echo -e "${YELLOW}Description:${NC} $description"
    echo ""

    if [ -d "$EXAMPLES_DIR/$dir" ]; then
        echo -e "${YELLOW}Location:${NC} $EXAMPLES_DIR/$dir"
        echo ""

        echo -e "${YELLOW}Files:${NC}"
        find "$EXAMPLES_DIR/$dir" -type f -name "*.py" | head -20 | sed 's/^/  /'

        if [ -f "$EXAMPLES_DIR/$dir/README.md" ]; then
            echo ""
            echo -e "${YELLOW}Quick Summary (from README):${NC}"
            head -15 "$EXAMPLES_DIR/$dir/README.md" | tail -10 | sed 's/^/  /'
        fi
    elif [ -f "$EXAMPLES_DIR/$dir.tar.gz" ]; then
        echo -e "${YELLOW}Available as tarball:${NC} $EXAMPLES_DIR/$dir.tar.gz"
        echo ""
        echo "Extract with:"
        echo "  tar -xzf $EXAMPLES_DIR/$dir.tar.gz"
    fi

    echo ""
}

# Show all examples
show_all_examples() {
    show_example "TODO LIST" "todo-app" "Simple todo management with CRUD and workflows"
    show_example "POKEMON" "pokemon-app" "Domain-specific modeling with game mechanics"
    show_example "E-COMMERCE" "ecommerce-app" "Enterprise app with parallelization patterns"
}

# Extract examples
extract_examples() {
    echo -e "${YELLOW}Extracting examples to /tmp/pulpo-examples...${NC}"
    mkdir -p /tmp/pulpo-examples

    cd "$EXAMPLES_DIR"

    for tarball in *.tar.gz; do
        if [ -f "$tarball" ]; then
            echo -e "${GREEN}Extracting $tarball...${NC}"
            tar -xzf "$tarball" -C /tmp/pulpo-examples
            echo -e "${GREEN}✓ $tarball extracted${NC}"
        fi
    done

    cd "$SCRIPT_DIR"

    echo ""
    echo -e "${GREEN}Done!${NC}"
    echo ""
    echo "Examples are in: /tmp/pulpo-examples"
    echo ""
    echo "Try these commands:"
    echo ""
    echo "  # Todo example"
    echo "  cd /tmp/pulpo-examples/todo-app"
    echo "  pulpo compile"
    echo "  pulpo up"
    echo ""
    echo "  # Pokemon example"
    echo "  cd /tmp/pulpo-examples/pokemon-app"
    echo "  pulpo compile"
    echo ""
    echo "  # E-commerce example"
    echo "  cd /tmp/pulpo-examples/ecommerce-app"
    echo "  pulpo compile"
    echo ""
}

# Show quick start
show_quickstart() {
    echo -e "${GREEN}=== QUICK START ===${NC}"
    echo ""
    echo "1. Extract an example:"
    echo "   tar -xzf examples/todo-app.tar.gz"
    echo "   cd todo-app"
    echo ""
    echo "2. Install Pulpo (if not already installed):"
    echo "   pip install -e ../core"
    echo ""
    echo "3. Generate API, UI, CLI:"
    echo "   pulpo compile"
    echo ""
    echo "4. Start all services:"
    echo "   pulpo up"
    echo ""
    echo "5. Access the application:"
    echo "   API:  http://localhost:8000/api/docs"
    echo "   UI:   http://localhost:3000"
    echo ""
    echo "6. View generated code:"
    echo "   cat .run_cache/generated_api.py"
    echo "   cat .run_cache/generated_ui_config.ts"
    echo ""
}

# Main loop
while true; do
    show_menu
    read -p "Enter your choice (1-6): " choice

    case $choice in
        1)
            clear
            show_example "TODO LIST" "todo-app" "Simple CRUD + workflows (4.9K, 2 models, 8 operations)"
            show_quickstart
            ;;
        2)
            clear
            show_example "POKEMON" "pokemon-app" "Domain modeling + game mechanics (5.5K, 5 models, 7 operations)"
            show_quickstart
            ;;
        3)
            clear
            show_example "E-COMMERCE" "ecommerce-app" "Parallelization patterns (7.4K, 4 models, 12 operations)"
            show_quickstart
            ;;
        4)
            clear
            show_all_examples
            show_quickstart
            ;;
        5)
            clear
            extract_examples
            ;;
        6)
            echo -e "${GREEN}Thank you for exploring Pulpo Core!${NC}"
            exit 0
            ;;
        *)
            echo -e "${YELLOW}Invalid choice. Please try again.${NC}"
            sleep 2
            clear
            ;;
    esac

    read -p "Press Enter to continue..."
    clear
done
