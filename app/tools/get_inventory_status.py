import os


ENABLE_ERROR_CODE_MAPPING = os.getenv("ENABLE_ERROR_CODE_MAPPING", "true").strip().lower() in {
    "1",
    "true",
    "yes",
    "on",
}


def get_inventory_status(part_name):

    inventory = {
        # Cooling/Thermal Parts
        "cooling_fan": 5,
        "heat_sink": 4,
        "heat_sink_assembly": 10,
        "coolant": 12,
        "coolant_pump": 7,
        "coolant_hoses": 4,
        "coolant_system_components": 9,
        "thermal_sensor_module": 6,
        "temperature_sensor": 8,
        "radiator": 3,
        "radiator_fan": 5,
        "thermostat": 6,
        
        # Electrical Parts
        "power_supply_unit": 5,
        "alternator": 4,
        "starter_motor": 3,
        "battery": 2,
        "voltage_regulator": 5,
        "ignition_coil": 4,
        "ignition_module": 4,
        "relay": 10,
        "capacitor": 15,
        "transformer": 2,
        "circuit_breaker": 8,
        "fuse": 20,
        "wiring_harness": 6,
        "connector": 12,
        
        # Mechanical/Engine Parts
        "motor_assembly": 6,
        "bearing_unit": 3,
        "fan_blade": 8,
        "piston": 4,
        "crankshaft": 2,
        "camshaft": 2,
        "valve": 10,
        "gasket": 8,
        "seal": 12,
        "bearing": 5,
        "pulley": 6,
        "belt": 8,
        "chain": 4,
        "sprocket": 5,
        
        # Fuel System Parts
        "fuel_pump": 2,
        "spark_plug": 20,
        "fuel_injector": 6,
        "fuel_filter": 8,
        "air_filter": 8,
        "carburetor": 2,
        "fuel_line": 6,
        "fuel_tank": 1,
        
        # Transmission/Fluid Parts
        "transmission_fluid": 15,
        "engine_oil": 12,
        "brake_fluid": 8,
        "power_steering_fluid": 6,
        "hydraulic_fluid": 10,
        "bearing_grease": 8,
        
        # HVAC Parts
        "compressor": 2,
        "condenser": 2,
        "evaporator": 2,
        "expansion_valve": 4,
        "refrigerant": 8,
        "ac_filter": 6,
        "blower_motor": 4,
        "thermostat_valve": 5,
        "ductwork": 3,
        
        # Hydraulic Parts
        "hydraulic_pump": 3,
        "hydraulic_motor": 2,
        "hydraulic_cylinder": 4,
        "hydraulic_valve": 6,
        "hydraulic_hose": 10,
        "hydraulic_accumulator": 2,
        
        # Sensor Parts
        "pressure_sensor": 8,
        "flow_sensor": 6,
        "level_sensor": 5,
        "proximity_sensor": 7,
        "rpm_sensor": 4,
        "vibration_sensor": 5,
        
        # Power/Control Parts
        "circuit_board": 4,
        "control_module": 3,
        "plc": 2,
        "inverter": 2,
        "rectifier": 3,
        "regulator_module": 4,
        
        # Structural Parts
        "mounting_bracket": 8,
        "base_plate": 4,
        "housing": 3,
        "casing": 5,
        "cover": 6,
    }

    aliases = {
        # Cooling/Thermal aliases
        "transmission_oil": "transmission_fluid",
        "transmission_fluid_oil": "transmission_fluid",
        "engine_coolant": "coolant",
        "antifreeze": "coolant",
        "engine_antifreeze": "coolant",
        "radiator_coolant": "coolant",
        "cooling_system_fluid": "coolant",
        "radiator_fan": "cooling_fan",
        "electric_fan": "cooling_fan",
        "engine_fan": "cooling_fan",
        "heatsink": "heat_sink",
        "thermal_heatsink": "heat_sink",
        
        # Engine/Mechanical aliases
        "engine_air_filter": "air_filter",
        "intake_air_filter": "air_filter",
        "air_intake_filter": "air_filter",
        "spark_plugs": "spark_plug",
        "spark_plug_set": "spark_plug",
        "starter": "starter_motor",
        "electric_starter": "starter_motor",
        "fuel_injection_pump": "fuel_pump",
        "fuelpump": "fuel_pump",
        "alternator_unit": "alternator",
        
        # Electrical aliases
        "power_supply": "power_supply_unit",
        "psu": "power_supply_unit",
        "voltage_regulation_module": "voltage_regulator",
        "regulator": "voltage_regulator",
        "ignition_controller": "ignition_coil",
        "coil_pack": "ignition_coil",
        
        # Fluid aliases
        "oil": "engine_oil",
        "motor_oil": "engine_oil",
        "transmission_oil": "transmission_fluid",
        "gearbox_fluid": "transmission_fluid",
        "brake_oil": "brake_fluid",
        "steering_fluid": "power_steering_fluid",
        "ps_fluid": "power_steering_fluid",
        
        # Sensor aliases
        "bearing": "bearing_unit",
        "thermal_sensor": "thermal_sensor_module",
        "temperature_sensor": "thermal_sensor_module",
        "fan": "cooling_fan",
        "motor": "motor_assembly",
        "pump": "coolant_pump",
        "ac_compressor": "compressor",
        "air_compressor": "compressor",
        "ac_condenser": "condenser",
        "ac_evaporator": "evaporator",
        "refrigerant_charge": "refrigerant",
        "coolant_refrigerant": "refrigerant",
        
        # HVAC aliases
        "air_conditioning_compressor": "compressor",
        "cooling_compressor": "compressor",
        "hvac_blower": "blower_motor",
        "air_blower": "blower_motor",
        "ac_blower": "blower_motor",
        
        # Control aliases
        "main_circuit_board": "circuit_board",
        "pcb": "circuit_board",
        "ecu": "control_module",
        "engine_control_unit": "control_module",
        "dsp": "circuit_board",
        
        # Generic aliases
        "unit": "",
        "assembly": "",
        "module": "",
        "component": "",
        "system": "",
    }

    normalized = str(part_name).strip().lower()
    normalized = normalized.replace("-", "_").replace(" ", "_")
    normalized = "_".join(segment for segment in normalized.split("_") if segment)

    if normalized in inventory:
        return {
            "part": part_name,
            "available": inventory[normalized]
        }

    if normalized in aliases:
        canonical = aliases[normalized]
        if canonical and canonical in inventory:
            return {
                "part": part_name,
                "available": inventory[canonical]
            }

    parts_to_check = [
        normalized.replace("_assembly", ""),
        normalized.replace("_unit", ""),
        normalized.replace("_components", ""),
        normalized.replace("_module", ""),
        normalized.replace("_motor", ""),
        normalized.replace("_pump", ""),
        normalized.replace("_system", ""),
        normalized.replace("_sensor", ""),
    ]

    for variant in parts_to_check:
        if variant in inventory:
            return {
                "part": part_name,
                "available": inventory[variant]
            }
        if variant in aliases:
            canonical = aliases[variant]
            if canonical and canonical in inventory:
                return {
                    "part": part_name,
                    "available": inventory[canonical]
                }

    return {
        "part": part_name,
        "available": inventory.get(normalized, 0)
    }


