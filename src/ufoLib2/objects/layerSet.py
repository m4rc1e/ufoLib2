from collections import OrderedDict
from typing import Any, Iterable, MutableMapping, Optional

import attr

from ufoLib2.constants import DEFAULT_LAYER_NAME
from ufoLib2.objects.layer import Layer
from ufoLib2.objects.misc import _NOT_LOADED, _deepcopy_unlazify_attrs


def _convert_layers(value: Iterable[Layer]) -> "OrderedDict[str, Layer]":
    # takes an iterable of Layer objects and returns an OrderedDict keyed
    # by layer name
    if isinstance(value, OrderedDict):
        return value
    layers: OrderedDict[str, Layer] = OrderedDict()
    for layer in value:
        if not isinstance(layer, Layer):
            raise TypeError("expected 'Layer', found '%s'" % type(layer).__name__)
        if layer.name in layers:
            raise KeyError("duplicate layer name: '%s'" % layer.name)
        layers[layer.name] = layer
    return layers


@attr.s(auto_attribs=True, slots=True, repr=False)
class LayerSet:
    """Represents a mapping of layer names to Layer objects.

    See http://unifiedfontobject.org/versions/ufo3/layercontents.plist/ for layer
    semantics.

    Behavior:
        LayerSet behaves **partly** like a dictionary of type ``Dict[str, Layer]``,
        but creating and loading layers is done through their own methods. Unless the
        font is loaded eagerly (with ``lazy=False``), the layer objects and their
        glyphs are by default only loaded into memory when accessed.

        To get the number of layers in the font::

            layerCount = len(font.layers)

        To iterate over all layers::

            for layer in font.layers:
                ...

        To check if a specific layer exists::

            exists = "myLayerName" in font.layers

        To get a specific layer::

            font.layers["myLayerName"]

        To delete a specific layer::

            del font.layers["myLayerName"]
    """

    _layers: MutableMapping[str, Layer] = attr.ib(
        factory=OrderedDict, converter=_convert_layers
    )
    defaultLayer: Optional[Layer] = None
    """The default layer of the UFO, typically named ``public.default``."""

    _reader: Optional[Any] = attr.ib(default=None, init=False, eq=False)

    def __attrs_post_init__(self):
        if not self._layers:
            # LayerSet is never empty; always contains at least the default
            if self.defaultLayer is not None:
                raise TypeError(
                    "'defaultLayer' argument is invalid with empty LayerSet"
                )
            self.defaultLayer = self.newLayer(DEFAULT_LAYER_NAME)
        elif self.defaultLayer is not None:
            # check that the specified default layer is in the layer set;
            default = self.defaultLayer
            for layer in self._layers.values():
                if layer is default:
                    break
            else:
                raise ValueError(
                    "defaultLayer %r is not among the specified layers" % default
                )
        elif len(self._layers) == 1:
            # there's only one, we assume it's the default
            self.defaultLayer = next(self._layers.values())
        else:
            if DEFAULT_LAYER_NAME not in self._layers:
                raise ValueError("default layer not specified")
            self.defaultLayer = self._layers[DEFAULT_LAYER_NAME]

    @classmethod
    def read(cls, reader, lazy=True):
        layers = OrderedDict()
        """Instantiates a LayerSet object from a :class:`fontTools.ufoLib.UFOReader`.

        Args:
            path: The path to the UFO to load.
            lazy: If True, load glyphs, data files and images as they are accessed. If
                False, load everything up front.
        """
        defaultLayer = None

        defaultLayerName = reader.getDefaultLayerName()

        for layerName in reader.getLayerNames():
            isDefault = layerName == defaultLayerName
            if isDefault or not lazy:
                layer = cls._loadLayer(reader, layerName, lazy, isDefault)
                if isDefault:
                    defaultLayer = layer
                layers[layerName] = layer
            else:
                layers[layerName] = _NOT_LOADED

        assert defaultLayer is not None

        self = cls(layers, defaultLayer=defaultLayer)
        if lazy:
            self._reader = reader

        return self

    def unlazify(self):
        """Load all layers into memory."""
        for layer in self:
            layer.unlazify()

    __deepcopy__ = _deepcopy_unlazify_attrs

    @staticmethod
    def _loadLayer(reader, layerName, lazy=True, default=False):
        # UFOReader.getGlyphSet method doesn't support 'defaultLayer'
        # keyword argument, whereas the UFOWriter.getGlyphSet method
        # requires it. In order to allow to use an instance of
        # UFOWriter as the 'reader', here we try both ways...
        try:
            glyphSet = reader.getGlyphSet(layerName, defaultLayer=default)
        except TypeError as e:
            # TODO use inspect module?
            if "keyword argument 'defaultLayer'" in str(e):
                glyphSet = reader.getGlyphSet(layerName)

        return Layer.read(layerName, glyphSet, lazy=lazy)

    def loadLayer(self, layerName, lazy=True, default=False):
        assert self._reader is not None
        if layerName not in self._layers:
            raise KeyError(layerName)
        layer = self._loadLayer(self._reader, layerName, lazy, default)
        self._layers[layerName] = layer
        return layer

    def __contains__(self, name):
        return name in self._layers

    def __delitem__(self, name):
        if name == self.defaultLayer.name:
            raise KeyError("cannot delete default layer %r" % name)
        del self._layers[name]

    def __getitem__(self, name):
        if self._layers[name] is _NOT_LOADED:
            return self.loadLayer(name)
        return self._layers[name]

    def __iter__(self):
        for layer_name, layer_object in self._layers.items():
            if layer_object is _NOT_LOADED:
                yield self.loadLayer(layer_name)
            else:
                yield layer_object

    def __len__(self):
        return len(self._layers)

    def get(self, name, default=None):
        try:
            return self[name]
        except KeyError:
            return default

    def keys(self):
        return self._layers.keys()

    def __repr__(self):
        n = len(self._layers)
        return "<{}.{} ({} layer{}) at {}>".format(
            self.__class__.__module__,
            self.__class__.__name__,
            n,
            "s" if n > 1 else "",
            hex(id(self)),
        )

    @property
    def layerOrder(self):
        """The font's layer order.

        Getter:
            Returns the font's layer order.

        Note:
            The getter always returns a new list, modifications to it do not change
            the LayerSet.

        Setter:
            Sets the font's layer order. The set order value must contain all layers
            that are present in the LayerSet.
        """
        return list(self._layers)

    @layerOrder.setter
    def layerOrder(self, order):
        assert set(order) == set(self._layers)
        layers = OrderedDict()
        for name in order:
            layers[name] = self._layers[name]
        self._layers = layers

    def newLayer(self, name, **kwargs):
        """Creates and returns a named layer.

        Args:
            name: The layer name.
            kwargs: Arguments passed to the constructor of Layer.
        """
        if name in self._layers:
            raise KeyError("layer %r already exists" % name)
        self._layers[name] = layer = Layer(name, **kwargs)
        return layer

    def renameGlyph(self, name, newName, overwrite=False):
        """Renames a glyph across all layers.

        Args:
            name: The old name.
            newName: The new name.
            overwrite: If False, raises exception if newName is already taken in any
                layer. If True, overwrites (read: deletes) the old Glyph object.
        """
        # Note: this would be easier if the glyph contained the layers!
        if name == newName:
            return
        # make sure we're copying something
        if not any(name in layer for layer in self):
            raise KeyError("name %r is not in layer set" % name)
        # prepare destination, delete if overwrite=True or error
        for layer in self:
            if newName in layer:
                if overwrite:
                    del layer[newName]
                else:
                    raise KeyError("target name %r already exists" % newName)
        # now do the move
        for layer in self:
            if name in layer:
                layer[newName] = glyph = layer.pop(name)
                glyph._name = newName

    def renameLayer(self, name, newName, overwrite=False):
        """Renames a layer.

        Args:
            name: The old name.
            newName: The new name.
            overwrite: If False, raises exception if newName is already taken. If True,
                overwrites (read: deletes) the old Layer object.
        """
        if name == newName:
            return
        if not overwrite and newName in self._layers:
            raise KeyError("target name %r already exists" % newName)
        layer = self[name]
        del self._layers[name]
        self._layers[newName] = layer
        layer._name = newName

    def write(self, writer, saveAs=None):
        """Writes this LayerSet to a :class:`fontTools.ufoLib.UFOWriter`.

        Args:
            writer(fontTools.ufoLib.UFOWriter): The writer to write to.
            saveAs: If True, tells the writer to save out-of-place. If False, tells the
                writer to save in-place. This affects how resources are cleaned before
                writing.
        """
        if saveAs is None:
            saveAs = self._reader is not writer
        # if in-place, remove deleted layers
        layers = self._layers
        if not saveAs:
            for name in set(writer.getLayerNames()).difference(layers):
                writer.deleteGlyphSet(name)
        # write layers
        defaultLayer = self.defaultLayer
        for name, layer in layers.items():
            default = layer is defaultLayer
            if layer is _NOT_LOADED:
                if saveAs:
                    layer = self.loadLayer(name, lazy=False)
                else:
                    continue
            glyphSet = writer.getGlyphSet(name, defaultLayer=default)
            layer.write(glyphSet, saveAs=saveAs)
        writer.writeLayerContents(self.layerOrder)
