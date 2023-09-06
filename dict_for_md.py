#MB_Dict = { 
#    1: {
#        '0' : 'leakage_fsm_status' ,
#        '1' : 'pwm_ctrl_status' ,
#        '2' : 'lock_engine_status_fsm' ,
#        '3' : 'relay_status_fsm' ,
#        '4' : 'state_3V' ,
#        '5' : 'state_0V' ,
#        '6' : 'state_6V' ,
#        '7' : 'state_9V' ,
#        '8' : 'state_12V' ,
#        '9' : 'state_Neg' ,
#        '10' : 'state_Invalid' ,
#        '11' : 'flag_has_plug_lockengine' ,
#        '12' : 'flag_phase_is_trifase' ,
#        '13' : 'flag_has_rfid_reader' ,
#        '14' : 'flag_has_car_powermeter_mid' ,
#        '15' : 'flag_has_domestic_powermeter' ,
#        '16' : 'flag_enable_fixed_pw_inhibit_mid' ,
#        '17' : 'flag_inverter_presence' ,
#        '18' : 'flag_has_started_pwm_fsm' ,
#        '19' : 'flag_simplified_pilot_mode' ,
#        '20' : 'flag_old_board_type' ,
#        '21' : 'flag_board_initial_collaudo' ,
#        '22' : 'CMPB' ,
#        '23' : 'flag_recharge_enabled' ,
#        '24' : 'wallbox_state' ,
##        '25' : 'Alarm_Id' ,
#        '26' : 'Alarm_Param' ,
#        '27' : 'Alarm_Severity',
#        '28' : 'Alarm_Action_Type',
#    },
#    2: {
#        '0' : 'Led_Brightness' ,
#        '1' : 'Led_Color' ,
#        '2' : 'Led_Blinking' ,
##        '3' : 'Power_Meter_Id' ,
#        '4' : 'Power_Meter_Id_Owner' ,
#        '5' : 'Pm_Voltage' ,
#        '6' : 'Pm_Voltage_Phase2' ,
#        '7' : 'Pm_Voltage_Phase3' ,
#        '8' : 'Pm_Current' ,
#        '9' : 'Pm_Current_Phase2' ,
#        '10' : 'Pm_Current_Phase3' ,
#        '11' : 'Pm_Active_Power' ,
#        '12' : 'Pm_Active_Power_Phase2' ,
#        '13' : 'Pm_Active_Power_Phase3' ,
#        '14' : 'wallboxPower' ,
#        '15' : 'wallboxCurrentR' ,
#        '16' : 'wallboxCurrentS' ,
#        '17' : 'wallboxCurrentT' ,
#        '18' : 'Power_Meter_Id_2' ,
#        '19' : 'Power_Meter_Id_2_Owner' ,
#        '20' : 'Pm2_Voltage' ,
#        '21' : 'Pm2_Voltage_Phase2' ,
#        '22' : 'Pm2_Voltage_Phase3' ,
#        '23' : 'Pm2_Current' ,
#        '24' : 'Pm2_Current_Phase2' ,
#        '25' : 'Pm2_Current_Phase3' ,
#        '26' : 'Pm2_Active_Power' ,
#        '27' : 'Pm2_Active_Power_Phase2' ,
#        '28' : 'Pm2_Active_Power_Phase3' ,
#        '29' : 'maxAvailablePower' ,
#    },
#    3: {
#        '0' : 'Pwm_Voltage_Id' ,
#        '1' : 'Pwm_Voltage_Id_Owner_Setter' ,
#        '2' : 'Worst_Alarm_Id' ,
#        '3' : 'V_Pos_Pwm' ,
#        '4' : 'V_Neg_Pwm' ,
#        '5' : 'insert_rfid_card' ,
#        '6' : 'standby' ,
#        '7' : 'restart' ,
#        '8' : 'swipe_rfid_card' ,
#        '9' : 'reset_alarms' ,
#        '10' : 'language_set' ,
#        '11' : 'sn_letter' ,
#        '12' : 'sn' ,
#        '13' : 'sn_year' ,
#        '14' : 'cable_capacity' ,
#        '15' : 'v12_psu_sns' ,
#        '16' : 'lock_isense' ,
#        '17' : 'vnegpwm' ,
#        '18' : 'vpospwm' ,
#        '19' : 'out_acs_dsp' ,
#        '20' : 'temp_an_1' ,
#        '21' : 'real_rated_power' ,
#        '22' : 'power_domestic' ,
#        '23' : 'available_current' ,
#        '24' : 'last_charge_cycle_E_consumed' ,
#        '25' : 'worktime' ,
#        '26' : 'Command' ,
#        '27' : 'power_rating' ,
#        '28' : 'enable_fixed_power' ,
#        '29' : 'enable_rfid' ,
#        '30' : 'enable_load_bal' ,
#        '31' : 'enable_occp' ,
#        '32' : 'enable_wallbox' ,
#        '33' : 'pause_wallbox' ,
#        '34' : 'stop_wallbox' ,
#        '35' : 'home_power_total',
#        '36' : 'rfid_validity_timeout',
#        '37' : 'meter_power_rating',
#        '38' : 'wallbox_rated_power' ,
#        '39' : 'led_intensity_factor',
#        '40' : 'board_initial_collaudo' ,
#        '41' : 'charge_paused_at_startup',
##        '42' : 'WallBoxType' ,
#        '43' : 'phase_is_triphase' ,
#        '44' : 'force_phase' ,
#        '45' : 'has_plug_lockengine',
#        '46' : 'force_plug_lockengine' ,
#        '47' : 'has_rfid_reader' ,
#        '48' : 'has_car_powermeter_mid' ,
#        '49' : 'has_domestic_powermeter' ,
#        '50' : 'enable_fixed_power_inhibit_mid' ,
#        '51' : 'DSP_wallbox_rated_power' ,
#        '52' : 'DSP_meter_power_rating' ,
#        '53' : 'Eth0_Mac_Address' ,
#        '54' : 'Wlan0_Mac_Address' ,
#    }
#}

