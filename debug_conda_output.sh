#!/bin/bash

# Debug script to test conda CGIF environment output capture
# Run this in your terminal to see if conda environment is causing output suppression

echo "=== Conda Environment Debug Script ==="
echo "Current time: $(date)"
echo ""

# Check conda environment
echo "--- Conda Environment Info ---"
echo "CONDA_DEFAULT_ENV: $CONDA_DEFAULT_ENV"
echo "CONDA_PREFIX: $CONDA_PREFIX"
echo "PATH (first 3 entries): $(echo $PATH | cut -d: -f1-3)"
echo ""

# Check Python version and location
echo "--- Python Info ---"
which python
python --version
echo "Python executable: $(which python)"
echo ""

# Test basic Python output
echo "--- Basic Python Output Test ---"
python -c "print('Hello from Python')"
echo "Exit code: $?"
echo ""

# Test Python with explicit output flushing
echo "--- Python with Explicit Flushing ---"
python -c "
import sys
print('Testing stdout...', flush=True)
sys.stderr.write('Testing stderr...\n')
sys.stderr.flush()
print('Done.', flush=True)
"
echo "Exit code: $?"
echo ""

# Test Python with environment variables
echo "--- Python with PYTHONUNBUFFERED ---"
PYTHONUNBUFFERED=1 python -c "
import sys
print('Testing unbuffered output...')
sys.stderr.write('Testing unbuffered stderr...\n')
"
echo "Exit code: $?"
echo ""

# Test the actual round-trip pipeline
echo "--- Round-Trip Pipeline Test ---"
cd /Users/mjh/Sync/GitHub/Arisbe
PYTHONPATH=src PYTHONUNBUFFERED=1 python -c "
import sys
print('=== Round-Trip Test in CGIF Environment ===')

try:
    from egif_parser_dau import EGIFParser
    from egdf_parser import EGDFParser
    print('✅ Core imports successful')
    
    # Test simple round-trip
    egif = '(Human \"Socrates\")'
    print(f'Input: {egif}')
    
    # EGIF → EGI
    parser = EGIFParser(egif)
    egi = parser.parse()
    print(f'EGIF→EGI: {len(egi.V)}V {len(egi.E)}E')
    
    # Create spatial primitives
    spatial_primitives = []
    for edge in egi.E:
        spatial_primitives.append({
            'element_id': edge.id,
            'element_type': 'predicate',
            'position': (100, 100),
            'bounds': (80, 90, 120, 110)
        })
    print(f'Created {len(spatial_primitives)} spatial primitives')
    
    # EGI → EGDF
    egdf_parser = EGDFParser()
    egdf_doc = egdf_parser.create_egdf_from_egi(egi, spatial_primitives)
    print('✅ EGI→EGDF: Success')
    
    # EGDF → EGI
    recovered_egi = egdf_parser.extract_egi_from_egdf(egdf_doc)
    print(f'✅ EGDF→EGI: {len(recovered_egi.V)}V {len(recovered_egi.E)}E')
    
    # Validate
    success = (len(egi.V) == len(recovered_egi.V) and len(egi.E) == len(recovered_egi.E))
    print(f'✅ Round-trip: {\"SUCCESS\" if success else \"FAILED\"}')
    
except ImportError as e:
    print(f'❌ Import error: {e}')
    import traceback
    traceback.print_exc()
except Exception as e:
    print(f'❌ Runtime error: {e}')
    import traceback
    traceback.print_exc()
" 2>&1
echo "Exit code: $?"
echo ""

# Test the bidirectional pipeline test
echo "--- Bidirectional Pipeline Test ---"
cd /Users/mjh/Sync/GitHub/Arisbe
PYTHONPATH=src PYTHONUNBUFFERED=1 python tests/bidirectional_pipeline_test.py 2>&1
echo "Exit code: $?"
echo ""

# Test with unittest directly
echo "--- Unittest Direct Test ---"
cd /Users/mjh/Sync/GitHub/Arisbe
PYTHONPATH=src PYTHONUNBUFFERED=1 python -m unittest tests.bidirectional_pipeline_test.BidirectionalPipelineTest.test_forward_pipeline_egif_to_egdf -v 2>&1
echo "Exit code: $?"
echo ""

# Check for any conda-specific output redirection
echo "--- Conda Configuration Check ---"
conda info --envs
echo ""
conda list | grep -E "(jupyter|ipython|notebook)" || echo "No Jupyter/IPython packages found"
echo ""

# Check for any Python site-packages that might interfere
echo "--- Python Site-Packages Check ---"
python -c "
import sys
import site
print('Site packages directories:')
for path in site.getsitepackages():
    print(f'  {path}')
print()
print('User site packages:', site.getusersitepackages())
"
echo ""

echo "=== Debug Script Complete ==="
echo "If you see this message, the script ran successfully."
echo "If you don't see output from the Python tests above, there's an environment issue."
