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

# Authentication Server
class Servidor_AS:
    def __init__(self):
        self.logger = l.getLogger(__name__)
        l.basicConfig(filename="./log/servidor_AS.log", encoding="utf-8", level=l.INFO, format="%(levelname)s - %(asctime)s: %(message)s")

        self.__NOME_DO_SERVER = ''
        self.__PORTA_DO_SERVER = 6000
        self.__TAM_BUFFER = 2048
        self.__ENDERECO_IP = (self.__NOME_DO_SERVER, self.__PORTA_DO_SERVER)
        self.__clientes = []
        
        self.__chave_cliente = ""
        self.__CHAVE_TGS = self.pesquisar("./data/AS_TGS.txt", "TGS")['senha']
        self.__numero_aleatorio = ri.randint(1000,10000)
        self.__chave_sessao_tgs = r.get_random_bytes(16).hex()
        self.__ticket_tgs = ""

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


    def fechar_conexao(self, cliente_socket : s.socket, endereco : tuple):
        resposta = self.mensagem_recebimento(cliente_socket, endereco).split("-")
        if resposta[0] == "OK":
            self.logger.warning(f"Cliente desconectado: {endereco}")
            self.__clientes.remove(cliente_socket)
            self.mensagem_envio(cliente_socket, endereco, 'OK-8-Desconectado')
            
            os.system('cls' if os.name == 'nt' else 'clear')
            self.titulo()
            print(f"{len(self.__clientes)} cliente(s) conectado(s)...")


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
    
    
    def criptografar(self, payload:str, chave:str) -> str:
        pad = lambda s: s + (AES.block_size - len(s) % AES.block_size) * chr(AES.block_size - len(s) % AES.block_size)
        
        chave = bytes.fromhex(chave)
        payload = b64.b64encode(pad(payload).encode('utf8'))
        iv = r.get_random_bytes(AES.block_size)
        cifra = AES.new(chave, AES.MODE_CFB, iv)
        texto_cripto = b64.b64encode(iv + cifra.encrypt(payload))
        
        iv_2 = r.new().read(AES.block_size)
        aes = AES.new(chave, AES.MODE_CFB, iv_2)
        criptografado = b64.b64encode(iv_2 + aes.encrypt(texto_cripto))
        return criptografado.decode('utf8')


    def descriptografar(self, criptografado:str, chave:str) -> str:
        unpad = lambda s: s[:-ord(s[-1:])]
        
        criptografado = criptografado.encode()
        chave = bytes.fromhex(chave)
        criptografado = b64.b64decode(criptografado)
        iv_2 = criptografado[:AES.block_size]
        aes = AES.new(chave, AES.MODE_CFB, iv_2)
        payload_cripto = b64.b64decode(aes.decrypt(criptografado[AES.block_size:]))
        
        iv = payload_cripto[:AES.block_size]
        cifra = AES.new(chave, AES.MODE_CFB, iv)
        payload = unpad(b64.b64decode(cifra.decrypt(payload_cripto[AES.block_size:])).decode('utf8'))
        return payload


    def verificar(self, cliente_socket:s.socket, endereco:tuple):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.titulo()
        print(f"{len(self.__clientes)} cliente(s) conectado(s)...")
        
        usuario_encontrado = False
        while not usuario_encontrado:
            recebido = self.mensagem_recebimento(cliente_socket, endereco)
            mensagem = j.loads(recebido.replace("'", "\""))
            
            pesquisa = self.pesquisar("./data/servidor_AS.txt", mensagem['usuario'])
            if pesquisa == {}:
                self.mensagem_envio(cliente_socket, endereco, "ERRO-1-Usuário não encontrado")
            else:
                try:
                    dados = self.descriptografar(mensagem['dados'], pesquisa['senha'])
                    dados = j.loads(dados.replace("'", "\""))
                    self.__chave_cliente = pesquisa['senha']
                    self.mensagem_envio(cliente_socket, endereco, "OK-1-Usuário autenticado")
                    usuario_encontrado = True
                except:
                    self.mensagem_envio(cliente_socket, endereco, "ERRO-2-Senha incorreta")
        
        if dados != {}:
            self.__chave_sessao_tgs = r.get_random_bytes(16).hex()
            
            ticket = {"usuario": mensagem['usuario'], 
                      "horario": str(d.datetime.now()), 
                      "tempo_servico": dados['tempo_servico'], 
                      "chave_sessao_tgs": self.__chave_sessao_tgs}
            self.__ticket_tgs = self.criptografar(str(ticket), self.__CHAVE_TGS)
            
            auth_payload = {"chave_sessao_tgs": self.__chave_sessao_tgs, 
                            "horario": str(d.datetime.now()), 
                            "numero_aleatorio": dados['numero_aleatorio']}
            auth_ack = self.criptografar(str(auth_payload), self.__chave_cliente)
            
            envio_final = {"auth": auth_ack, 
                           "ticket": self.__ticket_tgs}
            self.mensagem_envio(cliente_socket, endereco, str(envio_final))
            
        self.fechar_conexao(cliente_socket, endereco)


    def run(self):
        os.system('cls' if os.name == 'nt' else 'clear')
        self.titulo()
        print('Esperando resposta')

        while True:
            cliente_socket, endereco = self.__server_socket.accept()
            self.__clientes.append(cliente_socket)
            thread = th.Thread(target=self.verificar, args=(cliente_socket, endereco), daemon=True)
            thread.start()
        

if __name__ == "__main__":
    server_AS = Servidor_AS()
    server_AS.run()