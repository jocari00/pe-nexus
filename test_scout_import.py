"""Test Scout agent imports."""
try:
    from src.agents.scout import IntelligenceScoutAgent
    print("Scout agent: OK")
except Exception as e:
    print(f"Scout agent ERROR: {e}")

try:
    from src.services.peer_review import get_peer_review_service
    print("Peer review: OK")
except Exception as e:
    print(f"Peer review ERROR: {e}")

try:
    from src.api.routes.agents import router
    paths = [r.path for r in router.routes]
    scout_paths = [p for p in paths if 'scout' in p]
    print(f"Scout routes: {scout_paths}")
except Exception as e:
    print(f"Routes ERROR: {e}")
