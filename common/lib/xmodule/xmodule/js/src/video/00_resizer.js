(function (requirejs, require, define) {

define(
'video/00_resizer.js',
[],
function () {

    var Resizer = function (params) {
        var defaults = {
                container: window,
                element: null,
                containerRatio: null,
                elementRatio: null
            },
            callbacksList = [],
            module = {},
            mode = null,
            config;

        initialize.apply(module, arguments);

        return $.extend(true, module, {
            align: align,
            alignByWidthOnly: alignByWidthOnly,
            alignByHeightOnly: alignByHeightOnly,
            setParams: initialize,
            setMode: setMode,
            callbacks: {
                add: addCallback,
                once: addOnceCallback,
                remove: removeCallback,
                removeAll: removeCallbacks
            }
        });
    };

    Resizer.prototype = {
        initialize: initialize,
        getData: getData,
        align: align,
        alignByWidthOnly: alignByWidthOnly,
        alignByHeightOnly: alignByHeightOnly,
        setMode: setMode,
        addCallback: addCallback,
        addOnceCallback: addOnceCallback,
        fireCallbacks: fireCallbacks,
        removeCallbacks: removeCallbacks,
        removeCallback: removeCallback
    };

    return Resizer;

    function initialize(params) {
        if (config) {
            config = $.extend(true, config, params);
        } else {
            config = $.extend(true, {}, defaults, params);
        }

        if (!config.element) {
            console.log(
                '[Video info]: Required parameter `element` is not passed.'
            );
        }

        return module;
    }

    function getData() {
        var container = $(config.container),
            containerWidth = container.width(),
            containerHeight = container.height(),
            containerRatio = config.containerRatio,

            element = $(config.element),
            elementRatio = config.elementRatio;

        if (!containerRatio) {
            containerRatio = containerWidth/containerHeight;
        }

        if (!elementRatio) {
            elementRatio = element.width()/element.height();
        }

        return {
            containerWidth: containerWidth,
            containerHeight: containerHeight,
            containerRatio: containerRatio,
            element: element,
            elementRatio: elementRatio
        };
    }

    function align() {
        var data = getData();

        switch (mode) {
            case 'height':
                alignByHeightOnly();
                break;

            case 'width':
                alignByWidthOnly();
                break;

            default:
                if (data.containerRatio >= data.elementRatio) {
                    alignByHeightOnly();

                } else {
                    alignByWidthOnly();
                }
                break;
        }

        fireCallbacks();

        return module;
    }

    function alignByWidthOnly() {
        var data = getData(),
            height = data.containerWidth/data.elementRatio;

        data.element.css({
            'height': height,
            'width': data.containerWidth,
            'top': 0.5*(data.containerHeight - height),
            'left': 0
        });

        return module;
    }

    function alignByHeightOnly() {
        var data = getData(),
            width = data.containerHeight*data.elementRatio;

        data.element.css({
            'height': data.containerHeight,
            'width': data.containerHeight*data.elementRatio,
            'top': 0,
            'left': 0.5*(data.containerWidth - width)
        });

        return module;
    }

    function setMode(param) {
        if (_.isString(param)) {
            mode = param;
            align();
        }

        return module;
    }

    function addCallback(func) {
        if ($.isFunction(func)) {
            callbacksList.push(func);
        } else {
            console.error('[Video info]: TypeError: Argument is not a function.');
        }

        return module;
    }

    function addOnceCallback(func) {
        if ($.isFunction(func)) {
            var decorator = function () {
                func();
                removeCallback(func);
            };

            addCallback(decorator);
        } else {
            console.error('[Video info]: TypeError: Argument is not a function.');
        }

        return module;
    }

    function fireCallbacks() {
        $.each(callbacksList, function(index, callback) {
             callback();
        });
    }

    function removeCallbacks() {
        callbacksList.length = 0;

        return module;
    }

    function removeCallback(func) {
        var index = $.inArray(func, callbacksList);

        if (index !== -1) {
            return callbacksList.splice(index, 1);
        }
    }
});

}(RequireJS.requirejs, RequireJS.require, RequireJS.define));
