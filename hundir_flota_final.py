from colorama import Fore, init
from random import randrange
import random
import socket
import struct
import time
import sys
import os

def imprimirTablero(tablero):
    # imprime el tablero

    if tablero == miTablero:
        print("TU TABLERO:")
    else:
        print("TABLERO ENEMIGO:")

    print("~~"*23)
    print("~~"*23)
    print("   "+Fore.RED+"  ".join(LETRAS))

    for fila in range(15):
        print(Fore.RED + "%02d " %(fila+1) + Fore.BLUE + "  ".join(tablero[fila]))

    print("~~"*23)
    print("~~"*23)


def colocarBarcos(miTablero, flota):
    # coloca los barcos en el tablero
    
    for cantidad, tamaño in flota.values():
        for _ in range(cantidad):
            while True:
                # 1 para vertical y 0 para horizontal
                orientacion = random.randint(0,1)
                if orientacion:
                    limitex = 15
                    limitey = 15 - tamaño+1
                else:
                    limitex = 15 - tamaño+1
                    limitey = 15

                posicionx = randrange(limitex)
                posiciony = randrange(limitey)

                if comprobarTablero(miTablero, posicionx, posiciony, tamaño, orientacion):

                    if orientacion:
                        for x in range(posiciony, posiciony+tamaño):
                            for y in range(posicionx, posicionx+1):
                                miTablero[x][y] = '1'

                    else:
                        for x in range(posiciony, posiciony+1):
                            for y in range(posicionx, posicionx+tamaño):
                                miTablero[x][y] = '1'
                    
                    break


def comprobarTablero(miTablero, posicionx, posiciony, tamaño, orientacion):
    # comprueba que no haya barcos en la posición donde se va a colocar el barco, ni alrededor

    if orientacion:
        for x in range(posiciony-1, posiciony+tamaño+1):
            for y in range(posicionx-1,posicionx+2):
                try:
                    if miTablero[x][y] == '1':
                        return False
                except IndexError:
                    continue

        return True
    
    else:
        for x in range(posiciony-1, posiciony+2):
            for y in range(posicionx-1, posicionx+tamaño+1):
                try:
                    if miTablero[x][y] == '1':
                        return False
                except IndexError:
                    continue
        
        return True


def validarCoordenada(coord):
    # comprueba que la coordenada sea válida y la devuelve traducida a la posición del tablero a la que corresponde

    if coord == "" or coord[0].upper() not in LETRAS or int(coord[1:]) not in range(15):
        raise ValueError
    
    coordenada = []
    coordenada.append(LETRAS.index(coord[0].upper()))
    coordenada.append(int(coord[1:]))
    
    return coordenada


def comprobarHundido(miTablero, disparoEnemigo):
    # comprueba si el barco está tocado o hundido

    for x in range(disparoEnemigo[1], -1, -1):
        if miTablero[x][disparoEnemigo[0]] == '1':
            return False
        elif miTablero[x][disparoEnemigo[0]] in ('0', 'F'):
            break

    for x in range(disparoEnemigo[1], 15):
        if miTablero[x][disparoEnemigo[0]] == '1':
            return False
        elif miTablero[x][disparoEnemigo[0]] in ('0', 'F'):
            break

    for x in range(disparoEnemigo[0], -1, -1):
        if miTablero[disparoEnemigo[1]][x] == '1':
            return False
        elif miTablero[disparoEnemigo[1]][x] in ('0', 'F'):
            break

    for x in range(disparoEnemigo[0], 15):
        if miTablero[disparoEnemigo[1]][x] == '1':
            return False
        elif miTablero[disparoEnemigo[1]][x] in ('0', 'F'):
            break

    return True


def recibirDisparo(conexion, miTablero):
    # recibe disparo y devuelve agua, tocado o hundido

    disparo = conexion.recv(10).decode()
    print("\nEl enemigo ha disparado a la coordenada: ", disparo)
    coordenada = validarCoordenada(disparo)
    y = coordenada[0]
    x = coordenada[1]
    
    if miTablero[x][y] == '0' or miTablero[x][y] == 'F':
        miTablero[x][y] = 'F'
        return '0'
    else:
        if miTablero[x][y] == 'X':
            return '0'
        else:
            miTablero[x][y] = 'X'
            if comprobarHundido(miTablero, coordenada):
                for x in miTablero:
                    for y in x:
                        if y == '1':
                            return '2'
                return '3'
            return '1'


def enviarDisparo(conexion, direccion):
    # envia tu disparo, devuelve las coordenadas traducidas y la respuesta del enemigo

    while True:
        try:
            disparo = LETRAS[randrange(15)] + str(randrange(15))
            coordenadas = validarCoordenada(disparo)
            if disparo not in coordenadasEnviadas:
                coordenadasEnviadas.append(disparo)
                break
        except ValueError:
            continue
    
    print("Se ha disparado a la coordenada: ", disparo)
    conexion.sendto(disparo.encode(), direccion)
    return [conexion.recvfrom(5)[0].decode(), coordenadas]


def modificarTableroEnemigo(tableroEnemigo, disparo, respuesta):
    # se modifica el tablero del enemmigo a medida que le disparamos
    x = disparo[1]
    y = disparo[0]

    if respuesta == '0':
        if tableroEnemigo[x][y] == '0':
            tableroEnemigo[x][y] = 'F'
    else:
        tableroEnemigo[x][y] = 'X'


