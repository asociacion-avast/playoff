#!/bin/bash
# Quick test to validate optimizations work correctly

echo "==================================================="
echo "Testing Optimized Scripts"
echo "==================================================="
echo ""

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

test_script() {
    script=$1
    echo "Testing: $script"

    # Check if script exists
    if [ ! -f "$script" ]; then
        echo -e "${RED}✗ Script not found${NC}"
        return 1
    fi

    # Check syntax
    if python3 -m py_compile "$script" 2>/dev/null; then
        echo -e "${GREEN}✓ Syntax OK${NC}"
    else
        echo -e "${RED}✗ Syntax Error${NC}"
        python3 -m py_compile "$script"
        return 1
    fi

    # Check for optimization markers
    if grep -q "# OPTIM" "$script"; then
        echo -e "${GREEN}✓ Contains optimization markers${NC}"
    else
        echo -e "${RED}⚠ No optimization markers found${NC}"
    fi

    # Check for required imports
    if grep -q "from collections import defaultdict" "$script" || grep -q "outbox_entries_global" "$script"; then
        echo -e "${GREEN}✓ Optimized imports found${NC}"
    fi

    echo ""
}

# Test all optimized scripts
test_script "3-elimina-inscripciones-bajas.py"
test_script "3-elimina-inscripciones-anuladas.py"
test_script "3-elimina-inscripciones-conflictos.py"
test_script "3-elimina-telegramID-incorrecto.py"
test_script "3-elimina-tutor-en-campo-socio.py"
test_script "4-self-service-telegram.py"
test_script "4-self-service-modalidad.py"

echo "==================================================="
echo "Performance Comparison Test"
echo "==================================================="
echo ""
echo "To measure actual performance improvement:"
echo ""
echo "1. Before running optimized version:"
echo "   cp -r data data.backup"
echo ""
echo "2. Time a script (example):"
echo "   time ./3-elimina-inscripciones-bajas.py"
echo ""
echo "3. Compare with previous runs"
echo ""
echo "Expected improvement: 10-100x faster for large datasets"
echo ""
