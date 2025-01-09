import socket as s
import time as t
import datetime as d
import logging as l
import threading as th
import hashlib as h
import base64 as b64
import json as j
from Cryptodome.Cipher import AES
import Cryptodome.Random as r
import Crypto.Random.random as ri
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
        self.__chave_randomica_AS = ""
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


    def fechar_conexao(self, cliente_socket : s.socket, endereco : tuple):
        resposta = self.mensagem_recebimento(cliente_socket, endereco).split("-")
        if resposta[0] == "OK":
            self.logger.warning(f"Cliente desconectado: {endereco}")
            self.__clientes.remove(cliente_socket)
            self.mensagem_envio(cliente_socket, endereco, 'OK-8-Desconectado')
            
            #os.system('cls' if os.name == 'nt' else 'clear')
            #self.titulo()
            #print(f"{len(self.__clientes)} cliente(s) conectado(s)...")


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
        
    
    def ler_arquivo(self, caminho:str) -> list:
        cabecalho = []
        lista = []
        with open(caminho, 'r') as arquivo:
            for n, linha in enumerate(arquivo):
                registro = linha.replace("\n","").split(' ')
                if n == 0:
                    cabecalho = registro
                    continue
                lista.append(registro)
        
        dicionario = []
        for user in lista:
            dicionario.append(dict(zip(cabecalho, user)))
        
        return dicionario


    def pesquisar(self, caminho:str, texto:str) -> dict:
        lista = self.ler_arquivo(caminho)
        
        for dic in lista:
            for key, value in dic.items():
                if value == texto:
                    return dic
        return {}


    def escrever_arquivo(self, caminho:str, dados:dict) -> None:   
        with open(os.path.join(caminho), "a") as arquivo:
            arquivo.write(' '.join([''.join(i) for i in dados.values()]))
            arquivo.write('\n')
        arquivo.close()
    
    
    def criptografar(self, payload:str, chave:str) -> bytes:
        pad = lambda s: s + (AES.block_size - len(s) % AES.block_size) * chr(AES.block_size - len(s) % AES.block_size)
        
        chave = bytes.fromhex(chave)
        payload = b64.b64encode(pad(payload).encode())
        iv = r.get_random_bytes(AES.block_size)
        cifra = AES.new(chave, AES.MODE_CFB, iv)
        texto_cripto = b64.b64encode(iv + cifra.encrypt(payload))
        
        iv_2 = r.new().read(AES.block_size)
        aes = AES.new(chave, AES.MODE_CFB, iv_2)
        criptografado = b64.b64encode(iv_2 + aes.encrypt(texto_cripto))
        return criptografado


    def descriptografar(self, criptografado:str, chave:str) -> str:
        unpad = lambda s: s[:-ord(s[-1:])]
        
        criptografado = criptografado.encode()
        chave = bytes.fromhex(chave)
        criptografado = b64.b64decode(criptografado)
        iv_2 = criptografado[:AES.block_size]
        aes = AES.new(chave, AES.MODE_CFB, iv_2)
        texto_cripto = b64.b64decode(aes.decrypt(criptografado[AES.block_size:]))
        
        iv = texto_cripto[:AES.block_size]
        cifra = AES.new(chave, AES.MODE_CFB, iv)
        texto = unpad(b64.b64decode(cifra.decrypt(texto_cripto[AES.block_size:])).decode('utf8'))
        return texto


    def verificar(self, cliente_socket:s.socket, endereco:tuple, authenticator, tgt, tgr):
        recebido = self.mensagem_recebimento(cliente_socket, endereco)
        mensagem = j.loads(recebido.replace("'", "\""))
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
                
        self.fechar_conexao(cliente_socket, endereco)


    def run(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        iniciar_server = self.iniciar_servidor()
        os.system('cls' if os.name == 'nt' else 'clear')
        self.titulo()
        print('Esperando resposta')

        while iniciar_server:
            cliente_socket, endereco = self.__server_socket.accept()
            self.__clientes.append(cliente_socket)
            
            thread = th.Thread(target=self.verificar, args=(cliente_socket, endereco), daemon=True)
            thread.start()
        

if __name__ == "__main__":
    server_TGS = Servidor_TGS()
    server_TGS.run()