def borrarPantalla():

    if os.name == 'posix':
        os.system('clear')
    elif os.name == 'nt' or os.name == 'ce' or os.name == 'dos':
        os.system('cls')


def soyServidor(miTablero, tableroEnemigo):

    multicast_group = '224.3.29.71'
    server_address = ('', 8081)

    conexion = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    conexion.bind(server_address)

    group = socket.inet_aton(multicast_group)
    mreq = struct.pack('4sL', group, socket.INADDR_ANY)
    conexion.setsockopt(
        socket.IPPROTO_IP,
        socket.IP_ADD_MEMBERSHIP,
        mreq
    )

    try:
        print("Esperando al otro jugador...")
        respuesta, direccion = conexion.recvfrom(1024)

        print("Conexión establecida con",direccion)
        conexion.sendto(b'Bienvenido a Hundir la Flota', direccion)

        while True:
            while True:
                time.sleep(0.1)
                respuesta = recibirDisparo(conexion, miTablero)
                if respuesta == '0':
                    print("\nLa respuesta ha sido: agua\n")
                elif respuesta == '1':
                    print("\nLa respuesta ha sido: tocado\n")
                elif respuesta == '2':
                    print("\nLa respuesta ha sido: hundido\n")
                conexion.sendto(respuesta.encode(), direccion)

                if respuesta == '0' or respuesta == '3':
                    break

            if respuesta == '3':
                borrarPantalla()
                imprimirTablero(tableroEnemigo)
                print("\nHas perdido :(\n")
                break

            while True:
                time.sleep(0.1)
                respuesta, disparo = enviarDisparo(conexion, direccion)
                if respuesta == '0':
                    print("\nLa respuesta ha sido: agua\n")
                elif respuesta == '1':
                    print("\nLa respuesta ha sido: tocado\n")
                elif respuesta == '2':
                    print("\nLa respuesta ha sido: hundido\n")
                
                borrarPantalla()
                modificarTableroEnemigo(tableroEnemigo, disparo, respuesta)
                imprimirTablero(tableroEnemigo)

                if respuesta == '0' or respuesta == '3':
                    break

            if respuesta == '3':
                print("\n¡Enhorabuena, has ganado!\n")
                break

        print("\nCerrando el servidor...")
    
    finally:
        conexion.close()


def soyCliente(miTablero, tableroEnemigo):

    multicast_group = ('224.3.29.71', 8081)

    cliente = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

    ttl = struct.pack('b', 1)
    cliente.setsockopt(socket.IPPROTO_IP, socket.IP_MULTICAST_TTL, ttl)

    try:
        cliente.sendto(b"Conexion establecida con exito", multicast_group)
        respuesta, direccion = cliente.recvfrom(50)
        print(respuesta.decode())

        while True:
            while True:
                time.sleep(0.1)
                respuesta, disparo = enviarDisparo(cliente, direccion)
                if respuesta == '0':
                    print("\nLa respuesta ha sido: agua\n")
                elif respuesta == '1':
                    print("\nLa respuesta ha sido: tocado\n")
                elif respuesta == '2':
                    print("\nLa respuesta ha sido: hundido\n")
                
                borrarPantalla()
                modificarTableroEnemigo(tableroEnemigo, disparo, respuesta)
                imprimirTablero(tableroEnemigo)
                
                if respuesta == '0' or respuesta == '3':
                    break

            if respuesta == '3':
                print("\n¡Enhorabuena, has ganado!\n")
                break

            while True:
                time.sleep(0.1)
                respuesta = recibirDisparo(cliente, miTablero)
                if respuesta == '0':
                    print("\nLa respuesta ha sido: agua\n")
                elif respuesta == '1':
                    print("\nLa respuesta ha sido: tocado\n")
                elif respuesta == '2':
                    print("\nLa respuesta ha sido: hundido\n")
                cliente.sendto(respuesta.encode(), direccion)
                    
                if respuesta == '0' or respuesta == '3':
                    break

            if respuesta == '3':
                borrarPantalla()
                imprimirTablero(tableroEnemigo)
                print("\nHas perdido :(\n")
                break

        print("\nCerrando el servidor...")

    finally:
        cliente.close()



if __name__ == "__main__":

    init(autoreset=True)
    LETRAS = 'ABCDEFGHIJKLMNO'
    coordenadasEnviadas = []

    miTablero = [["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15]
    tableroEnemigo = [["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15, ["0"] * 15]

    flota = {
        'lanchas': [4, 1],
        'fragatas': [3, 2],
        'submarinos': [2, 3],
        'buques': [1, 4],
        'portaaviones': [1, 5]
    }

    colocarBarcos(miTablero, flota)
    imprimirTablero(miTablero)

    while True:
        try:
            tipo = int(input("¿Vas a jugar como servidor o como cliente?\n1. Servidor\n2. Cliente\nElige una opción: "))
            if tipo == 1:
                soyServidor(miTablero, tableroEnemigo)
                break
            elif tipo == 2:
                soyCliente(miTablero, tableroEnemigo)
                break
            else:
                print("\nDebes elegir una opción válida.")
                print()
        except ValueError:
            print("\nDebes elegir una opción válida.")
            print()

    os.system('Pause')

