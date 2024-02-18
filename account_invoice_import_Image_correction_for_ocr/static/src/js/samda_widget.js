odoo.define('account_invoice_import_Image_correction_for_ocr.samda_widget', function (require) {
    'use strict';

    var Widget = require('web.Widget');
    var core = require('web.core');
    var _t = core._t;

    var SamdaWidget = Widget.extend({
        template: 'account_invoice_import_Image_correction_for_ocr.samda_widget',
        
        init: function (parent, monochromeThreshold, presetValues) {
            this._super.apply(this, arguments);
            this.monochromeThreshold = monochromeThreshold || 129; // Default value
            this.presetValues = presetValues || [];
        },

        start: function () {
            this.$('.oe_button').on('click', this._onPresetButtonClick.bind(this));
            this._updateThresholdDisplay();
            return this._super.apply(this, arguments);
        },

        _onPresetButtonClick: function (event) {
            var presetValue = parseInt(event.currentTarget.dataset.presetValue);
            this._setValue(presetValue);
        },

        _setValue: function (value) {
            this.monochromeThreshold = value;
            this._updateThresholdDisplay();
        },

        _updateThresholdDisplay: function () {
            this.$('span').text(this.monochromeThreshold);
        },
    });

    core.form_widget_registry.add('samda_widget', SamdaWidget);

    return SamdaWidget;
});





















// odoo.define('account_invoice_import_Image_correction_for_ocr.samda_widget', function (require) {
//     'use strict';

//     var Widget = require('web.Widget');
//     var core = require('web.core');

//     var SamdaWidget = Widget.extend({
//         template: 'account_invoice_import_Image_correction_for_ocr.samda_widget',
        
//         init: function (parent, monochromeThreshold, presetValues) {
//             this._super.apply(this, arguments);
//             this.monochromeThreshold = monochromeThreshold || 129; // Default value
//             this.presetValues = presetValues || [];
//         },

//         start: function () {
//             this.$el.find('.oe_button').on('click', this._onPresetButtonClick.bind(this));
//             this._updateThresholdDisplay();
//             return this._super.apply(this, arguments);
//         },

//         _onPresetButtonClick: function (event) {
//             var presetValue = parseInt($(event.currentTarget).data('preset-value'));
//             this._setValue(presetValue);
//         },

//         _setValue: function (value) {
//             this.monochromeThreshold = value;
//             this._updateThresholdDisplay();
//         },

//         _updateThresholdDisplay: function () {
//             this.$el.find('span').text(this.monochromeThreshold);
//         },
//     });

//     core.form_widget_registry.add('samda_widget', SamdaWidget);

//     return SamdaWidget;
// });




// odoo.define('account_invoice_import_Image_correction_for_ocr.samda_widget', function (require) {
//     'use strict';

//     var Widget = require('web.Widget');
//     var core = require('web.core');

//     var SamdaWidget = Widget.extend({
//         template: 'account_invoice_import_Image_correction_for_ocr.samda_widget',
//         init: function (parent, value) {
//             this._super.apply(this, arguments);
//             this.value = value || 'Default Value';
//         },
//         start: function () {
//             this.$el.text(this.value);
//             return this._super.apply(this, arguments);
//         },
//     });

//     core.form_widget_registry.add('samda_widget', SamdaWidget);

//     return SamdaWidget;
// });

