// Copyright © 2016 Jeffery Harrell <jefferyharrell@gmail.com>
// See file 'LICENSE' for use and warranty information.
//
// This program is free software; you can redistribute it and/or modify
// it under the terms of the GNU General Public License as published by
// the Free Software Foundation, either version 3 of the License, or
// (at your option) any later version.
//
// This program is distributed in the hope that it will be useful,
// but WITHOUT ANY WARRANTY; without even the implied warranty of
// MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
// GNU General Public License for more details.
//
// You should have received a copy of the GNU General Public License
// along with this program.  If not, see <http://www.gnu.org/licenses/>.

define(
    ['freeipa/ipa', 'freeipa/menu', 'freeipa/phases', 'freeipa/reg', 'freeipa/rpc', 'freeipa/net'],
    function(IPA, menu, phases, reg, rpc, NET) {
    // dependencies path: install/ui/src/freeipa

        var exp = IPA.alm = {};
    //different types of facets:
    //Details: for output of user-show command
    //Search: for user-find
    //Association: to display member*
    //Nested search: special kind of search for nested objects (eg. automount keys in automount maps)

//// Validators ///////////////////////////////////////////////////////////////


        // IPA.almrange_validator = function(spec) {

        //     spec = spec || {};
        //     spec.message = spec.message || 'Range must be of the form x.x.x.x y.y.y.y, where x.x.x.x is the first IP address in the pool and y.y.y.y is the last IP address in the pool.';
        //     var that = IPA.validator(spec);

        //     that.validate = function(value) {
        //         if (IPA.is_empty(value)) return that.true_result();

        //         that.address_type = 'IPv4';

        //         var components = value.split(" ");
        //         if (components.length != 2) {
        //             return that.false_result();
        //         }

        //         var start = NET.ip_address(components[0]);
        //         var end = NET.ip_address(components[1]);

        //         if (!start.valid || start.type != 'v4-quads' || !end.valid || end.type != 'v4-quads') {
        //             return that.false_result();
        //         }

        //         return that.true_result();
        //     };

        //     that.almrange_validate = that.validate;
        //     return that;
        // };


        // IPA.almrange_subnet_validator = function(spec) {
        //     spec = spec || {};
        //     spec.message = spec.message || 'Invalid IP range.';
        //     var that = IPA.validator(spec);

        //     that.validate = function(value, context) {
        //         if (context.container.rangeIsValid) {
        //             return that.true_result();
        //         }
        //         that.message = context.container.invalidRangeMessage;
        //         return that.false_result();
        //     }

        //     that.almrange_subnet_validate = that.validate;
        //     return that;
        // };


//// Factories ////////////////////////////////////////////////////////////////


        // IPA.alm.almpool_adder_dialog = function(spec) {
        //     spec = spec || {}; //调用函数的时候如果 options 没指定，就给它赋值 {} , {} 是一个空的 Object。
        //     var that = IPA.entity_adder_dialog(spec);

        //     that.previous_almrange = [];

        //     that.rangeIsValid = false;
        //     that.invalidRangeMessage = "Invalid IP range."

        //     that.create_content = function() {
        //         that.entity_adder_dialog_create_content();
        //         var almrange_widget = that.fields.get_field('almrange').widget;
        //         almrange_widget.value_changed.attach(that.almrange_changed);
        //     };

        //     that.almrange_changed = function() {

        //         var almrange_widget = that.fields.get_field('almrange').widget;
        //         var almrange = almrange_widget.get_value();
        //         var name_widget = that.fields.get_field('cn').widget;
        //         var name = name_widget.get_value();

        //         if (name.length == 0) {
        //             name_widget.update(almrange);
        //         }

        //         if (name.length > 0 && name[0] == that.previous_almrange) {
        //             name_widget.update(almrange);
        //         }

        //         that.previous_almrange = almrange;

        //         // var firstValidationResult = that.fields.get_field('almrange').validators[0].validate(that.fields.get_field('almrange').get_value()[0])

        //         // if (firstValidationResult.valid) {
        //         //     setValidFlagCommand = rpc.command({
        //         //         entity: 'almpool',
        //         //         method: 'is_valid',
        //         //         args: that.pkey_prefix.concat([almrange]),
        //         //         options: {},
        //         //         retry: false,
        //         //         on_success: that.setValidFlag
        //         //     });
        //         //     setValidFlagCommand.execute();
        //         // }
        //     }

        //     that.setValidFlag = function(data, text_status, xhr) {
        //         that.rangeIsValid = data.result.result;
        //         that.invalidRangeMessage = data.result.value;
        //         that.validate();
        //     }

        //     return that;
        // }


//// almservice //////////////////////////////////////////////////////////////


        var make_almservice_spec = function() {
            return {
                name: 'almservice',
                defines_key: false,
                facets: [
                    {
                        $type: 'details',
                        sections: [
                            {
                                name: 'options',
                                label: 'Options',
                                fields: [
                                    {
                                        name: 'domainname',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'domainnameservers',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'domainsearch',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        name: 'defaultleasetime',
                                        measurement_unit: 'seconds',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        name: 'maxleasetime',
                                        measurement_unit: 'seconds',
                                        flags: ['w_if_no_aci']
                                    },
                                ]
                            },
                            {
                                name: 'almparameters',
                                label: 'alm Parameters',
                                fields: [
                                    {
                                        name: 'almprimarydn',
                                        read_only: true,
                                        formatter: 'dn'
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'almsecondarydn',
                                        read_only: true,
                                        formatter: 'dn'
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'almstatements',
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'almoption',
                                    },
                                    {
                                        $type: 'textarea',
                                        name: 'almcomments'
                                    }
                                ]
                            }
                        ]
                    }
                ]
            };
        };
        exp.almservice_entity_spec = make_almservice_spec();


//// almpool /////////////////////////////////////////////////////////////////


        var make_almpool_spec = function() {
            return {
                name: 'almpool',
                containing_entity: 'almservice',
                facets: [
                    {
                        $type: 'search',
                        columns: [
                            'cn',
                            'almpooltype',
                            'almrange'
                        ]
                    },
                    {
                        $type: 'details',
                        sections: [
                            {
                                name: 'options',
                                label: 'Options',
                                fields: [
                                    {
                                        name: 'defaultleasetime',
                                        measurement_unit: 'seconds',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        name: 'maxleasetime',
                                        measurement_unit: 'seconds',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        $type: 'checkbox',
                                        name: 'permitknownclients',
                                        flags: ['w_if_no_aci']
                                    },
                                    {
                                        $type: 'checkbox',
                                        name: 'permitunknownclients',
                                        flags: ['w_if_no_aci']
                                    },
                                ]
                            },
                            {
                                name: 'almparameters',
                                label: 'alm Parameters',
                                fields: [
                                    {
                                        name: 'cn'
                                    },
                                    {
                                        name: 'almrange'
                                    },
                                    {
                                        name: 'almpooltype'
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'almpermitlist'
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'almstatements'
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'almoption'
                                    },
                                    {
                                        $type: 'textarea',
                                        name: 'almcomments'
                                    }
                                ]
                            }
                        ],
                        actions: [
                            'delete'
                        ],
                        header_actions: ['delete']
                    }
                ],
                adder_dialog: {
                    fields: [
                        {
                            //$type: 'entity_select',
                            name: 'cn',
                            required: true
                        },
                        {
                            name: 'almrange',
                            required: true
                        },
                        {
                            name: 'almpooltype',
                            required: true
                        }
                    ]
                },
                deleter_dialog: {
                    fields: [
                        {
                            //$type: 'entity_select',
                            name: 'cn',
                            required: true
                        },
                        {
                            name: 'almrange',
                            required: true
                        },
                        {
                            name: 'almpooltype',
                            required: true
                        }
                    ]
                }
            };
        };
        exp.almpool_entity_spec = make_almpool_spec();

//// almlease /////////////////////////////////////////////////////////////////

        var make_almleases_spec = function() {
            return {
                name: 'almleases',
                containing_entity: 'almservice',
                facets: [
                    {
                        $type: 'search',
                        columns: [
                            'cn',
                            'almstatements'
                        ],
                        actions: [
                            'release'
                        ],
                        header_actions: ['release'
                        ]
                    },
                    {
                        $type: 'details',
                        sections: [
                            {
                                name: 'almparameters',
                                label: 'alm Parameters',
                                fields: [
                                    {
                                        name: 'cn'
                                    },
                                    {
                                        name: 'almaddressstate',
                                    },
                                    {
                                        name: 'almleasestarttime'
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'almstatements'
                                    },
                                    {
                                        $type: 'multivalued',
                                        name: 'almoption'
                                    },
                                    {
                                        $type: 'textarea',
                                        name: 'almcomments'
                                    }
                                ]
                            }
                        ],
                        actions: [
                            'release'
                        ],
                        header_actions: ['release'
                        ]
                    }
                ],
                adder_dialog: {
                	//name: 'lease',
            		//method: 'alm_lease',
                    fields: [
                        {
                            name: 'clientid',
                            required: true
                        },
                        {
                            name: 'poolname',
                            required: true
                        },
                        {
                            name: 'almpooltype',
                            required: true
                        },
                        {
                            name: 'requiredaddress'
                        },
                        {
                        	name: 'expires'
                        }
                    ]
                }

            };
        };
        exp.almleases_entity_spec = make_almleases_spec();
//// alm.action ///////////////////////////////////////////////////////////////
// IPA.alm.create_lease_action = function(spec) {

//     spec = spec || {};

//     spec.name = spec.name || 'create_alm_lease';
//     spec.label = spec.label || 'create_alm_lease';

//     var that = IPA.action(spec);

//     that.execute_action = function() {
//         var spec = {
//             title: '@i18n:objects.almleases.create_lease',
//             message: '@i18n:objects.almleases.create_lease_msg',
//             ok_label: '@i18n:objects.almleases.create_lease.'
//         };

//         that.dialog = IPA.confirm_dialog(spec);

//         that.dialog.on_ok = function() {

//             var command = rpc.command({
//                 //entity: 'almleases',
//                 method: 'alm_lease',
//                 //args: 
//                 options: {
//                     clientid: 'uitester',
//                     poolname: 'uitestpool',
//                     almpooltype: 'ipv4'
//                 }
//             });

//             command.execute();
//         };

//         that.dialog.open();
//     };

//     return that;
// };

// alm_release //////////////////////////////////////////////////////////////
// IPA.user.release_action = function(spec) {
//     spec = spec || {};
//     spec.name = spec.name || 'delete_alm_lease';
//     spec.label = spec.label || '@i18n:buttons.remove';

//     var that = IPA.action(spec);

//     that.execute_action = function(facet) {

//         var pkey = facet.get_pkey();
//         var msg = text.get('@i18n:actions.delete_confirm');
//         msg = msg.replace('${object}', pkey);

//         var spec = {
//             message: msg,
//             on_ok: function() {
//                 rpc.command({
//                     //entity: facet.entity.name,
//                     method: 'alm_release',
//                     //args: [pkey],
//                     options: {
//                         clientid: facet[1].sections[0].fields[3].name[0];
//                         poolname: facet[1].sections[0].fields[3].name[1];
//                         almpooltype: facet[1].sections[0].fields[3].name[2];
//                         leasedaddress: facet[1].sections[0].fields[3].name[3];
//                         //preserve: dialog.option_radio.get_value()[0]
//                     },
//                     on_success: function(data) {
//                         IPA.notify_success(data.result.summary);
//                         facet.on_update.notify();
//                         facet.redirect();
//                     }
//                 }).execute();
//             }
//         };

//         var dialog = IPA.user.details_delete_dialog(spec);

//         dialog.open();
//     };

//     return that;
// };
/// release two ////////////////
        exp.release_action = function(spec) {
            spec = spec || {};
            spec.name = spec.name || 'release';
            spec.method = spec.method || 'alm_release';
            spec.label = spec.label || '@i18n:buttons.revoke';
            spec.needs_confirm = spec.needs_confirm !== undefined ? spec.needs_confirm : true;
            spec.confirm_msg = spec.confirm_msg || '@i18n:actions.delete_confirm';
            //spec.disable_cond = spec.disable_cond || ['oc_posixgroup','oc_ipaexternalgroup'];
            //exp.entity.get_facet()
            //var facets = facet.entity.facets;
            //spec.options = 
            //                 clientid: facet.sections[0].fields[3].name[0].split(' ')[1],
            //                 poolname: facet.sections[0].fields[3].name[1].split(' ')[1],
            //                 almpooltype: facet.sections[0].fields[3].name[2].split(' ')[1],
            //                 leasedaddress: facet.sections[0].fields[3].name[3].split(' ')[1]
            //                 //preserve: dialog.option_radio.get_value()[0]
            // };
        
            var that = IPA.object_action(spec);

            that.execute_action = function(facet, on_success, on_error) {
            	//var arg = facet.get_facet_groups();
            	//var summary = data.result.summary || {};
            	console.log(facet);
            	var data = facet.data.result.result;

            	//console.log(IPA.field);
            	var data2options = {
            						"clientid": data.almstatements[0].split(' ')[1],
            						"poolname": data.almstatements[1].split(' ')[1],
            						"almpooltype": data.almstatements[2].split(' ')[1],
            						"leasedaddress": data.almstatements[3].split(' ')[1],
            	}

            	
                rpc.command({
                //entity: entity_name,
                method: that.method,
                args: [],//facet.get_facet_groups(),
                options: data2options,
                on_success: that.get_on_success(facet, on_success),
                on_error: that.get_on_error(facet, on_error)
                }).execute();

                //facet.close();
            };

            return that;
        };

//// exp.register /////////////////////////////////////////////////////////////


        exp.register = function() {
            // var v = reg.validator;
            // v.register('almrange', IPA.almrange_validator);
            // v.register('almrange_subnet', IPA.almrange_subnet_validator);
            var a = reg.action;
            var e = reg.entity;
            

            a.register('release', exp.release_action);
            e.register({type: 'almservice', spec: exp.almservice_entity_spec});
            // e.register({type: 'almsubnet', spec: exp.almsubnet_entity_spec});
            e.register({type: 'almpool', spec: exp.almpool_entity_spec});
            e.register({type: 'almleases', spec: exp.almleases_entity_spec});
            // e.register({type: 'almserver', spec: exp.almserver_entity_spec});
            
        }


//// menu spec ////////////////////////////////////////////////////////////////


        exp.alm_menu_spec = {
            name: 'alm',
            label: 'Address lease manager',
            children: [
                {
                    entity: 'almservice',
                    label: 'Configuration',
                    children: [
                        {
                            entity: 'almpool',
                            label: 'Address pools'
                            //hidden: true
                        },
                        {
                            entity: 'almleases',
                            label: 'Leases'
                            //hidden: true
                        }
                    ]
                }

            ]
        }

        exp.add_menu_items = function() {
            network_services_item = menu.query({name: 'network_services'});
            if (network_services_item.length > 0) {
                menu.add_item( exp.alm_menu_spec, 'network_services' );
            }
        };


//// customize_host_ui ////////////////////////////////////////////////////////


        exp.customize_host_ui = function() {
            var adder_dialog = IPA.host.entity_spec.adder_dialog;
            var fields = adder_dialog.sections[1].fields;
            var macaddress_field_spec = {
                $type: 'multivalued',
                name: 'macaddress'
            }
            fields.splice(2, 0, macaddress_field_spec)
        };


//// phases ///////////////////////////////////////////////////////////////////


        phases.on('customization', exp.customize_host_ui);
        phases.on('registration', exp.register);
        phases.on('profile', exp.add_menu_items, 20);

        return exp;

    }
);
