def classify_hurricane(wind_speed):
    if wind_speed < 74:
        return "Tropical Storm"
    elif 74 <= wind_speed <= 95:
        return "Category 1 Hurricane"
    elif 96 <= wind_speed <= 110:
        return "Category 2 Hurricane"
    elif 111 <= wind_speed <= 129:
        return "Category 3 Hurricane"
    elif 130 <= wind_speed <= 156:
        return "Category 4 Hurricane"
    else:
        return "Category 5 Hurricane"