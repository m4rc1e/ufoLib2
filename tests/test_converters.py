from __future__ import annotations

from typing import Any

import pytest
from fontTools.misc.transform import Transform

from ufoLib2.constants import DATA_LIB_KEY
from ufoLib2.converters import default_converter
from ufoLib2.objects import (
    Anchor,
    Component,
    Contour,
    DataSet,
    Font,
    Glyph,
    Guideline,
    Image,
    ImageSet,
    Info,
    Kerning,
    Layer,
    LayerSet,
    Lib,
    Point,
)
from ufoLib2.objects.info import (
    GaspBehavior,
    GaspRangeRecord,
    NameRecord,
    WidthClass,
    WoffMetadataCopyright,
    WoffMetadataCredit,
    WoffMetadataCredits,
    WoffMetadataDescription,
    WoffMetadataExtension,
    WoffMetadataExtensionItem,
    WoffMetadataExtensionName,
    WoffMetadataExtensionValue,
    WoffMetadataLicense,
    WoffMetadataLicensee,
    WoffMetadataText,
    WoffMetadataTrademark,
    WoffMetadataUniqueID,
    WoffMetadataVendor,
)


@pytest.mark.parametrize(
    "obj, expected",
    [
        (Anchor(0, 0), {"x": 0, "y": 0}),
        (
            Anchor(1, -2, "top", "1,0,0,1", "01234"),
            {"x": 1, "y": -2, "name": "top", "color": "1,0,0,1", "identifier": "01234"},
        ),
        (Point(0, 0), {"x": 0, "y": 0}),
        (
            Point(1.5, -2.1, "qcurve", True, "foobar", "12345"),
            {
                "x": 1.5,
                "y": -2.1,
                "type": "qcurve",
                "smooth": True,
                "name": "foobar",
                "identifier": "12345",
            },
        ),
        (Component("a"), {"baseGlyph": "a"}),
        (
            Component("b", Transform(1, 0, 0, 0.5, 10, 20), "abcd1234"),
            {
                "baseGlyph": "b",
                "transformation": (1, 0, 0, 0.5, 10, 20),
                "identifier": "abcd1234",
            },
        ),
        (Contour(), {}),
        (
            Contour([Point(0, 0), Point(1, 2)], "zzzz"),
            {"points": [{"x": 0, "y": 0}, {"x": 1, "y": 2}], "identifier": "zzzz"},
        ),
        (Image(), {}),
        (
            Image("path/to/image.png", Transform(2, 0, 0, 2, 0, 0), "1,1,1,1"),
            {
                "fileName": "path/to/image.png",
                "transformation": (2, 0, 0, 2, 0, 0),
                "color": "1,1,1,1",
            },
        ),
        (Lib(), {}),
        (Lib(foo="bar"), {"foo": "bar"}),
        (Lib(foo=[1, 2], bar={"baz": 3}), {"foo": [1, 2], "bar": {"baz": 3}}),
        (
            Lib(foo={"bar": b"baz"}, oof=[b"rab", "zab"]),
            {
                "foo": {
                    "bar": {"data": "YmF6", "type": DATA_LIB_KEY},
                },
                "oof": [
                    {"data": "cmFi", "type": DATA_LIB_KEY},
                    "zab",
                ],
            },
        ),
        (Guideline(x=0, name="foo"), {"x": 0, "name": "foo"}),
        (Guideline(y=1, name="bar"), {"y": 1, "name": "bar"}),
        (
            Guideline(
                x=1, y=2, angle=45.0, name="baz", color="0,1,0.5,1", identifier="0001"
            ),
            {
                "x": 1,
                "y": 2,
                "angle": 45.0,
                "name": "baz",
                "color": "0,1,0.5,1",
                "identifier": "0001",
            },
        ),
        (Glyph(), {}),
        (
            Glyph(
                "a",
                width=1000,
                height=800,
                unicodes=[97],
                lib=Lib(foo=b"bar"),
                note="Latin lowercase 'a'",
                anchors=[Anchor(100, 200, "top"), Anchor(100, -50, "bottom")],
                contours=[
                    Contour(
                        [Point(0, 0, "line"), Point(1, 1, "line"), Point(1, 0, "line")]
                    ),
                    Contour(
                        [
                            Point(2, 2, "move"),
                            Point(3, 2),
                            Point(4, 1),
                            Point(4, -1, "curve"),
                        ]
                    ),
                ],
                guidelines=[Guideline(x=10)],
            ),
            {
                "name": "a",
                "width": 1000,
                "height": 800,
                "unicodes": [97],
                "lib": {"foo": {"data": "YmFy", "type": DATA_LIB_KEY}},
                "note": "Latin lowercase 'a'",
                "anchors": [
                    {"name": "top", "x": 100, "y": 200},
                    {"name": "bottom", "x": 100, "y": -50},
                ],
                "contours": [
                    {
                        "points": [
                            {"x": 0, "y": 0, "type": "line"},
                            {"x": 1, "y": 1, "type": "line"},
                            {"x": 1, "y": 0, "type": "line"},
                        ]
                    },
                    {
                        "points": [
                            {"x": 2, "y": 2, "type": "move"},
                            {"x": 3, "y": 2},
                            {"x": 4, "y": 1},
                            {"x": 4, "y": -1, "type": "curve"},
                        ]
                    },
                ],
                "guidelines": [{"x": 10}],
            },
        ),
        (Kerning(), {}),
        (
            Kerning({("a", "b"): -10, ("a", "d"): 5, ("b", "d"): 0}),
            {"a": {"b": -10, "d": 5}, "b": {"d": 0}},
        ),
        (
            Info(
                familyName="Test",
                styleName="Bold",
                versionMajor=2,
                versionMinor=1,
                unitsPerEm=1000,
                guidelines=[Guideline(y=500, name="x-height")],
                openTypeGaspRangeRecords=[
                    GaspRangeRecord(
                        rangeMaxPPEM=18,
                        rangeGaspBehavior=[GaspBehavior.SYMMETRIC_SMOOTHING],
                    )
                ],
                openTypeHeadFlags=[0, 1, 2],
                openTypeNameRecords=[
                    NameRecord(
                        nameID=5,
                        platformID=0,
                        encodingID=0,
                        languageID=0,
                        string="Version 2.1",
                    )
                ],
                openTypeOS2WidthClass=WidthClass.MEDIUM,
                postscriptBlueScale=0.25,
                woffMajorVersion=1,
                woffMinorVersion=0,
                woffMetadataUniqueID=WoffMetadataUniqueID(
                    "com.example.fontvendor.demofont.rev12345"
                ),
                woffMetadataVendor=WoffMetadataVendor(
                    name="Font Vendor",
                    url="http://fontvendor.example.com",
                ),
                woffMetadataCredits=WoffMetadataCredits(
                    [
                        WoffMetadataCredit(
                            name="Font Designer",
                            url="http://fontdesigner.example.com",
                            role="Lead",
                        ),
                        WoffMetadataCredit(
                            name="Another Font Designer",
                            url="http://anotherdesigner.example.com",
                            role="Contributor",
                        ),
                    ]
                ),
                woffMetadataDescription=WoffMetadataDescription(
                    text=[
                        WoffMetadataText(
                            "A member of the Demo font family...", language="en"
                        )
                    ]
                ),
                woffMetadataLicense=WoffMetadataLicense(
                    id="fontvendor-Web-corporate-v2",
                    url="http://fontvendor.example.com/license",
                    text=[
                        WoffMetadataText("A license goes here", language="en"),
                        WoffMetadataText("Un permis va ici", language="fr"),
                    ],
                ),
                woffMetadataCopyright=WoffMetadataCopyright(
                    [
                        WoffMetadataText("Copyright ©2009 Font Vendor", language="en"),
                        WoffMetadataText("저작권 ©2009 Font Vendor", language="ko"),
                    ],
                ),
                woffMetadataTrademark=WoffMetadataTrademark(
                    [
                        WoffMetadataText(
                            "Demo Font is a trademark of Font Vendor", language="en"
                        ),
                        WoffMetadataText(
                            "Demo Font est une marque déposée de Font Vendor",
                            language="fr",
                        ),
                    ]
                ),
                woffMetadataLicensee=WoffMetadataLicensee(
                    "Wonderful Websites, Inc.",
                ),
                woffMetadataExtensions=[
                    WoffMetadataExtension(
                        id="org.example.fonts.metadata.v1",
                        names=[
                            WoffMetadataExtensionName(
                                "Additional font information", language="en"
                            ),
                            WoffMetadataExtensionName(
                                "L'information supplémentaire de fonte", language="fr"
                            ),
                        ],
                        items_=[
                            WoffMetadataExtensionItem(
                                id="org.example.fonts.metadata.v1.why",
                                names=[
                                    WoffMetadataExtensionName("Purpose", language="en"),
                                    WoffMetadataExtensionName("But", language="fr"),
                                ],
                                values_=[
                                    WoffMetadataExtensionValue(
                                        "An example of WOFF packaging", language="en"
                                    ),
                                    WoffMetadataExtensionValue(
                                        "Un exemple de l'empaquetage de WOFF",
                                        language="fr",
                                    ),
                                ],
                            )
                        ],
                    )
                ],
            ),
            {
                "familyName": "Test",
                "styleName": "Bold",
                "versionMajor": 2,
                "versionMinor": 1,
                "unitsPerEm": 1000,
                "guidelines": [{"y": 500, "name": "x-height"}],
                "openTypeGaspRangeRecords": [
                    {"rangeMaxPPEM": 18, "rangeGaspBehavior": [3]},
                ],
                "openTypeHeadFlags": [0, 1, 2],
                "openTypeNameRecords": [
                    {
                        "nameID": 5,
                        "platformID": 0,
                        "encodingID": 0,
                        "languageID": 0,
                        "string": "Version 2.1",
                    }
                ],
                "openTypeOS2WidthClass": 5,
                "postscriptBlueScale": 0.25,
                "woffMajorVersion": 1,
                "woffMinorVersion": 0,
                "woffMetadataUniqueID": {
                    "id": "com.example.fontvendor.demofont.rev12345"
                },
                "woffMetadataVendor": {
                    "name": "Font Vendor",
                    "url": "http://fontvendor.example.com",
                },
                "woffMetadataCredits": {
                    "credits": [
                        {
                            "name": "Font Designer",
                            "role": "Lead",
                            "url": "http://fontdesigner.example.com",
                        },
                        {
                            "name": "Another Font Designer",
                            "role": "Contributor",
                            "url": "http://anotherdesigner.example.com",
                        },
                    ]
                },
                "woffMetadataDescription": {
                    "text": [
                        {
                            "language": "en",
                            "text": "A member of the Demo font family...",
                        }
                    ]
                },
                "woffMetadataLicense": {
                    "id": "fontvendor-Web-corporate-v2",
                    "text": [
                        {"language": "en", "text": "A license goes here"},
                        {"language": "fr", "text": "Un permis va ici"},
                    ],
                    "url": "http://fontvendor.example.com/license",
                },
                "woffMetadataCopyright": {
                    "text": [
                        {"language": "en", "text": "Copyright ©2009 Font Vendor"},
                        {"language": "ko", "text": "저작권 ©2009 Font Vendor"},
                    ]
                },
                "woffMetadataTrademark": {
                    "text": [
                        {
                            "language": "en",
                            "text": "Demo Font is a trademark of Font Vendor",
                        },
                        {
                            "language": "fr",
                            "text": "Demo Font est une marque déposée "
                            "de Font Vendor",
                        },
                    ]
                },
                "woffMetadataLicensee": {"name": "Wonderful Websites, Inc."},
                "woffMetadataExtensions": [
                    {
                        "id": "org.example.fonts.metadata.v1",
                        "names": [
                            {"language": "en", "text": "Additional font information"},
                            {
                                "language": "fr",
                                "text": "L'information supplémentaire de fonte",
                            },
                        ],
                        "items": [
                            {
                                "id": "org.example.fonts.metadata.v1.why",
                                "names": [
                                    {"language": "en", "text": "Purpose"},
                                    {"language": "fr", "text": "But"},
                                ],
                                "values": [
                                    {
                                        "language": "en",
                                        "text": "An example of WOFF packaging",
                                    },
                                    {
                                        "language": "fr",
                                        "text": "Un exemple de l'empaquetage de WOFF",
                                    },
                                ],
                            }
                        ],
                    }
                ],
            },
        ),
        # 'public.default' is a special case, default=True by definition
        (Layer(), {"name": "public.default", "default": True}),
        (Layer("foo", default=True), {"name": "foo", "default": True}),
        (Layer("bar"), {"name": "bar"}),
        (
            Layer(
                name="foreground",
                glyphs={"a": Glyph("a"), "b": Glyph("b")},
                color="1,0,1,1",
                lib=Lib(foobar=0.1),
                default=True,
            ),
            {
                "name": "foreground",
                "glyphs": [{"name": "a"}, {"name": "b"}],
                "color": "1,0,1,1",
                "lib": {"foobar": 0.1},
                "default": True,
            },
        ),
        (LayerSet.default(), [{"name": "public.default", "default": True}]),
        (
            LayerSet.from_iterable(
                [Layer("foreground"), Layer("background")],
                defaultLayerName="foreground",  # deprecated
            ),
            [{"name": "foreground", "default": True}, {"name": "background"}],
        ),
        (
            LayerSet.from_iterable(
                [Layer("foreground", default=True), Layer("background")],
            ),
            [{"name": "foreground", "default": True}, {"name": "background"}],
        ),
        (DataSet(), {}),
        (DataSet({"foo": b"bar"}), {"foo": "YmFy"}),
        (ImageSet(), {}),
        (ImageSet({"foo": b"bar"}), {"foo": "YmFy"}),
        (Font(), {"layers": [{"name": "public.default", "default": True}]}),
        (
            Font(
                layers=[
                    Layer(name="foreground", default=True),
                    Layer(name="background"),
                ]
            ),
            {
                "layers": [
                    {"name": "foreground", "default": True},
                    {"name": "background"},
                ],
            },
        ),
        (
            Font(
                layers=[Layer(glyphs=[Glyph("a")])],
                info=Info(familyName="Test"),
                features="languagesystem DFLT dflt;",
                groups={"LOWERCASE": ["a"]},
                kerning={("a", "a"): 10},
                lib={"foo": "bar"},
                data={"baz": b"\0"},
                images={"foobarbaz": b"\0"},
            ),
            {
                "layers": [
                    {
                        "name": "public.default",
                        "glyphs": [{"name": "a"}],
                        "default": True,
                    }
                ],
                "info": {"familyName": "Test"},
                "features": "languagesystem DFLT dflt;",
                "groups": {"LOWERCASE": ["a"]},
                "kerning": {"a": {"a": 10}},
                "lib": {"foo": "bar"},
                "data": {"baz": "AA=="},
                "images": {"foobarbaz": "AA=="},
            },
        ),
    ],
)
def test_unstructure_structure(obj: Any, expected: dict[str, Any]) -> None:
    assert default_converter.unstructure(obj) == expected
    assert default_converter.structure(expected, type(obj)) == obj


def test_unstructure_lazy_font(ufo_UbuTestData: Font) -> None:
    font1 = ufo_UbuTestData
    assert font1._lazy

    font_data = default_converter.unstructure(font1)

    font2 = default_converter.structure(font_data, Font)
    assert font2 == font1

    assert not font2._lazy