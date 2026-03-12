# backend/debug_imports.py

import sys
sys.path.insert(0, '.')

def test_import(module_path, description):
    """Test if a module can be imported"""
    try:
        exec(f"from {module_path} import *")
        print(f"✅ {description}")
        return True
    except Exception as e:
        print(f"❌ {description}")
        print(f"   Error: {type(e).__name__}: {e}")
        return False

print("=" * 60)
print("IMPORT DEBUGGING - Academic Advisor Backend")
print("=" * 60)

# Test core dependencies first
print("\n📦 Core Dependencies:")
test_import("fastapi", "FastAPI")
test_import("beanie", "Beanie ODM")
test_import("motor.motor_asyncio", "Motor (MongoDB)")
test_import("pydantic", "Pydantic")

# Test app config
print("\n⚙️ App Configuration:")
test_import("app.config", "App Config")
test_import("app.core.security", "Security (get_current_user)")

# Test models
print("\n📊 Models:")
test_import("app.models.student_profile", "StudentProfile Model")
test_import("app.models.faculty", "Faculty Model")
test_import("app.models.student_projects", "StudentProject Model")

# Test services
print("\n🔧 Services:")
test_import("app.services.ml_service", "ML Service (enhanced_ml_service)")
test_import("app.services.ml_performance_analysis", "ML Performance Analysis")
test_import("app.core.curriculum", "Curriculum (get_semester_subjects)")

# Test routers
print("\n🛣️ Routers:")
test_import("app.api.v1.endpoints.student_profile", "Student Profile Router")
test_import("app.api.v1.endpoints.ml_insights", "ML Insights Router")

# Final test - the main api router
print("\n🚀 Main API Router:")
test_import("app.api.v1.api", "API Router Aggregator")

print("\n" + "=" * 60)