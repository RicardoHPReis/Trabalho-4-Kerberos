import socket as s
import time as t
import datetime as d
import string as st
import logging as l
import threading as th
import hashlib as h
import base64 as b64
import json as j
from Cryptodome.Cipher import AES
import Cryptodome.Random as r
import Crypto.Random.random as ri
import os

# Authentication Server
class Servidor_AS:
    def __init__(self):
        self.logger = l.getLogger(__name__)
        l.basicConfig(filename="./log/servidor_AS.log", encoding="utf-8", level=l.INFO, format="%(levelname)s - %(asctime)s: %(message)s")

        self.__NOME_DO_SERVER = ''
        self.__PORTA_DO_SERVER = 6000
        self.__TAM_BUFFER = 2048
        self.__ENDERECO_IP = (self.__NOME_DO_SERVER, self.__PORTA_DO_SERVER)
        self.__CHAVE_CLIENTE = h.sha256("oi".encode()).digest()
        self.__CHAVE_ALEATORIA = r.get_random_bytes(16)
        self.__CHAVE_TGS = h.sha256("S0m3MA5T3RK3YY".encode()).digest()
        self.__numero_aleatorio = ri.randint(1000,10000)
        self.__chave_sessao_tgs = ""
        self.__ticket_tgs = ""
        self.__clientes = []

        self.__server_socket = s.socket(s.AF_INET, s.SOCK_STREAM)
        self.__server_socket.bind(self.__ENDERECO_IP)
        self.__server_socket.listen()
        self.__server_socket.settimeout(30)
        self.logger.info(f"Socket do servidor criado na porta: '{self.__PORTA_DO_SERVER}'")
        
    
    def __del__(self):
        self.logger.info(f"Socket finalizado!")
        for cliente in self.__clientes:
            self.cliente.close()
            
        self.__clientes.clear()
        self.__server_socket.close()
        os.system('cls' if os.name == 'nt' else 'clear')
        
    
    def titulo(self):
        print("--------------------")
        print("    SERVIDOR AS")
        print("--------------------\n")


    def mensagem_envio(self, cliente_socket : s.socket, endereco : tuple, mensagem : str):
        try:
            cliente_socket.send(mensagem.encode())
            self.logger.info(f"Destinatário: {endereco} - Enviado:  '{mensagem}'")
        except:
            self.logger.error(f"Cliente removido:  {endereco}")
            self.__clientes.remove(cliente_socket)


    def mensagem_recebimento(self, cliente_socket : s.socket, endereco : tuple):
        try:
            mensagem = cliente_socket.recv(self.__TAM_BUFFER).decode('utf-8')
            self.logger.info(f"Remetente: {endereco} - Recebido: '{mensagem}'")
            return mensagem
        except:
            self.logger.error(f"Cliente removido:  {endereco}")
            self.__clientes.remove(cliente_socket)

    
    def criptografar(self, payload:str, chave:bytes) -> bytes:
        pad = lambda s: s + (AES.block_size - len(s) % AES.block_size) * chr(AES.block_size - len(s) % AES.block_size)
        
        payload = b64.b64encode(pad(payload).encode('utf8'))
        iv = r.get_random_bytes(AES.block_size)
        cifra = AES.new(chave, AES.MODE_CFB, iv)
        texto_cripto = b64.b64encode(iv + cifra.encrypt(payload))
        
        iv_2 = r.new().read(AES.block_size)
        aes = AES.new(chave, AES.MODE_CFB, iv_2)
        criptografado = b64.b64encode(iv_2 + aes.encrypt(texto_cripto))
        return criptografado


    def descriptografar(self, criptografado:bytes, chave:bytes) -> str:
        unpad = lambda s: s[:-ord(s[-1:])]
        
        criptografado = b64.b64decode(criptografado)
        iv_2 = criptografado[:AES.block_size]
        aes = AES.new(chave, AES.MODE_CFB, iv_2)
        texto_cripto = b64.b64decode(aes.decrypt(criptografado[AES.block_size:]))
        
        iv = texto_cripto[:AES.block_size]
        cifra = AES.new(chave, AES.MODE_CFB, iv)
        texto = unpad(b64.b64decode(cifra.decrypt(texto_cripto[AES.block_size:])).decode('utf8'))
        return texto


    def verificar(self, cliente_socket:s.socket, endereco:tuple):
        recebido = self.mensagem_recebimento(cliente_socket, endereco)
        mensagem = j.loads(recebido.replace("'", "\""))
        dados = self.descriptografar(mensagem['dados'].encode(), self.__CHAVE_CLIENTE)
        dados = j.loads(dados.replace("'", "\""))
        
        if dados != {}:
            self.__chave_sessao_tgs = r.get_random_bytes(16)
            
            # TicketGrantingTicket payload
            ticket = {"usuario": mensagem['usuario'], "horario": d.datetime.now(), "tempo_servico": dados['tempo_servico'], "chave_sessao_tgs": self.__chave_sessao_tgs}
            self.__ticket_tgs = self.criptografar(str(ticket), self.__CHAVE_TGS)
            
            # Authentication acknowledgement payload.
            auth_payload = {"chave_sessao_tgs": self.__chave_sessao_tgs, "horario": str(d.datetime.now()), "numero_aleatorio": dados['numero_aleatorio']}
            auth_ack = self.criptografar(str(auth_payload), self.__CHAVE_CLIENTE)
            
            envio_final = {"auth": auth_ack.decode('utf8'), "ticket": self.__ticket_tgs.decode('utf8')}
            self.mensagem_envio(cliente_socket, endereco, str(envio_final))


    def iniciar_servidor(self):
        inicializar = ''
        iniciar_server = False
        while inicializar == '':
            os.system('cls' if os.name == 'nt' else 'clear')
            self.titulo()
            inicializar = input("Deseja inicializar o servidor [S/N] ? ").lower().strip()
            match inicializar:
                case 's':
                    iniciar_server = True
                    self.logger.info("Servidor foi inicializado!")
                case 'sim':
                    iniciar_server = True
                    self.logger.info("Servidor foi inicializado!")
                case 'n':
                    iniciar_server = False
                    self.logger.info("Servidor não foi inicializado!")
                case 'não':
                    iniciar_server = False
                    self.logger.info("Servidor não foi inicializado!")
                case _:
                    print('A escolha precisa estar nas opções acima!')
                    self.logger.warning("Resposta para o servidor não foi aceita!")
                    t.sleep(2)
                    inicializar = ''
        return iniciar_server


    def opcoes_servidor(self, cliente_socket:s.socket, endereco:tuple):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.titulo()
        print(f"{len(self.__clientes)} cliente(s) conectado(s)...")
        
        opcao = 0
        cliente_opcao = self.mensagem_recebimento(cliente_socket, endereco).split("-")
        
        if cliente_opcao[0] == 'OPTION':
            opcao = int(cliente_opcao[1])
            
        match opcao:
            case 1:
                self.verificar(cliente_socket, endereco)
                self.opcoes_servidor(cliente_socket, endereco)
            case 2:
                self.opcoes_servidor(cliente_socket, endereco)
            case 3:
                self.opcoes_servidor(cliente_socket, endereco)
            case 4:
                resposta = self.mensagem_recebimento(cliente_socket, endereco).split("-")
                if resposta[0] == "OK":
                    self.logger.warning(f"Cliente desconectado: {endereco}")
                    self.__clientes.remove(cliente_socket)
                    self.mensagem_envio(cliente_socket, endereco, 'OK-8-Desconectado')
                    
                    os.system('cls' if os.name == 'nt' else 'clear')
                    self.titulo()
                    print(f"{len(self.__clientes)} cliente(s) conectado(s)...")


    def run(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        iniciar_server = self.iniciar_servidor()
        os.system('cls' if os.name == 'nt' else 'clear')
        self.titulo()
        print('Esperando resposta')

        while iniciar_server:
            cliente_socket, endereco = self.__server_socket.accept()
            self.__clientes.append(cliente_socket)
            
            thread = th.Thread(target=self.opcoes_servidor, args=(cliente_socket, endereco), daemon=True)
            thread.start()
        

if __name__ == "__main__":
    server_AS = Servidor_AS()
    server_AS.run()