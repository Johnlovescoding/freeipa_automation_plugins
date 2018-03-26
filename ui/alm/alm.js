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
    ['freeipa/ipa', 'freeipa/menu', 'freeipa/phases', 'freeipa/reg', 'freeipa/rpc', 'freeipa/net', 'freeipa/search', 'freeipa/text'],
    function(IPA, menu, phases, reg, rpc, NET, mod_search, text) {
    // dependencies path: install/ui/src/freeipa

        var exp = IPA.alm = {};

//// modify search_facet //////////////////////////////////////////////
        IPA.alm.leases_search_facet = function(spec) {
            spec = spec || {};

            var that = IPA.search_facet(spec);
            
            //var dataResult = that.data.result.result;

            that.create_remove_dialog = function() {
                var values = that.get_selected_values();

                var title;
                if (!values.length) {
                    title = text.get('@i18n:dialogs.remove_empty');
                    window.alert(title);
                    return null;
                }
                var dataResult = that.data.result.result;
                dialog = IPA.alm.leases_search_deleter_dialog({}, dataResult);
                //dialog.dataResult = dataResult;

                dialog.entity_name = that.managed_entity.name;
                dialog.entity = that.managed_entity;
                dialog.facet = that;
                dialog.pkey_prefix = that.managed_entity_pkey_prefix();

                title = text.get('@i18n:dialogs.remove_title');
                var label = that.managed_entity.metadata.label;
                dialog.title = title.replace('${entity}', label);

                dialog.set_values(values);

                return dialog;
            };


            return that;
        };


//// modify search_deleter_dialog //////////////////////////////////////////////
        IPA.alm.leases_search_deleter_dialog = function(spec, dataResult) {
            
            spec = spec || {};

            var that = IPA.search_deleter_dialog(spec);

            that.create_command = function() {
                var batch = rpc.batch_command({
                    error_message: '@i18n:search.partial_delete',
                    name: that.entity.name + '_batch_del'
                });

                console.log(dataResult);
                ///extend values with statements
                for (var i = 0; i < that.values.length; i++) {
                    for (var j = 0; j < dataResult.length; j++) {
                        if (that.values[i] === dataResult[j].cn[0]) {
                            that.values[i] = {
                                cn : that.values[i],
                                almstatements : dataResult[j].almstatements
                            };
                        }
                    }
                }
                console.log(that.values);   



                for (var i=0; i<that.values.length; i++) {
                    //console.log(table);
                    //console.log(that);
                    var command = rpc.command({
                        entity: 'alm',
                        method: 'release'
                    });

                    //if (that.pkey_prefix.length) command.add_args(that.pkey_prefix);

                    var value = that.values[i];
                    if (value instanceof Object) {
                        if (value.hasOwnProperty("almstatements")) {
                            command.set_option("clientid", value.almstatements[0].split(' ')[1]);
                            command.set_option("poolname", value.almstatements[1].split(' ')[1]);
                            command.set_option("almpooltype", value.almstatements[2].split(' ')[1]);
                            command.set_option("leasedaddress", value.almstatements[3].split(' ')[1]);
                        }
                    }

                    var add_attrs = that.additional_table_attrs;
                    if (add_attrs && add_attrs.length && add_attrs.length > 0) {
                        command = that.extend_command(command, add_attrs, value);
                    }

                    batch.add_command(command);
                }

                return batch;
            };

            return that;
        };


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
                        $factory: IPA.alm.leases_search_facet,
                        //no_update: true,
                        columns: [
                            'cn',
                            'almstatements'
                        ],
                        deleter_dialog: {
                            $factory: IPA.alm.leases_search_deleter_dialog
                        }
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
                ]
            };
        };
        exp.almleases_entity_spec = make_almleases_spec();

/// release action ////////////////
        exp.release_action = function(spec) {
            spec = spec || {};
            spec.name = spec.name || 'release';
            spec.method = spec.method || 'alm_release';
            spec.label = spec.label || '@i18n:buttons.revoke';
            spec.needs_confirm = spec.needs_confirm !== undefined ? spec.needs_confirm : true;
            spec.confirm_msg = spec.confirm_msg || '@i18n:actions.delete_confirm';

        
            var that = IPA.object_action(spec);

            that.execute_action = function(facet, on_success, on_error) {
            	//var arg = facet.get_facet_groups();
            	//var summary = data.result.summary || {};
            	//console.log(facet);
            	var data = facet.data.result.result;

            	//console.log(IPA.field);
            	var data2options = {
            						"clientid": data.almstatements[0].split(' ')[1],
            						"poolname": data.almstatements[1].split(' ')[1],
            						"almpooltype": data.almstatements[2].split(' ')[1],
            						"leasedaddress": data.almstatements[3].split(' ')[1]
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
            a.register('release', exp.release_action);
            
            var e = reg.entity;
            //var d = reg.dialog;
            //var fa = reg.facet;
            e.register({type: 'almservice', spec: exp.almservice_entity_spec});
            // e.register({type: 'almsubnet', spec: exp.almsubnet_entity_spec});
            e.register({type: 'almpool', spec: exp.almpool_entity_spec});
            e.register({type: 'almleases', spec: exp.almleases_entity_spec});
            //d.register('')
            // e.register({type: 'almserver', spec: exp.almserver_entity_spec});
            
        };


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
        };

        exp.add_menu_items = function() {
            //top = menu.get();
            //console.log(top);
            menu.add_item( exp.alm_menu_spec, 'network_services');
            //menu.add_item( exp.alm_menu_spec, 'admin');
            //top.push(exp.alm_menu_spec);
            //network_services_item = menu.query({name: 'network_services'});
            // if (network_services_item.length > 0) {
            //     menu.add_item( exp.alm_menu_spec, 'network_services' );
            // }
        };


//// customize_host_ui ////////////////////////////////////////////////////////


        exp.customize_host_ui = function() {
            var adder_dialog = IPA.host.entity_spec.adder_dialog;
            var deleter_dialog = IPA.alm.leases_search_deleter_dialog;
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
