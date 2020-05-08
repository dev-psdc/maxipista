odoo.define('ae_odoo_customisation.filter_data', function (require) {
'use strict';

var ajax = require('web.ajax');

$(document).ready(function() {
    $('#booking_modal').on('click', 'select[name="province_id"]', function(ev) {
        ev.preventDefault();
        var province_id = ev.target.value;
        if (province_id) {
            ajax.jsonRpc("/booking/filterdata", 'call',{
                'province_id' : province_id,
            }).then(function (result) {
                if (result && result.districts) {
                    var options = '<option value=""> -- Seleccione Distrito -- </option>';
                    _.each(result.districts, function(district) {
                        var id = Object.keys(district)[0];
                        var name = district[id];
                        options += '<option class="sortMe" value="' + id + '">' + name + '</option>';
                    });
                    $('select#id_district').html(options);
                }
                if (result && result.regions) {
                    var options = '<option value=""> -- Seleccione Región -- </option>';
                    _.each(result.regions, function(region) {
                        var id = Object.keys(region)[0];
                        var name = region[id];
                        options += '<option class="sortMe" value="' + id + '">' + name + '</option>';
                    });
                    $('select[name="region_id"]').html(options);
                }
            });
        }
    });
    $('#booking_modal').on('change', 'select#id_district', function(ev) {
        ev.preventDefault();
        var district_id = ev.target.value;
        if (district_id) {
            ajax.jsonRpc("/booking/filterdata", 'call',{
                'district_id' : district_id,
            }).then(function (result) {
                if (result && result.sectors) {
                    var options = '<option value=""> -- Seleccione Corregimiento -- </option>';
                    _.each(result.sectors, function(sector) {
                        var id = Object.keys(sector)[0];
                        var name = sector[id];
                        options += '<option class="sortMe" value="' + id + '">' + name + '</option>';
                    });
                    $('select#id_sector').html(options);
                }
            });
        }        
    });
});
});
