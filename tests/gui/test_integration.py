# tests/gui/test_integration.py
import unittest
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from PySide6.QtWidgets import QApplication
from gui.main_window import MainWindow
from eg_types import EGGraph

class TestGUIIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication([])
        
    def test_main_window_creation(self):
        window = MainWindow()
        self.assertIsNotNone(window)
        
    def test_graph_display(self):
        window = MainWindow()
        graph = EGGraph.create_empty()
        window.graph_canvas.set_graph(graph)
        self.assertEqual(window.graph_canvas.current_graph, graph)