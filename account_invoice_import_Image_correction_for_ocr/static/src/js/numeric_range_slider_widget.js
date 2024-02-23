odoo.define('account_invoice_import_Image_correction_for_ocr.custom_image_correction', function (require) {
    "use strict";

    var core = require('web.core');
    var _t = core._t;

    var FormController = require('web.FormController');

    FormController.include({
        renderButtons: function ($node) {
            this._super.apply(this, arguments);
            if (this.$buttons) {
                this.$buttons.find('.oe_stat_button.fa-arrow-circle-o-left').click(this._onClickPresetMin.bind(this));
                this.$buttons.find('.oe_stat_button.fa-dot-circle-o').click(this._onClickPresetMid.bind(this));
                this.$buttons.find('.oe_stat_button.fa-arrow-circle-o-right').click(this._onClickPresetMax.bind(this));
            }
        },

        _onClickPresetMin: function () {
            this._setMonochromeThreshold(70);
            console.log("Running?")
        },

        _onClickPresetMid: function () {
            this._setMonochromeThreshold(129);
        },

        _onClickPresetMax: function () {
            this._setMonochromeThreshold(180);
        },

        _setMonochromeThreshold: function (threshold) {
            var self = this;
            var record = this.model.get(this.handle);
            if (record) {
                record.monochrome_threshold = threshold;
                this.model.save(record).then(function () {
                    self.reload();
                });
            }
        },
    });

});



// odoo.define(
//   "account_invoice_import_Image_correction_for_ocr.samda_widget",
//   function (require) {
//     "use strict";

//     var Widget = require("web.Widget");
//     var core = require("web.core");

//     var SamdaWidget = Widget.extend({
//       init: function (parent, options) {
//         this._super.apply(this, arguments);
//       },
//       start: function () {
//         this._super.apply(this, arguments);
//         this._setupPresetButtonHandlers();
//       },
//       _setupPresetButtonHandlers: function () {
//         var self = this;

//         this.$(".oe_stat_button.fa-arrow-circle-o-left").click(function () {
//           self._handlePreset("min");
//         });

//         this.$(".oe_stat_button.fa-dot-circle-o").click(function () {
//           self._handlePreset("mid");
//         });

//         this.$(".oe_stat_button.fa-arrow-circle-o-right").click(function () {
//           self._handlePreset("max");
//         });
//       },
//       _handlePreset: function (preset) {
//         var currentThreshold = this.model.get(
//           this.handle,
//           "monochrome_threshold"
//         );

//         var newThreshold;
//         if (preset === "min") {
//           newThreshold = 70;
//         } else if (preset === "mid") {
//           newThreshold = 129;
//         } else if (preset === "max") {
//           newThreshold = 180;
//         }

//         if (currentThreshold !== newThreshold) {
//           this.model.set(this.handle, "monochrome_threshold", newThreshold);
//           this.model.save(this.handle);
//         }
//       },
//     });

//     core.action_registry.add(
//       "account_invoice_import.ImageCorrection",
//       SamdaWidget
//     );

//     return SamdaWidget;
//   }
// );
















// odoo.define('account_invoice_import_Image_correction_for_ocr.samda_widget', function (require) {
//     'use strict';

//     var Widget = require('web.Widget');
//     var core = require('web.core');
//     var _t = core._t;

//     var SamdaWidget = Widget.extend({
//         template: 'account_invoice_import_Image_correction_for_ocr.samda_widget',
        
//         init: function (parent, monochromeThreshold, presetValues) {
//             this._super.apply(this, arguments);
//             this.monochromeThreshold = monochromeThreshold || 129; // Default value
//             this.presetValues = presetValues || [];
//         },

//         start: function () {
//             this.$('.oe_button').on('click', this._onPresetButtonClick.bind(this));
//             this._updateThresholdDisplay();
//             return this._super.apply(this, arguments);
//         },

//         _onPresetButtonClick: function (event) {
//             var presetValue = parseInt(event.currentTarget.dataset.presetValue);
//             this._setValue(presetValue);
//         },

//         _setValue: function (value) {
//             this.monochromeThreshold = value;
//             this._updateThresholdDisplay();
//         },

//         _updateThresholdDisplay: function () {
//             this.$('span').text(this.monochromeThreshold);
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

