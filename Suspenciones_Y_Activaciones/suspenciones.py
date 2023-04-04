from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import smtplib

from datetime import datetime
import sys
import numpy as np
# from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
# from matplotlib.backends.backend_qt5agg import NavigationToolbar2QT
# from matplotlib.figure import Figure
import sys
# import os
from PyQt5 import QtWidgets,uic
from PyQt5.QtWidgets import QFileDialog
import csv
import re
from pathlib import Path
import subprocess
from router import Router

# VARIABLES GLOBALES 
router1=Router("admin","password","direccion_ip")
router2=Router("admin","password","direccion_ip")

mikrotiks=[router1,router2]
clientesTotales=[]
clienteErrorComando=[]
IpSuspendidaConfirmada=[]
IpActivadaConfirmada=[]

class Principal(QtWidgets.QMainWindow):
    cedulasSuspender=[]
    nombreSuspender=[]
    clientesBalanceo=""
    clientesPajarito=""
    clienteErrorComando=[]
    IpSuspendidaConfirmada=[]

    def __init__(self):
        super(Principal,self).__init__()
        uic.loadUi('./interfaz.ui',self)
        # Listado de clientes a suspender
        self.btn_ingrezar_csv.clicked.connect(self.loadClientesCSV)

        # Listado descargado desde el Mikrotik
        self.btn_clientes.clicked.connect(self.loadClientes)
        # self.btn_clientes_balanceo.setEnabled(False)
        # self.btn_clientes_pajarito.setEnabled(False)
        self.btn_suspender.setEnabled(False)
        self.btn_activar.setEnabled(False)
        self.btn_suspender.clicked.connect(self.suspenderClientes)
        self.btn_activar.clicked.connect(self.activarClientes)

    def loadClientesCSV(self):
        global nombreSuspender,cedulasSuspender
        file=QFileDialog.getOpenFileName(self,'Cargar Archivo', './','*')
        # print(type(file))
        file=file[0]
        nombreSuspender,cedulasSuspender = lecturaCSV(file)
        
        if nombreSuspender:
            with open(file,newline="") as file:
                read = file.read()
            self.textEdit.setText(read)
            # if file!="":
            self.textEdit.setEnabled(True)

            if self.textEdit.isEnabled() and read:
                self.btn_clientes.setEnabled(True)

    def loadClientes(self):
        global clientesBalanceo, clientesTotales, clientesPajarito
        clientesBalanceo=obtenerClientes(router1)
        clientesPajarito=obtenerClientes(router2)
        if len(clientesBalanceo) >=1 and len(clientesPajarito) >=1:
            self.label_clientes.setText("Clientes Cargados")
            
            self.label_clientes.setEnabled(True)
            if (clientesBalanceo!="" or clientesPajarito !="") and  self.textEdit.isEnabled() :
                self.btn_suspender.setEnabled(True)
                self.btn_activar.setEnabled(True)
        else:
            print("No se pudo acceder a todos los Routers")
    
    def suspenderClientes(self):
        global cedulasSuspender, clientesBalanceo, clientesPajarito, clienteErrorComando, IpSuspendidaConfirmada
        
        clientesSeparadosBalanceo=separarClientes(clientesBalanceo)
        clientesSeparadosPajarito=separarClientes(clientesPajarito)
        todosClientes=np.append(clientesSeparadosBalanceo,clientesSeparadosPajarito)
        # todosClientes=np.append(clientesSeparadosBalanceo,clientesSeparadosPajarito)
        clientesBalanceoEncontrados,noEncontradosBalanceo=buscarClientes(cedulasSuspender,clientesSeparadosBalanceo)
        # for item in noEncontradosBalanceo:
        #     print(item)
        clientesPajaritoEncontrados, vecCedulasNoCoinciden=buscarClientes(noEncontradosBalanceo,clientesSeparadosPajarito)
        ipsBalanceo=buscarIP(clientesBalanceoEncontrados)
        ipsPajarito=buscarIP(clientesPajaritoEncontrados)
        for item in ipsBalanceo:
            # print(item)
            respuesta=activarSuspender(router1,item,True)
            if respuesta:
                clienteErrorComando.append(item)
                # print(respuesta)
            else:
                IpSuspendidaConfirmada.append(item)
        for item in ipsPajarito:
            # print(item)
            respuesta=activarSuspender(router2,item,True)
            if respuesta:
                clienteErrorComando.append(item)
                # print(respuesta)
            else:
                IpSuspendidaConfirmada.append(item)

        GuardarArchivosSuspendidos(ClientesSuspendidos(IpSuspendidaConfirmada, todosClientes), vecCedulasNoCoinciden, clienteErrorComando)
        enviarCorreoSuspendidos()
        self.label_proceso.setText("Suspención Finalizada")
        self.label_proceso.setEnabled(True)

    def activarClientes(self):
        global cedulasSuspender, clientesBalanceo, clientesPajarito, clienteErrorComando, IpActivadaConfirmada
        
        clientesSeparadosBalanceo=separarClientes(clientesBalanceo)
        clientesSeparadosPajarito=separarClientes(clientesPajarito)
        todosClientes=np.append(clientesSeparadosBalanceo,clientesSeparadosPajarito)
        # todosClientes=np.append(clientesSeparadosBalanceo,clientesSeparadosPajarito)
        clientesBalanceoEncontrados,noEncontradosBalanceo=buscarClientes(cedulasSuspender,clientesSeparadosBalanceo)
        # for item in noEncontradosBalanceo:
        #     print(item)
        clientesPajaritoEncontrados, vecCedulasNoCoinciden=buscarClientes(noEncontradosBalanceo,clientesSeparadosPajarito)
        ipsBalanceo=buscarIP(clientesBalanceoEncontrados)
        ipsPajarito=buscarIP(clientesPajaritoEncontrados)
        for item in ipsBalanceo:
            respuesta=activarSuspender(router1,item,False)
            if respuesta:
                clienteErrorComando.append(item)
                print(respuesta)
            else:
                IpActivadaConfirmada.append(item)
            # print("Respuesta: "+activarSuspender(mikBalanceo,item,True))
        for item in ipsPajarito:
            respuesta=activarSuspender(router2,item,False)
            if respuesta:
                clienteErrorComando.append(item)
                print(respuesta)
            else:
                IpActivadaConfirmada.append(item)
        GuardarArchivosActivos(ClientesSuspendidos(IpActivadaConfirmada, todosClientes), vecCedulasNoCoinciden, clienteErrorComando)
        enviarCorreoActivos()
        self.label_proceso.setText("Activación Finalizada")
        self.label_proceso.setEnabled(True)

