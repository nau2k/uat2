odoo.define('wingroup_lib.WgDigitalSign', function (require) {
"use strict";

var AbstractAction = require('web.AbstractAction');
var ajax = require('web.ajax');
var core = require('web.core');
var rpc = require('web.rpc');
var session = require('web.session');
var web_client = require('web.web_client');
var _t = core._t;
var QWeb = core.qweb;

var WgDigitalSign = AbstractAction.extend({
    template: 'wg_digital_sign',
    events: {
         'click .sign_record': '_onclick_sign_record',
    },

    init: function(parent, state, params) {
        this.title = state.params.title;
        this.socket = state.params.socket;
        this.model = state.params.model;
        this.record_id = state.params.record_id;
        this.show_signed_file = state.params.show_signed_file;
        this.html_data = false;
        this.html_link = false;
        this.portal_token = this.portal_token;
        this.model = this.model;

        this._super.apply(this, arguments);

        this.ws = new WebSocket(this.socket);
        this.ws.onopen = function() {
            console.log("KL Connected.")
        };
        var self_init = this;
        this.ws.onmessage = function(evt) {
            var self = this;
            if (evt.data && JSON.parse(evt.data).dataSigned && JSON.parse(evt.data).dataSigned.contentB64) {
                $.ajax({
                    type: "POST",
                    url: "/post-sign?portal_token=" + self_init.portal_token,
                    dataType: "json",
                    data: {
                        'model': self_init.model,
                        'content': JSON.parse(evt.data).dataSigned.contentB64,
                        'serial': JSON.parse(evt.data).dataSigned.serial,
                        'issuer': JSON.parse(evt.data).dataSigned.issuer,
                        'subject': JSON.parse(evt.data).dataSigned.subject,
                        'valid_from': JSON.parse(evt.data).dataSigned.valid_from,
                        'valid_to': JSON.parse(evt.data).dataSigned.valid_to,
                    },                        
                    success: function(result){
                        self_init.do_action({
                            type: 'ir.actions.act_window',
                            res_model: self_init.model,
                            view_mode: 'form',
                            res_id: self_init.record_id,
                            views: [[false,'form']],
                        });
                    }
                });
            }
        };
        this.ws.onclose = function() {
            console.log("KL Connection is closed...");
        };
        this.ws.onerror = function(e) {
            console.log(e.msg);
        }
    },

    start: function() {
        console.log('start wg_digital_sign');
        var self = this;
        this.set("title", this.title);        
        return this._super().then(function() {
            self.render_dashboards();
        });
    },


    willStart: function() {
        console.log('willStart');
        var self = this;
        return $.when(ajax.loadLibs(this), this._super()).then(function() {
            return self.fetch_data();
        });
    },

    fetch_data: function() {
        var self = this;
        var def1 =  this._rpc({
            model: this.model,
            method: 'wg_get_data_to_show_sign',
            args: [[this.record_id], this.show_signed_file]
        }).then(function(result) {
            console.log('fetch_data', result);
            self.portal_token = result.portal_token;
            self.html_data = result.html_data;
            self.html_link = result.html_link;
            self.serialnumber = result.serialnumber;
        });
        return $.when(def1);
    },

    render_dashboards: function() {
        var self = this;
        if (self.html_link) {
            self.$('.o_dynamic_dashboard').append(
                '<div class="col-12"><iframe  style="width: 100%; min-height: 600px;" src="' + self.html_link +  '"></iframe></div>'
            );    
        } else {
            self.$('.o_dynamic_dashboard').append(
                '<div class="col-12">' + self.html_data +  '</div>'
            ); 
        }
        
    },

    _onclick_sign_record : function(e){
        var self = this;
        this._rpc({
            model: self.model,
            method: 'wg_get_xml_data_to_sign',
            args: [[this.record_id]]
        }).then(function(result) {
            console.log('_onclick_sign_record', result)
            self.ws.send(JSON.stringify(result));
        });
    },


});


core.action_registry.add('wg_digital_sign', WgDigitalSign);

return WgDigitalSign;

});