# Error codes and failure type mapping
ERROR_CODE_MAPPING = {
    # Thermal/Cooling Errors
    "E-HEAT": "thermal_overheat",
    "OVRHT": "thermal_overheat",
    "TEMP-HI": "thermal_overheat",
    "E001": "thermal_overheat",
    "E-COOL": "cooling_failure",
    "E-FAN": "fan_failure",
    "COOL-01": "cooling_system_failure",
    
    # Electrical Errors
    "E-ELEC": "electrical_fault",
    "BATT-LOW": "battery_low",
    "VOLT-HIGH": "voltage_high",
    "VOLT-LOW": "voltage_low",
    "E002": "electrical_failure",
    "POWER-LOSS": "power_loss",
    "SUPPLY-FAIL": "power_supply_failure",
    
    # Mechanical Errors
    "E-MECH": "mechanical_fault",
    "VIBR-HIGH": "excessive_vibration",
    "BEARING-FAIL": "bearing_failure",
    "E003": "mechanical_failure",
    "NOISE-ABNORMAL": "abnormal_noise",
    
    # Fuel System Errors
    "E-FUEL": "fuel_system_fault",
    "FUEL-PUMP": "fuel_pump_failure",
    "INJECTOR-FAIL": "fuel_injector_failure",
    "SPARK-FAIL": "spark_plug_failure",
    "E004": "fuel_system_failure",
    
    # Transmission/Fluid Errors
    "E-TRANS": "transmission_fault",
    "OIL-PRESS": "oil_pressure_low",
    "FLUID-LEAK": "fluid_leak",
    "E005": "transmission_failure",
    "SHIFT-FAULT": "shifting_failure",
    
    # Sensor Errors
    "E-SENSOR": "sensor_malfunction",
    "TEMP-SENSOR": "temperature_sensor_fault",
    "PRESS-SENSOR": "pressure_sensor_fault",
    "E006": "sensor_failure",
    
    # Hydraulic Errors
    "E-HYD": "hydraulic_fault",
    "HYD-LOSS": "hydraulic_pressure_loss",
    "PUMP-FAIL": "pump_failure",
    "E007": "hydraulic_failure",
    
    # Control System Errors
    "E-CTRL": "control_system_fault",
    "ECU-FAIL": "control_unit_failure",
    "COMMS-FAIL": "communication_failure",
    "E008": "control_failure",
} if ENABLE_ERROR_CODE_MAPPING else {}

