import socket as s
import time as t
import datetime as d
import string as st
import logging as l
import threading as th
import hashlib as h
from Crypto.Cipher import AES
import Crypto.Random as r
import Crypto.Random.random as ri
from Crypto.Util.Padding import pad, unpad
import os

# Ticket
class Servidor_TGS:
    def __init__(self):
        self.logger = l.getLogger(__name__)
        l.basicConfig(filename="./log/servidor_TGS.log", encoding="utf-8", level=l.INFO, format="%(levelname)s - %(asctime)s: %(message)s")

        self.__NOME_DO_SERVER = ''
        self.__PORTA_DO_SERVER = 7000
        self.__TAM_BUFFER = 2048
        self.__ENDERECO_IP = (self.__NOME_DO_SERVER, self.__PORTA_DO_SERVER)
        self.__CHAVE_AS = self.pesquisar("./data/AS_TGS.txt", "TGS")
        self.__CHAVE_ALEATORIA = r.get_random_bytes(16).hex()
        self.__chave_servico = ""
        self.__tempo_permitido = 0
        self.__numero_aleatorio = ri.randint(1000,10000)
        self.__chave_sessao_servico = ""
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
        print("    SERVIDOR TGS")
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
        
    
    def criptografar(self, cliente_socket:s.socket, endereco:tuple, payload, senha_secreta, vetor_inicial):
        self.mensagem_envio(cliente_socket, endereco, f"{str(payload)} - {senha_secreta} - {vetor_inicial}")
        
        padded_senha_secreta = senha_secreta.ljust((len(senha_secreta) // 16 + 1) * 16).encode('utf8')
        padded_vetor_inicial = vetor_inicial.ljust((len(vetor_inicial) // 16 + 1) * 16).encode('utf8')
        
        cifra = AES.new(padded_senha_secreta, AES.MODE_CFB, padded_vetor_inicial)
        criptografado_payload = cifra.encrypt(str(payload).encode('utf8'))
        self.mensagem_envio(cliente_socket, endereco, str(criptografado_payload.hex()))
        return criptografado_payload.hex()


    def descriptografar(self, cliente_socket:s.socket, endereco:tuple, payload, senha_secreta, vetor_inicial):
        self.mensagem_envio(cliente_socket, endereco, f"{str(payload)} - {senha_secreta} - {vetor_inicial}")
        payload_bytes = bytes.fromhex(payload)
        
        padded_senha_secreta = senha_secreta.ljust((len(senha_secreta) // 16 + 1) * 16).encode('utf8')
        padded_vetor_inicial = vetor_inicial.ljust((len(vetor_inicial) // 16 + 1) * 16).encode('utf8')
        
        cifra = AES.new(padded_senha_secreta, AES.MODE_CFB, padded_vetor_inicial)
        payload_descriptografado = cifra.decrypt(payload_bytes)
        descriptografado_str = payload_descriptografado.decode('utf8').rstrip()
        
        self.mensagem_envio(cliente_socket, endereco, str(descriptografado_str))
        
        return descriptografado_str 


    def verificar(self, cliente_socket:s.socket, endereco:tuple, authenticator, tgt, tgr):
        mensagem = self.mensagem_recebimento(cliente_socket, endereco)
        dados = self.descriptografar(cliente_socket, endereco, mensagem, self.__CHAVE_CLIENTE)
        dados = dict(dados)
        
        service_secret_key = fetched_service.get_secret_key()
        if service_secret_key:
            status, fetched_tgs = self.db.fetch_service("tgs")
            tgs_secret_key = fetched_tgs.get_secret_key()
            if tgs_secret_key:
                ticket_granting_ticket_plain = self.descriptografar(tgt, tgs_secret_key, self.master_key)
                print("Received TGT from Client obtained from Authentication Server")
            else:
                print("Tgs secret key or service not found")

            authenticator_plain = self.descriptografar(authenticator, ticket_granting_ticket_plain.get('tgs_session_key'), self.master_key)

            # compare the username from authenticator as well as tgt
            if authenticator_plain.get('usuario') == ticket_granting_ticket_plain.get('usuario'):
                auth_timestamp = d.datetime.strptime(authenticator_plain.get('timestamp'), "%Y-%m-%d %H:%M:%S.%f")
                tgt_timestamp = d.datetime.strptime(ticket_granting_ticket_plain.get('timestamp'), "%Y-%m-%d %H:%M:%S.%f")
                elapsed_time_in_hours = divmod((auth_timestamp - tgt_timestamp).seconds, 3600)[0]
    
                if True:
                    self.__chave_sessao_servico = ''.join([r.choice(st.ascii_letters + st.digits) for n in range(16)])[0:16]

                    # prepare the service payload for client
                    service_payload = {"usuario": str(authenticator_plain.get('usuario')), 
                                        "servico": str(tgr.get('server_id')),
                                        "timestamp": str(d.datetime.now()), 
                                        "lifetime_of_ticket": "2", 
                                        "service_session_key": str(self.__chave_sessao_servico)}

                    # encrypt the service payload using service_secret_key
                    service_ticket_encrypted = self.criptografar(cliente_socket, endereco, service_payload, dados["Senha"], self.master_key)

                    # prepare the tgs payload for client
                    tgs_ack_payload = {"servico": str(tgr.get('service_id')), 
                                        "horario": str(d.datetime.now()), 
                                        "lifetime_of_ticket": "2", 
                                        "chave_sessao_servico": str(self.__chave_sessao_servico)}
     
                    # encrypt the tgs payload using tgs session key
                    tgs_ack_encrypted = self.criptografar(cliente_socket, endereco, tgs_ack_payload, ticket_granting_ticket_plain.get('tgs_session_key'), self.master_key)

                    print("TGS Ack and Service Ticket sent to client")
                    return 1, {"tgs_ack_ticket": tgs_ack_encrypted, "service_ticket": service_ticket_encrypted}


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
                self.enviar_arquivo(cliente_socket, endereco)
                self.opcoes_servidor(cliente_socket, endereco)
            case 2:
                self.opcoes_servidor(cliente_socket, endereco)
            case 3:
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
    server_TGS = Servidor_TGS()
    server_TGS.run()