def buscarClientes(vectorCedulas,vectorClientes):
    clientesEncontrados=[]
    cedulasNoEncontradas=[]

    for itemCedulas in vectorCedulas:
        count=0
        for itemClientes in vectorClientes:
            try:
                if itemClientes.index(itemCedulas) > 0:
                    clientesEncontrados.append(itemClientes)
                    count+=1
            except ValueError:
                o=0
        if count==0:
            cedulasNoEncontradas.append(itemCedulas)
            
    return clientesEncontrados,cedulasNoEncontradas;        


def lecturaCSV(archivo):
    cedulas =[]
    nombres=[]
    valor=[]

    try:
        with open(archivo, newline='') as File:  
            reader = csv.reader(File)
            for row in reader:
                nombres.append(row[0])
                cedulas.append(row[1])
                # valor.append(row[2])
        nombres.pop(0)
        cedulas.pop(0)
        # valor.pop(0)

        return nombres,cedulas
    except FileNotFoundError:
        print("No se pudo abrir el archivo")
        return nombres,cedulas

def leerArchivo(archivo):
    with open(archivo,newline="") as file:
        read = file.read()
    return read

def buscarIP(vecClientes):
    ips=[]
    vec=[]
    er = "\\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\\b"
    for item in vecClientes:
        # print(item)
    # with open("ips.txt") as archclienteErrorComandoivo:
        found = re.findall(er, item)
        vec.append(found)
    for item in vec:
        for ip in item:
            ips.append(ip)
        
    return ips

def separarClientes(datos):
    vec=[]
    vector=datos.split(";;;")
    i=1
    for i in range(len(vector)):
        vec.append(vector[i])
        
    vec.remove(vec[0])
    return vec

