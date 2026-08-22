def get_sensor_context(device, error_code):

    return {
        "pattern_match": "Cooling failure pattern detected",
        "confidence": 0.81,
        "additional_info": "Based on vibration + temp profile"
    }
