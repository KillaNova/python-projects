try:
    getal = int(input("geef een getal: "))
    print(100 / getal)
except ZeroDivisionError:
    print("kan niet delen door nul.")
except ValueError:
    print("Dat is geen geldig getal.")

try:
    getal = int(input("Getal 1: "))
    macht = int(input("Tot de macht: "))
    print(getal**macht)
except ValueError:
    print("Dat is geen geldig getal.")
except ZeroDivisionError:
    print("Kan niet delen door nul.")

    # vooraf var controleren maak de exception abosoleet
    # controleer de logica - exception alleen naar gebruiker toe en niet standaard in code houden ("Te duur voor in code")