MB_Dict = {
    '0' : 'leakage_fsm_status' ,
    '1' : 'pwm_ctrl_status' ,
    '2' : 'lock_engine_status_fsm' ,
    '3' : 'relay_status_fsm' ,
    '4' : 'state_3V' ,
    '5' : 'state_0V' ,
    '6' : 'state_6V' ,
    '7' : 'state_9V' ,
    '8' : 'state_12V' ,
    '9' : 'state_Neg' ,
    '10' : 'state_Invalid' ,
    '11' : 'flag_has_plug_lockengine' ,
    '12' : 'flag_phase_is_trifase' ,
    '13' : 'flag_has_rfid_reader' ,
    '14' : 'flag_has_car_powermeter_mid' ,
    '15' : 'flag_has_domestic_powermeter' ,
    '16' : 'flag_enable_fixed_pw_inhibit_mid' ,
    '17' : 'flag_inverter_presence' ,
    '18' : 'flag_has_started_pwm_fsm', 
    '19' : 'flag_simplified_pilot_mode', 
    '20' : 'flag_old_board_type' ,
    '21' : 'flag_board_initial_collaudo' ,
    '22' : 'CMPB' ,
    '23' : 'flag_recharge_enabled' ,
    '24' : 'wallbox_state' ,
    '25' : 'Alarm_Param' ,
    '26' : 'Alarm_Severity',
    '27' : 'Alarm_Action_Type',
    '28' : 'Led_Brightness' ,
    '29' : 'Led_Color' ,
    '30' : 'Led_Blinking' ,
    '31' : 'Power_Meter_Id_Owner' ,
    '32' : 'Pm_Voltage' ,
    '33' : 'Pm_Voltage_Phase2' ,
    '34' : 'Pm_Voltage_Phase3' ,
    '35' : 'Pm_Current' ,
    '36' : 'Pm_Current_Phase2' ,
    '37' : 'Pm_Current_Phase3' ,
    '38' : 'Pm_Active_Power' ,
    '39' : 'Pm_Active_Power_Phase2' ,
    '40' : 'Pm_Active_Power_Phase3' ,
    '41' : 'wallboxPower' ,
    '42' : 'wallboxCurrentR' ,
    '43' : 'wallboxCurrentS' ,
    '44' : 'wallboxCurrentT' ,
    '45' : 'Power_Meter_Id_2' ,
    '46' : 'Power_Meter_Id_2_Owner' ,
    '47' : 'Pm2_Voltage' ,
    '48' : 'Pm2_Voltage_Phase2' ,
    '49' : 'Pm2_Voltage_Phase3' ,
    '50' : 'Pm2_Current' ,
    '51' : 'Pm2_Current_Phase2' ,
    '52' : 'Pm2_Current_Phase3' ,
    '53' : 'Pm2_Active_Power' ,
    '54' : 'Pm2_Active_Power_Phase2' ,
    '55' : 'Pm2_Active_Power_Phase3' ,
    '56' : 'maxAvailablePower' ,
    '57' : 'Pwm_Voltage_Id' ,
    '58' : 'Pwm_Voltage_Id_Owner_Setter' ,
    '59' : 'Worst_Alarm_Id' ,
    '60' : 'V_Pos_Pwm' ,
    '61' : 'V_Neg_Pwm' ,
    '62' : 'insert_rfid_card' ,
    '63' : 'standby' ,
    '64' : 'restart' ,
    '65' : 'swipe_rfid_card' ,
    '66' : 'reset_alarms' ,
    '67' : 'language_set' ,
    '68' : 'sn_letter' ,
    '69' : 'sn' ,
    '70' : 'sn_year' ,
    '71' : 'cable_capacity' ,
    '72' : 'v12_psu_sns' ,
    '73' : 'lock_isense' ,
    '74' : 'vnegpwm' ,
    '75' : 'vpospwm' ,
    '76' : 'out_acs_dsp' ,
    '77' : 'temp_an_1' ,
    '78' : 'real_rated_power', 
    '79' : 'power_domestic' ,
    '80' : 'available_current' ,
    '81' : 'last_charge_cycle_E_consumed' ,
    '82' : 'worktime' ,
    '83' : 'Command' ,
    '84' : 'power_rating' ,
    '85' : 'enable_fixed_power' ,
    '86' : 'enable_rfid' ,
    '87' : 'enable_load_bal' ,
    '88' : 'enable_occp' ,
    '89' : 'enable_wallbox' ,
    '90' : 'pause_wallbox' ,
    '91' : 'stop_wallbox' ,
    '92' : 'home_power_total',
    '93' : 'rfid_validity_timeout',
    '94' : 'meter_power_rating',
    '95' : 'wallbox_rated_power', 
    '96' : 'led_intensity_factor',
    '97' : 'board_initial_collaudo' ,
    '98' : 'charge_paused_at_startup',
    '99' : 'phase_is_triphase' ,
    '100' : 'force_phase' ,
    '101' : 'has_plug_lockengine',
    '102' : 'force_plug_lockengine' ,
    '103' : 'has_rfid_reader' ,
    '104' : 'has_car_powermeter_mid' ,
    '105' : 'has_domestic_powermeter' ,
    '106' : 'enable_fixed_power_inhibit_mid' ,
    '107' : 'DSP_wallbox_rated_power' ,
    '108' : 'DSP_meter_power_rating' ,
    '109' : 'Eth0_Mac_Address' ,
    '110' : 'Wlan0_Mac_Address' ,
}