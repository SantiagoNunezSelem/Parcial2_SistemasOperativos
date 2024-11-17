import math
from tabulate import tabulate
import os
import bisect

import ProcessControlBlock as PCB

# Variables globales
memory_size = 0  # Tamaño de la memoria en KB
os_size = 0  # Tamaño del SO en KB
frame_size = 0  # Tamaño de cada frame en KB
num_frames_max = 0  # Número de frames maximo por proceso
frames = []  # Lista de frames (0 = libre, 's' = asignado al SO, 'u' = asignado al usuario)
processesControlBlock = []
processesWaiting = [] #Procesos que tienen al menos una pagina que necesita ser ingresada en memoria

def clearTerminal():
    os.system('cls' if os.name == 'nt' else 'clear')

def enterMemoryData(opt):
    global memory_size, os_size, frame_size, num_frames_max, frames, processesControlBlock, processesWaiting

    if(opt == 'no back option'):
        memory_size = int(get_positive_integer("Ingrese el tamaño de la memoria real en KB: "))
    else:
        memory_size = int(get_positive_integer_with_cero("Ingrese el tamaño de la memoria real en KB (0 = atras): "))
        if(memory_size == 0):
            return -1
        
    os_size = get_positive_integer("Ingrese el tamaño del SO en KB: ")
    frame_size = get_positive_integer("Ingrese el tamaño de cada frame en KB: ")
    num_frames_max = get_positive_integer("Ingrese la cantidad de frames a asignar a todos los procesos: ")
    
    # Inicializar los frames (0 = libre, 's' = asignado al SO, 'u' = asignado al usuario)
    frames_os = math.ceil(os_size / frame_size)
    frames_user = (memory_size - os_size) // frame_size
    frames = ['s'] * frames_os + ['0'] * frames_user
    
    print(f"\nMemoria configurada con {memory_size} KB, tamaño de frame {frame_size} KB")
    print(f"Cantidad maxima asignada a cada frame: {num_frames_max} KB")

def get_positive_integer(prompt):
    while True:
        try:
            value = int(input(prompt))
            if value > 0:
                return value
            print("\nEl valor debe ser un número entero positivo. Intente nuevamente")
        except ValueError:
            print("\nEntrada inválida. Por favor, ingrese un número entero")

def get_positive_integer_with_cero(prompt):
    while True:
        try:
            value = int(input(prompt))
            if value >= 0:
                return value
            print("\nEl valor debe ser un número entero positivo. Intente nuevamente")
        except ValueError:
            print("\nEntrada inválida. Por favor, ingrese un número entero")

def verifyMemoryData():
    if(memory_size == 0 or os_size == 0 or frame_size == 0 or num_frames_max == 0):
        print("\nPrimero debe ingresar la informacion de la memoria (opcion 1)\n")

        enterMemoryData('no back option')

def showFrameTable():
    # Use tabulate to display the frame table
    headers = ["Frame", "Estado", "Asignado a"]
    
    rows = []
    for i, frame in enumerate(frames):
        estado = "Ocupado" if frame != '0' else "Libre"
        asignado_a = "SO" if frame == 's' else ("Usuario" if frame == 'u' else "N/A")
        rows.append([i, estado, asignado_a])

    print("\nTabla de Frames:")
    print(tabulate(rows, headers=headers, tablefmt="grid"))

def searchProcess(pid):
    verifyMemoryData()

    #processesControlBlock is sorted
    left = 0
    right = len(processesControlBlock) - 1

    while left <= right:
        mid = (left + right) // 2

        # Compare the PID with the middle element
        if processesControlBlock[mid].pid == pid:
            return mid
        elif processesControlBlock[mid].pid < pid:
            left = mid + 1
        else:
            right = mid - 1

    return -1

def insertSorted(list, new_object):
    # Extract the key for sorting (id in this case)
    keys = [element.pid for element in list]
    # Find the position to insert using bisect
    position = bisect.bisect_left(keys, new_object.pid)
    # Insert the object at the correct position
    list.insert(position, new_object)

def addProcess():
    verifyMemoryData()

    notAvailableId = True

    while(notAvailableId):
        pid = int(get_positive_integer_with_cero("\nIngrese el identificador del proceso (0 = atras): "))

        if(pid == 0):
            return -1
    
        if(searchProcess(pid) != -1):
            print("Este indetificador ya existe, ingrese uno nuevo")
        else:
            notAvailableId = False

    size = int(get_positive_integer("Ingrese el tamaño del proceso en KB: "))

    processCB = PCB.ProcessControlBlock(pid,size,frame_size)

    insertSorted(processesControlBlock,processCB)

    processCB.addToMemory(frames,num_frames_max)

    # If the process is waiting to be added to memory, add it to the waitingProcesses list 
    # (some pages might still be waiting to be added, not all)
    if(processCB.hasPagesWaiting(num_frames_max)):
        processesWaiting.append(processCB)

