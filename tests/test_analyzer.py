"""分析器模块测试."""

from pathlib import Path

from test_auto.analyzer.java_parser import parse_java_file, parse_methods
from test_auto.analyzer.manifest_parser import parse_manifest
from test_auto.analyzer.coverage import analyze_coverage, CoverageReport
from test_auto.models.schemas import ClassInfo, MethodInfo


FUOS_ROOT = Path("workspace/fuos")


def test_parse_java_file():
    f = FUOS_ROOT / "sdk/widget/src/main/java/com/fuos/sdk/widget/FuosButton.java"
    if not f.exists():
        return  # skip if not cloned
    info = parse_java_file(f)
    assert info is not None
    assert info.name == "FuosButton"
    assert info.package == "com.fuos.sdk.widget"
    assert info.superclass == "AppCompatButton"
    assert len(info.constructors) == 3


def test_parse_methods():
    f = FUOS_ROOT / "sdk/utils/src/main/java/com/fuos/sdk/utils/DisplayUtils.java"
    if not f.exists():
        return
    methods = parse_methods(f)
    assert len(methods) == 5
    assert all(m.is_static for m in methods)
    assert all(m.is_public for m in methods)


def test_parse_manifest():
    m = FUOS_ROOT / "demo/src/main/AndroidManifest.xml"
    if not m.exists():
        return
    info = parse_manifest(m)
    assert info is not None
    assert len(info.activities) == 9


def test_coverage_report():
    classes = [
        ClassInfo(name="A", package="com.test", methods=["foo"]),
        ClassInfo(name="B", package="com.test", methods=["bar"]),
    ]
    methods = [
        MethodInfo(name="foo", class_name="A", is_public=True),
        MethodInfo(name="bar", class_name="B", is_public=True),
    ]
    # 无测试文件
    report = analyze_coverage(classes, methods, Path("/nonexistent"))
    assert report.total_classes == 2
    assert report.tested_classes == 0
    assert report.class_coverage == 0.0
