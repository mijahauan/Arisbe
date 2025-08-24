import pytest

from src.egi_controller import create_egi_controller


@pytest.fixture
def controller():
    """Provide an initialized EGIController for tests requiring it."""
    ctrl = create_egi_controller()
    # Initialize with demo graph so tests can assume populated state
    ctrl.initialize_demo_graph()
    return ctrl
