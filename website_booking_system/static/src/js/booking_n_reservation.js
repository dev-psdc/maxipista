/* Copyright (c) 2016-Present Webkul Software Pvt. Ltd. (<https://webkul.com/>) */
/* See LICENSE file for full copyright and licensing details. */
/* @License       : https://store.webkul.com/license.html */

odoo.define('website_booking_system.booking_n_reservation', function(require) {
    "use strict";

    var ajax = require('web.ajax');
    var core = require('web.core');
    var _t = core._t;

    var Days = {
        'sun' : 0,
        'mon' : 1,
        'tue' : 2,
        'wed' : 3,
        'thu' : 4,
        'fri' : 5,
        'sat' : 6,
    }

    $(document).ready(function() {

        var reset_total_price = function(){
            var bk_total_price = $('#booking_modal').find('.bk_total_price .oe_currency_value');
            bk_total_price.html('0.00');
        }

        var get_w_closed_days = function(w_c_days){
            var data = w_c_days.map(day => Days[day])
            return data
        }

        // Booking pop-up modal
        $('#booking_and_reservation').click(function(evnt){
            var appdiv = $('#booking_modal');
            var bk_loader = $('#bk_n_res_loader');
            var product_id = parseInt(appdiv.data('res_id'),10);
            var redirect = window.location.pathname;
            bk_loader.show();
            ajax.jsonRpc("/booking/reservation/modal", 'call',{
                'product_id' : product_id,
            })
            .then(function (modal) {
                bk_loader.hide();
                var $modal = $(modal);
                $modal.appendTo(appdiv)
                    .modal('show')
                    .on('hidden.bs.modal', function () {
                        $(this).remove();
                    });
                    // Booking Date Selection Picker
                    $(function () {
                        $('#bk_datepicker').datetimepicker({
                            format: 'YYYY-MM-DD',
                            icons: {
                                date: 'fa fa-calendar',
                                next: 'fa fa-chevron-right',
                                previous: 'fa fa-chevron-left',
                            },
                            // defaultDate : new Date(),
                            minDate : $('#bk_datepicker').data('bk_default_date'),
                            maxDate : $('#bk_datepicker').data('bk_end_date'),
                            daysOfWeekDisabled : get_w_closed_days($('#bk_datepicker').data('w_c_days')),
                        });
                    });

                    $('#bk_datepicker').on("change.datetimepicker", function (e) {
                    // $('#bk_datepicker').on("dp.change", function (e) {
                        var date = new Date(e.date);
                        var o_date = new Date(e.oldDate);
                        function GetFormate(num){
                            if(num<10)
                            {
                                return '0'+num;
                            }
                            return num
                        }
                        function GetFormattedDate(date) {
                            var month = GetFormate(date .getMonth() + 1);
                            var day = GetFormate(date .getDate());
                            var year = date .getFullYear();
                            return day + "/" + month + "/" + year;
                        }
                        if(GetFormattedDate(date) != GetFormattedDate(o_date)){
                            bk_loader.show();
                            ajax.jsonRpc("/booking/reservation/modal/update", 'call',{
                                'product_id' : product_id,
                                'new_date' : GetFormattedDate(date),
                            })
                            .then(function (result) {
                                bk_loader.hide();
                                if((date.getMonth() != o_date.getMonth()) || (date.getFullYear() != o_date.getFullYear())){
                                    var date_str = date.toUTCString();
                                    date_str = date_str.split(' ').slice(2,4)
                                    document.getElementById("dsply_bk_date").innerHTML = date_str.join(", ");
                                }
                                var bk_slots_main_div = appdiv.find('.bk_slots_main_div');
                                reset_total_price();
                                bk_slots_main_div.html(result);
                            });
                        }
                    });
            });
        });

        // Booking day slot selection
        $('#booking_modal').on('click','.bk_slot_div',function(evnt){
            var $this = $(this);
            var slot_plans = $this.data('slot_plans');
            var booking_modal = $('#booking_modal');
            var bk_loader = $('#bk_n_res_loader');
            var time_slot_id = parseInt($this.data('time_slot_id'),10);
            var model_plans = booking_modal.find('.bk_model_plans');
            var bk_modal_slots = booking_modal.find('.bk_modal_slots');
            var product_id = parseInt(booking_modal.data('res_id'),10);
            var bk_sel_date = $('#bk_sel_date');
            bk_loader.show();
            ajax.jsonRpc("/booking/reservation/slot/plans", 'call',{
                'time_slot_id' : time_slot_id,
                'slot_plans' : slot_plans,
                'sel_date' : bk_sel_date.val(),
                'product_id' : product_id,
            })
            .then(function (result) {
                bk_loader.hide();
                reset_total_price();
                model_plans.html(result);
            });
            bk_modal_slots.find('.bk_slot_div').not($this).each(function(){
                var $this = $(this);
                if($this.hasClass('bk_active')){
                    $this.removeClass('bk_active');
                }
            });
            if(!$this.hasClass('bk_active')){
                $this.addClass('bk_active');
            }
        });

        // Booking Week Day Selection
        $('#booking_modal').on('click','.bk_days',function(evnt){
            var $this = $(this);
            if($this.hasClass('bk_disable')){
                return false;
            };
            var booking_modal = $('#booking_modal');
            var bk_loader = $('#bk_n_res_loader');
            var product_id = parseInt(booking_modal.data('res_id'),10);
            var bk_week_days = booking_modal.find('.bk_week_days');
            var bk_model_cart = booking_modal.find('.bk_model_cart');
            var bk_model_plans = booking_modal.find('.bk_model_plans');
            var bk_slots_n_plans_div = booking_modal.find('.bk_slots_n_plans_div');
            var w_day = $this.data('w_day');
            var w_date = $this.data('w_date');
            var bk_sel_date = $('#bk_sel_date');
            bk_week_days.find('.bk_days').not($this).each(function(){
                var $this = $(this);
                if($this.hasClass('bk_active')){
                    $this.removeClass('bk_active');
                }
            });
            if(!$this.hasClass('bk_active')){
                $this.addClass('bk_active');
            }
            bk_loader.show();
            ajax.jsonRpc("/booking/reservation/update/slots", 'call',{
                'w_day' : w_day,
                'w_date' : w_date,
                'product_id' : product_id,
            })
            .then(function (result) {
                bk_loader.hide();
                reset_total_price();
                bk_slots_n_plans_div.html(result);
            });
            bk_sel_date.val(w_date);
        });

        // Booking quantity Selection
        $('#booking_modal').on('change','.bk_qty_sel',function(evnt){
            var bk_qty = parseInt($(this).val(), 10);
            var booking_modal = $('#booking_modal');
            // var add_qty = booking_modal.closest('form').find("input[name='add_qty']");
            var bk_base_price = parseFloat(booking_modal.find(".bk_plan_base_price .oe_currency_value").html(), 10);
            var bk_total_price = booking_modal.find('.bk_total_price .oe_currency_value');
            // add_qty.val(bk_qty);
            bk_total_price.html((bk_base_price*bk_qty).toFixed(2));
        });

        // Booking district Selection
        $('#booking_modal').on('change','.form-control',function(evnt){
            var mylist = $('#id_district');
            var listitems = mylist.children('option.sortMe').get();
            listitems.sort(function(a, b) {
               var compA = $(a).text().toUpperCase();
               var compB = $(b).text().toUpperCase();
               return (compA < compB) ? -1 : (compA > compB) ? 1 : 0;
            })
            $.each(listitems, function(idx, itm) { mylist.append(itm); });
        });

        // Booking sector Selection
        $('#booking_modal').on('change','.form-control',function(evnt){
            var mylist = $('#id_sector');
            var listitems = mylist.children('option.sortMe').get();
            listitems.sort(function(a, b) {
               var compA = $(a).text().toUpperCase();
               var compB = $(b).text().toUpperCase();
               return (compA < compB) ? -1 : (compA > compB) ? 1 : 0;
            })
            $.each(listitems, function(idx, itm) { mylist.append(itm); });
        });

        // Click on Book Now button on booking modal: submit a form available on product page
        $('#booking_modal').on('click','.bk-submit',function(event){
            var $this = $(this);
            var booking_modal = $('#booking_modal');
            var bk_loader = $('#bk_n_res_loader');
            var product_id = parseInt(booking_modal.data('res_id'),10);
            var bk_model_plans = booking_modal.find('.bk_model_plans').find("input[name='bk_plan']:checked");
            var bk_model_plans_1 = booking_modal.find('.bk_model_plans').find("input[name='bk_patient_name']").val();
            var bk_model_plans_2 = booking_modal.find('.bk_model_plans').find("input[name='bk_id_card']").val();
            var bk_model_plans_3 = booking_modal.find('.bk_model_plans').find("input[name='bk_birthday']").val();
            var bk_model_plans_4 = booking_modal.find('.bk_model_plans').find("input[name='sex']:checked");
            var bk_modal_err = booking_modal.find('.bk_modal_err');
            if(bk_model_plans.length == 0){
                bk_modal_err.html("Por favor seleccione un plan para continuar!").show();
                setTimeout(function() {
                    bk_modal_err.empty().hide()
                }, 3000);
            }
            else if (bk_model_plans_1 == ""){
                bk_modal_err.html("Por favor introduzca su nombre!").show();
                setTimeout(function() {
                    bk_modal_err.empty().hide()
                }, 3000);
            }
            else if (bk_model_plans_2 == ""){
                bk_modal_err.html("Por favor introduzca su cedula!").show();
                setTimeout(function() {
                    bk_modal_err.empty().hide()
                }, 3000);
            }
            else if (bk_model_plans_3 == ""){
                bk_modal_err.html("Por favor introduzca su fecha de nacimiento!").show();
                setTimeout(function() {
                    bk_modal_err.empty().hide()
                }, 3000);
            }
            else if (bk_model_plans_4.length == 0){
                bk_modal_err.html("Por favor introduzca su sexo!").show();
                setTimeout(function() {
                    bk_modal_err.empty().hide()
                }, 3000);
            }
            else{
                if (!event.isDefaultPrevented() && !$this.is(".disabled")) {
                    bk_loader.show();
                    ajax.jsonRpc("/booking/reservation/cart/validate", 'call',{
                        'product_id' : product_id,
                    })
                    .then(function (result) {
                        if(result == true){
                            event.preventDefault();
                            $this.closest('form').submit();
                        }
                        else{
                            bk_loader.hide();
                            bk_modal_err.html("Este producto ya está en su carrito. Elimínelo del carro e intente nuevamente.").show();
                            setTimeout(function() {
                                bk_modal_err.empty().hide()
                            }, 3000);
                        }
                    });
                }
            }
        });

        // Booking Slot Plan Selection
        $('#booking_modal').on('click', "input[name='bk_plan']", function(event){
            var booking_modal = $('#booking_modal');
            var bk_plan_div = $(this).closest('label').find('.bk_plan_div');
            var bk_plan_base_price = $('#booking_modal').find(".bk_plan_base_price .oe_currency_value");
            var base_price = parseInt(bk_plan_div.data('plan_price'), 10);
            var bk_total_price = booking_modal.find('.bk_total_price .oe_currency_value');
            var bk_qty = parseInt(booking_modal.find('.bk_qty_sel').val(),10);
            if(bk_plan_div.hasClass('bk_disable')){
                return false;
            };
            if(isNaN(base_price)){
                base_price = 0.0;
            }
            bk_plan_base_price.html(base_price.toFixed(2));
            bk_total_price.html((base_price*bk_qty).toFixed(2));
        });

        // Click on remove button available on sold out product in cart line
        $('.oe_website_sale').each(function() {
            var oe_website_sale = this;
            $(oe_website_sale).on('click', '.remove-cart-line', function() {
                var $dom = $(this).closest('tr');
                var td_qty = $dom.find('.td-qty');
                var line_id = parseInt(td_qty.data('line-id'), 10);
                var product_id = parseInt(td_qty.data('product-id'), 10);
                ajax.jsonRpc("/shop/cart/update_json", 'call', {
                    'line_id': line_id,
                    'product_id': product_id,
                    'set_qty': 0.0
                })
                .then(function(data) {
                    var $q = $(".my_cart_quantity");
                    $q.parent().parent().removeClass("hidden", !data.quantity);
                    $q.html(data.cart_quantity).hide().fadeIn(600);
                    location.reload();
                });
            });
        });
    });
});
