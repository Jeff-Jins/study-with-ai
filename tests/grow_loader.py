"""확장자 없는 grow 스크립트를 테스트에서 import하기 위한 로더."""
import importlib.machinery
import importlib.util
import sys
from pathlib import Path

_PATH = Path(__file__).resolve().parent.parent / "grow"
_loader = importlib.machinery.SourceFileLoader("grow", str(_PATH))
_spec = importlib.util.spec_from_loader("grow", _loader)
grow = importlib.util.module_from_spec(_spec)
sys.modules["grow"] = grow  # dataclass가 모듈을 찾을 수 있게
_loader.exec_module(grow)