def showPageTable():
    notValidId = True

    while(notValidId):
        pid = int(get_positive_integer_with_cero("\nIngrese el identificador del proceso (0 = atras): "))

        if(pid == 0):
            return -1

        index = searchProcess(pid)
        if(index == -1):
            print("Este indetificador no existe, vuelva a intentarlo")
        else:
            notValidId = False
    
    processControlBlock = processesControlBlock[index]

    #Use tabulate to display the page Use tabulate to display the frame table
    headers = ["Pagina", "Frame", "Bit Validez"]
    
    rows = []
    for i, pag in enumerate(processControlBlock.pageTable):
        numPage = i
        numFrame = pag[0] if pag[0] != -1 else "N/A"
        vBit = pag[1]
        rows.append([numPage, numFrame, vBit])

    print("\nTabla de Frames:")
    print(tabulate(rows, headers=headers, tablefmt="grid"))

def addWaitingProcesses():
    # Verify if there are processes waiting to be added to memory
    if len(processesWaiting) > 0:

        # Iterate over memory frames to find an empty space
        for frameIndex, frame in enumerate(frames):
            if frame == '0':  # Check for an empty frame

                # If there are processes waiting, pick the first one
                if len(processesWaiting) > 0:
                    process = processesWaiting[0]
                    framesNumber = process.countFrames()

                    # Iterate over the process's page table to find an unassigned page
                    for pageIndex, page in enumerate(process.pageTable):
                        if framesNumber >= num_frames_max:
                            break  # Stop if maximum frames for the process are assigned

                        if page[1] == 'i':  # Check if the page is not yet assigned
                            # Assign the page to the memory frame
                            page[0] = frameIndex 
                            page[1] = 'v'
                            frames[frameIndex] = 'u'
                            print(f'Pagina de proceso PID:{process.pid} asignada a frame en memoria')
                            break  # Exit page table loop after assigning one page

                    # If all pages of the process are assigned, remove it from the waiting list
                    if all(p[1] == 'v' for p in process.pageTable):
                        processesWaiting.pop(0)

                else:
                    break  # Exit if no processes are waiting

def deleteProcess():
    verifyMemoryData()

    notValidId = True

    while(notValidId):
        pid = int(get_positive_integer_with_cero("\nIngrese el identificador del proceso (0 = atras): "))

        if(pid == 0):
            return -1

        index = searchProcess(pid)
        if(index == -1):
            print("Este indetificador no existe, vuelva a intentarlo")
        else:
            notValidId = False
    
    #Get numbers of frames in memory to delete them
    numberOfFrames = []
    for element in processesControlBlock[index].pageTable:
        if(element[1] == 'v'):                                  #Verify content with valid bit
            numberOfFrames.append(element[0])

    del processesControlBlock[index]    #delete the process in the processesControlBlock list

    for i,process in enumerate(processesWaiting):
        if(process.pid == pid):
            del processesWaiting[i]     #delete the process in the processesWaiting list

    for index in numberOfFrames:
        frames[index] = '0'

    print("\n--- Proceso eliminado con exito ---")

    #Add processes waiting to be added
    addWaitingProcesses()
    

def showMenu():
    while True:
        print("\n----- MENÚ DE ADMINISTRACIÓN DE MEMORIA -----")
        print("1) Ingresar datos de memoria")
        print("2) Mostrar tabla de frames")
        print("3) Ingresar un proceso")
        print("4) Mostrar tabla de páginas de un proceso")
        print("5) Eliminar un proceso")
        print("6) Simular acceso a páginas con LRU")
        print("7) Mostrar dirección física de una dirección lógica")
        print("0) Salir")
        
        opt = input("Seleccione una opción: ")
        
        if opt == '1':
            enterMemoryData('')
            pass
        elif opt == '2':
            showFrameTable()
            pass
        elif opt == '3':
            addProcess()
            pass
        elif opt == '4':
            showPageTable()
            pass
        elif opt == '5':
            deleteProcess()
            pass
        elif opt == '6':
            # Llamar a la función para simular el acceso a páginas con LRU
            pass
        elif opt == '7':
            # Llamar a la función para mostrar la dirección física
            pass
        elif opt == '0':
            print("Saliendo del programa...")
            break
        else:
            print("Opción no válida. Intente nuevamente.")


def main() -> int:
    showMenu()

main()