def obtenerClientes(mikrotik):
    command="ip firewall address-list print without-paging where list=clientes_fsd"
    result = subprocess.run(["sh", "./script-ssh.sh", mikrotik.user, mikrotik.password, mikrotik.ip, command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,encoding='utf-8', errors='ignore')
    # print(result.stdout)
    return result.stdout

def activarSuspender(mikrotik,ipSuspender,suspender):
    if suspender==True:
        confirmar="yes"
        command="ip firewall address-list set [find where address={}] disable={}".format(ipSuspender, confirmar)
        # print(command)
        result = subprocess.run(["sh", "./script-ssh.sh", mikrotik.user, mikrotik.password, mikrotik.ip, command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,encoding='utf-8', errors='ignore')
        # print(result.stdout)
        return result.stdout 
    else:
        confirmar="no"
        command="ip firewall address-list set [find where address={}] disable={}".format(ipSuspender, confirmar)
        # print(command)
        result = subprocess.run(["sh", "./script-ssh.sh", mikrotik.user, mikrotik.password, mikrotik.ip, command], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True,encoding='utf-8', errors='ignore')
        # print(result.stdout)
        return result.stdout 


def ClientesSuspendidos(IpsSuspendida, listaTodosClientesEncontrados):
    ClientesSuspendidosVec=[]
    for item in IpsSuspendida:
        for line in listaTodosClientesEncontrados:
            try:
                if line.index(item) >=0:
                    if line[line.index(item):line.index(item)+len(item)+1] == item+" ":
                        print("Ingreso "+line[line.index(item):line.index(item)+len(item)+1:])
                        ClientesSuspendidosVec.append(line)   
            except ValueError:
                o=0
    return ClientesSuspendidosVec

def GuardarArchivosSuspendidos(ClientesSuspendidosVec, vecCedulasNoCoinciden, clienteErrorComando):
    # --------Clientes Suspendidos----------
    text=""
    for line in ClientesSuspendidosVec:
        text=text+line+"\n"
    myfile = Path('ArchivosSuspendidos/clientesSuspendidos.txt')
    myfile.touch(exist_ok=True)
    with open(myfile, 'w') as myfile:
        myfile.write(text)   
    myfile.close()
    #--------Clientes No Coinciden----------
    text=""
    for line in vecCedulasNoCoinciden:
        text=text+line+"\n"
    myfile = Path('ArchivosSuspendidos/clientesQueNoCoinciden.txt')
    myfile.touch(exist_ok=True)
    with open(myfile, 'w') as myfile:
        myfile.write(text)   
    myfile.close()
    
    # --------Clientes con error al ejecutar comando----------
    text=""
    for line in clienteErrorComando:
        text=text+line+"\n"
    myfile = Path('ArchivosSuspendidos/ClientesErrorMikrotik.txt')
    myfile.touch(exist_ok=True)
    with open(myfile, 'w') as myfile:
        myfile.write(text)   
    myfile.close()

def enviarCorreoSuspendidos():
    now = datetime.now()
    now=str(now)

    mail_content = "Hola Compañeros,\nSe informa que la suspensión de clientes se acaba de llevar a cabo, a continuación se adjuntan archivos con los clientes que se han suspendido y cuales presentan algún error. \n"
    sender_address ='suspension.clientes@ottis.com.co'
    sender_pass ='830502580*fsd'
    receiver_address ='programacion@ottis.com.co,direccion.servicio@ottis.com.co,auxiliar.cartera@ottis.com.co,coordinador.egresos@ottis.com.co,gerencia.operativa@ottis.com.co,gerencia@ottis.com.co,mesaservicio@ottis.com.co,back.operativa@ottis.com.co,coordinador.facturacion@ottis.com.co,auxiliar.facturacion@ottis.com.co'#Setup the MIME
    message = MIMEMultipart()
    message['From']= sender_address
    message['To']= receiver_address
    message['Subject']='Suspension de Clientes '+now[0:16] #The subject line#The body and the attachments for the mail
    message.attach(MIMEText(mail_content,'plain4277810'))
    Cc="software.dev@ottis.com.co"

    attach_file_name ='ArchivosSuspendidos/clientesSuspendidos.txt'
    attach_file =open(attach_file_name,'rb')# Open the file as binary mode
    payload =MIMEBase('application','octate-stream')
    payload.set_payload((attach_file).read())

    attach_file_name2 ='ArchivosSuspendidos/clientesQueNoCoinciden.txt'
    attach_file2 =open(attach_file_name2,'rb')# Open the file as binary mode
    payload2 =MIMEBase('application','octate-stream')
    payload2.set_payload((attach_file2).read())

    attach_file_name3 ='ArchivosSuspendidos/ClientesErrorMikrotik.txt'
    attach_file3 =open(attach_file_name3,'rb')# Open the file as binary mode
    payload3 =MIMEBase('application','octate-stream')
    payload3.set_payload((attach_file3).read())
    
    # attach_file_name4 ='ArchivosSuspendidos/clientesPajaritoASuspender.txt'
    # attach_file4 =open(attach_file_name4,'rb')# Open the file as binary mode
    # payload4 =MIMEBase('application','octate-stream')
    # payload4.set_payload((attach_file4).read())

    encoders.encode_base64(payload)#encode the attachment#add payload header with filename
    payload.add_header('Content-Disposition','attachment', filename=attach_file_name)
    encoders.encode_base64(payload2)#encode the attachment#add payload header with filename
    payload2.add_header('Content-Disposition','attachment', filename=attach_file_name2)
    encoders.encode_base64(payload3)#encode the attachment#add payload header with filename
    payload3.add_header('Content-Disposition','attachment', filename=attach_file_name3)
    # encoders.encode_base64(payload4)#encode the attachment#add payload header with filename
    # payload4.add_header('Content-Disposition','attachment', filename=attach_file_name4)

    message.attach(payload)#Create SMTP session for sending the mail
    message.attach(payload2)
    message.attach(payload3)
    # message.attach(payload4)
    session = smtplib.SMTP('mail.ottis.com.co',26)#use gmail with port
    session.starttls()#enable security
    session.login(message['From'], sender_pass)#login with mail_id and password
    text = message.as_string()
    session.sendmail(sender_address, str(message['To']).split(","), text)
    
    session.quit()    

def GuardarArchivosActivos(ClientesSuspendidosVec, vecCedulasNoCoinciden, clienteErrorComando):
    # --------Clientes Suspendidos----------
    text=""
    for line in ClientesSuspendidosVec:
        text=text+line+"\n"
    myfile = Path('ArchivosActivados/clientesActivados.txt')
    myfile.touch(exist_ok=True)
    with open(myfile, 'w') as myfile:
        myfile.write(text)   
    myfile.close()
    #--------Clientes No Coinciden----------
    text=""
    for line in vecCedulasNoCoinciden:
        text=text+line+"\n"
    myfile = Path('ArchivosActivados/clientesQueNoCoinciden.txt')
    myfile.touch(exist_ok=True)
    with open(myfile, 'w') as myfile:
        myfile.write(text)   
    myfile.close()
    
    # --------Clientes con error al ejecutar comando----------
    text=""
    for line in clienteErrorComando:
        text=text+line+"\n"
    myfile = Path('ArchivosActivados/ClientesErrorMikrotik.txt')
    myfile.touch(exist_ok=True)
    with open(myfile, 'w') as myfile:
        myfile.write(text)   
    myfile.close()

def enviarCorreoActivos():
    now = datetime.now()
    now=str(now)

    mail_content = "Hola Compañeros,\nSe informa que la activación de clientes se acaba de llevar a cabo, a continuación se adjuntan archivos con los clientes que se han suspendido y cuales presentan algún error. \n"
    sender_address ='suspension.clientes@ottis.com.co'
    sender_pass ='830502580*fsd'
    receiver_address ='programacion@ottis.com.co,direccion.servicio@ottis.com.co,auxiliar.cartera@ottis.com.co,coordinador.egresos@ottis.com.co,gerencia.operativa@ottis.com.co,gerencia@ottis.com.co,mesaservicio@ottis.com.co,back.operativa@ottis.com.co,coordinador.facturacion@ottis.com.co,auxiliar.facturacion@ottis.com.co'#Setup the MIME
    message = MIMEMultipart()
    message['From']= sender_address
    message['To']= receiver_address
    message['Subject']='Suspension de Clientes '+now[0:16] #The subject line#The body and the attachments for the mail
    message.attach(MIMEText(mail_content,'plain'))

    attach_file_name ='ArchivosActivados/clientesActivados.txt'
    attach_file =open(attach_file_name,'rb')# Open the file as binary mode
    payload =MIMEBase('application','octate-stream')
    payload.set_payload((attach_file).read())

    attach_file_name2 ='ArchivosActivados/clientesQueNoCoinciden.txt'
    attach_file2 =open(attach_file_name2,'rb')# Open the file as binary mode
    payload2 =MIMEBase('application','octate-stream')
    payload2.set_payload((attach_file2).read())

    attach_file_name3 ='ArchivosActivados/ClientesErrorMikrotik.txt'
    attach_file3 =open(attach_file_name3,'rb')# Open the file as binary mode
    payload3 =MIMEBase('application','octate-stream')
    payload3.set_payload((attach_file3).read())
    
    # attach_file_name4 ='ArchivosActivos/clientesPajaritoASuspender.txt'
    # attach_file4 =open(attach_file_name4,'rb')# Open the file as binary mode
    # payload4 =MIMEBase('application','octate-stream')
    # payload4.set_payload((attach_file4).read())

    encoders.encode_base64(payload)#encode the attachment#add payload header with filename
    payload.add_header('Content-Disposition','attachment', filename=attach_file_name)
    encoders.encode_base64(payload2)#encode the attachment#add payload header with filename
    payload2.add_header('Content-Disposition','attachment', filename=attach_file_name2)
    encoders.encode_base64(payload3)#encode the attachment#add payload header with filename
    payload3.add_header('Content-Disposition','attachment', filename=attach_file_name3)
    # encoders.encode_base64(payload4)#encode the attachment#add payload header with filename
    # payload4.add_header('Content-Disposition','attachment', filename=attach_file_name4)

    message.attach(payload)#Create SMTP session for sending the mail
    message.attach(payload2)
    message.attach(payload3)
    # message.attach(payload4)
    session = smtplib.SMTP('mail.ottis.com.co',26)#use gmail with port
    session.starttls()#enable security
    session.login(message['From'], sender_pass)#login with mail_id and password
    text = message.as_string()
    session.sendmail(sender_address, str(message['To']).split(","), text)
    
    session.quit()     
    
if __name__=="__main__":
    print("Ejecutando...")
    app=QtWidgets.QApplication(sys.argv)
    ventana=Principal()

    ventana.show()
    sys.exit(app.exec_())

